#!/usr/bin/env python3
"""
scripts/fetch_openalex.py

Manisa Celal Bayar Üniversitesi - Büyük Veri Analistliği
Sosyal Ağ Analizi Projesi: Türk Üniversiteleri Arası Bilimsel İş Birliği

OpenAlex API'sinden 2020-01-01 ile 2025-12-31 tarihleri arasında Türkiye adresli
kurumların bilgisayar bilimi (Computer Science, field:17) alanındaki çalışmalarını
ve Türkiye'deki eğitim kurumlarının (üniversiteler) üstverilerini çeker.

Kurallar:
- Anahtarsız erişim (OpenAlex Polite Pool, User-Agent mailto başlığı ile).
- Cursor paging KULLANILMAZ. per_page=100 ile standart page sayfalaması yapılır.
- 10.000 limitini aşan dilimler dinamik olarak daha küçük alt dilimlere bölünür.
- HTTP 429 ve 5xx hatalarında üstel bekleme (exponential backoff) uygulanır.
- İndirilen veriler data/raw/ dizininde önbelleğe alınır; tekrar indirme yapılmaz.
"""

import os
import sys
import time
import json
import logging
import argparse
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("fetch_openalex")

BASE_URL = "https://api.openalex.org"
USER_AGENT = "TurkUniCollaborationNetwork/1.0 (mailto:mcbu_student@example.edu.tr; SAA_Project)"
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json"
}


def make_request_with_backoff(url: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 5, backoff_factor: float = 2.0) -> Dict[str, Any]:
    """
    HTTP isteği gönderir; 429 ve 5xx durumlarında üstel bekleme (exponential backoff) uygular.
    """
    delay = 1.0
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, params=params, headers=DEFAULT_HEADERS, timeout=40)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                wait_time = delay * (backoff_factor ** (attempt - 1))
                logger.warning(f"HTTP 429 (Hız Sınırı). {wait_time:.1f} saniye bekleniyor... (Deneme {attempt}/{max_retries})")
                time.sleep(wait_time)
            elif 500 <= response.status_code < 600:
                wait_time = delay * (backoff_factor ** (attempt - 1))
                logger.warning(f"HTTP {response.status_code} (Sunucu Hatası). {wait_time:.1f} saniye bekleniyor... (Deneme {attempt}/{max_retries})")
                time.sleep(wait_time)
            else:
                logger.error(f"HTTP {response.status_code} Hatası: {response.text}")
                response.raise_for_status()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries:
                logger.error(f"Ağ isteği başarısız oldu ({url}): {e}")
                raise
            wait_time = delay * (backoff_factor ** (attempt - 1))
            logger.warning(f"İstek istisnası: {e}. {wait_time:.1f} saniye bekleniyor...")
            time.sleep(wait_time)

    raise RuntimeError(f"{url} adresine yapılan {max_retries} deneme başarısız oldu.")


def verify_computer_science_field() -> str:
    """
    OpenAlex resmi /fields endpoint'inden 'Computer Science' alanını arar ve tam ID'yi doğrular.
    ID tahmin edilmez; canlı endpoint üzerinden tespit edilir.
    """
    logger.info("OpenAlex /fields endpoint'inden 'Computer Science' alan kimliği doğrulanıyor...")
    url = f"{BASE_URL}/fields"
    data = make_request_with_backoff(url, params={"search": "Computer Science"})
    
    cs_id = None
    for item in data.get("results", []):
        if item.get("display_name", "").strip().lower() == "computer science":
            cs_id = item.get("id")
            logger.info(f"Doğrulanan Alan: '{item.get('display_name')}' -> ID: {cs_id}")
            break
            
    if not cs_id:
        raise ValueError("OpenAlex /fields endpoint'inde 'Computer Science' alanı bulunamadı!")
        
    # ID örneği: https://openalex.org/fields/17 -> 'fields/17' veya '17'
    field_short_id = cs_id.split("/")[-1]
    return f"fields/{field_short_id}"


def fetch_and_cache_tr_institutions(output_file: str = "data/raw/institutions_tr.json") -> List[Dict[str, Any]]:
    """
    Türkiye'de bulunan 'type:education' kurumlarının tamamını çeker ve önbelleğe kaydeder.
    """
    if os.path.exists(output_file) and os.path.getsize(output_file) > 100:
        logger.info(f"Türkiye kurumları yerel önbellekten yükleniyor: {output_file}")
        with open(output_file, "r", encoding="utf-8") as f:
            return json.load(f)

    logger.info("OpenAlex'ten Türkiye eğitim kurumları (type:education, country_code:TR) çekiliyor...")
    url = f"{BASE_URL}/institutions"
    params = {
        "filter": "country_code:TR,type:education",
        "per_page": 100,
        "page": 1
    }
    
    all_institutions = []
    page = 1
    while True:
        params["page"] = page
        data = make_request_with_backoff(url, params=params)
        results = data.get("results", [])
        if not results:
            break
        all_institutions.extend(results)
        meta = data.get("meta", {})
        total_count = meta.get("count", 0)
        logger.info(f"Kurumlar Sayfa {page}: {len(results)} kurum alındı. (Toplam: {len(all_institutions)}/{total_count})")
        if len(all_institutions) >= total_count or len(results) < 100:
            break
        page += 1
        time.sleep(0.3)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_institutions, f, ensure_ascii=False, indent=2)

    logger.info(f"Toplam {len(all_institutions)} Türkiye eğitim kurumu kaydedildi -> {output_file}")
    return all_institutions


def fetch_works_page_slice(from_date: str, to_date: str, field_filter: str, output_path: str, max_pages: Optional[int] = None) -> int:
    """
    Belirli bir tarih aralığındaki çalışmaları per_page=100 ile sayfalayarak çeker.
    Eğer toplam sonuç 10.000'den fazlaysa, aralık daha küçük dilimlere bölünür.
    Çalışmalar JSONL dosyasına satır satır yazılır.
    """
    url = f"{BASE_URL}/works"
    filter_query = f"primary_topic.field.id:{field_filter},from_publication_date:{from_date},to_publication_date:{to_date},institutions.country_code:TR"
    
    # İlk istek: toplam kayıt sayısını kontrol et
    check_params = {
        "filter": filter_query,
        "per_page": 1,
        "page": 1
    }
    initial_data = make_request_with_backoff(url, params=check_params)
    meta = initial_data.get("meta", {})
    total_count = meta.get("count", 0)
    logger.info(f"Tarih Aralığı [{from_date} - {to_date}]: Toplam {total_count} çalışma tespit edildi.")
    
    if total_count == 0:
        return 0

    # 10.000 sınır kontrolü: Eğer count > 10.000 ise bu dilim bölünmeli!
    if total_count > 10000:
        logger.warning(f"Kayıt sayısı ({total_count}) OpenAlex normal sayfalama sınırını (10.000) aşıyor! Tarih dilimi ikiye bölünüyor...")
        d1 = datetime.strptime(from_date, "%Y-%m-%d")
        d2 = datetime.strptime(to_date, "%Y-%m-%d")
        mid_date = d1 + (d2 - d1) / 2
        mid_str_1 = mid_date.strftime("%Y-%m-%d")
        mid_str_2 = (mid_date + (d2 - d1) / 2 - (d2 - d1) / 2).strftime("%Y-%m-%d") # sonraki gün
        # alt dilimler
        c1 = fetch_works_page_slice(from_date, mid_str_1, field_filter, output_path, max_pages)
        # mid_date + 1 gün
        next_day = (mid_date.date() + (date(2000, 1, 2) - date(2000, 1, 1))).strftime("%Y-%m-%d")
        c2 = fetch_works_page_slice(next_day, to_date, field_filter, output_path, max_pages)
        return c1 + c2

    # Normal sayfalama (per_page=100)
    params = {
        "filter": filter_query,
        "select": "id,doi,title,publication_year,publication_date,authorships,primary_topic",
        "per_page": 100,
        "page": 1
    }

    # Zaten indirilmiş mevcut id'leri topla (tekrar indirmeme / resume desteği)
    existing_ids = set()
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        record = json.loads(line)
                        if "id" in record:
                            existing_ids.add(record["id"])
                    except json.JSONDecodeError:
                        pass

    if len(existing_ids) >= total_count and total_count > 0:
        logger.info(f"[{from_date} - {to_date}] için tüm veriler ({len(existing_ids)} kayıt) zaten indirilmiş, atlanıyor.")
        return len(existing_ids)

    logger.info(f"[{from_date} - {to_date}] indirmesi başlıyor. Hedef: {total_count} çalışma (mevcut: {len(existing_ids)}).")

    page = 1
    total_pages = (total_count + 99) // 100
    if max_pages:
        total_pages = min(total_pages, max_pages)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fetched_in_this_run = 0

    with open(output_path, "a", encoding="utf-8") as out_f:
        while page <= total_pages:
            params["page"] = page
            data = make_request_with_backoff(url, params=params)
            results = data.get("results", [])
            if not results:
                break

            new_in_page = 0
            for item in results:
                item_id = item.get("id")
                if item_id not in existing_ids:
                    out_f.write(json.dumps(item, ensure_ascii=False) + "\n")
                    existing_ids.add(item_id)
                    new_in_page += 1
                    fetched_in_this_run += 1

            logger.info(f"  Sayfa {page}/{total_pages} tamamlandı ({len(results)} kayıt alındı, {new_in_page} yeni). Toplam tekil: {len(existing_ids)}")
            page += 1
            # Kibar API hızı (polite pool sınırlarına saygı)
            time.sleep(0.25)

    return len(existing_ids)


def main():
    parser = argparse.ArgumentParser(description="OpenAlex Veri Çekme Scripti (Türkiye Bilgisayar Bilimi Ortak Yayın Ağı)")
    parser.add_argument("--start-year", type=int, default=2020, help="Başlangıç yılı (Varsayılan: 2020)")
    parser.add_argument("--end-year", type=int, default=2025, help="Bitiş yılı (Varsayılan: 2025)")
    parser.add_argument("--sample-only", action="store_true", help="Yalnızca test amaçlı küçük bir örnek çeker")
    parser.add_argument("--dry-run", action="store_true", help="İndirme yapmadan sadece toplam sayıları sorgular")
    args = parser.parse_args()

    # 1. Computer Science Alan ID doğrulaması
    field_filter = verify_computer_science_field()
    logger.info(f"Kullanılacak Field Filtresi: {field_filter}")

    # 2. Kurum bilgilerini çek
    inst_file = "data/raw/institutions_tr.json"
    fetch_and_cache_tr_institutions(inst_file)

    # 3. Yıllara göre çalışmaları çek
    years = list(range(args.start_year, args.end_year + 1))
    logger.info(f"İşlenecek yıllar: {years}")

    grand_total = 0
    for year in years:
        from_date = f"{year}-01-01"
        to_date = f"{year}-12-31"
        output_file = f"data/raw/works_{year}.jsonl"

        if args.dry_run:
            url = f"{BASE_URL}/works"
            filter_query = f"primary_topic.field.id:{field_filter},from_publication_date:{from_date},to_publication_date:{to_date},institutions.country_code:TR"
            data = make_request_with_backoff(url, params={"filter": filter_query, "per_page": 1})
            cnt = data.get("meta", {}).get("count", 0)
            logger.info(f"[DRY-RUN] Yıl {year}: {cnt} yayın")
            grand_total += cnt
            continue

        max_p = 2 if args.sample_only else None
        count = fetch_works_page_slice(from_date, to_date, field_filter, output_file, max_pages=max_p)
        grand_total += count
        logger.info(f"Yıl {year} tamamlandı: {count} çalışma dosyada mevcut ({output_file}).")

    logger.info(f"Tüm süreç başarıyla tamamlandı. Toplam çalışma sayısı: {grand_total}")


if __name__ == "__main__":
    main()
