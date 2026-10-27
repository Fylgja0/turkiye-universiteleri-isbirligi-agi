# Veri Manifestosu (Data Manifest)

**Proje:** Türkiye Üniversiteleri Arası Bilimsel İş Birliği Sosyal Ağ Analizi  
**Kurum:** Manisa Celal Bayar Üniversitesi — Büyük Veri Analistliği  
**Aşama:** 26 Ekim 2026 Ara Kontrol Denetimi ve Veri Kökeni Belgesi  
**Veri Kaynağı:** [OpenAlex REST API](https://api.openalex.org/) (CC0 Kamu Malı Lisansı)  
**Veri Toplama Tarihi:** 26 Ekim 2026  

---

## 1. Veri Toplama Parametreleri ve API Sorguları

| Parametre | Değer / Filtre | Gerekçe / Açıklama |
| :--- | :--- | :--- |
| **Endpoint** | `/works` | Bilimsel yayın kayıtları |
| **Disiplin Doğrulaması** | `primary_topic.field.id:fields/17` | `/fields` endpoint'i üzerinden dinamik sorgulanan "Computer Science" disiplini |
| **Zaman Aralığı** | `from_publication_date:2020-01-01,to_publication_date:2025-12-31` | 2020–2025 arası 6 yıllık dönem |
| **Ülke Filtresi** | `institutions.country_code:TR` | Yazarları arasında Türkiye adresli kurum bulunan yayınlar |
| **Sayfalama** | `per_page=100`, standart `page=1..N` | Cursor paging kullanılmamış; OpenAlex 10.000 kayıt sınırı nedeniyle yıllık dilimler uygulanmıştır |

---

## 2. Ham Veri Dosyaları, Boyutları ve SHA-256 Hash Değerleri

> [!IMPORTANT] **GitHub Deposu ve `.gitignore` Bildirimi:**  
> Aşağıdaki ham veri dosyaları toplam **128.229.572 bayt (122,29 MiB)** boyuta sahip olduğundan `.gitignore` (`data/raw/*.json`, `data/raw/*.jsonl`) kuralı ile GitHub deposu dışında tutulmuştur. Bu durum yerel verilerin silindiği anlamına gelmez; tüm ham kayıtlar yerel çalışma ortamında eksiksiz muhafaza edilmektedir. Uzak depoda ham veriler bulunmadığı durumlarda bütünlük kontrolü aşağıdaki SHA-256 hash'leri ile sağlanır.

*(Not: Boyutlar ikili standartta [$1\text{ MiB} = 1.048.576\text{ Bayt}$] hesaplanmıştır; ondalık sistemde toplam ham veri boyutu 128,23 MB'tır).*

| Dosya Yolu | Kesin Boyut (Bayt) | Boyut (MiB) | Kayıt Sayısı | SHA-256 Sağlama Özeti (Checksum) |
| :--- | :---: | :---: | :---: | :--- |
| `data/raw/institutions_tr.json` | 7.045.561 | 6,72 MiB | 222 kurum | `a4ca61c563b9b5c02de341714e33a2df697fbb18cc8a2075a6036e4ce39094a7` |
| `data/raw/works_2020.jsonl` | 13.719.127 | 13,08 MiB | 4.153 yayın | `c194f046be14f8021249dd98348f1cefb484a83f37d9b5c25a8ab2644f0ccf55` |
| `data/raw/works_2021.jsonl` | 17.387.880 | 16,58 MiB | 5.045 yayın | `65f9d56f8f42c171d901b858d633b228502e85030d9cf347196d8118abd7bf2a` |
| `data/raw/works_2022.jsonl` | 18.878.378 | 18,00 MiB | 5.422 yayın | `c019d54e51b0945fd54f331b0a08b68e3279ce341fecfcdb2c24d4527d9409ea` |
| `data/raw/works_2023.jsonl` | 21.378.439 | 20,39 MiB | 6.166 yayın | `40e5bf32d4d76fa3ef0a6c733e7f81ec5ac4688d26e1c40a70b96ed4b5023f70` |
| `data/raw/works_2024.jsonl` | 22.423.463 | 21,38 MiB | 6.516 yayın | `54b6f47d00f000e1945fd69ee7c7ee7eddb919d17fcf6e6c007b615de18ddbb6` |
| `data/raw/works_2025.jsonl` | 27.396.724 | 26,13 MiB | 7.812 yayın | `d3886157c72068ca8a04d4157ba5126cb334197521c2ed04de9a6b2c5e7227ba` |
| **TOPLAM** | **128.229.572** | **122,29 MiB** | **35.114 yayın** | *Tüm ham veriler doğrulanmış ve yerel diskte korunmaktadır* |

---

## 3. İşlenmiş Nihai Ağ Verileri (`data/processed/`)

İşlenmiş dosyalar depoda yer almakta olup güncel sağlama özetleri şunlardır:

| Dosya Yolu | Kesin Boyut (Bayt) | Boyut (MiB) | Eleman Sayısı | SHA-256 Sağlama Özeti (Checksum) |
| :--- | :---: | :---: | :---: | :--- |
| `data/processed/institutions.csv` | 36.305 | 0,03 MiB | 205 düğüm | `2ec986d9cc74a0d44df563efb9c535fb7deaf6e54f36ed8431946595e857b3cf` |
| `data/processed/edges.csv` | 260.545 | 0,25 MiB | 3.970 kenar | `13e474bb5849ae8940bc0a2dc1b864af87c5c1fac0800c9053d35dae08030ab9` |
| `data/processed/collaboration.graphml` | 671.656 | 0,64 MiB | 205 düğüm, 3.970 kenar | `e0f5352d9feab9bca045a9e4c685371b37a4e7f73d78cc5f57c03dd7721849cb` |
| `data/processed/excluded_works_summary.csv` | 140.481 | 0,13 MiB | 641 satır | `0d6bfbb1e175b7711f0ffb2e8858edb499ed5c07bd8e585facc2d39eae555859` |

---

## 4. Dışlanan 641 Çalışmanın Denetim ve Doğrulama Durumu

OpenAlex API seviyesinde `institutions.country_code:TR` filtresi uygulandığı için:
- **640 çalışma**, yazarları arasında Türkiye bağlantılı kurumlar bulunmasına karşın bu kurumların hiçbiri `education` türünde (üniversite/yükseköğretim) olmadığı için dışlanmıştır (sanayi Ar-Ge: 315, kamu: 290, sağlık: 22, tesis/vakıf: 13).
- **1 çalışma** (`W4416850727`), yazar-kurum üstverisinde Türkiye bağlantılı hiçbir kurum bulunmadığı (Michigan State University gibi yabancı kurumlara bağlı yazarlar) için ayrılmıştır (`no_tr_institution_in_authorships`).

Bu 641 çalışmanın denetimi:
- `scripts/audit_excluded_works.py` betiği ile yerel ham veriden doğrudan yeniden üretilip `excluded_works_summary.csv` ile bütün alanlar (`work_id`, `publication_year`, `title`, `exclusion_reason`, `affiliation_sample`) bazında karşılaştırılır.
- **Yerel Doğrulama Durumu:** Yerel diskte ham veriler (`data/raw/works_*.jsonl`) mevcutken çalıştırıldığında 0 eksik, 0 fazla, 0 uyuşmazlık ile %100 tam eşleşme doğrulanmakta ve çıkış kodu `0` dönmektedir.
- **Uzak Depo / Eksik Veri Sınırı:** Ham veriler `.gitignore` nedeniyle GitHub'da bulunmadığından, yerel ham verilerin olmadığı bir ortamda betik salt satır kontrolüyle başarı bildirmemekte; sonucu açıkça `[DOĞRULANAMADI]` olarak raporlayarak çıkış kodu `2` vermektedir.
- Yıllara göre dağılım:
  - 2020: 69
  - 2021: 76
  - 2022: 106
  - 2023: 132
  - 2024: 106
  - 2025: 152
  - **Toplam: 641 çalışma**

Yeniden denetim komutu:
```bash
python scripts/audit_excluded_works.py
```
