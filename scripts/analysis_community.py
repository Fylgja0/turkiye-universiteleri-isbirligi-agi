"""
scripts/analysis_community.py

Topluluk tespiti ve kararlılık analizi modülü:
- Louvain (NetworkX) ve Leiden (igraph & leidenalg) algoritmaları.
- Ağırlıklı kenarlar ('weight') üzerinde uyumlu optimizasyon.
- 10 farklı sabit tohum (seed) ile tekrarlanabilir çalıştırma.
- NMI (Normalized Mutual Information) ve ARI (Adjusted Rand Index) ile kararlılık analizi.
- En büyük toplulukların kurum dökümü, hub'ları ve yapısal özellikleri.
"""

import itertools
import logging
from typing import Dict, Any, List, Tuple, Optional
import networkx as nx
import pandas as pd
import numpy as np
from sklearn.metrics import normalized_mutual_info_score, adjusted_rand_score
import igraph as ig
import leidenalg

logger = logging.getLogger(__name__)

SEEDS_10 = [42, 101, 2024, 7, 1923, 999, 12345, 54321, 888, 2026]


def nx_to_igraph(G: nx.Graph) -> Tuple[ig.Graph, Dict[int, str], Dict[str, int]]:
    """NetworkX grafiğini düğüm sırasını ve kenar ağırlıklarını koruyarak igraph nesnesine dönüştürür."""
    nodes = list(G.nodes())
    node_to_idx = {n: i for i, n in enumerate(nodes)}
    idx_to_node = {i: n for i, n in enumerate(nodes)}

    edges = []
    weights = []
    for u, v, d in G.edges(data=True):
        edges.append((node_to_idx[u], node_to_idx[v]))
        weights.append(float(d.get("weight", 1.0)))

    ig_G = ig.Graph(n=len(nodes), edges=edges, directed=False)
    ig_G.es["weight"] = weights
    ig_G.vs["name"] = nodes
    return ig_G, idx_to_node, node_to_idx


def run_louvain_trials(G: nx.Graph, seeds: List[int] = SEEDS_10) -> List[Dict[str, Any]]:
    """NetworkX Louvain algoritmasını belirtilen tohumlarla çalıştırır."""
    trials = []
    nodes = sorted(list(G.nodes()))

    for s in seeds:
        communities = nx.community.louvain_communities(G, weight="weight", seed=s, resolution=1.0)
        # Toplulukları boyuta göre sırala
        sorted_comms = sorted(communities, key=len, reverse=True)
        modularity = nx.community.modularity(G, sorted_comms, weight="weight")

        # Üyelik sözlüğü ve listesi
        node_comm_map = {}
        for c_idx, comm in enumerate(sorted_comms):
            for node in comm:
                node_comm_map[node] = c_idx

        membership_vector = [node_comm_map[n] for n in nodes]

        trials.append({
            "seed": s,
            "algorithm": "louvain",
            "num_communities": len(sorted_comms),
            "modularity": float(modularity),
            "communities": sorted_comms,
            "membership_dict": node_comm_map,
            "membership_vector": membership_vector
        })
    return trials


def run_leiden_trials(G: nx.Graph, seeds: List[int] = SEEDS_10) -> List[Dict[str, Any]]:
    """igraph ve leidenalg ile Leiden algoritmasını belirtilen tohumlarla çalıştırır."""
    ig_G, idx_to_node, node_to_idx = nx_to_igraph(G)
    nodes = sorted(list(G.nodes()))
    trials = []

    for s in seeds:
        partition = leidenalg.find_partition(
            ig_G,
            leidenalg.ModularityVertexPartition,
            weights="weight",
            seed=s,
            n_iterations=-1
        )

        modularity = float(partition.modularity)
        
        # Toplulukları ayrıştır
        cluster_dict = {}
        for v_idx, c_id in enumerate(partition.membership):
            node_name = idx_to_node[v_idx]
            cluster_dict.setdefault(c_id, []).append(node_name)

        # Boyuta göre yeniden sırala
        sorted_comms = sorted(cluster_dict.values(), key=len, reverse=True)
        node_comm_map = {}
        for c_idx, comm in enumerate(sorted_comms):
            for node in comm:
                node_comm_map[node] = c_idx

        membership_vector = [node_comm_map[n] for n in nodes]

        trials.append({
            "seed": s,
            "algorithm": "leiden",
            "num_communities": len(sorted_comms),
            "modularity": modularity,
            "communities": sorted_comms,
            "membership_dict": node_comm_map,
            "membership_vector": membership_vector
        })
    return trials


def compute_stability_metrics(trials: List[Dict[str, Any]]) -> Dict[str, float]:
    """10 deneme arasındaki tüm ikili çiftlerin NMI ve ARI değerlerini hesaplar."""
    nmi_list = []
    ari_list = []

    for t1, t2 in itertools.combinations(trials, 2):
        v1 = t1["membership_vector"]
        v2 = t2["membership_vector"]
        nmi = normalized_mutual_info_score(v1, v2)
        ari = adjusted_rand_score(v1, v2)
        nmi_list.append(nmi)
        ari_list.append(ari)

    return {
        "nmi_mean": float(np.mean(nmi_list)) if nmi_list else 1.0,
        "nmi_std": float(np.std(nmi_list)) if nmi_list else 0.0,
        "ari_mean": float(np.mean(ari_list)) if ari_list else 1.0,
        "ari_std": float(np.std(ari_list)) if ari_list else 0.0
    }


def analyze_communities(
    G: nx.Graph,
    inst_metadata_df: Optional[pd.DataFrame] = None,
    seeds: List[int] = SEEDS_10
) -> Dict[str, Any]:
    """
    Louvain ve Leiden algoritmalarını çalıştırır, kararlılıklarını hesaplar
    ve en belirgin topluluk profillerini çıkarır.
    """
    louvain_trials = run_louvain_trials(G, seeds=seeds)
    leiden_trials = run_leiden_trials(G, seeds=seeds)

    louvain_stability = compute_stability_metrics(louvain_trials)
    leiden_stability = compute_stability_metrics(leiden_trials)

    # İki algoritma arasındaki mutabakat (örneğin seed=42'de Louvain vs Leiden)
    cross_nmi = float(normalized_mutual_info_score(
        louvain_trials[0]["membership_vector"],
        leiden_trials[0]["membership_vector"]
    ))
    cross_ari = float(adjusted_rand_score(
        louvain_trials[0]["membership_vector"],
        leiden_trials[0]["membership_vector"]
    ))

    # Temsili bölümleme olarak ilk tohumun (seed=42) sonuçlarını al
    rep_louvain = louvain_trials[0]
    rep_leiden = leiden_trials[0]

    # Kurum üstverisi sözlüğü
    meta_dict = {}
    if inst_metadata_df is not None:
        for _, r in inst_metadata_df.iterrows():
            meta_dict[r["id"]] = r.to_dict()

    # Üyelik DataFrame'i
    nodes = sorted(list(G.nodes()))
    membership_records = []
    for n in nodes:
        meta = meta_dict.get(n, {})
        membership_records.append({
            "id": n,
            "display_name": meta.get("display_name", n),
            "city": meta.get("city", ""),
            "is_egean": meta.get("is_egean", False),
            "period_cs_works_count": meta.get("period_cs_works_count", 0),
            "degree": G.degree(n),
            "weighted_degree": G.degree(n, weight="weight"),
            "louvain_community": rep_louvain["membership_dict"].get(n, -1),
            "leiden_community": rep_leiden["membership_dict"].get(n, -1)
        })
    df_membership = pd.DataFrame(membership_records)

    # En büyük toplulukların dökümü (Louvain seed=42)
    top_cluster_records = []
    for c_id, comm in enumerate(rep_louvain["communities"][:5]):
        sub_g = G.subgraph(comm)
        internal_weight = sum(d.get("weight", 1) for _, _, d in sub_g.edges(data=True))
        
        # En yüksek dereceye sahip merkez kurumlar (Hubs)
        hubs = sorted(comm, key=lambda n: G.degree(n), reverse=True)[:3]
        hub_names = [meta_dict.get(h, {}).get("display_name", h) for h in hubs]
        
        # Ege kurum sayısı
        egean_in_c = sum(1 for n in comm if meta_dict.get(n, {}).get("is_egean", False))
        
        top_cluster_records.append({
            "community_id": c_id,
            "size": len(comm),
            "ratio": float(len(comm) / len(nodes)),
            "internal_edge_weight": int(internal_weight),
            "egean_institutions_count": egean_in_c,
            "top_hub_institutions": ", ".join(hub_names),
            "member_sample": ", ".join([meta_dict.get(n, {}).get("display_name", n) for n in list(comm)[:5]])
        })
    df_top_clusters = pd.DataFrame(top_cluster_records)

    summary = {
        "louvain": {
            "num_communities_mean": float(np.mean([t["num_communities"] for t in louvain_trials])),
            "modularity_mean": float(np.mean([t["modularity"] for t in louvain_trials])),
            "modularity_std": float(np.std([t["modularity"] for t in louvain_trials])),
            "stability": louvain_stability,
            "trials_summary": [{"seed": t["seed"], "k": t["num_communities"], "modularity": t["modularity"]} for t in louvain_trials]
        },
        "leiden": {
            "num_communities_mean": float(np.mean([t["num_communities"] for t in leiden_trials])),
            "modularity_mean": float(np.mean([t["modularity"] for t in leiden_trials])),
            "modularity_std": float(np.std([t["modularity"] for t in leiden_trials])),
            "stability": leiden_stability,
            "trials_summary": [{"seed": t["seed"], "k": t["num_communities"], "modularity": t["modularity"]} for t in leiden_trials]
        },
        "cross_algorithm_agreement": {
            "nmi": cross_nmi,
            "ari": cross_ari,
            "notes": "Louvain ve Leiden (seed=42) arasındaki NMI ve ARI mutabakatı."
        }
    }

    return {
        "summary": summary,
        "membership_df": df_membership,
        "top_clusters_df": df_top_clusters
    }
