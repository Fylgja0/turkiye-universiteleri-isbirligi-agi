"""
scripts/run_final_analysis.py

Sosyal Ağ Analizi Projesi (30 Ekim 2026 Final Teslimi)
Tüm Final Analiz Hattını Çalıştıran Ana Orkestratör Betik:
1. Temel Ağ Ölçüleri ve Merkeziyetler (Kapsam B1 ve Kapsam B duyarlılık analizi)
2. Derece Dağılımı ve Güç Yasası (Power Law vs Üstel vs Log-Normal)
3. Louvain ve Leiden Topluluk Tespiti (10 tohum kararlılık analizi)
4. Null Model (Derece korumalı 100 rastgele ağ, Z-skorları ve Small-Worldness)
5. Çekim (Gravity) Modeli Regresyonu (Poisson & Negative Binomial GLM, aşırı yayılım kontrolü)
6. Türkiye Coğrafi İş Birliği Haritası (Folium HTML)

Tüm çıktılar 'reports/generated/' dizinine üretilir ve test edilebilir.
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, Any, Tuple
import pandas as pd
import networkx as nx

# Analiz modülleri
from scripts.analysis_metrics import (
    compute_network_topology,
    compute_centralities,
)
from scripts.analysis_powerlaw import fit_powerlaw_distribution
from scripts.analysis_community import analyze_communities, SEEDS_10
from scripts.analysis_null_model import run_null_model_experiments
from scripts.analysis_gravity import build_dyadic_dataset, fit_gravity_models
from scripts.visualize_map import generate_collaboration_map

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("run_final_analysis")


def load_network_data(
    institutions_path: str = "data/processed/institutions.csv",
    edges_path: str = "data/processed/edges.csv"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """İşlenmiş kurum ve kenar CSV dosyalarını yükler."""
    if not os.path.exists(institutions_path):
        raise FileNotFoundError(f"Kurum dosyası bulunamadı: {institutions_path}")
    if not os.path.exists(edges_path):
        raise FileNotFoundError(f"Kenar dosyası bulunamadı: {edges_path}")

    df_inst = pd.read_csv(institutions_path)
    df_edges = pd.read_csv(edges_path)
    return df_inst, df_edges


def build_scope_graph(
    df_inst: pd.DataFrame,
    df_edges: pd.DataFrame,
    allowed_categories: list
) -> Tuple[nx.Graph, pd.DataFrame]:
    """Belirtilen kategorilere göre filtrelenmiş alt grafiği oluşturur."""
    df_filtered_inst = df_inst[df_inst["category"].isin(allowed_categories)].copy()
    valid_ids = set(df_filtered_inst["id"])

    # Düğümleri ekle
    G = nx.Graph()
    for _, row in df_filtered_inst.iterrows():
        G.add_node(
            row["id"],
            display_name=row["display_name"],
            category=row["category"],
            city=row.get("city", ""),
            is_egean=bool(row.get("is_egean", False)),
            latitude=row.get("latitude"),
            longitude=row.get("longitude"),
            period_cs_works_count=int(row.get("period_cs_works_count", 0)),
        )

    # Geçerli kenarları ekle
    df_filtered_edges = df_edges[
        df_edges["source"].isin(valid_ids) & df_edges["target"].isin(valid_ids)
    ]
    for _, row in df_filtered_edges.iterrows():
        G.add_edge(row["source"], row["target"], weight=int(row["weight"]))

    return G, df_filtered_inst


def main():
    parser = argparse.ArgumentParser(description="Türkiye Üniversiteleri SNA Final Analiz Hattı")
    parser.add_argument("--institutions", default="data/processed/institutions.csv", help="Kurumlar CSV")
    parser.add_argument("--edges", default="data/processed/edges.csv", help="Kenarlar CSV")
    parser.add_argument("--output-dir", default="reports/generated", help="Çıktı klasörü")
    parser.add_argument("--null-trials", type=int, default=100, help="Null model rastgele ağ sayısı")
    parser.add_argument("--edge-threshold", type=int, default=5, help="Harita kenar filtre eşiği")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    logger.info("=== Final Analiz Hattı Başlatılıyor ===")

    # 1. Veri Yükleme
    df_inst, df_edges = load_network_data(args.institutions, args.edges)
    logger.info(f"Yüklenen: {len(df_inst)} kurum, {len(df_edges)} kenar.")

    # Scope B1 (Birincil Kapsam: 186 Aktif Üniversite)
    G_b1, df_inst_b1 = build_scope_graph(df_inst, df_edges, allowed_categories=["active_university"])
    logger.info(f"Scope B1 Grafı: {G_b1.number_of_nodes()} düğüm, {G_b1.number_of_edges()} kenar.")

    # Scope B (Duyarlılık Kapsamı: 194 Üniversite - Aktif + KHK/CBK Kapatılanlar)
    G_b, df_inst_b = build_scope_graph(
        df_inst, df_edges,
        allowed_categories=["active_university", "closed_2016_khk", "closed_2020_cbk"]
    )
    logger.info(f"Scope B Grafı: {G_b.number_of_nodes()} düğüm, {G_b.number_of_edges()} kenar.")

    # =========================================================================
    # AŞAMA 1: TEMEL AĞ ÖLÇÜLERİ VE MERKEZİYET ANALİZLERİ
    # =========================================================================
    logger.info(">>> Aşama 1: Temel Ağ Ölçüleri ve Merkeziyetler Hesaplanıyor...")
    topo_b1 = compute_network_topology(G_b1, scope_name="Scope B1 (Aktif Üniversiteler)")
    topo_b = compute_network_topology(G_b, scope_name="Scope B (Tüm Üniversiteler)")

    topology_summary = {
        "primary_scope_b1": topo_b1,
        "sensitivity_scope_b": topo_b
    }
    with open(os.path.join(args.output_dir, "network_topology_summary.json"), "w", encoding="utf-8") as f:
        json.dump(topology_summary, f, ensure_ascii=False, indent=2)

    # Merkeziyetler (Scope B1 üzerinde)
    centrality_df, top10_df, spearman_df = compute_centralities(G_b1, inst_metadata_df=df_inst_b1)
    centrality_df.to_csv(os.path.join(args.output_dir, "centrality_metrics.csv"), index=False)
    top10_df.to_csv(os.path.join(args.output_dir, "centrality_top10_comparison.csv"), index=False)
    spearman_df.to_csv(os.path.join(args.output_dir, "centrality_spearman_correlation.csv"))
    logger.info("Aşama 1 tamamlandı.")

    # =========================================================================
    # AŞAMA 2: DERECE DAĞILIMI VE GÜÇ YASASI (POWER LAW)
    # =========================================================================
    logger.info(">>> Aşama 2: Güç Yasası Analizi ve Grafikler Üretiliyor...")
    degrees_b1 = [d for _, d in G_b1.degree()]
    powerlaw_plot_path = os.path.join(args.output_dir, "degree_distribution_powerlaw.png")
    powerlaw_results = fit_powerlaw_distribution(degrees_b1, output_plot_path=powerlaw_plot_path)

    with open(os.path.join(args.output_dir, "powerlaw_fit_results.json"), "w", encoding="utf-8") as f:
        json.dump(powerlaw_results, f, ensure_ascii=False, indent=2)
    logger.info("Aşama 2 tamamlandı.")

    # =========================================================================
    # AŞAMA 3: LOUVAIN VE LEIDEN TOPLULUK TESPİTİ
    # =========================================================================
    logger.info(">>> Aşama 3: Louvain ve Leiden Algoritmaları (10 Tohum) Çalıştırılıyor...")
    community_results = analyze_communities(G_b1, inst_metadata_df=df_inst_b1, seeds=SEEDS_10)

    with open(os.path.join(args.output_dir, "community_detection_summary.json"), "w", encoding="utf-8") as f:
        json.dump(community_results["summary"], f, ensure_ascii=False, indent=2)

    community_results["membership_df"].to_csv(
        os.path.join(args.output_dir, "community_assignments.csv"), index=False
    )
    community_results["top_clusters_df"].to_csv(
        os.path.join(args.output_dir, "community_top_clusters.csv"), index=False
    )
    logger.info("Aşama 3 tamamlandı.")

    # =========================================================================
    # AŞAMA 4: NULL MODEL ANALİZİ (100 RASTGELE AĞ)
    # =========================================================================
    logger.info(f">>> Aşama 4: Null Model Analizi ({args.null_trials} rastgele ağ) Yürütülüyor...")
    null_results = run_null_model_experiments(G_b1, n_trials=args.null_trials, base_seed=42)

    with open(os.path.join(args.output_dir, "null_model_comparison.json"), "w", encoding="utf-8") as f:
        json.dump(null_results["summary"], f, ensure_ascii=False, indent=2)

    null_results["comparison_df"].to_csv(
        os.path.join(args.output_dir, "null_model_comparison.csv"), index=False
    )
    logger.info("Aşama 4 tamamlandı.")

    # =========================================================================
    # AŞAMA 5: ÇEKİM (GRAVITY) MODELİ REGRESYON ANALİZİ
    # =========================================================================
    logger.info(">>> Aşama 5: İkili Çekim Modeli Veri Seti ve GLM Regresyonları...")
    df_dyads, audit_dyads = build_dyadic_dataset(G_b1, df_inst_b1, intra_city_offset_km=1.0)
    logger.info(f"İkili çift sayısı: {len(df_dyads)} (Kurumsal sıfır oranı: {audit_dyads['sparsity_ratio']:.2%})")

    # İlk 200 çiftlik temsilci örnek dosyası (tam veri 17.205 satır)
    df_dyads.head(200).to_csv(
        os.path.join(args.output_dir, "gravity_model_dyadic_sample.csv"), index=False
    )

    gravity_results = fit_gravity_models(df_dyads)
    gravity_results["dyadic_audit"] = audit_dyads

    with open(os.path.join(args.output_dir, "gravity_model_results.json"), "w", encoding="utf-8") as f:
        json.dump(gravity_results, f, ensure_ascii=False, indent=2)

    # Katsayılar Karşılaştırma Tablosu (Poisson vs Negative Binomial)
    records_coef = []
    terms = ["Intercept", "log_size_i", "log_size_j", "log_distance", "both_egean"]
    for t in terms:
        p_info = gravity_results["poisson_model"]["parameters"].get(t, {})
        nb_info = gravity_results["negative_binomial_model"]["parameters"].get(t, {}) if gravity_results["negative_binomial_model"] else {}
        records_coef.append({
            "term": t,
            "poisson_coef": p_info.get("coef"),
            "poisson_se": p_info.get("std_err"),
            "poisson_p": p_info.get("p_value"),
            "poisson_exp_coef": p_info.get("exp_coef"),
            "nb_coef": nb_info.get("coef"),
            "nb_se": nb_info.get("std_err"),
            "nb_p": nb_info.get("p_value"),
            "nb_exp_coef": nb_info.get("exp_coef")
        })
    df_coef = pd.DataFrame(records_coef)
    df_coef.to_csv(os.path.join(args.output_dir, "gravity_model_summary.csv"), index=False)
    logger.info("Aşama 5 tamamlandı.")

    # =========================================================================
    # AŞAMA 6: COĞRAFİ İŞ BİRLİĞİ HARİTASI
    # =========================================================================
    logger.info(">>> Aşama 6: Folium Coğrafi İş Birliği Haritası Üretiliyor...")
    map_html_path = os.path.join(args.output_dir, "turkey_collaboration_map.html")
    generate_collaboration_map(
        G_b1,
        df_inst_b1,
        output_html_path=map_html_path,
        edge_weight_threshold=args.edge_threshold
    )
    logger.info(f"Harita kaydedildi: {map_html_path}")

    logger.info("=== Final Analiz Hattı Başarıyla Tamamlandı! ===")


if __name__ == "__main__":
    main()
