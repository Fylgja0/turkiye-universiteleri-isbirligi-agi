"""
tests/test_final_analysis.py

Final analiz hattı (30 Ekim 2026 Final Teslimi) modüllerinin birim ve entegrasyon testleri:
1. Topoloji ve bağlantısız ağ LCC ayrımı (test_network_topology)
2. 5 merkeziyet ölçüsü ve Spearman korelasyonu (test_centralities)
3. Güç yasası fiti ve log-likelihood testleri (test_powerlaw_fit)
4. Louvain & Leiden 10-tohum kararlılık analizi (test_community_detection)
5. Null model derece dizisi korunumu ve Z-skorları (test_null_model)
6. Çekim modeli ikili veri seti ve GLM regresyonları (test_gravity_models)
7. Coğrafi iş birliği haritası üretimi (test_collaboration_map)
"""

import os
import tempfile
import pytest
import networkx as nx
import pandas as pd
import numpy as np

from scripts.analysis_metrics import compute_network_topology, compute_centralities
from scripts.analysis_powerlaw import fit_powerlaw_distribution
from scripts.analysis_community import (
    run_louvain_trials,
    run_leiden_trials,
    analyze_communities,
    SEEDS_10
)
from scripts.analysis_null_model import generate_degree_preserving_null_network, run_null_model_experiments
from scripts.analysis_gravity import haversine_distance, build_dyadic_dataset, fit_gravity_models
from scripts.visualize_map import generate_collaboration_map


@pytest.fixture
def sample_graph():
    """Testler için 10 düğümlü, ağırlıklı sentetik bağlı graf oluşturur."""
    G = nx.erdos_renyi_graph(n=10, p=0.4, seed=42)
    # Grafiğin tek bileşen olmasını garantile
    if not nx.is_connected(G):
        components = list(nx.connected_components(G))
        for i in range(len(components) - 1):
            u = list(components[i])[0]
            v = list(components[i + 1])[0]
            G.add_edge(u, v)

    for u, v in G.edges():
        G[u][v]["weight"] = np.random.randint(1, 10)
    return G


@pytest.fixture
def sample_metadata():
    """10 düğüm için sentetik kurum metaverisi."""
    records = []
    cities = ["Istanbul", "Ankara", "Izmir", "Manisa", "Trabzon"]
    for i in range(10):
        records.append({
            "id": i,
            "display_name": f"University {i}",
            "city": cities[i % len(cities)],
            "is_egean": (cities[i % len(cities)] in ["Izmir", "Manisa"]),
            "category": "active_university",
            "period_cs_works_count": 50 + i * 20,
            "latitude": 38.0 + (i * 0.2),
            "longitude": 27.0 + (i * 0.3)
        })
    return pd.DataFrame(records)


def test_network_topology_connected(sample_graph):
    """Bağlantılı grafikte topoloji metriklerini doğrular."""
    topo = compute_network_topology(sample_graph, scope_name="Test Connected")
    assert topo["number_of_nodes"] == 10
    assert topo["number_connected_components"] == 1
    assert topo["is_connected"] is True
    assert topo["number_isolated_nodes"] == 0
    assert topo["full_network_average_path_length"] is not None
    assert topo["full_network_diameter"] is not None
    assert topo["largest_connected_component"]["ratio"] == 1.0


def test_network_topology_disconnected():
    """Bağlantısız ağda tüm ağ ile LCC ayrımını doğrular."""
    G = nx.Graph()
    G.add_nodes_from([1, 2, 3, 4, 5])
    G.add_edge(1, 2)
    G.add_edge(2, 3)
    G.add_edge(1, 3)
    # 4 ve 5 izole
    topo = compute_network_topology(G, scope_name="Test Disconnected")
    assert topo["is_connected"] is False
    assert topo["number_connected_components"] == 3
    assert topo["number_isolated_nodes"] == 2
    assert topo["full_network_average_path_length"] is None
    assert topo["full_network_diameter"] is None
    assert topo["largest_connected_component"]["size"] == 3
    assert topo["largest_connected_component"]["ratio"] == 0.6
    assert topo["largest_connected_component"]["average_shortest_path_length"] > 0


def test_centralities(sample_graph, sample_metadata):
    """5 merkeziyet ölçüsü ve Spearman matrisini doğrular."""
    df_cent, df_top10, corr_matrix = compute_centralities(sample_graph, inst_metadata_df=sample_metadata)
    assert len(df_cent) == 10
    assert "degree" in df_cent.columns
    assert "weighted_degree" in df_cent.columns
    assert "betweenness_centrality" in df_cent.columns
    assert "closeness_centrality" in df_cent.columns
    assert "pagerank" in df_cent.columns

    # Korelasyon matrisi kontrolleri
    assert corr_matrix.shape[0] == corr_matrix.shape[1]
    assert np.allclose(np.diag(corr_matrix), 1.0)


def test_powerlaw_fit():
    """Güç yasası fiti ve karşılaştırma testlerini doğrular."""
    # Sentetik zipf/güç yasası derece dizisi
    degrees = np.random.zipf(a=2.5, size=50).tolist()
    results = fit_powerlaw_distribution(degrees)
    assert "alpha" in results
    assert "xmin" in results
    assert "comparison" in results
    assert "vs_exponential" in results["comparison"]
    assert "vs_lognormal" in results["comparison"]


def test_community_detection_stability(sample_graph, sample_metadata):
    """Louvain ve Leiden 10 tohum kararlılık testlerini doğrular."""
    results = analyze_communities(sample_graph, inst_metadata_df=sample_metadata, seeds=[1, 2, 3])
    summary = results["summary"]
    
    assert "louvain" in summary
    assert "leiden" in summary
    assert 0.0 <= summary["louvain"]["stability"]["nmi_mean"] <= 1.0
    assert 0.0 <= summary["leiden"]["stability"]["ari_mean"] <= 1.0
    assert "membership_df" in results
    assert len(results["membership_df"]) == 10


def test_null_model_degree_preservation(sample_graph):
    """Derece korumalı kenar takasında derece dizisinin tam korunduğunu doğrular."""
    G_null, is_exact = generate_degree_preserving_null_network(
        sample_graph, n_swaps_factor=2, seed=123, ensure_connected=True
    )
    assert is_exact is True
    assert sorted([d for _, d in sample_graph.degree()]) == sorted([d for _, d in G_null.degree()])


def test_null_model_experiments(sample_graph):
    """Null model 5 denemelik sentetik çalıştırmasını doğrular."""
    results = run_null_model_experiments(sample_graph, n_trials=5, base_seed=42)
    assert results["summary"]["successful_null_models"] == 5
    assert results["summary"]["degree_sequence_preserved"] is True
    assert "clustering" in results["summary"]
    assert "shortest_path" in results["summary"]
    assert "small_worldness" in results["summary"]


def test_haversine_distance():
    """Haversine formülünün bilinen şehirler arasındaki mesafesini doğrular."""
    # Istanbul (41.0082, 28.9784) - Ankara (39.9334, 32.8597) ~ 350 km
    dist = haversine_distance(41.0082, 28.9784, 39.9334, 32.8597)
    assert 340.0 < dist < 360.0
    # Sıfır mesafe aynı nokta
    assert haversine_distance(41.0, 29.0, 41.0, 29.0) == 0.0


def test_gravity_dyadic_dataset_and_glm(sample_graph, sample_metadata):
    """İkili veri seti kurulumu, sıfır mesafesi ve GLM modellerini doğrular."""
    df_dyads, audit = build_dyadic_dataset(sample_graph, sample_metadata, intra_city_offset_km=1.0)
    expected_pairs = 10 * 9 // 2  # 45 çift
    assert len(df_dyads) == expected_pairs
    assert audit["total_theoretical_pairs"] == expected_pairs
    assert "collab_count" in df_dyads.columns
    assert "log_distance" in df_dyads.columns
    assert "both_egean" in df_dyads.columns

    # GLM Modelleri
    models = fit_gravity_models(df_dyads)
    assert "poisson_model" in models
    assert "negative_binomial_model" in models
    assert "synthesis" in models
    assert "parameters" in models["poisson_model"]
    assert "log_distance" in models["poisson_model"]["parameters"]


def test_collaboration_map_generation(sample_graph, sample_metadata):
    """Folium haritasının oluşturulduğunu ve HTML dosyasının üretildiğini doğrular."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_html = os.path.join(tmpdir, "test_map.html")
        m = generate_collaboration_map(
            sample_graph, sample_metadata, output_html_path=out_html, edge_weight_threshold=1
        )
        assert os.path.exists(out_html)
        assert os.path.getsize(out_html) > 1000
