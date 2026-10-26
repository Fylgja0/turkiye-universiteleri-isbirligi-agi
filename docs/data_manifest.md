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
> Aşağıdaki ham veri dosyaları toplam **128.229.572 bayt (122,29 MB)** boyuta sahip olduğundan `.gitignore` (`data/raw/*.json`, `data/raw/*.jsonl`) kuralı ile GitHub deposu dışında tutulmuştur. Bu durum yerel verilerin silindiği anlamına gelmez; tüm ham kayıtlar yerel çalışma ortamında eksiksiz muhafaza edilmektedir. Uzak depoda ham veriler bulunmadığı durumlarda bütünlük kontrolü aşağıdaki SHA-256 hash'leri ile sağlanır.

| Dosya Yolu | Kesin Boyut (Bayt) | Boyut (MB) | Kayıt Sayısı | SHA-256 Sağlama Özeti (Checksum) |
| :--- | :---: | :---: | :---: | :--- |
| `data/raw/institutions_tr.json` | 7.045.561 | 6,72 MB | 222 kurum | `a4ca61c563b9b5c02de341714e33a2df697fbb18cc8a2075a6036e4ce39094a7` |
| `data/raw/works_2020.jsonl` | 13.719.127 | 13,08 MB | 4.153 yayın | `c194f046be14f8021249dd98348f1cefb484a83f37d9b5c25a8ab2644f0ccf55` |
| `data/raw/works_2021.jsonl` | 17.387.880 | 16,58 MB | 5.045 yayın | `65f9d56f8f42c171d901b858d633b228502e85030d9cf347196d8118abd7bf2a` |
| `data/raw/works_2022.jsonl` | 18.878.378 | 18,00 MB | 5.422 yayın | `c019d54e51b0945fd54f331b0a08b68e3279ce341fecfcdb2c24d4527d9409ea` |
| `data/raw/works_2023.jsonl` | 21.378.439 | 20,39 MB | 6.166 yayın | `40e5bf32d4d76fa3ef0a6c733e7f81ec5ac4688d26e1c40a70b96ed4b5023f70` |
| `data/raw/works_2024.jsonl` | 22.423.463 | 21,38 MB | 6.516 yayın | `54b6f47d00f000e1945fd69ee7c7ee7eddb919d17fcf6e6c007b615de18ddbb6` |
| `data/raw/works_2025.jsonl` | 27.396.724 | 26,13 MB | 7.812 yayın | `d3886157c72068ca8a04d4157ba5126cb334197521c2ed04de9a6b2c5e7227ba` |
| **TOPLAM** | **128.229.572** | **122,29 MB** | **35.114 yayın** | *Tüm ham veriler doğrulanmış ve yerel diskte korunmaktadır* |

---

## 3. İşlenmiş Nihai Ağ Verileri (`data/processed/`)

İşlenmiş dosyalar depoda yer almakta olup sağlama özetleri şunlardır:

| Dosya Yolu | Kesin Boyut (Bayt) | Boyut (MB) | Eleman Sayısı | SHA-256 Sağlama Özeti (Checksum) |
| :--- | :---: | :---: | :---: | :--- |
| `data/processed/institutions.csv` | 35.239 | 0,03 MB | 205 düğüm | `1a6023cb5552c7102d155e52c521a95c68fbd8a82cc5a42581a536473996806b` |
| `data/processed/edges.csv` | 260.545 | 0,25 MB | 3.970 kenar | `13e474bb5849ae8940bc0a2dc1b864af87c5c1fac0800c9053d35dae08030ab9` |
| `data/processed/collaboration.graphml` | 664.583 | 0,63 MB | 205 düğüm, 3.970 kenar | `395333edf69f7ded8ba1f2d2f441c2f516c8c521fe08699e756dda50f028705c` |
| `data/processed/excluded_works_summary.csv` | 140.481 | 0,13 MB | 641 satır | `0d6bfbb1e175b7711f0ffb2e8858edb499ed5c07bd8e585facc2d39eae555859` |

---

## 4. Dışlanan 641 Çalışmanın Denetim ve Doğrulama Durumu

OpenAlex API seviyesinde `institutions.country_code:TR` filtresi uygulandığı için, yazarları arasında üniversite bulunmayan sanayi, kamu ve sağlık kuruluşları da yanıta dahil olmuştur.

Bu 641 çalışmanın denetimi:
- `scripts/audit_excluded_works.py` betiği ile yerel ham veriden doğrudan yeniden üretilip `excluded_works_summary.csv` ile bütün alanlar (`work_id`, `publication_year`, `title`, `exclusion_reason`, `affiliation_sample`) bazında karşılaştırılmıştır.
- **Karşılaştırma Sonucu:** 0 eksik, 0 fazla, 0 uyuşmazlık ile %100 tam eşleşme doğrulanmıştır.
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
