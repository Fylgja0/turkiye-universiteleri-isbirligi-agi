"""
tests/test_network.py

Birim testler: Ağ kurma, kurum sınıflandırma, kapsam metrikleri
ve veri işleme kurallarının doğrulanması.

Test Kapsamı:
1. ID normalizasyonu ve Ege bölgesi tespit doğruluğu
2. Sentetik küçük örnekle ağ kurma kuralları (self-loop engeli, ağırlık hesabı, izole düğüm koruma)
3. 2016 KHK ile kapatılan kurumlar ve aktif üniversitelerin ID bazlı sınıflandırma doğruluğu
4. Kapatılan İzmir Üniversitesi'nin ve aktif Malatya Turgut Özal Üniversitesi'nin ayrımı
5. Ham veriler/işlenmiş dosyalar üzerinde GraphML ve CSV tutarlılığı, düğüm/kenar eşitliği
6. Kapsam A, Kapsam B ve Kapsam B1 düğüm/kenar sayısı tutarlılığı
"""

import os
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
    2016 KHK ile kapatılan kurumların, aktif üniversitelerin, MYO ve akademilerin
    ID bazında ve unverified güvenliğiyle doğru sınıflandırıldığını doğrular.
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

    # 5. Kapatılan Gediz, Şifa, Bursa Orhangazi, Canik Başarı
    for iid, name in [
        ("https://openalex.org/I149028718", "Gediz University"),
        ("https://openalex.org/I334480368", "Şifa University"),
        ("https://openalex.org/I3003364", "Bursa Orhangazi University"),
        ("https://openalex.org/I264664839", "Canik Başarı University")
    ]:
        c, u = classify_institution(iid, name)
        assert c == "closed_2016_khk", f"{name} should be closed_2016_khk"
        assert u is True

    # 6. Bağımsız MYO kontrolü
    cat_myo, is_uni_myo = classify_institution("https://openalex.org/I4210151063", "İzmir Kavram Meslek Yüksekokulu", raw_status="active")
    assert cat_myo == "vocational_college"
    assert is_uni_myo is False

    # 7. Askeri Akademi kontrolü
    cat_mil, is_uni_mil = classify_institution("https://openalex.org/I157637111", "Naval Academy", raw_status="active")
    assert cat_mil == "academy_or_institute"
    assert is_uni_mil is False

    # 8. Tanınmayan kurum ve inactive status kontrolü -> unverified
    cat_unv, is_uni_unv = classify_institution("https://openalex.org/I999999", "Random Unknown Research Lab", raw_status="active")
    assert cat_unv == "unverified"
    assert is_uni_unv is False

    cat_inact, is_uni_inact = classify_institution("https://openalex.org/I888888", "Some Fake Entity", raw_status="inactive")
    assert cat_inact == "unverified"
    assert is_uni_inact is False


def test_network_construction_rules():
    """
    Örnek sentetik yayınlarla kuralları test eder:
    - Yayın 1: Kurum A (2 yazar), Kurum B (1 yazar) -> (A, B) ağırlığı 1 olmalı, (A, A) self-loop OLMAMALI.
    - Yayın 2: Kurum A, Kurum B, Kurum C -> (A, B), (A, C), (B, C) ağırlıkları +1 artmalı.
    - Yayın 3: Kurum D tek başına yayın yapmış -> D izole düğüm olarak ağda kalmalı (degree=0).
    """
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
        # Yayın 1: Kurum A'dan 2 yazar, Kurum B'den 1 yazar
        {
            "id": "https://openalex.org/W1",
            "title": "Paper 1",
            "authorships": [
                {"institutions": [{"id": "https://openalex.org/I_A", "country_code": "TR", "type": "education"}]},
                {"institutions": [{"id": "https://openalex.org/I_A", "country_code": "TR", "type": "education"}]},
                {"institutions": [{"id": "https://openalex.org/I_B", "country_code": "TR", "type": "education"}]}
            ]
        },
        # Yayın 2: Kurum A, B, C üçlü iş birliği
        {
            "id": "https://openalex.org/W2",
            "title": "Paper 2",
            "authorships": [
                {"institutions": [{"id": "https://openalex.org/I_A", "country_code": "TR", "type": "education"}]},
                {"institutions": [{"id": "https://openalex.org/I_B", "country_code": "TR", "type": "education"}]},
                {"institutions": [{"id": "https://openalex.org/I_C", "country_code": "TR", "type": "education"}]}
            ]
        },
        # Yayın 3: Kurum D tek başına (izole düğüm testi)
        {
            "id": "https://openalex.org/W3",
            "title": "Paper 3",
            "authorships": [
                {"institutions": [{"id": "https://openalex.org/I_D", "country_code": "TR", "type": "education"}]}
            ]
        },
        # Yayın 4: Yabancı kurum veya geçersiz veri (elenmeli)
        {
            "id": "https://openalex.org/W4",
            "title": "Paper 4",
            "authorships": [
                {"institutions": [{"id": "https://openalex.org/I_FOREIGN", "country_code": "US", "type": "education"}]},
                {"institutions": []}
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
        assert "period_cs_works_count" in inst_df.columns
        assert "all_time_works_count" in inst_df.columns


def test_processed_files_consistency():
    """
    Mevcut data/processed dizinindeki gerçek GraphML ve CSV dosyalarının
    toplam tutarlılığını, eşitliğini ve kenar bağlantılarını doğrular.
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

    # 1. Toplam düğüm ve kenar sayıları tam eşit olmalı
    assert len(inst_df) == 205
    assert G.number_of_nodes() == 205
    assert len(edges_df) == 3970
    assert G.number_of_edges() == 3970

    # 2. Düğüm kimlikleri kümesi birebir eşleşmeli
    csv_node_set = set(inst_df["id"])
    graph_node_set = set(G.nodes())
    assert csv_node_set == graph_node_set

    # 3. Tüm kenarların source ve target uçları geçerli birer düğüm olmalı
    for _, row in edges_df.iterrows():
        src = row["source"]
        tgt = row["target"]
        assert src in csv_node_set, f"Geçersiz source düğümü: {src}"
        assert tgt in csv_node_set, f"Geçersiz target düğümü: {tgt}"
        assert src != tgt, f"Self-loop bulundu: {src} == {tgt}"
        assert row["weight"] >= 1

    # 4. Kategori dağılımı toplamı tam 205 olmalı
    cat_counts = inst_df["category"].value_counts().to_dict()
    assert cat_counts["active_university"] == 188
    assert cat_counts["closed_2016_khk"] == 7
    assert cat_counts["academy_or_institute"] == 5
    assert cat_counts["hospital_or_other"] == 3
    assert cat_counts["vocational_college"] == 2
    assert sum(cat_counts.values()) == 205

    # 5. Kapatılan İzmir Üniversitesi ve aktif Malatya Turgut Özal kontrolü
    izmir_row = inst_df[inst_df["id"] == "https://openalex.org/I132257509"].iloc[0]
    assert izmir_row["category"] == "closed_2016_khk"
    assert izmir_row["is_university"] == True

    malatya_row = inst_df[inst_df["id"] == "https://openalex.org/I4210110665"].iloc[0]
    assert malatya_row["category"] == "active_university"
    assert malatya_row["is_university"] == True


def test_scopes_metrics_exact_values():
    """
    Kapsam A, Kapsam B ve Kapsam B1 için hesaplanan kesin metrikleri doğrular.
    """
    G = nx.read_graphml("data/processed/collaboration.graphml")

    # Kapsam A
    assert G.number_of_nodes() == 205
    assert G.number_of_edges() == 3970
    assert nx.number_connected_components(G) == 4
    assert len(list(nx.isolates(G))) == 3

    # Kapsam B: is_university == True (195 düğüm)
    uni_nodes = [n for n, d in G.nodes(data=True) if d.get("is_university", True)]
    G_B = G.subgraph(uni_nodes)
    assert G_B.number_of_nodes() == 195
    assert G_B.number_of_edges() == 3896
    assert nx.number_connected_components(G_B) == 2
    assert len(list(nx.isolates(G_B))) == 1

    # Kapsam B1: category == "active_university" (188 düğüm)
    active_uni_nodes = [n for n, d in G.nodes(data=True) if d.get("category") == "active_university"]
    G_B1 = G.subgraph(active_uni_nodes)
    assert G_B1.number_of_nodes() == 188
    assert G_B1.number_of_edges() == 3861
    assert nx.number_connected_components(G_B1) == 1
    assert len(list(nx.isolates(G_B1))) == 0
