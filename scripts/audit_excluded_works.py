#!/usr/bin/env python3
"""
scripts/audit_excluded_works.py

Ham OpenAlex yayın dosyalarını (works_2020..2025.jsonl) inceleyerek
ağ kurma algoritması tarafından dışlanan 641 çalışmayı denetler ve doğrular.
Yerel ham dosyalar mevcut olduğunda 641 kaydı bağımsız olarak yeniden üretir
ve data/processed/excluded_works_summary.csv ile karşılaştırır.
"""

import os
import glob
import json
import logging
from typing import Dict, List, Any, Set, Tuple
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


def audit_excluded_works(
    raw_pattern: str = "data/raw/works_*.jsonl",
    metadata_file: str = "data/raw/institutions_tr.json",
    output_csv: str = "data/processed/excluded_works_summary.csv"
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Ham dosyaları tarayarak Türkiye eğitim kurumu İÇERMEYEN 641 yayını doğrular.
    """
    file_paths = sorted(glob.glob(raw_pattern))
    tr_education_ids = load_tr_education_ids(metadata_file)

    if not file_paths:
        logger.warning(f"Ham yayın dosyaları '{raw_pattern}' deseninde bulunamadı (büyük veri boyutu nedeniyle .gitignore'dadır).")
        if os.path.exists(output_csv):
            logger.info(f"Mevcut işlenmiş dosya üzerinden denetim yapılıyor: {output_csv}")
            df = pd.read_csv(output_csv)
            stats = {
                "total_excluded": len(df),
                "unique_works": df["work_id"].nunique(),
                "by_year": df["publication_year"].value_counts().to_dict(),
                "verified_from_raw": False
            }
            return df, stats
        else:
            raise FileNotFoundError(f"Ne ham dosyalar ne de {output_csv} bulunabildi!")

    logger.info(f"{len(file_paths)} ham yayın dosyası taranıyor...")
    excluded_records = []
    total_processed = 0
    included_count = 0

    for fpath in file_paths:
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    work = json.loads(line)
                except json.JSONDecodeError:
                    continue

                total_processed += 1
                work_id = normalize_id(work.get("id"))
                pub_year = work.get("publication_year")
                title = work.get("title", "")
                authorships = work.get("authorships", [])

                has_tr_education = False
                tr_non_edu_types = set()
                aff_samples = []

                for auth in authorships:
                    insts = auth.get("institutions", [])
                    for inst in insts:
                        norm_iid = normalize_id(inst.get("id"))
                        country = inst.get("country_code")
                        itype = inst.get("type")
                        disp_name = inst.get("display_name", "")

                        if norm_iid in tr_education_ids or (country == "TR" and itype == "education"):
                            has_tr_education = True
                            break
                        elif country == "TR":
                            tr_non_edu_types.add(itype or "unknown")
                            if disp_name:
                                aff_samples.append(f"{disp_name} ({itype or 'unknown'})")

                    if has_tr_education:
                        break

                if has_tr_education:
                    included_count += 1
                else:
                    if tr_non_edu_types:
                        reason = f"non_education_tr_types: {','.join(sorted(tr_non_edu_types))}"
                    else:
                        reason = "no_tr_institution_in_authorships"

                    sample_str = "; ".join(aff_samples[:3]) if aff_samples else "No affiliation string"
                    excluded_records.append({
                        "work_id": work_id,
                        "publication_year": pub_year,
                        "title": title,
                        "exclusion_reason": reason,
                        "affiliation_sample": sample_str
                    })

    df_excluded = pd.DataFrame(excluded_records)
    stats = {
        "total_works_processed": total_processed,
        "included_in_network": included_count,
        "total_excluded": len(df_excluded),
        "unique_works": df_excluded["work_id"].nunique(),
        "by_year": df_excluded["publication_year"].value_counts().to_dict(),
        "verified_from_raw": True
    }

    logger.info(f"Ham veri taraması tamamlandı: {total_processed} toplam, {included_count} dahil, {len(df_excluded)} dışlanan.")
    return df_excluded, stats


if __name__ == "__main__":
    df, stats = audit_excluded_works()
    print("\n--- DENETİM RAPORU ---")
    print(f"Toplam İşlenen Yayın: {stats.get('total_works_processed', 'N/A')}")
    print(f"Ağa Dahil Edilen Türkiye Eğitim Yayını: {stats.get('included_in_network', 'N/A')}")
    print(f"Dışlanan Çalışma Sayısı: {stats['total_excluded']}")
    print(f"Tekil Dışlanan Yayın: {stats['unique_works']}")
    print("Yıllara Göre Dağılım:")
    for yr, cnt in sorted(stats["by_year"].items()):
        print(f"  {yr}: {cnt}")
