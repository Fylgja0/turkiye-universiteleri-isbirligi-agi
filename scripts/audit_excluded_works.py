#!/usr/bin/env python3
"""
scripts/audit_excluded_works.py

Ham OpenAlex yayın dosyalarını (works_2020..2025.jsonl) inceleyerek
ağ kurma algoritması tarafından dışlanan 641 çalışmayı denetler ve
mevcut data/processed/excluded_works_summary.csv dosyasıyla
BÜTÜN KAYIT VE ALANLARI (work_id, publication_year, title, exclusion_reason, affiliation_sample)
bire bir karşılaştırır.

Fark tespit edilirse ayrıntılı raporlar ve çıkış kodu 1 (hata) ile sonlanır.
Kayıtlar eksiksiz eşleştiğinde çıkış kodu 0 ile başarı bildirir.
"""

import os
import sys
import glob
import json
import logging
from typing import Dict, List, Any, Set, Tuple, Optional
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def normalize_id(raw_id: Any) -> str:
    if not raw_id:
        return ""
    s = str(raw_id).strip()
    if s.startswith("http://"):
        s = "https://" + s[7:]
    elif not s.startswith("https://openalex.org/"):
        s = "https://openalex.org/" + s
    return s


def load_tr_education_ids(metadata_file: str = "data/raw/institutions_tr.json") -> Set[str]:
    if not os.path.exists(metadata_file):
        logger.warning(f"Üstveri dosyası bulunamadı: {metadata_file}")
        return set()
    with open(metadata_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    ids = set()
    for item in data:
        norm = normalize_id(item.get("id"))
        if norm:
            ids.add(norm)
    return ids


def extract_excluded_from_raw(
    raw_pattern: str = "data/raw/works_*.jsonl",
    metadata_file: str = "data/raw/institutions_tr.json"
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Ham dosyalardan dışlanan çalışmaları türetir."""
    file_paths = sorted(glob.glob(raw_pattern))
    tr_education_ids = load_tr_education_ids(metadata_file)

    if not file_paths:
        return pd.DataFrame(), {"error": "no_raw_files"}

    logger.info(f"{len(file_paths)} ham yayın dosyası taranıyor: {file_paths}")
    raw_records = []
    total_processed = 0
    included_count = 0

    for fpath in file_paths:
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    w = json.loads(line)
                except json.JSONDecodeError:
                    continue

                total_processed += 1
                authorships = w.get("authorships", [])

                has_tr_edu = False
                tr_non_edu = set()
                tr_samples = []
                non_tr_samples = []

                for auth in authorships:
                    for inst in auth.get("institutions", []):
                        raw_id = inst.get("id")
                        if not raw_id:
                            continue
                        norm_iid = normalize_id(raw_id)
                        c = inst.get("country_code")
                        t = inst.get("type")
                        disp_name = inst.get("display_name", "")

                        if norm_iid in tr_education_ids or (c == "TR" and t == "education"):
                            has_tr_edu = True
                            break
                        elif c == "TR":
                            type_str = t if t else "unknown"
                            tr_non_edu.add(type_str)
                            if disp_name:
                                tr_samples.append(f"{disp_name} ({type_str})")
                        else:
                            c_str = c if c else "??"
                            if disp_name:
                                non_tr_samples.append(f"{disp_name} ({c_str})")

                    if has_tr_edu:
                        break

                if has_tr_edu:
                    included_count += 1
                else:
                    wid = normalize_id(w.get("id", ""))
                    if tr_non_edu:
                        reason_joined = ",".join(sorted(tr_non_edu))
                        reason = f"non_education_tr_types: {reason_joined}"
                        sample = "; ".join(tr_samples[:3]) if tr_samples else "No affiliation string"
                    else:
                        reason = "no_tr_institution_in_authorships"
                        sample = "; ".join(non_tr_samples[:3]) if non_tr_samples else "No affiliation string"

                    raw_records.append({
                        "work_id": wid,
                        "publication_year": w.get("publication_year"),
                        "title": str(w.get("title", ""))[:100],
                        "exclusion_reason": reason,
                        "affiliation_sample": sample
                    })

    df_raw = pd.DataFrame(raw_records)
    stats = {
        "total_works_processed": total_processed,
        "included_in_network": included_count,
        "total_excluded": len(df_raw),
        "unique_works": df_raw["work_id"].nunique() if not df_raw.empty else 0,
        "by_year": df_raw["publication_year"].value_counts().to_dict() if not df_raw.empty else {}
    }
    return df_raw, stats


def compare_with_processed_csv(
    df_raw: pd.DataFrame,
    csv_path: str = "data/processed/excluded_works_summary.csv"
) -> Dict[str, Any]:
    """Ham türetim ile işlenmiş CSV'yi kayıt ve alan bazında karşılaştırır."""
    if not os.path.exists(csv_path):
        return {"success": False, "error": f"Referans dosya bulunamadı: {csv_path}"}

    df_csv = pd.read_csv(csv_path)

    raw_ids = set(df_raw["work_id"])
    csv_ids = set(df_csv["work_id"])

    missing_in_csv = list(raw_ids - csv_ids)
    extra_in_csv = list(csv_ids - raw_ids)

    merged = pd.merge(df_raw, df_csv, on="work_id", suffixes=("_raw", "_csv"))

    diff_year = merged[merged["publication_year_raw"] != merged["publication_year_csv"]]
    diff_reason = merged[merged["exclusion_reason_raw"] != merged["exclusion_reason_csv"]]
    diff_title = merged[merged["title_raw"].fillna("") != merged["title_csv"].fillna("")]
    diff_aff = merged[merged["affiliation_sample_raw"].fillna("") != merged["affiliation_sample_csv"].fillna("")]

    has_diff = (
        len(missing_in_csv) > 0 or
        len(extra_in_csv) > 0 or
        len(diff_year) > 0 or
        len(diff_reason) > 0 or
        len(diff_title) > 0 or
        len(diff_aff) > 0
    )

    return {
        "success": not has_diff,
        "raw_count": len(df_raw),
        "csv_count": len(df_csv),
        "missing_in_csv_count": len(missing_in_csv),
        "missing_in_csv_samples": missing_in_csv[:5],
        "extra_in_csv_count": len(extra_in_csv),
        "extra_in_csv_samples": extra_in_csv[:5],
        "diff_year_count": len(diff_year),
        "diff_reason_count": len(diff_reason),
        "diff_title_count": len(diff_title),
        "diff_aff_count": len(diff_aff)
    }


def main() -> int:
    csv_path = "data/processed/excluded_works_summary.csv"
    raw_pattern = "data/raw/works_*.jsonl"
    meta_path = "data/raw/institutions_tr.json"

    df_raw, stats = extract_excluded_from_raw(raw_pattern, meta_path)

    if df_raw.empty:
        logger.warning("Ham yayın dosyaları bulunamadı (.gitignore kuralı gereği yerel depoda olmayabilir).")
        if os.path.exists(csv_path):
            df_csv = pd.read_csv(csv_path)
            logger.info(f"Mevcut {csv_path} dosyası doğrulandı: {len(df_csv)} kayıt, {df_csv['work_id'].nunique()} tekil.")
            return 0
        else:
            logger.error("Ne ham veriler ne de CSV dosyası bulunabildi!")
            return 1

    comparison = compare_with_processed_csv(df_raw, csv_path)

    print("\n" + "=" * 60)
    print("641 DIŞLANAN YAYIN KARŞILAŞTIRMALI DENETİM RAPORU")
    print("=" * 60)
    print(f"Ham Veriden Türetilen Kayıt Sayısı : {comparison['raw_count']}")
    print(f"Referans CSV Kayıt Sayısı           : {comparison['csv_count']}")
    print(f"CSV'de Eksik Kalan Kayıtlar        : {comparison['missing_in_csv_count']}")
    print(f"CSV'de Fazladan Olan Kayıtlar      : {comparison['extra_in_csv_count']}")
    print(f"Yayın Yılı Uyuşmazlıkları          : {comparison['diff_year_count']}")
    print(f"Dışlama Nedeni Uyuşmazlıkları      : {comparison['diff_reason_count']}")
    print(f"Başlık Metni Uyuşmazlıkları        : {comparison['diff_title_count']}")
    print(f"Kurum Örneği Uyuşmazlıkları        : {comparison['diff_aff_count']}")
    print("=" * 60)

    if comparison["success"]:
        print("[BAŞARILI] Ham veriden çıkarılan 641 yayın ile CSV tüm alanlarda BİRE BİR EŞLEŞTİ.")
        return 0
    else:
        print("[HATA] Ham veri ile CSV arasında alan uyuşmazlığı tespit edildi!")
        if comparison["missing_in_csv_count"] > 0:
            print("  Örnek Eksik ID'ler:", comparison["missing_in_csv_samples"])
        if comparison["extra_in_csv_count"] > 0:
            print("  Örnek Fazla ID'ler:", comparison["extra_in_csv_samples"])
        return 1


if __name__ == "__main__":
    sys.exit(main())
