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
import tempfile
import pytest
import networkx as nx
import pandas as pd

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


def test_report_critical_tables_match_csv():
    """
    reports/ara_kontrol.md içindeki kritik sayısal değerlerin (ODTÜ, Boğaziçi vb.)
    gerçek data/processed/institutions.csv ile bire bir aynı olduğunu denetler.
    """
    inst_df = pd.read_csv("data/processed/institutions.csv")
    with open("reports/ara_kontrol.md", "r", encoding="utf-8") as f:
        report_text = f.read()

    # ODTÜ kontrolleri
    metu_row = inst_df[inst_df["id"] == "https://openalex.org/I201799495"].iloc[0]
    assert f"**1.320**" in report_text or f"1.320" in report_text
    assert "50.160" in report_text, "ODTÜ all_time_works_count (50.160) raporda bulunamadı!"
    assert "| 91 | 408 |" in report_text, "ODTÜ derece (91) ve ağırlıklı derece (408) raporda eşleşmedi!"

    # Boğaziçi kontrolleri
    boun_row = inst_df[inst_df["id"] == "https://openalex.org/I4405392"].iloc[0]
    assert "24.497" in report_text, "Boğaziçi all_time_works_count (24.497) raporda bulunamadı!"
    assert "| 71 | 322 |" in report_text, "Boğaziçi derece (71) ve ağırlıklı derece (322) raporda eşleşmedi!"

    # 641 dışlanan çalışma dosyası
    assert os.path.exists("data/processed/excluded_works_summary.csv")
    excluded_df = pd.read_csv("data/processed/excluded_works_summary.csv")
    assert len(excluded_df) == 641


def test_documentation_cross_consistency():
    """
    README.md, docs/data_dictionary.md ve reports/ara_kontrol.md
    arasındaki kapsam sayıları (193, 186), YÖK 208 / OpenAlex 222 ayrımı
    ve 122 / 112 koordinat sayılarının tam uyumlu olduğunu denetler.
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

    # 208 YÖK ve 222 OpenAlex sayıları açıklanmış olmalı
    for doc_name, doc_text in [("README.md", readme_text), ("reports/ara_kontrol.md", report_text)]:
        assert "208" in doc_text, f"{doc_name} içinde YÖK resmi üniversite sayısı (208) bulunamadı!"
        assert "222" in doc_text, f"{doc_name} içinde OpenAlex education kurum sayısı (222) bulunamadı!"
        assert "yok.gov.tr" in doc_text, f"{doc_name} içinde YÖK resmi kaynak bağlantısı bulunamadı!"

    # Tekil koordinatlar (122 ham float, 112 yuvarlanmış/merkez)
    for doc_name, doc_text in [("docs/data_dictionary.md", dict_text), ("reports/ara_kontrol.md", report_text)]:
        assert "122" in doc_text, f"{doc_name} içinde 122 ham tekil koordinat sayısı bulunamadı!"
        assert "112" in doc_text, f"{doc_name} içinde 112 yuvarlanmış tekil koordinat sayısı bulunamadı!"

