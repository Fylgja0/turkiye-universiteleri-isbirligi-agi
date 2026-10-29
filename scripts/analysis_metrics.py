"""
scripts/analysis_metrics.py

Temel ağ ölçüleri ve merkeziyet analizleri modülü:
- Düğüm ve kenar sayıları, yoğunluk, bağlı bileşenler ve izole düğümler.
- Ortalama en kısa yol uzunluğu ve ağ çapı (bağlantısız ağlarda dev bağlı bileşen ayrımı).
- Ortalama kümelenme katsayısı ve derece benzeşimi (degree assortativity).
- Degree, weighted degree (strength), betweenness, closeness ve PageRank merkeziyetleri.
- İlk 10 kurum karşılaştırma tablosu ve merkeziyetler arası Spearman sıra korelasyonu.
"""

import os
import json
import logging
from typing import Dict, Any, Tuple, List, Optional
import networkx as nx
import pandas as pd
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


def compute_network_topology(G: nx.Graph, scope_name: str = "Scope B1") -> Dict[str, Any]:
    """
    Belirtilen graf için genel topolojik ağ ölçülerini hesaplar.
    Ağ bağlantısızsa tüm ağ ile en büyük bağlı bileşenin (LCC)
    ölçülerini açıkça birbirinden ayırır.
    """
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    density = float(nx.density(G)) if num_nodes > 1 else 0.0
    num_components = nx.number_connected_components(G) if num_nodes > 0 else 0
    isolates = list(nx.isolates(G))
    num_isolates = len(isolates)

    # Derece dizisi
    degrees = [d for _, d in G.degree()]
    avg_degree = float(np.mean(degrees)) if degrees else 0.0

    # Kümelenme ve Benzeşim
    avg_clustering = float(nx.average_clustering(G)) if num_nodes > 0 else 0.0
    try:
        assortativity = float(nx.degree_assortativity_coefficient(G))
    except Exception as e:
        logger.warning(f"Derece benzeşimi hesaplanamadı: {e}")
        assortativity = float("nan")

    # En büyük bağlı bileşen (LCC)
    if num_nodes > 0 and num_components > 0:
        lcc_nodes = max(nx.connected_components(G), key=len)
        G_lcc = G.subgraph(lcc_nodes).copy()
        lcc_size = len(lcc_nodes)
        lcc_ratio = float(lcc_size / num_nodes)
        
        # LCC yolu ve çapı
        if lcc_size > 1:
            lcc_avg_path = float(nx.average_shortest_path_length(G_lcc))
            lcc_diameter = int(nx.diameter(G_lcc))
        else:
            lcc_avg_path = 0.0
            lcc_diameter = 0
    else:
        lcc_size = 0
        lcc_ratio = 0.0
        lcc_avg_path = 0.0
        lcc_diameter = 0

    # Tüm ağ bağlantılı mı?
    is_connected = nx.is_connected(G) if num_nodes > 0 else False
    if is_connected and num_nodes > 1:
        full_avg_path = float(nx.average_shortest_path_length(G))
        full_diameter = int(nx.diameter(G))
    else:
        full_avg_path = None  # Bağlantısız ağlarda ortalama yol sonsuzdur / tanımsızdır
        full_diameter = None

    metrics = {
        "scope_name": scope_name,
        "number_of_nodes": num_nodes,
        "number_of_edges": num_edges,
        "density": density,
        "average_degree": avg_degree,
        "average_clustering_coefficient": avg_clustering,
        "degree_assortativity": assortativity,
        "number_connected_components": num_components,
        "number_isolated_nodes": num_isolates,
        "isolated_node_ids": isolates,
        "is_connected": is_connected,
        "full_network_average_path_length": full_avg_path,
        "full_network_diameter": full_diameter,
        "largest_connected_component": {
            "size": lcc_size,
            "ratio": lcc_ratio,
            "average_shortest_path_length": lcc_avg_path,
            "diameter": lcc_diameter
        }
    }
    return metrics


def compute_centralities(G: nx.Graph, inst_metadata_df: Optional[pd.DataFrame] = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Ağdaki tüm düğümler için 5 farklı merkeziyet metriğini hesaplar:
    1. Degree Centrality (k_i normalized)
    2. Weighted Degree / Strength (s_i, toplam ortak yayın hacmi)
    3. Betweenness Centrality (aradalık)
    4. Closeness Centrality (yakınlık)
    5. PageRank (ağırlıklı, alpha=0.85)

    Dönüş:
    - full_centralities_df: Tüm kurumların merkeziyet metrikleri
    - top10_comparison_df: Her metriğe göre ilk 10 kurumun karşılaştırması
    - spearman_corr_df: Merkeziyet ölçüleri arası Spearman sıra korelasyon matrisi
    """
    deg_cent = nx.degree_centrality(G)
    w_deg = dict(G.degree(weight="weight"))
    raw_deg = dict(G.degree())
    bet_cent = nx.betweenness_centrality(G, normalized=True)
    clo_cent = nx.closeness_centrality(G)
    pagerank = nx.pagerank(G, alpha=0.85, weight="weight")

    records = []
    meta_dict = {}
    if inst_metadata_df is not None:
        for _, row in inst_metadata_df.iterrows():
            meta_dict[row["id"]] = row.to_dict()

    for node_id in G.nodes():
        meta = meta_dict.get(node_id, {})
        records.append({
            "id": node_id,
            "display_name": meta.get("display_name", node_id),
            "city": meta.get("city", ""),
            "is_egean": meta.get("is_egean", False),
            "category": meta.get("category", ""),
            "period_cs_works_count": meta.get("period_cs_works_count", 0),
            "degree": raw_deg.get(node_id, 0),
            "degree_centrality": deg_cent.get(node_id, 0.0),
            "weighted_degree": w_deg.get(node_id, 0),
            "betweenness_centrality": bet_cent.get(node_id, 0.0),
            "closeness_centrality": clo_cent.get(node_id, 0.0),
            "pagerank": pagerank.get(node_id, 0.0)
        })

    df = pd.DataFrame(records)

    # Spearman Korelasyon Matrisi
    metric_cols = [
        "degree",
        "weighted_degree",
        "betweenness_centrality",
        "closeness_centrality",
        "pagerank",
        "period_cs_works_count"
    ]
    corr_matrix = df[metric_cols].corr(method="spearman")

    # İlk 10 Karşılaştırma Tablosu:
    # Her merkeziyete göre ilk 10'u bir araya getir
    top10_dfs = []
    for col in ["degree", "weighted_degree", "betweenness_centrality", "closeness_centrality", "pagerank"]:
        top_k = df.sort_values(by=col, ascending=False).head(10).reset_index(drop=True)
        top_k["rank"] = range(1, 11)
        top_k["metric"] = col
        top_k["metric_value"] = top_k[col]
        top10_dfs.append(top_k[["metric", "rank", "id", "display_name", "city", "metric_value", "period_cs_works_count"]])

    top10_df = pd.concat(top10_dfs, ignore_index=True)

    return df, top10_df, corr_matrix
