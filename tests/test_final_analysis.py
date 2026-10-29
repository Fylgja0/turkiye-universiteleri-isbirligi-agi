"""
tests/test_final_analysis.py

Final analiz hattı (30 Ekim 2026 Final Teslimi) modüllerinin birim ve entegrasyon testleri:
1. Topoloji ve bağlantısız ağ LCC ayrımı (test_network_topology_connected, test_network_topology_disconnected)
2. 5 merkeziyet ölçüsü ve Spearman korelasyonu (test_centralities)
3. Güç yasası fiti ve sabit tohumlu dağılım testleri (test_powerlaw_fit)
4. Louvain ve Leiden 10-tohum kararlılık ve Leiden ortak modülerlik doğrulaması (test_community_detection_stability, test_leiden_common_modularity_matches_exported_memberships)
5. Ağırlıksız null model derece korunumu, bağlantılılık ve ampirik p-değeri hesabı (test_null_model_degree_and_connectivity_preservation, test_null_model_unweighted_and_p_value_consistency)
6. Çekim modeli ikili veri seti, MLE alfa tahmini, esas model sentezi katsayı eşleşmesi (test_gravity_dyadic_dataset, test_gravity_mle_alpha_and_synthesis_consistency)
7. Coğrafi iş birliği haritası üretimi (test_collaboration_map_generation)
"""

import os
import tempfile
import pytest
import networkx as nx
import pandas as pd
import numpy as np
from sklearn.metrics import adjusted_rand_score

import leidenalg

from scripts.analysis_metrics import compute_network_topology, compute_centralities
from scripts.analysis_powerlaw import fit_powerlaw_distribution
from scripts.analysis_community import (
    nx_to_igraph,
    run_louvain_trials,
    run_leiden_trials,
    analyze_communities,
    SEEDS_10
)
from scripts.analysis_null_model import (
    generate_degree_preserving_null_network,
    run_null_model_experiments
)
from scripts.analysis_gravity import (
    haversine_distance,
    build_dyadic_dataset,
    fit_gravity_models
)
from scripts.visualize_map import generate_collaboration_map


@pytest.fixture
def sample_graph():
    """Testler için 10 düğümlü, deterministik tohumlu ağırlıklı sentetik bağlı graf oluşturur."""
    np.random.seed(42)
    G = nx.erdos_renyi_graph(n=10, p=0.45, seed=42)
    # Grafiğin tek bileşen olmasını garantile
    if not nx.is_connected(G):
        components = list(nx.connected_components(G))
        for i in range(len(components) - 1):
            u = list(components[i])[0]
            v = list(components[i + 1])[0]
            G.add_edge(u, v)

    # Kenarlara deterministik ağırlıklar ata
    weights = [3, 1, 5, 2, 7, 4, 2, 6, 8, 3, 1, 4, 5, 2, 6, 9, 3, 1, 4, 2]
    for idx, (u, v) in enumerate(G.edges()):
        G[u][v]["weight"] = weights[idx % len(weights)]
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
    """Sabit tohumlu sentetik dizide güç yasası fiti ve karşılaştırma testlerini doğrular."""
    np.random.seed(42)
    degrees = np.random.zipf(a=2.5, size=60).tolist()
    results = fit_powerlaw_distribution(degrees)
    assert "alpha" in results
    assert "xmin" in results
    assert "comparison" in results
    assert "vs_exponential" in results["comparison"]
    assert "vs_lognormal" in results["comparison"]
    assert results["alpha"] > 1.0


def test_community_detection_stability(sample_graph, sample_metadata):
    """Louvain ve Leiden çoklu tohum kararlılık testlerini doğrular."""
    results = analyze_communities(sample_graph, inst_metadata_df=sample_metadata, seeds=[42, 101, 7])
    summary = results["summary"]
    
    assert "louvain" in summary
    assert "leiden" in summary
    assert 0.0 <= summary["louvain"]["stability"]["nmi_mean"] <= 1.0
    assert 0.0 <= summary["leiden"]["stability"]["ari_mean"] <= 1.0
    assert "raw_partition_modularity_mean" in summary["leiden"]
    assert "membership_df" in results
    assert len(results["membership_df"]) == 10


def test_leiden_weights_differentiate_partition():
    """
    Sentetik bir ağ üzerinde ağırlıklı Leiden'ın kenar ağırlıklarını gerçekten
    kullandığını ve ağırlıksız bölüntüden kesinlikle farklılaştığını kanıtlar.
    Ayrıca partition.quality() ile NetworkX ağırlıklı modülerliğin birebir eşitliğini doğrular.
    """
    # 6 düğümlü sentetik graf: iki güçlü 3'lü klik ve aralarında zayıf kenarlar
    G = nx.Graph()
    G.add_edge(0, 1, weight=10.0)
    G.add_edge(1, 2, weight=10.0)
    G.add_edge(0, 2, weight=10.0)
    G.add_edge(3, 4, weight=10.0)
    G.add_edge(4, 5, weight=10.0)
    G.add_edge(3, 5, weight=10.0)
    # Ağırlıksız bakıldığında onları birbirine yaklaştıran zayıf çapraz kenarlar
    G.add_edge(0, 3, weight=0.1)
    G.add_edge(1, 4, weight=0.1)
    G.add_edge(2, 5, weight=0.1)
    G.add_edge(0, 4, weight=0.1)
    G.add_edge(1, 5, weight=0.1)

    ig_G, idx_to_n, _ = nx_to_igraph(G)
    
    # 1. Ağırlıklı Leiden
    part_w = leidenalg.find_partition(
        ig_G,
        leidenalg.ModularityVertexPartition,
        weights=list(ig_G.es["weight"]),
        seed=42
    )
    # 2. Ağırlıksız Leiden
    part_unw = leidenalg.find_partition(
        ig_G,
        leidenalg.ModularityVertexPartition,
        weights=None,
        seed=42
    )

    # Bölümlemeleri kanonik topluluk kümeleri (frozenset kümeleri) olarak çıkar (etiket permutasyonundan bağımsız)
    def get_canonical_communities(membership):
        c_dict = {}
        for idx, comm_id in enumerate(membership):
            c_dict.setdefault(comm_id, set()).add(idx_to_n[idx])
        return {frozenset(s) for s in c_dict.values()}

    canonical_w = get_canonical_communities(part_w.membership)
    canonical_unw = get_canonical_communities(part_unw.membership)

    # 1. Kanonik küme karşılaştırması: Ağırlıklı ve ağırlıksız bölüntüler kesinlikle farklıdır
    assert canonical_w != canonical_unw

    # 2. Adjusted Rand Index (ARI): Etiket numaralarından bağımsız olarak iki bölümleme tam uyuşmaz (ARI < 1.0)
    ari = adjusted_rand_score(part_w.membership, part_unw.membership)
    assert ari < 1.0

    # Ağırlıklı Leiden iki güçlü 3'lü kliği eksiksiz ayırmalıdır ({0, 1, 2} ve {3, 4, 5})
    assert canonical_w == {frozenset({0, 1, 2}), frozenset({3, 4, 5})}

    # partition.quality() hedef fonksiyonunun Newman ağırlıklı modülerliğe makine hassasiyetinde eşitliği:
    nx_mod = nx.community.modularity(G, [set(c) for c in canonical_w], weight="weight")
    assert np.isclose(part_w.quality(), nx_mod, atol=1e-6)


def test_leiden_common_modularity_matches_exported_memberships(sample_graph, sample_metadata):
    """
    Leiden için raporlanan ortak modülerlik değerinin, dışarı aktarılan
    üyeliklerle nx.community.modularity(G, comms, weight='weight') ile
    hesaplanan değerle birebir eşleştiğini doğrular.
    """
    results = analyze_communities(sample_graph, inst_metadata_df=sample_metadata, seeds=[42])
    rep_modularity = results["summary"]["leiden"]["trials_summary"][0]["modularity"]
    rep_quality = results["summary"]["leiden"]["trials_summary"][0]["partition_quality"]

    # partition.quality() ve ortak NetworkX modülerliğinin eşitliği
    assert np.isclose(rep_quality, rep_modularity, atol=1e-6)

    # Dışarı aktarılan üyeliklerden toplulukları yeniden oluştur
    df_mem = results["membership_df"]
    cluster_groups = df_mem.groupby("leiden_community")["id"].apply(list).tolist()

    # NetworkX ile bağımsız olarak hesaplanan ağırlıklı modülerlik
    expected_modularity = float(nx.community.modularity(sample_graph, cluster_groups, weight="weight"))
    assert np.isclose(rep_modularity, expected_modularity, atol=1e-6)


def test_null_model_degree_and_connectivity_preservation(sample_graph):
    """
    Derece korumalı kenar takasında derece dizisinin ve
    bağlantılılık durumunun kesinlikle korunduğunu doğrular.
    """
    G_null, is_exact = generate_degree_preserving_null_network(
        sample_graph, n_swaps_factor=3, seed=123, ensure_connected=True
    )
    assert is_exact is True
    assert nx.is_connected(G_null) is True
    assert sorted([d for _, d in sample_graph.degree()]) == sorted([d for _, d in G_null.degree()])


def test_null_model_unweighted_and_p_value_consistency(sample_graph):
    """
    Null modelin tamamen ağırlıksız topoloji (weight=None) kullandığını,
    ortalama kümelenme, en kısa yol ve modülerliğin ağırlıksız tanımla
    ve ampirik p-değerlerinin doğru kuyruk formülüyle (Monte Carlo (r+1)/(B+1))
    bağımsız olarak doğrulanmasını sağlar.
    """
    results = run_null_model_experiments(sample_graph, n_trials=10, base_seed=42)
    summary = results["summary"]
    null_samples = results["null_samples"]
    
    assert summary["degree_sequence_preserved"] is True
    assert summary["successful_null_models"] == 10
    
    # Ağırlıksız gözlenen değerlerin tutarlılığı
    G_unweighted = nx.Graph()
    G_unweighted.add_nodes_from(sample_graph.nodes())
    G_unweighted.add_edges_from(sample_graph.edges())

    expected_c_obs = float(nx.average_clustering(G_unweighted))
    assert np.isclose(summary["clustering"]["observed"], expected_c_obs, atol=1e-6)

    # Bağımsız ampirik p-değeri doğrulaması:
    # C: sağ kuyruk p = [count(null >= obs) + 1] / [B + 1]
    # Q: sağ kuyruk p = [count(null >= obs) + 1] / [B + 1]
    # L: iki kuyruk p = min(1.0, 2 * min(p_left, p_right))
    obs_c = summary["clustering"]["observed"]
    obs_l = summary["shortest_path"]["observed"]
    obs_q = summary["modularity"]["observed"]

    arr_c = np.array(null_samples["clustering"])
    arr_l = np.array(null_samples["shortest_path"])
    arr_q = np.array(null_samples["modularity"])
    B = len(arr_c)
    assert B == 10

    expected_p_c = float((np.sum(arr_c >= obs_c) + 1) / (B + 1))
    expected_p_q = float((np.sum(arr_q >= obs_q) + 1) / (B + 1))

    p_left_l = (np.sum(arr_l <= obs_l) + 1) / (B + 1)
    p_right_l = (np.sum(arr_l >= obs_l) + 1) / (B + 1)
    expected_p_l = float(min(1.0, 2.0 * min(p_left_l, p_right_l)))

    assert np.isclose(summary["clustering"]["empirical_p_value"], expected_p_c, atol=1e-6)
    assert np.isclose(summary["modularity"]["empirical_p_value"], expected_p_q, atol=1e-6)
    assert np.isclose(summary["shortest_path"]["empirical_p_value"], expected_p_l, atol=1e-6)

    # Small-worldness katsayılarının doğruluğu
    gamma = summary["small_worldness"]["gamma (C/C_null)"]
    lambda_val = summary["small_worldness"]["lambda (L/L_null)"]
    sigma = summary["small_worldness"]["sigma"]
    assert np.isclose(sigma, gamma / lambda_val, atol=1e-6)


def test_haversine_distance():
    """Haversine formülünün bilinen şehirler arasındaki mesafesini doğrular."""
    dist = haversine_distance(41.0082, 28.9784, 39.9334, 32.8597)
    assert 340.0 < dist < 360.0
    assert haversine_distance(41.0, 29.0, 41.0, 29.0) == 0.0


def test_gravity_dyadic_dataset(sample_graph, sample_metadata):
    """İkili veri seti kurulumu, sıfır mesafesi ve çift sayısını doğrular."""
    df_dyads, audit = build_dyadic_dataset(sample_graph, sample_metadata, intra_city_offset_km=1.0)
    expected_pairs = 10 * 9 // 2  # 45 çift
    assert len(df_dyads) == expected_pairs
    assert audit["total_theoretical_pairs"] == expected_pairs
    assert "collab_count" in df_dyads.columns
    assert "log_distance" in df_dyads.columns
    assert "both_egean" in df_dyads.columns


def test_gravity_mle_alpha_and_synthesis_consistency(sample_graph, sample_metadata):
    """
    Çekim modelinde Negatif Binom modelinin alfa parametresini tahmin ettiğini,
    aşırı yayılım durumunda esas model olarak Negatif Binom'un seçildiğini ve
    sentezdeki katsayıların seçilen esas modelle birebir eşleştiğini doğrular.
    """
    df_dyads, _ = build_dyadic_dataset(sample_graph, sample_metadata, intra_city_offset_km=1.0)
    models = fit_gravity_models(df_dyads)
    
    assert "poisson_model" in models
    assert "negative_binomial_model" in models
    assert "synthesis" in models
    
    # Alfa parametresinin varlığı
    nb_model = models["negative_binomial_model"]
    assert "alpha_parameter" in nb_model
    assert nb_model["alpha_parameter"]["estimated_alpha"] > 0

    # Sentez katsayılarının seçilen esas model ile eşleşmesi
    primary_name = models["primary_model_name"]
    synth = models["synthesis"]
    
    if primary_name.startswith("Negative"):
        target_params = nb_model["parameters"]
    else:
        target_params = models["poisson_model"]["parameters"]

    synth_dist_coef = synth["scientific_conclusion"]["distance_elasticity"]["coef"]
    target_dist_coef = target_params["log_distance"]["coef"]
    assert np.isclose(synth_dist_coef, target_dist_coef, atol=1e-6)

    synth_ege_coef = synth["scientific_conclusion"]["regional_egean_effect"]["coef"]
    target_ege_coef = target_params["both_egean"]["coef"]
    assert np.isclose(synth_ege_coef, target_ege_coef, atol=1e-6)


def test_collaboration_map_generation(sample_graph, sample_metadata):
    """Folium haritasının oluşturulduğunu ve HTML dosyasının üretildiğini doğrular."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_html = os.path.join(tmpdir, "test_map.html")
        m = generate_collaboration_map(
            sample_graph, sample_metadata, output_html_path=out_html, edge_weight_threshold=1
        )
        assert os.path.exists(out_html)
        assert os.path.getsize(out_html) > 1000
