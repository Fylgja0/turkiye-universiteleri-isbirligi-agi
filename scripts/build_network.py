#!/usr/bin/env python3
"""
scripts/build_network.py

Manisa Celal Bayar Üniversitesi - Büyük Veri Analistliği
Sosyal Ağ Analizi Projesi: Türk Üniversiteleri Arası Bilimsel İş Birliği

İndirilen ham verileri (data/raw/works_*.jsonl ve data/raw/institutions_tr.json)
işleyerek yönsüz ve ağırlıklı iş birliği ağını kurar.

Üretilen Çıktılar:
- data/processed/edges.csv (source, target, weight)
- data/processed/institutions.csv (id, display_name, country_code, type, latitude, longitude, city, works_count, is_egean, degree)
- data/processed/collaboration.graphml (NetworkX GraphML)

Kurallar:
- Düğüm: Türkiye'deki üniversite/eğitim kurumları.
- Kenar: Aynı yayında yer alan farklı Türk kurumları arası ortak yazarlık.
- Ağırlık: Ortak yayın sayısı.
- Yinelenen kurumlar yayında tekilleştirilir; self-loop oluşturulmaz.
- İzole düğümler (ortak yayını olmayan ama veride yer alan kurumlar) ağdan silinmez.
"""

import os
import glob
import json
import logging
import itertools
import unicodedata
from collections import defaultdict
from typing import Dict, Set, Tuple, Any, Optional

import pandas as pd
import networkx as nx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("build_network")

EGEAN_CITIES = {
    "izmir", "manisa", "aydın", "aydin", "denizli",
    "muğla", "mugla", "afyonkarahisar", "afyon", "kütahya", "kutahya", "uşak", "usak"
}


def normalize_id(openalex_id: Optional[str]) -> Optional[str]:
    """OpenAlex ID'sini standart URL formatına getirir."""
    if not openalex_id:
        return None
    openalex_id = openalex_id.strip()
    if openalex_id.startswith("http://"):
        openalex_id = "https://" + openalex_id[7:]
    if not openalex_id.startswith("https://openalex.org/"):
        if openalex_id.startswith("I"):
            return f"https://openalex.org/{openalex_id}"
    return openalex_id


def is_egean_institution(display_name: str, city: Optional[str]) -> bool:
    """Kurumun Ege Bölgesi'nde yer alıp almadığını tespit eder."""
    if city and city.strip():
        # Şehir bilgisi biliniyorsa doğrudan Ege şehirleri listesine bak
        return city.strip().lower() in EGEAN_CITIES

    # Şehir bilgisi yoksa kurum adından kontrol et
    name_lower = display_name.lower()
    if "istanbul aydın" in name_lower or "istanbul aydin" in name_lower:
        return False
    for ege_city in EGEAN_CITIES:
        if ege_city in name_lower:
            return True
    if "ege university" in name_lower or "dokuz eylül" in name_lower or "celal bayar" in name_lower:
        return True
    if "pamukkale" in name_lower or "adnan menderes" in name_lower or "muğla sıtkı koçman" in name_lower:
        return True
    return False


def load_tr_institutions(metadata_file: str = "data/raw/institutions_tr.json") -> Dict[str, Dict[str, Any]]:
    """OpenAlex'ten çekilen Türkiye kurumları üstverisini yükler."""
    if not os.path.exists(metadata_file):
        logger.warning(f"Kurum üstveri dosyası bulunamadı: {metadata_file}. Boş sözlük ile devam ediliyor.")
        return {}

    with open(metadata_file, "r", encoding="utf-8") as f:
        inst_list = json.load(f)

    institutions_dict = {}
    for item in inst_list:
        raw_id = item.get("id")
        norm_id = normalize_id(raw_id)
        if not norm_id:
            continue

        geo = item.get("geo") or {}
        city = geo.get("city")
        lat = geo.get("latitude")
        lon = geo.get("longitude")
        display_name = item.get("display_name", "").strip()

        institutions_dict[norm_id] = {
            "id": norm_id,
            "display_name": display_name,
            "country_code": item.get("country_code", "TR"),
            "type": item.get("type", "education"),
            "latitude": lat if lat is not None else None,
            "longitude": lon if lon is not None else None,
            "city": city if city is not None else "",
            "works_count": item.get("works_count", 0),
            "status": item.get("status", "active"),
            "is_egean": is_egean_institution(display_name, city)
        }

    logger.info(f"{len(institutions_dict)} Türkiye eğitim kurumu üstverisi yüklendi.")
    return institutions_dict


def classify_institution(iid: str, display_name: str, raw_status: Optional[str] = None) -> Tuple[str, bool]:
    """
    Kurumu ROR/OpenAlex ve resmi kayıtlar doğrultusunda sınıflandırır:
    - active_university (Halen aktif üniversiteler ve yüksek teknoloji enstitüleri)
    - closed_2016_khk (2016 KHK ile kapatılmış tarihsel vakıf üniversiteleri)
    - vocational_college (Vakıf Meslek Yüksekokulları - Bağımsız MYO)
    - academy_or_institute (Harp Okulları, Polis Akademisi, yabancı enstitüler)
    - hospital_or_other (EAH, İl MEM, araştırma merkezleri vb.)
    - unverified (Resmi üniversite statüsü doğrulanamamış/kanıtlanmamış kurumlar)
    Dönüş: (kategori_adi, is_university_flag)
    """
    name_l = display_name.lower().strip()
    
    # 1. 2016 yılında 667 sayılı KHK ile kapatılan vakıf üniversiteleri (ID bazında kesin doğrulama)
    closed_2016_map = {
        "https://openalex.org/I6573832": "Turgut Özal University",
        "https://openalex.org/I32462889": "Fatih University",
        "https://openalex.org/I149028718": "Gediz University",
        "https://openalex.org/I334480368": "Şifa University",
        "https://openalex.org/I3003364": "Bursa Orhangazi University",
        "https://openalex.org/I264664839": "Canik Başarı University",
        "https://openalex.org/I132257509": "Izmir University"
    }
    if iid in closed_2016_map:
        return "closed_2016_khk", True

    # 2. Doğrulanmamış veya hukuki statüsü kısıtlı kurumlar (ID bazında doğrulama)
    # - Lefke Avrupa Üniversitesi: Coğrafi olarak KKTC'de yer alır, Türkiye sınırları içinde değildir.
    # - İstanbul Şehir Üniversitesi: 30 Haziran 2020'de 2814 sayılı CBK ile kapatılmıştır; OpenAlex status active görünse de hukuken aktif değildir.
    unverified_special_map = {
        "https://openalex.org/I116528569": "European University of Lefke",
        "https://openalex.org/I13419840": "Istanbul Şehir University"
    }
    if iid in unverified_special_map:
        return "unverified", False

    # 3. OpenAlex raw_status kontrolü (aktif olmayan kayıtlar doğrudan aktif üniversite olamaz)
    if raw_status and str(raw_status).strip().lower() in ["inactive", "closed", "defunct"]:
        return "unverified", False
        
    # 3. Bağımsız Meslek Yüksekokulları (MYO)
    if "meslek yüksekokulu" in name_l or "vocational school" in name_l:
        return "vocational_college", False
        
    # 4. Askeri / Polis Akademileri ve Yabancı Enstitüler
    if any(k in name_l for k in ["naval academy", "air force academy", "military academy", "police academy", "british institute"]):
        return "academy_or_institute", False
        
    # 5. Sağlık / İdari / Araştırma Merkezleri
    if any(k in name_l for k in ["hospital", "hastanesi", "directorate of national education", "research center for built environment"]):
        return "hospital_or_other", False
        
    # 6. Doğrulanmış Aktif Üniversiteler
    norm_name = unicodedata.normalize("NFKD", display_name).encode("ASCII", "ignore").decode("utf-8").lower()
    is_uni_named = any(k in norm_name for k in ["university", "universite", "institute of technology", "universitat"])
    if is_uni_named and (raw_status is None or str(raw_status).strip().lower() == "active"):
        return "active_university", True

    # 7. Kanıtlanmamış / resmi üniversite statüsü belirsiz olan kurumlar
    return "unverified", False


def process_works_and_build_network(
    works_files_pattern: str = "data/raw/works_*.jsonl",
    institutions_metadata: Optional[Dict[str, Dict[str, Any]]] = None
) -> Tuple[nx.Graph, pd.DataFrame, pd.DataFrame]:
    """
    Ham yayın kayıtlarını okuyarak ortak yazarlık ağını kurar.
    """
    if institutions_metadata is None:
        institutions_metadata = load_tr_institutions()

    file_paths = sorted(glob.glob(works_files_pattern))
    if not file_paths:
        raise FileNotFoundError(f"'{works_files_pattern}' desenine uyan çalışma dosyası bulunamadı!")

    logger.info(f"{len(file_paths)} çalışma dosyası işlenecek: {file_paths}")

    # Ağ yapıları
    edge_weights: Dict[Tuple[str, str], int] = defaultdict(int)
    observed_in_works: Set[str] = set()
    period_cs_works: Dict[str, int] = defaultdict(int)
    total_works_processed = 0
    works_with_tr_inst = 0
    works_with_collaboration = 0

    # Ekstra kurum keşfi (metadata dosyasında olmayan ama makalede education + TR olanlar için)
    dynamic_institutions: Dict[str, Dict[str, Any]] = {}

    for fpath in file_paths:
        logger.info(f"Dosya okunuyor: {fpath}...")
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    work = json.loads(line)
                except json.JSONDecodeError:
                    continue

                total_works_processed += 1
                authorships = work.get("authorships", [])
                
                # Bu çalışmada yer alan geçerli Türkiye kurumlarını tekilleştir
                paper_institutions: Set[str] = set()
                for auth in authorships:
                    inst_list = auth.get("institutions", [])
                    for inst in inst_list:
                        raw_id = inst.get("id")
                        norm_id = normalize_id(raw_id)
                        if not norm_id:
                            continue

                        country = inst.get("country_code")
                        inst_type = inst.get("type")
                        
                        # Eğer metadata'da zaten varsa veya country_code TR ise
                        if norm_id in institutions_metadata:
                            paper_institutions.add(norm_id)
                        elif country == "TR" and inst_type == "education":
                            paper_institutions.add(norm_id)
                            if norm_id not in dynamic_institutions:
                                disp_name = inst.get("display_name", "")
                                dynamic_institutions[norm_id] = {
                                    "id": norm_id,
                                    "display_name": disp_name,
                                    "country_code": "TR",
                                    "type": "education",
                                    "latitude": None,
                                    "longitude": None,
                                    "city": "",
                                    "works_count": 0,
                                    "is_egean": is_egean_institution(disp_name, None)
                                }

                if paper_institutions:
                    works_with_tr_inst += 1
                    observed_in_works.update(paper_institutions)
                    for inst_id in paper_institutions:
                        period_cs_works[inst_id] += 1

                # Farklı kurumlar arasında kenar oluştur
                if len(paper_institutions) >= 2:
                    works_with_collaboration += 1
                    # Kombinasyonları sıralı alarak yönsüzlüğü garanti et (u < v)
                    sorted_insts = sorted(list(paper_institutions))
                    for u, v in itertools.combinations(sorted_insts, 2):
                        # Self-loop kontrolü
                        if u == v:
                            continue
                        edge_weights[(u, v)] += 1

    logger.info(f"Toplam işlenen yayın: {total_works_processed}")
    logger.info(f"Türkiye kurumu içeren yayın: {works_with_tr_inst}")
    logger.info(f"En az iki Türk kurumu arasında iş birliği içeren yayın: {works_with_collaboration}")
    logger.info(f"Yayınlarda gözlemlenen tekil Türk kurumu sayısı: {len(observed_in_works)}")
    logger.info(f"Oluşturulan tekil kenar sayısı: {len(edge_weights)}")

    # NetworkX Grafiğini Oluştur
    G = nx.Graph()

    # Düğümleri ekle
    for node_id in observed_in_works:
        meta = institutions_metadata.get(node_id) or dynamic_institutions.get(node_id, {})
        disp_name = meta.get("display_name", node_id)
        city = meta.get("city", "")
        is_ege = meta.get("is_egean", False)
        lat = meta.get("latitude")
        lon = meta.get("longitude")
        all_time_w = meta.get("works_count", 0)
        period_w = period_cs_works.get(node_id, 0)
        raw_stat = meta.get("status")
        cat, is_uni = classify_institution(node_id, disp_name, raw_status=raw_stat)

        node_attrs = {
            "name": disp_name,
            "display_name": disp_name,
            "country_code": "TR",
            "type": "education",
            "category": cat,
            "is_university": bool(is_uni),
            "raw_status": str(raw_stat) if raw_stat else "active",
            "city": city or "",
            "is_egean": bool(is_ege),
            "works_count": int(all_time_w) if all_time_w is not None else 0,
            "all_time_works_count": int(all_time_w) if all_time_w is not None else 0,
            "period_cs_works_count": int(period_w)
        }
        if lat is not None:
            node_attrs["latitude"] = float(lat)
        if lon is not None:
            node_attrs["longitude"] = float(lon)

        G.add_node(node_id, **node_attrs)

    # Kenarları ekle
    edge_rows = []
    for (u, v), w in edge_weights.items():
        if u in G and v in G and w > 0:
            G.add_edge(u, v, weight=int(w))
            edge_rows.append({
                "source": u,
                "target": v,
                "weight": int(w)
            })

    edges_df = pd.DataFrame(edge_rows)
    if not edges_df.empty:
        edges_df = edges_df.sort_values(by="weight", ascending=False).reset_index(drop=True)

    # Kurumlar tablosunu hazırla
    inst_rows = []
    for node_id in G.nodes():
        attrs = G.nodes[node_id]
        degree = G.degree(node_id)
        weighted_degree = G.degree(node_id, weight="weight")
        inst_rows.append({
            "id": node_id,
            "display_name": attrs.get("display_name", ""),
            "country_code": attrs.get("country_code", "TR"),
            "type": attrs.get("type", "education"),
            "category": attrs.get("category", "active_university"),
            "is_university": attrs.get("is_university", True),
            "raw_status": attrs.get("raw_status", "active"),
            "latitude": attrs.get("latitude", None),
            "longitude": attrs.get("longitude", None),
            "city": attrs.get("city", ""),
            "all_time_works_count": attrs.get("all_time_works_count", 0),
            "period_cs_works_count": attrs.get("period_cs_works_count", 0),
            "works_count": attrs.get("works_count", 0),
            "is_egean": attrs.get("is_egean", False),
            "degree": degree,
            "weighted_degree": weighted_degree,
            "is_isolated": (degree == 0)
        })

    inst_df = pd.DataFrame(inst_rows)
    if not inst_df.empty:
        inst_df = inst_df.sort_values(by="degree", ascending=False).reset_index(drop=True)

    return G, edges_df, inst_df


def save_processed_network(
    G: nx.Graph,
    edges_df: pd.DataFrame,
    inst_df: pd.DataFrame,
    output_dir: str = "data/processed"
):
    """İşlenen ağ verilerini belirtilen çıktı dizinine kaydeder."""
    os.makedirs(output_dir, exist_ok=True)

    edges_csv_path = os.path.join(output_dir, "edges.csv")
    inst_csv_path = os.path.join(output_dir, "institutions.csv")
    graphml_path = os.path.join(output_dir, "collaboration.graphml")

    edges_df.to_csv(edges_csv_path, index=False, encoding="utf-8")
    logger.info(f"Ağırlıklı kenar listesi kaydedildi -> {edges_csv_path} ({len(edges_df)} kenar)")

    inst_df.to_csv(inst_csv_path, index=False, encoding="utf-8")
    logger.info(f"Kurumlar tablosu kaydedildi -> {inst_csv_path} ({len(inst_df)} kurum)")

    # GraphML yazımı: NetworkX öznitelik tiplerini korur
    nx.write_graphml(G, graphml_path)
    logger.info(f"GraphML ağı kaydedildi -> {graphml_path}")


def print_network_summary(G: nx.Graph, inst_df: pd.DataFrame, edges_df: pd.DataFrame):
    """Ağ metriklerini özetler ve terminale basar."""
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    density = nx.density(G)
    num_components = nx.number_connected_components(G)
    isolated_nodes = list(nx.isolates(G))
    egean_count = inst_df[inst_df["is_egean"] == True].shape[0] if not inst_df.empty else 0

    print("\n" + "="*70)
    print("AĞ ANALİZİ VE YAPI METRİKLERİ: KAPSAM A (TÜM EDUCATION KURUMLARI)")
    print("="*70)
    print(f"Toplam Düğüm Sayısı (Kurum) : {num_nodes}")
    print(f"Toplam Kenar Sayısı         : {num_edges}")
    print(f"Ağ Yoğunluğu (Density)      : {density:.6f}")
    print(f"Bağlı Bileşen Sayısı        : {num_components}")
    print(f"İzole Düğüm Sayısı          : {len(isolated_nodes)}")
    print(f"Ege Bölgesi Kurum Sayısı    : {egean_count}")

    if num_components > 0 and num_nodes > 0:
        largest_cc = max(nx.connected_components(G), key=len)
        print(f"Dev Bileşen (Giant Comp.)   : {len(largest_cc)} düğüm ({len(largest_cc)/num_nodes*100:.1f}%)")

    # Kapsam B (Yalnızca Üniversiteler)
    uni_nodes = [n for n, d in G.nodes(data=True) if d.get("is_university", True)]
    G_B = G.subgraph(uni_nodes).copy()
    num_nodes_b = G_B.number_of_nodes()
    num_edges_b = G_B.number_of_edges()
    density_b = nx.density(G_B) if num_nodes_b > 1 else 0
    num_comp_b = nx.number_connected_components(G_B)
    isolates_b = list(nx.isolates(G_B))
    largest_cc_b = max(nx.connected_components(G_B), key=len) if num_nodes_b > 0 else []

    print("\n" + "-"*70)
    print("AĞ ANALİZİ VE YAPI METRİKLERİ: KAPSAM B (YALNIZCA ÜNİVERSİTELER - TARİHSEL DAHİL)")
    print("-"*70)
    print(f"Toplam Düğüm Sayısı         : {num_nodes_b}")
    print(f"Toplam Kenar Sayısı         : {num_edges_b}")
    print(f"Ağ Yoğunluğu (Density)      : {density_b:.6f}")
    print(f"Bağlı Bileşen Sayısı        : {num_comp_b}")
    print(f"İzole Düğüm Sayısı          : {len(isolates_b)}")
    print(f"Dev Bileşen (Giant Comp.)   : {len(largest_cc_b)} düğüm ({len(largest_cc_b)/num_nodes_b*100:.1f}%)")

    # Kapsam B1 (Yalnızca Halen Aktif Üniversiteler)
    active_uni_nodes = [n for n, d in G.nodes(data=True) if d.get("category") == "active_university"]
    G_B1 = G.subgraph(active_uni_nodes).copy()
    num_nodes_b1 = G_B1.number_of_nodes()
    num_edges_b1 = G_B1.number_of_edges()
    density_b1 = nx.density(G_B1) if num_nodes_b1 > 1 else 0
    num_comp_b1 = nx.number_connected_components(G_B1)
    isolates_b1 = list(nx.isolates(G_B1))

    print("\n" + "-"*70)
    print("AĞ ANALİZİ VE YAPI METRİKLERİ: KAPSAM B1 (YALNIZCA HALEN AKTİF ÜNİVERSİTELER)")
    print("-"*70)
    print(f"Toplam Düğüm Sayısı         : {num_nodes_b1}")
    print(f"Toplam Kenar Sayısı         : {num_edges_b1}")
    print(f"Ağ Yoğunluğu (Density)      : {density_b1:.6f}")
    print(f"Bağlı Bileşen Sayısı        : {num_comp_b1}")
    print(f"İzole Düğüm Sayısı          : {len(isolates_b1)}")
    if num_comp_b1 > 0 and num_nodes_b1 > 0:
        largest_cc_b1 = max(nx.connected_components(G_B1), key=len)
        print(f"Dev Bileşen (Giant Comp.)   : {len(largest_cc_b1)} düğüm ({len(largest_cc_b1)/num_nodes_b1*100:.1f}%)")

    if not inst_df.empty:
        top_inst = inst_df.head(5)
        print("\nEn Yüksek Dereceye Sahip İlk 5 Üniversite (Kapsam A):")
        for _, row in top_inst.iterrows():
            print(f" - {row['display_name']} ({row['city']}): Derece={row['degree']}, Ağırlıklı={row['weighted_degree']}, 2020-25 CS={row['period_cs_works_count']}, Tüm Zamanlar={row['all_time_works_count']}")

    print("="*70 + "\n")


def main():
    metadata = load_tr_institutions("data/raw/institutions_tr.json")
    G, edges_df, inst_df = process_works_and_build_network(
        works_files_pattern="data/raw/works_*.jsonl",
        institutions_metadata=metadata
    )
    save_processed_network(G, edges_df, inst_df, output_dir="data/processed")
    print_network_summary(G, inst_df, edges_df)


if __name__ == "__main__":
    main()
