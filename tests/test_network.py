"""
tests/test_network.py

Birim testler: Ağ kurma ve veri işleme kurallarının doğrulanması.
Küçük yerel örnek veri kullanarak:
- Yinelenen kurumların tekilleştirilmesi,
- Self-loop'ların engellenmesi,
- İkili kombinasyon ve ağırlık hesaplama doğruluğu,
- İzole düğümlerin silinmemesi,
- Eksik veya hatalı alanların güvenle ele alınması test edilir.
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
    assert is_egean_institution("Dokuz Eylül University", "") is True
    assert is_egean_institution("Pamukkale University", "Denizli") is True
    assert is_egean_institution("Middle East Technical University", "Ankara") is False
    assert is_egean_institution("Istanbul Technical University", "Istanbul") is False


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
            "display_name": "Kurum A (Ege)",
            "city": "Izmir",
            "type": "education",
            "country_code": "TR",
            "latitude": 38.42,
            "longitude": 27.14,
            "works_count": 100,
            "is_egean": True
        },
        "https://openalex.org/I_B": {
            "id": "https://openalex.org/I_B",
            "display_name": "Kurum B (Ankara)",
            "city": "Ankara",
            "type": "education",
            "country_code": "TR",
            "latitude": 39.93,
            "longitude": 32.85,
            "works_count": 200,
            "is_egean": False
        },
        "https://openalex.org/I_C": {
            "id": "https://openalex.org/I_C",
            "display_name": "Kurum C (Istanbul)",
            "city": "Istanbul",
            "type": "education",
            "country_code": "TR",
            "latitude": 41.01,
            "longitude": 28.97,
            "works_count": 150,
            "is_egean": False
        },
        "https://openalex.org/I_D": {
            "id": "https://openalex.org/I_D",
            "display_name": "Kurum D (Izole)",
            "city": "Trabzon",
            "type": "education",
            "country_code": "TR",
            "latitude": 41.00,
            "longitude": 39.72,
            "works_count": 50,
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

        # 1. Düğüm sayısı doğrulaması: A, B, C, D olmak üzere tam 4 düğüm olmalı
        assert G.number_of_nodes() == 4
        assert "https://openalex.org/I_A" in G
        assert "https://openalex.org/I_B" in G
        assert "https://openalex.org/I_C" in G
        assert "https://openalex.org/I_D" in G
        assert "https://openalex.org/I_FOREIGN" not in G

        # 2. Self-loop kontrolü: Hiçbir düğümün kendisine kenarı olmamalı
        assert nx.number_of_selfloops(G) == 0

        # 3. İzole düğüm kontrolü: Kurum D'nin derecesi 0 olmalı ve ağda bulunmalı
        assert G.degree("https://openalex.org/I_D") == 0
        assert nx.is_isolate(G, "https://openalex.org/I_D")

        # 4. Kenar ağırlıkları kontrolü
        # A <-> B: Paper 1 (+1) ve Paper 2 (+1) -> ağırlık 2 olmalı
        assert G.has_edge("https://openalex.org/I_A", "https://openalex.org/I_B")
        assert G["https://openalex.org/I_A"]["https://openalex.org/I_B"]["weight"] == 2

        # A <-> C: Paper 2 (+1) -> ağırlık 1 olmalı
        assert G.has_edge("https://openalex.org/I_A", "https://openalex.org/I_C")
        assert G["https://openalex.org/I_A"]["https://openalex.org/I_C"]["weight"] == 1

        # B <-> C: Paper 2 (+1) -> ağırlık 1 olmalı
        assert G.has_edge("https://openalex.org/I_B", "https://openalex.org/I_C")
        assert G["https://openalex.org/I_B"]["https://openalex.org/I_C"]["weight"] == 1

        # Toplam kenar sayısı 3 olmalı
        assert G.number_of_edges() == 3

        # 5. DataFrame doğrulamaları
        assert len(edges_df) == 3
        assert set(edges_df.columns) == {"source", "target", "weight"}
        assert edges_df["weight"].min() >= 1

        assert len(inst_df) == 4
        assert "is_egean" in inst_df.columns
        ege_rows = inst_df[inst_df["id"] == "https://openalex.org/I_A"]
        assert ege_rows.iloc[0]["is_egean"] == True
