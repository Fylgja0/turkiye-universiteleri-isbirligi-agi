"""
tests/test_network.py

Birim testler ve otomatik denetim paketi:
Ağ kurma kuralları, kurum sınıflandırma, GraphML-CSV kenar/ağırlık birebir eşitliği,
derece/ağırlıklı derece bağımsız yeniden hesaplama doğrulaması,
Kapsam A/B/B1 metrik tutarlılığı ve rapor tabloları çapraz kontrolü.
"""

import os
import re
import json
import glob
import tempfile
import pytest
import networkx as nx
import pandas as pd
from typing import List, Dict, Any, Set, Tuple

from scripts.build_network import (
    normalize_id,
    is_egean_institution,
    classify_institution,
    process_works_and_build_network
)


def test_normalize_id():
    assert normalize_id("https://openalex.org/I123") == "https://openalex.org/I123"
    assert normalize_id("http://openalex.org/I123") == "https://openalex.org/I123"
    assert normalize_id("I123") == "https://openalex.org/I123"
    assert normalize_id(None) is None
    assert normalize_id("") is None


def test_is_egean_institution():
    assert is_egean_institution("Ege University", "Izmir") is True
    assert is_egean_institution("Manisa Celal Bayar University", "Manisa") is True
    assert is_egean_institution("Dokuz Eylül University", "Izmir") is True
    assert is_egean_institution("Pamukkale University", "Denizli") is True
    assert is_egean_institution("Istanbul Aydın University", "Istanbul") is False
    assert is_egean_institution("Middle East Technical University", "Ankara") is False
    assert is_egean_institution("Istanbul Technical University", "Istanbul") is False


def test_classify_institution_khk_and_active():
    """
    2016 KHK ile kapatılan kurumların, aktif üniversitelerin, MYO, akademilerin
    ve unverified (Lefke, Şehir Üniversitesi vb.) kurumların doğru sınıflandırıldığını doğrular.
    """
    # 1. Kapatılan İzmir Üniversitesi (667 KHK)
    cat, is_uni = classify_institution("https://openalex.org/I132257509", "Izmir University", raw_status="active")
    assert cat == "closed_2016_khk"
    assert is_uni is True

    # 2. Kapatılan Turgut Özal Üniversitesi (Ankara)
    cat, is_uni = classify_institution("https://openalex.org/I6573832", "Turgut Özal University", raw_status="active")
    assert cat == "closed_2016_khk"
    assert is_uni is True

    # 3. Halen Aktif Olan Malatya Turgut Özal Üniversitesi (2018'de kurulan devlet üniversitesi)
    cat, is_uni = classify_institution("https://openalex.org/I4210110665", "Malatya Turgut Özal Üniversitesi", raw_status="active")
    assert cat == "active_university"
    assert is_uni is True

    # 4. Kapatılan Fatih Üniversitesi vs Aktif Fatih Sultan Mehmet Vakıf Üniversitesi
    cat_closed, is_uni_closed = classify_institution("https://openalex.org/I32462889", "Fatih University", raw_status="active")
    assert cat_closed == "closed_2016_khk"
    assert is_uni_closed is True

    cat_active, is_uni_active = classify_institution("https://openalex.org/I4210146544", "Fatih Sultan Mehmet Waqf University", raw_status="active")
    assert cat_active == "active_university"
    assert is_uni_active is True

    # 5. Doğrulanmamış/kapsam dışı veya hukuki kapatılmış kurumlar (unverified)
    cat_lefke, is_uni_lefke = classify_institution("https://openalex.org/I116528569", "European University of Lefke", raw_status="active")
    assert cat_lefke == "unverified"
    assert is_uni_lefke is False

    cat_sehir, is_uni_sehir = classify_institution("https://openalex.org/I13419840", "Istanbul Şehir University", raw_status="active")
    assert cat_sehir == "unverified"
    assert is_uni_sehir is False

    # 6. Kapatılan Gediz, Şifa, Bursa Orhangazi, Canik Başarı
    for iid, name in [
        ("https://openalex.org/I149028718", "Gediz University"),
        ("https://openalex.org/I334480368", "Şifa University"),
        ("https://openalex.org/I3003364", "Bursa Orhangazi University"),
        ("https://openalex.org/I264664839", "Canik Başarı University")
    ]:
        c, u = classify_institution(iid, name)
        assert c == "closed_2016_khk", f"{name} should be closed_2016_khk"
        assert u is True

    # 7. Bağımsız MYO kontrolü
    cat_myo, is_uni_myo = classify_institution("https://openalex.org/I4210151063", "İzmir Kavram Meslek Yüksekokulu", raw_status="active")
    assert cat_myo == "vocational_college"
    assert is_uni_myo is False

    # 8. Askeri Akademi kontrolü
    cat_mil, is_uni_mil = classify_institution("https://openalex.org/I157637111", "Naval Academy", raw_status="active")
    assert cat_mil == "academy_or_institute"
    assert is_uni_mil is False

    # 9. Tanınmayan kurum ve inactive status kontrolü -> unverified
    cat_unv, is_uni_unv = classify_institution("https://openalex.org/I999999", "Random Unknown Research Lab", raw_status="active")
    assert cat_unv == "unverified"
    assert is_uni_unv is False

    cat_inact, is_uni_inact = classify_institution("https://openalex.org/I888888", "Some Fake Entity", raw_status="inactive")
    assert cat_inact == "unverified"
    assert is_uni_inact is False


def test_network_construction_rules():
    """Küçük sentetik veri setiyle temel ağ kurma kurallarını doğrular."""
    mock_metadata = {
        "https://openalex.org/I_A": {
            "id": "https://openalex.org/I_A",
            "display_name": "Kurum A (Ege University)",
            "city": "Izmir",
            "type": "education",
            "country_code": "TR",
            "latitude": 38.42,
            "longitude": 27.14,
            "works_count": 100,
            "status": "active",
            "is_egean": True
        },
        "https://openalex.org/I_B": {
            "id": "https://openalex.org/I_B",
            "display_name": "Kurum B (Ankara University)",
            "city": "Ankara",
            "type": "education",
            "country_code": "TR",
            "latitude": 39.93,
            "longitude": 32.85,
            "works_count": 200,
            "status": "active",
            "is_egean": False
        },
        "https://openalex.org/I_C": {
            "id": "https://openalex.org/I_C",
            "display_name": "Kurum C (Istanbul University)",
            "city": "Istanbul",
            "type": "education",
            "country_code": "TR",
            "latitude": 41.01,
            "longitude": 28.97,
            "works_count": 150,
            "status": "active",
            "is_egean": False
        },
        "https://openalex.org/I_D": {
            "id": "https://openalex.org/I_D",
            "display_name": "Kurum D (Karadeniz Technical University)",
            "city": "Trabzon",
            "type": "education",
            "country_code": "TR",
            "latitude": 41.00,
            "longitude": 39.72,
            "works_count": 50,
            "status": "active",
            "is_egean": False
        }
    }

    mock_works = [
        {
            "id": "https://openalex.org/W1",
            "title": "Paper 1",
            "authorships": [
                {"institutions": [{"id": "https://openalex.org/I_A", "country_code": "TR", "type": "education"}]},
                {"institutions": [{"id": "https://openalex.org/I_A", "country_code": "TR", "type": "education"}]},
                {"institutions": [{"id": "https://openalex.org/I_B", "country_code": "TR", "type": "education"}]}
            ]
        },
        {
            "id": "https://openalex.org/W2",
            "title": "Paper 2",
            "authorships": [
                {"institutions": [{"id": "https://openalex.org/I_A", "country_code": "TR", "type": "education"}]},
                {"institutions": [{"id": "https://openalex.org/I_B", "country_code": "TR", "type": "education"}]},
                {"institutions": [{"id": "https://openalex.org/I_C", "country_code": "TR", "type": "education"}]}
            ]
        },
        {
            "id": "https://openalex.org/W3",
            "title": "Paper 3",
            "authorships": [
                {"institutions": [{"id": "https://openalex.org/I_D", "country_code": "TR", "type": "education"}]}
            ]
        }
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        works_file = os.path.join(tmpdir, "works_mock.jsonl")
        with open(works_file, "w", encoding="utf-8") as f:
            for w in mock_works:
                f.write(json.dumps(w) + "\n")

        G, edges_df, inst_df = process_works_and_build_network(
            works_files_pattern=os.path.join(tmpdir, "works_*.jsonl"),
            institutions_metadata=mock_metadata
        )

        assert G.number_of_nodes() == 4
        assert nx.number_of_selfloops(G) == 0
        assert G.degree("https://openalex.org/I_D") == 0
        assert nx.is_isolate(G, "https://openalex.org/I_D")
        assert G["https://openalex.org/I_A"]["https://openalex.org/I_B"]["weight"] == 2
        assert G.number_of_edges() == 3
        assert len(edges_df) == 3
        assert len(inst_df) == 4


def test_processed_files_deep_consistency():
    """
    CSV ve GraphML kenarlarının yalnızca sayıca değil,
    HER KENARIN İKİ UÇ NOKTASI VE AĞIRLIĞI BAKIMINDAN BİREBİR AYNI OLDUĞUNU,
    ve CSV'deki her düğümün degree / weighted_degree değerlerinin kenarlardan
    yeniden hesaplanarak tam eşleştiğini doğrular.
    """
    edges_path = "data/processed/edges.csv"
    inst_path = "data/processed/institutions.csv"
    graphml_path = "data/processed/collaboration.graphml"

    assert os.path.exists(edges_path), f"Eksik dosya: {edges_path}"
    assert os.path.exists(inst_path), f"Eksik dosya: {inst_path}"
    assert os.path.exists(graphml_path), f"Eksik dosya: {graphml_path}"

    edges_df = pd.read_csv(edges_path)
    inst_df = pd.read_csv(inst_path)
    G = nx.read_graphml(graphml_path)

    # 1. Toplam düğüm ve kenar sayıları tam eşit
    assert len(inst_df) == 205
    assert G.number_of_nodes() == 205
    assert len(edges_df) == 3970
    assert G.number_of_edges() == 3970

    # 2. GraphML ve CSV kenarlarının uç noktaları ve ağırlıkları birebir aynı
    csv_edges_dict = {}
    for _, r in edges_df.iterrows():
        u = min(r["source"], r["target"])
        v = max(r["source"], r["target"])
        csv_edges_dict[(u, v)] = int(r["weight"])

    graphml_edges_dict = {}
    for u_node, v_node, data in G.edges(data=True):
        u = min(u_node, v_node)
        v = max(u_node, v_node)
        w = int(data.get("weight", 1))
        graphml_edges_dict[(u, v)] = w

    assert len(csv_edges_dict) == 3970
    assert len(graphml_edges_dict) == 3970
    assert csv_edges_dict == graphml_edges_dict, "CSV ve GraphML kenar uçları veya ağırlıkları uyuşmuyor!"

    # 3. CSV'deki her düğümün degree ve weighted_degree değerlerinin kenarlardan yeniden hesaplanması
    computed_degree = {n: 0 for n in inst_df["id"]}
    computed_weighted_degree = {n: 0 for n in inst_df["id"]}
    for (u, v), w in csv_edges_dict.items():
        computed_degree[u] += 1
        computed_degree[v] += 1
        computed_weighted_degree[u] += w
        computed_weighted_degree[v] += w

    for _, r in inst_df.iterrows():
        nid = r["id"]
        expected_deg = computed_degree[nid]
        expected_wdeg = computed_weighted_degree[nid]
        assert r["degree"] == expected_deg, f"{r['display_name']} derece uyumsuz: CSV={r['degree']}, hesaplanan={expected_deg}"
        assert r["weighted_degree"] == expected_wdeg, f"{r['display_name']} ağırlıklı derece uyumsuz: CSV={r['weighted_degree']}, hesaplanan={expected_wdeg}"

    # 4. Kategori toplamlarının 205 düğümü doğru biçimde kapsaması ve is_university tutarlılığı
    cat_counts = inst_df["category"].value_counts().to_dict()
    assert cat_counts["active_university"] == 186
    assert cat_counts["closed_2016_khk"] == 7
    assert cat_counts["academy_or_institute"] == 5
    assert cat_counts["hospital_or_other"] == 3
    assert cat_counts["vocational_college"] == 2
    assert cat_counts["unverified"] == 2
    assert sum(cat_counts.values()) == 205

    for _, r in inst_df.iterrows():
        cat = r["category"]
        is_u = bool(r["is_university"])
        if cat in ["active_university", "closed_2016_khk"]:
            assert is_u is True, f"{r['display_name']} ({cat}) is_university True olmalı!"
        else:
            assert is_u is False, f"{r['display_name']} ({cat}) is_university False olmalı!"


def parse_markdown_table_rows(markdown_text: str, header_keyword: str) -> List[Dict[str, str]]:
    """
    Markdown metni içerisindeki belirli bir başlığı içeren tabloyu bulur
    ve satırlarını sözlük listesi olarak ayrıştırır.
    """
    lines = markdown_text.splitlines()
    in_table = False
    headers = []
    rows = []

    for i, line in enumerate(lines):
        striped = line.strip()
        if not in_table:
            if striped.startswith("|") and header_keyword in striped:
                # Tablo başlığı bulundu
                in_table = True
                headers = [c.strip() for c in striped.split("|")[1:-1]]
        else:
            if not striped.startswith("|"):
                # Tablo bitti
                break
            if re.match(r"^\|?\s*[-:]+[-| :]*$", striped):
                # Ayırıcı satır (---)
                continue
            cells = [c.strip() for c in striped.split("|")[1:-1]]
            if len(cells) == len(headers):
                row_dict = {h: c for h, c in zip(headers, cells)}
                rows.append(row_dict)

    return rows


def test_scopes_metrics_exact_values():
    """
    Kapsam A, Kapsam B (193 düğüm) ve Kapsam B1 (186 düğüm) için
    yoğunluk, bağlı bileşen, izole düğüm ve en büyük bileşen boyutlarını doğrular.
    """
    G = nx.read_graphml("data/processed/collaboration.graphml")

    # Kapsam A (Tüm 205 Düğüm)
    assert G.number_of_nodes() == 205
    assert G.number_of_edges() == 3970
    assert abs(nx.density(G) - 0.189861) < 1e-5
    assert nx.number_connected_components(G) == 4
    assert len(list(nx.isolates(G))) == 3
    assert len(max(nx.connected_components(G), key=len)) == 202

    # Kapsam B (is_university == True -> 186 aktif + 7 KHK = 193 Düğüm)
    uni_nodes = [n for n, d in G.nodes(data=True) if d.get("is_university", True)]
    G_B = G.subgraph(uni_nodes)
    assert G_B.number_of_nodes() == 193
    assert G_B.number_of_edges() == 3883
    assert abs(nx.density(G_B) - 0.209575) < 1e-5
    assert nx.number_connected_components(G_B) == 2
    assert len(list(nx.isolates(G_B))) == 1  # Canik Başarı University
    assert len(max(nx.connected_components(G_B), key=len)) == 192

    # Kapsam B1 (category == 'active_university' -> 186 Düğüm)
    active_uni_nodes = [n for n, d in G.nodes(data=True) if d.get("category") == "active_university"]
    G_B1 = G.subgraph(active_uni_nodes)
    assert G_B1.number_of_nodes() == 186
    assert G_B1.number_of_edges() == 3848
    assert abs(nx.density(G_B1) - 0.223656) < 1e-5
    assert nx.number_connected_components(G_B1) == 1
    assert len(list(nx.isolates(G_B1))) == 0
    assert len(max(nx.connected_components(G_B1), key=len)) == 186

    # Markdown Kapsam Tablolarının (ara_kontrol.md ve README.md) grafikten dinamik doğrulanması
    with open("reports/ara_kontrol.md", "r", encoding="utf-8") as f:
        rep_text = f.read()
    scope_rows = parse_markdown_table_rows(rep_text, "Kapsam A (Tüm 205 Education Kurumu)")
    assert len(scope_rows) >= 6, "Kapsam tablosu parse edilemedi!"

    # Tablo satırlarını metrik adına göre sözlüğe dönüştür
    scope_map = {}
    for r in scope_rows:
        m_name = list(r.values())[0].replace("*", "").strip()
        scope_map[m_name] = r

    col_a = "Kapsam A (Tüm 205 Education Kurumu)"
    col_b = "Kapsam B (186 Kural Tabanlı Aktif + 7 KHK Kurumu, 193 Düğüm)"
    col_b1 = "Kapsam B1 (186 Kural Tabanlı Aktif Üniversite)"

    # Düğüm Sayısı
    node_row = [v for k, v in scope_map.items() if "Düğüm Sayısı" in k][0]
    assert int(node_row[col_a].replace("*", "")) == G.number_of_nodes()
    assert int(node_row[col_b].replace("*", "")) == G_B.number_of_nodes()
    assert int(node_row[col_b1].replace("*", "")) == G_B1.number_of_nodes()

    # Kenar Sayısı
    edge_row = [v for k, v in scope_map.items() if "Kenar Sayısı" in k][0]
    assert int(edge_row[col_a].replace("*", "").replace(".", "")) == G.number_of_edges()
    assert int(edge_row[col_b].replace("*", "").replace(".", "")) == G_B.number_of_edges()
    assert int(edge_row[col_b1].replace("*", "").replace(".", "")) == G_B1.number_of_edges()

    # Ağ Yoğunluğu
    density_row = [v for k, v in scope_map.items() if "Yoğunluğu" in k][0]
    assert abs(float(density_row[col_a].replace("*", "")) - nx.density(G)) < 1e-4
    assert abs(float(density_row[col_b].replace("*", "")) - nx.density(G_B)) < 1e-4
    assert abs(float(density_row[col_b1].replace("*", "")) - nx.density(G_B1)) < 1e-4

    # Bağlı Bileşen Sayısı
    comp_row = [v for k, v in scope_map.items() if "Bileşen Sayısı" in k][0]
    assert int(comp_row[col_a].replace("*", "")) == nx.number_connected_components(G)
    assert int(comp_row[col_b].replace("*", "")) == nx.number_connected_components(G_B)
    assert int(comp_row[col_b1].replace("*", "")) == nx.number_connected_components(G_B1)

    # İzole Düğüm Sayısı
    iso_row = [v for k, v in scope_map.items() if "İzole Düğüm" in k][0]
    assert int(iso_row[col_a].replace("*", "")) == len(list(nx.isolates(G)))
    assert int(iso_row[col_b].split()[0].replace("*", "")) == len(list(nx.isolates(G_B)))
    assert int(iso_row[col_b1].replace("*", "")) == len(list(nx.isolates(G_B1)))

    # Dev Bileşen Büyüklüğü
    giant_row = [v for k, v in scope_map.items() if "Dev Bileşen" in k][0]
    assert int(giant_row[col_a].split()[0].replace("*", "")) == len(max(nx.connected_components(G), key=len))
    assert int(giant_row[col_b].split()[0].replace("*", "")) == len(max(nx.connected_components(G_B), key=len))
    assert int(giant_row[col_b1].split()[0].replace("*", "")) == len(max(nx.connected_components(G_B1), key=len))


def test_graphml_and_csv_node_attributes_deep_match():
    """
    GraphML ve CSV'deki tüm düğüm özniteliklerinin (display_name, category, is_university,
    period_cs_works_count, all_time_works_count, city, is_egean) ve grafikten
    hesaplanan derece / ağırlıklı derece değerlerinin tam eşleştiğini doğrular.
    """
    G = nx.read_graphml("data/processed/collaboration.graphml")
    inst_df = pd.read_csv("data/processed/institutions.csv")

    assert set(G.nodes()) == set(inst_df["id"]), "GraphML ve CSV düğüm ID setleri uyuşmuyor!"

    for _, r in inst_df.iterrows():
        nid = r["id"]
        g_data = G.nodes[nid]
        
        assert g_data.get("display_name") == r["display_name"], f"{nid} display_name uyumsuz!"
        assert g_data.get("category") == r["category"], f"{nid} category uyumsuz!"
        assert bool(g_data.get("is_university")) == bool(r["is_university"]), f"{nid} is_university uyumsuz!"
        assert int(g_data.get("period_cs_works_count", 0)) == int(r["period_cs_works_count"]), f"{nid} period_cs_works_count uyumsuz!"
        assert int(g_data.get("all_time_works_count", 0)) == int(r["all_time_works_count"]), f"{nid} all_time_works_count uyumsuz!"
        assert bool(g_data.get("is_egean")) == bool(r["is_egean"]), f"{nid} is_egean uyumsuz!"
        
        # Grafiğin topolojisinden bağımsız hesaplanan derece ve ağırlıklı derece
        deg_calc = G.degree(nid)
        wdeg_calc = int(G.degree(nid, weight="weight"))
        assert deg_calc == int(r["degree"]), f"{nid} derece uyumsuz! GraphML={deg_calc}, CSV={r['degree']}"
        assert wdeg_calc == int(r["weighted_degree"]), f"{nid} ağırlıklı derece uyumsuz! GraphML={wdeg_calc}, CSV={r['weighted_degree']}"


def test_report_critical_tables_match_csv():
    """
    reports/ara_kontrol.md içindeki kritik tabloları (İlk 10 ve Ege Tablosu)
    doğrudan Markdown tablosunu ayrıştırarak CSV'deki gerçek değerlerle karşılaştırır.
    """
    inst_df = pd.read_csv("data/processed/institutions.csv")
    with open("reports/ara_kontrol.md", "r", encoding="utf-8") as f:
        report_text = f.read()

    # 1. İlk 10 Tablosu Ayrıştırma ve Hücre Bazlı Karşılaştırma
    top10_rows = parse_markdown_table_rows(report_text, "2020–2025 CS Eser Sayısı")
    assert len(top10_rows) >= 10, f"İlk 10 tablosu parse edilemedi! Bulunan satır: {len(top10_rows)}"

    top10_csv = inst_df.sort_values(by="period_cs_works_count", ascending=False).head(10).reset_index(drop=True)

    for i in range(10):
        row = top10_rows[i]
        csv_row = top10_csv.iloc[i]

        rep_cs = int(row["2020–2025 CS Eser Sayısı"].replace("*", "").replace(".", "").strip())
        rep_all = int(row["Tüm Zamanlar Eser Sayısı"].replace("*", "").replace(".", "").strip())
        rep_deg = int(row["Derece ($k_i$)"].replace("*", "").strip())
        rep_wdeg = int(row["Ağırlıklı Derece ($s_i$)"].replace("*", "").strip())

        assert rep_cs == csv_row["period_cs_works_count"], f"Sıra {i+1} period_cs uyumsuz: Rapor={rep_cs}, CSV={csv_row['period_cs_works_count']}"
        assert rep_all == csv_row["all_time_works_count"], f"Sıra {i+1} all_time uyumsuz: Rapor={rep_all}, CSV={csv_row['all_time_works_count']}"
        assert rep_deg == csv_row["degree"], f"Sıra {i+1} degree uyumsuz: Rapor={rep_deg}, CSV={csv_row['degree']}"
        assert rep_wdeg == csv_row["weighted_degree"], f"Sıra {i+1} weighted_degree uyumsuz: Rapor={rep_wdeg}, CSV={csv_row['weighted_degree']}"

    # MCBÜ satırı kontrolü (Tablo 3'ün son satırı)
    mcbu_row = inst_df[inst_df["id"] == "https://openalex.org/I16748637"].iloc[0]
    mcbu_tab_rows = [r for r in top10_rows if "Celal Bayar" in r["Üniversite Adı"]]
    assert len(mcbu_tab_rows) == 1, "İlk 10 tablosundaki MCBÜ referans satırı bulunamadı!"
    mcbu_tab = mcbu_tab_rows[0]
    assert int(mcbu_tab["2020–2025 CS Eser Sayısı"].replace("*", "").replace(".", "").strip()) == mcbu_row["period_cs_works_count"]
    assert int(mcbu_tab["Tüm Zamanlar Eser Sayısı"].replace("*", "").replace(".", "").strip()) == mcbu_row["all_time_works_count"]
    assert int(mcbu_tab["Derece ($k_i$)"].replace("*", "").strip()) == mcbu_row["degree"]
    assert int(mcbu_tab["Ağırlıklı Derece ($s_i$)"].replace("*", "").strip()) == mcbu_row["weighted_degree"]

    # 2. Ege Tablosu (14 Aktif Kurum) Ayrıştırma ve Sıralama Karşılaştırması
    ege_rows = parse_markdown_table_rows(report_text, "Sıra (CS Hacmine Göre)")
    assert len(ege_rows) == 14, f"Ege tablosunda 14 aktif kurum bekleniyordu, {len(ege_rows)} bulundu!"

    ege_active_csv = inst_df[(inst_df["is_egean"] == True) & (inst_df["category"] == "active_university")].sort_values(
        by="period_cs_works_count", ascending=False
    ).reset_index(drop=True)

    for i in range(14):
        row = ege_rows[i]
        csv_row = ege_active_csv.iloc[i]

        rep_cs = int(row["2020–25 CS Eser"].replace("*", "").replace(".", "").strip())
        rep_deg = int(row["Derece ($k_i$)"].replace("*", "").strip())
        rep_wdeg = int(row["Ağırlıklı Derece ($s_i$)"].replace("*", "").strip())
        rep_all = int(row["Tüm Zamanlar Eser"].replace("*", "").replace(".", "").strip())

        assert rep_cs == csv_row["period_cs_works_count"], f"Ege Sıra {i+1} CS eser uyumsuz!"
        assert rep_deg == csv_row["degree"], f"Ege Sıra {i+1} degree uyumsuz!"
        assert rep_wdeg == csv_row["weighted_degree"], f"Ege Sıra {i+1} weighted_degree uyumsuz!"
        assert rep_all == csv_row["all_time_works_count"], f"Ege Sıra {i+1} all_time uyumsuz!"

    # MCBÜ Sıralama ve Metin Doğrulaması (Tablo ve Metin Uyumu)
    assert mcbu_row["period_cs_works_count"] == 322
    assert mcbu_row["degree"] == 66
    assert mcbu_row["weighted_degree"] == 198
    assert "3. sırada" in report_text, "MCBÜ'nün CS üretimindeki 3. sırası raporda bulunamadı!"
    assert "4. sırada" in report_text, "MCBÜ'nün derece merkeziliğindeki 4. sırası raporda bulunamadı!"
    assert "2. sırada" in report_text, "MCBÜ'nün ağırlıklı derecedeki 2. sırası raporda bulunamadı!"


def test_documentation_cross_consistency():
    """
    README.md, docs/data_dictionary.md ve reports/ara_kontrol.md
    arasındaki kapsam sayıları (193, 186), YÖK 204+4=208 ayrımı
    ve 122 ham / 112 round(4) koordinat sayılarının tam uyumlu olduğunu denetler.
    """
    with open("README.md", "r", encoding="utf-8") as f:
        readme_text = f.read()
    with open("docs/data_dictionary.md", "r", encoding="utf-8") as f:
        dict_text = f.read()
    with open("reports/ara_kontrol.md", "r", encoding="utf-8") as f:
        report_text = f.read()

    # Kapsam B (193) ve B1 (186) sayıları tüm belgelerde tutarlı olmalı
    for doc_name, doc_text in [("README.md", readme_text), ("docs/data_dictionary.md", dict_text), ("reports/ara_kontrol.md", report_text)]:
        assert "193" in doc_text, f"{doc_name} içinde Kapsam B düğüm sayısı (193) bulunamadı!"
        assert "186" in doc_text, f"{doc_name} içinde Kapsam B1 düğüm sayısı (186) bulunamadı!"
        assert "3.883" in doc_text or "3883" in doc_text, f"{doc_name} içinde Kapsam B kenar sayısı (3.883) bulunamadı!"
        assert "3.848" in doc_text or "3848" in doc_text, f"{doc_name} içinde Kapsam B1 kenar sayısı (3.848) bulunamadı!"

    # 204 üniversite, 4 MYO ve 208 yükseköğretim kurumu dağılımı
    for doc_name, doc_text in [("README.md", readme_text), ("docs/data_dictionary.md", dict_text), ("reports/ara_kontrol.md", report_text)]:
        assert "204" in doc_text, f"{doc_name} içinde 204 üniversite sayısı bulunamadı!"
        assert "208" in doc_text, f"{doc_name} içinde toplam 208 yükseköğretim kurumu sayısı bulunamadı!"

    for doc_name, doc_text in [("README.md", readme_text), ("reports/ara_kontrol.md", report_text)]:
        assert "222" in doc_text, f"{doc_name} içinde OpenAlex education kurum sayısı (222) bulunamadı!"
        assert "yok.gov.tr" in doc_text, f"{doc_name} içinde YÖK resmi kaynak bağlantısı bulunamadı!"

    # Tekil koordinatlar (122 ham float, 112 round(4) yuvarlanmış/merkez)
    inst_df = pd.read_csv("data/processed/institutions.csv")
    raw_unique_coords = len(inst_df[["latitude", "longitude"]].dropna().drop_duplicates())
    round4_unique_coords = len(inst_df[["latitude", "longitude"]].dropna().round(4).drop_duplicates())
    assert raw_unique_coords == 122, f"Beklenen ham tekil koordinat 122, bulunan: {raw_unique_coords}"
    assert round4_unique_coords == 112, f"Beklenen round(4) tekil koordinat 112, bulunan: {round4_unique_coords}"

    for doc_name, doc_text in [("docs/data_dictionary.md", dict_text), ("reports/ara_kontrol.md", report_text)]:
        assert "122" in doc_text, f"{doc_name} içinde 122 ham tekil koordinat sayısı bulunamadı!"
        assert "112" in doc_text, f"{doc_name} içinde 112 yuvarlanmış tekil koordinat sayısı bulunamadı!"


def test_excluded_works_integrity_and_provenance():
    """
    data/processed/excluded_works_summary.csv dosyasının 641 tekil kaydını,
    yıllara göre tam dağılımını ve etiket tutarlılığını doğrular.
    """
    excluded_path = "data/processed/excluded_works_summary.csv"
    assert os.path.exists(excluded_path), f"Eksik dosya: {excluded_path}"
    df = pd.read_csv(excluded_path)

    assert len(df) == 641, f"Beklenen 641 dışlanan çalışma, bulunan: {len(df)}"
    assert df["work_id"].nunique() == 641, "Dışlanan çalışmalar içinde mükerrer work_id var!"

    # Yıllara göre dağılım
    year_counts = df["publication_year"].value_counts().to_dict()
    expected_years = {2020: 69, 2021: 76, 2022: 106, 2023: 132, 2024: 106, 2025: 152}
    assert year_counts == expected_years, f"Yıllık dışlanan yayın dağılımı uyuşmuyor: {year_counts}"


def test_audit_excluded_works_synthetic_pipeline():
    """
    Yerel ham veriler olmadan da çalışan, sentetik veriyle
    dışlama tespit ve CSV karşılaştırma motorunu uçtan uca doğrulayan test.
    """
    from scripts.audit_excluded_works import extract_excluded_from_raw, compare_with_processed_csv

    mock_institutions = [
        {"id": "https://openalex.org/I1", "display_name": "Test University", "type": "education", "country_code": "TR"}
    ]

    mock_works = [
        # 1. Dahil edilecek çalışma (TR eğitim kurumu var)
        {
            "id": "https://openalex.org/W_INC",
            "title": "Included Paper",
            "publication_year": 2023,
            "authorships": [{"institutions": [{"id": "https://openalex.org/I1", "country_code": "TR", "type": "education"}]}]
        },
        # 2. Dışlanacak çalışma: Yalnızca özel sektör Ar-Ge (company)
        {
            "id": "https://openalex.org/W_EXC_CORP",
            "title": "Corporate Research Work",
            "publication_year": 2022,
            "authorships": [{"institutions": [{"id": "https://openalex.org/I_CORP", "display_name": "Defense Industry Inc.", "country_code": "TR", "type": "company"}]}]
        },
        # 3. Dışlanacak çalışma: Türkiye kurumu hiç yok
        {
            "id": "https://openalex.org/W_EXC_FOREIGN",
            "title": "Foreign Collab Work",
            "publication_year": 2024,
            "authorships": [{"institutions": [{"id": "https://openalex.org/I_FOR", "display_name": "Foreign University", "country_code": "DE", "type": "education"}]}]
        }
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        meta_file = os.path.join(tmpdir, "institutions_tr.json")
        works_file = os.path.join(tmpdir, "works_mock.jsonl")
        ref_csv = os.path.join(tmpdir, "excluded_ref.csv")

        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(mock_institutions, f)

        with open(works_file, "w", encoding="utf-8") as f:
            for w in mock_works:
                f.write(json.dumps(w) + "\n")

        # Ham veriden ayıklama
        df_raw, stats = extract_excluded_from_raw(
            raw_pattern=os.path.join(tmpdir, "works_*.jsonl"),
            metadata_file=meta_file
        )

        assert stats["total_works_processed"] == 3
        assert stats["included_in_network"] == 1
        assert stats["total_excluded"] == 2
        assert len(df_raw) == 2

        # Referans CSV ile tam eşleşme testi
        df_raw.to_csv(ref_csv, index=False)
        comp_perfect = compare_with_processed_csv(df_raw, csv_path=ref_csv)
        assert comp_perfect["success"] is True
        assert comp_perfect["raw_count"] == 2
        assert comp_perfect["diff_reason_count"] == 0

        # Bilinçli alan uyuşmazlığı testi (hata tespit kontrolü)
        df_tampered = df_raw.copy()
        df_tampered.loc[0, "exclusion_reason"] = "tampered_reason"
        df_tampered.to_csv(ref_csv, index=False)
        comp_mismatch = compare_with_processed_csv(df_raw, csv_path=ref_csv)
        assert comp_mismatch["success"] is False
        assert comp_mismatch["diff_reason_count"] == 1


def test_audit_excluded_works_real_data_match():
    """
    Yerel data/raw/ dizininde gerçek OpenAlex ham verileri mevcut olduğunda,
    641 dışlanan çalışmanın tamamını sıfırdan türetir ve
    data/processed/excluded_works_summary.csv ile ALAN BAZINDA TAM EŞLEŞTİĞİNİ doğrular.
    """
    from scripts.audit_excluded_works import extract_excluded_from_raw, compare_with_processed_csv

    raw_files = glob.glob("data/raw/works_*.jsonl")
    if not raw_files or not os.path.exists("data/raw/institutions_tr.json"):
        pytest.skip("Yerel ham veriler (data/raw/) bulunamadığı için gerçek veri karşılaştırma testi atlandı.")

    df_raw, stats = extract_excluded_from_raw(
        raw_pattern="data/raw/works_*.jsonl",
        metadata_file="data/raw/institutions_tr.json"
    )

    csv_path = "data/processed/excluded_works_summary.csv"
    comp = compare_with_processed_csv(df_raw, csv_path=csv_path)

    assert comp["success"] is True, f"Ham veri ile CSV arasında uyumsuzluk tespit edildi: {comp}"
    assert comp["raw_count"] == 641, f"Beklenen 641 kayıt, bulunan: {comp['raw_count']}"
    assert comp["csv_count"] == 641
    assert comp["missing_in_csv_count"] == 0
    assert comp["extra_in_csv_count"] == 0
    assert comp["diff_year_count"] == 0
    assert comp["diff_reason_count"] == 0
    assert comp["diff_title_count"] == 0
    assert comp["diff_aff_count"] == 0


def test_audit_excluded_works_main_exit_codes():
    """
    scripts/audit_excluded_works.py betiğinin:
    - Gerçek ham veri mevcut olduğunda 0 (başarılı) döndüğünü,
    - Ham veri bulunamadığında ise 2 (DOĞRULANAMADI) döndüğünü doğrular.
    """
    from unittest.mock import patch
    from scripts import audit_excluded_works

    # 1. Ham veriler mevcutken main() çağrısı -> 0
    if os.path.exists("data/raw/works_2020.jsonl"):
        assert audit_excluded_works.main() == 0

    # 2. Ham veri bulunamadığında main() çağrısı -> 2 (DOĞRULANAMADI)
    with patch("scripts.audit_excluded_works.extract_excluded_from_raw", return_value=(pd.DataFrame(), {})):
        exit_code = audit_excluded_works.main()
        assert exit_code == 2, f"Ham veri yokken beklenen çıkış kodu 2, alınan: {exit_code}"




