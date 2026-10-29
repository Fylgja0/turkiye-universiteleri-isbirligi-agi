"""
scripts/analysis_null_model.py

Null Model (Derece Korumalı Rastgele Ağlar) analiz modülü:
- Düğümlerin tam derece dizisini koruyan (degree-preserving rewiring: double edge swap)
  basit ve yönsüz rastgele ağların üretilmesi.
- Derece dizisinin kesinlikle korunduğunun doğrulanması.
- En az 100 geçerli rastgele ağ üzerinden:
  * Ortalama kümelenme katsayısı (C)
  * Ortalama en kısa yol uzunluğu (L)
  * Louvain modülerliği (Q)
- Gözlenen değer (Observed), Null ortalaması, standart sapma, Z-skoru, ampirik p-değeri ve
  Küçük Dünya (Small-Worldness) katsayısının (sigma) hesaplanması.
"""

import copy
import random
import logging
from typing import Dict, Any, List, Tuple, Optional
import networkx as nx
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def generate_degree_preserving_null_network(
    G: nx.Graph,
    n_swaps_factor: int = 5,
    max_tries_factor: int = 25,
    seed: int = 42,
    ensure_connected: bool = True
) -> Tuple[Optional[nx.Graph], bool]:
    """
    Verilen grafiğin derece dizisini koruyarak kenar takası (double edge swap) yapar.
    ensure_connected=True ise sonucun bağlı olduğunu garantiler.
    """
    G_null = G.copy()
    num_edges = G_null.number_of_edges()
    nswap = num_edges * n_swaps_factor
    max_tries = num_edges * max_tries_factor

    # Rastgele tohumu ayarla
    random.seed(seed)

    try:
        if ensure_connected and nx.is_connected(G):
            # Bağlantılılığı koruyarak takas yap
            nx.connected_double_edge_swap(G_null, nswap=nswap, seed=seed)
        else:
            nx.double_edge_swap(G_null, nswap=nswap, max_tries=max_tries, seed=seed)

        # Doğrulama: Derece dizisi tam korunmuş mu?
        orig_deg = sorted([d for _, d in G.degree()])
        null_deg = sorted([d for _, d in G_null.degree()])
        is_exact_degree = (orig_deg == null_deg)
        
        return G_null, is_exact_degree
    except Exception as e:
        logger.warning(f"Seed {seed} ile null ağ üretilemedi: {e}")
        return None, False


def run_null_model_experiments(
    G: nx.Graph,
    n_trials: int = 100,
    base_seed: int = 1000
) -> Dict[str, Any]:
    """
    Gözlenen ağın kenar ağırlıklarını taşımayan basit, ağırlıksız topolojik grafiğini oluşturur
    ve tam derece dizisini koruyan n_trials (varsayılan 100) rastgele ağ üreterek
    ampirik topoloji ile kümelenme (C), en kısa yol (L) ve modülerlik (Q) metriklerini karşılaştırır.
    """
    if G.number_of_nodes() == 0:
        raise ValueError("Boş grafik üzerinde null model çalıştırılamaz.")

    # 1. Gözlenen grafiği ağırlıksız topolojik basit grafiğe dönüştür
    G_unweighted = nx.Graph()
    G_unweighted.add_nodes_from(G.nodes(data=True))
    G_unweighted.add_edges_from(G.edges())

    # Gözlenen Değerler (Observed - Tamamı ağırlıksız topolojik)
    is_connected = nx.is_connected(G_unweighted)
    c_obs = float(nx.average_clustering(G_unweighted))
    
    if is_connected:
        l_obs = float(nx.average_shortest_path_length(G_unweighted))
    else:
        # Bağlantısızsa LCC üzerinden
        lcc = max(nx.connected_components(G_unweighted), key=len)
        l_obs = float(nx.average_shortest_path_length(G_unweighted.subgraph(lcc)))

    # Gözlenen Louvain modülerliği (ağırlıksız topoloji: weight=None)
    comms_obs = nx.community.louvain_communities(G_unweighted, weight=None, seed=42)
    q_obs = float(nx.community.modularity(G_unweighted, comms_obs, weight=None))

    null_c_list = []
    null_l_list = []
    null_q_list = []

    successful_trials = 0
    failed_trials = 0

    logger.info(f"{n_trials} adet ağırlıksız ve derece korumalı null model ağı üretiliyor...")

    trial_idx = 0
    while successful_trials < n_trials and trial_idx < n_trials * 3:
        seed = base_seed + trial_idx
        trial_idx += 1

        G_null, deg_preserved = generate_degree_preserving_null_network(
            G_unweighted,
            n_swaps_factor=5,
            seed=seed,
            ensure_connected=is_connected
        )

        if G_null is None or not deg_preserved:
            failed_trials += 1
            continue

        c_null = float(nx.average_clustering(G_null))

        if is_connected:
            l_null = float(nx.average_shortest_path_length(G_null))
        else:
            lcc_null = max(nx.connected_components(G_null), key=len)
            l_null = float(nx.average_shortest_path_length(G_null.subgraph(lcc_null)))

        # Null modülerlik: weight=None ile
        comms_null = nx.community.louvain_communities(G_null, weight=None, seed=seed)
        q_null = float(nx.community.modularity(G_null, comms_null, weight=None))

        null_c_list.append(c_null)
        null_l_list.append(l_null)
        null_q_list.append(q_null)
        successful_trials += 1

    # İstatistiksel metriklerin ve ampirik p-değerlerinin hesaplanması
    def calc_stats(obs_val: float, null_vals: List[float], alternative: str = "right") -> Dict[str, Any]:
        arr = np.array(null_vals)
        mean_val = float(np.mean(arr))
        std_val = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
        z_score = float((obs_val - mean_val) / std_val) if std_val > 0 else 0.0
        
        # Monte Carlo ampirik p-değeri formülü: p = (r + 1) / (B + 1)
        if alternative == "right":
            # Yüksek değer alternatifi (H1: obs > null)
            p_val = float((np.sum(arr >= obs_val) + 1) / (len(arr) + 1))
            test_desc = "right-tailed (H1: obs > null, p = [count(null >= obs) + 1] / [B + 1])"
        elif alternative == "left":
            # Düşük değer alternatifi (H1: obs < null)
            p_val = float((np.sum(arr <= obs_val) + 1) / (len(arr) + 1))
            test_desc = "left-tailed (H1: obs < null, p = [count(null <= obs) + 1] / [B + 1])"
        else:
            # İki yönlü alternatif (H1: obs != null)
            p_left = (np.sum(arr <= obs_val) + 1) / (len(arr) + 1)
            p_right = (np.sum(arr >= obs_val) + 1) / (len(arr) + 1)
            p_val = float(min(1.0, 2.0 * min(p_left, p_right)))
            test_desc = "two-tailed (H1: obs != null, p = min(1.0, 2 * min(p_left, p_right)))"

        return {
            "observed": obs_val,
            "null_mean": mean_val,
            "null_std": std_val,
            "z_score": z_score,
            "empirical_p_value": p_val,
            "test_direction": test_desc
        }

    clustering_stats = calc_stats(c_obs, null_c_list, alternative="right")
    path_stats = calc_stats(l_obs, null_l_list, alternative="two-sided")
    modularity_stats = calc_stats(q_obs, null_q_list, alternative="right")

    # Küçük Dünya (Small-Worldness) Katsayısı: sigma = (C / C_null) / (L / L_null)
    gamma = c_obs / clustering_stats["null_mean"] if clustering_stats["null_mean"] > 0 else 0.0
    lambda_val = l_obs / path_stats["null_mean"] if path_stats["null_mean"] > 0 else 0.0
    small_worldness_sigma = float(gamma / lambda_val) if lambda_val > 0 else 0.0

    comparison_table = [
        {"metric": "Average Clustering Coefficient (C)", **clustering_stats},
        {"metric": "Average Shortest Path Length (L)", **path_stats},
        {"metric": "Louvain Modularity (Q)", **modularity_stats}
    ]
    df_comparison = pd.DataFrame(comparison_table)

    summary = {
        "model_type": "Unweighted topological degree-preserving random graphs (connected double edge swap)",
        "successful_null_models": successful_trials,
        "failed_trials": failed_trials,
        "clustering": clustering_stats,
        "shortest_path": path_stats,
        "modularity": modularity_stats,
        "small_worldness": {
            "gamma (C/C_null)": float(gamma),
            "lambda (L/L_null)": float(lambda_val),
            "sigma": small_worldness_sigma,
            "is_small_world": bool(small_worldness_sigma > 1.0)
        },
        "degree_sequence_preserved": True
    }

    return {
        "summary": summary,
        "comparison_df": df_comparison,
        "null_samples": {
            "clustering": null_c_list,
            "shortest_path": null_l_list,
            "modularity": null_q_list
        }
    }
