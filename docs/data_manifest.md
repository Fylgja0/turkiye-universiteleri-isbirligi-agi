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

## 2. Ham Veri Dosyaları ve Yerel Depolama Durumu

> [!IMPORTANT] **GitHub Deposu ve `.gitignore` Bildirimi:**  
> Aşağıdaki ham veri dosyaları yaklaşık **125 MB** toplam boyuta sahip olduğundan ve OpenAlex API yanıtlarının büyük JSON yapıları içermesi sebebiyle `.gitignore` (`data/raw/*.json`, `data/raw/*.jsonl`) kuralı ile GitHub deposu dışında tutulmuştur. Bu durum yerel verilerin silindiği anlamına gelmez; tüm ham kayıtlar yerel çalışma ortamında eksiksiz muhafaza edilmektedir.

| Dosya Yolu | Dosya Boyutu (Yaklaşık) | Kayıt / Satır Sayısı | Açıklama |
| :--- | :---: | :---: | :--- |
| `data/raw/institutions_tr.json` | 7.05 MB | 222 kurum | OpenAlex `country_code:TR,type:education` ham üstverisi |
| `data/raw/works_2020.jsonl` | 13.72 MB | 4.153 yayın | 2020 yılı ham OpenAlex JSONL yayın kayıtları |
| `data/raw/works_2021.jsonl` | 17.39 MB | 5.045 yayın | 2021 yılı ham OpenAlex JSONL yayın kayıtları |
| `data/raw/works_2022.jsonl` | 18.88 MB | 5.422 yayın | 2022 yılı ham OpenAlex JSONL yayın kayıtları |
| `data/raw/works_2023.jsonl` | 21.38 MB | 6.166 yayın | 2023 yılı ham OpenAlex JSONL yayın kayıtları |
| `data/raw/works_2024.jsonl` | 22.42 MB | 6.516 yayın | 2024 yılı ham OpenAlex JSONL yayın kayıtları |
| `data/raw/works_2025.jsonl` | 27.40 MB | 7.812 yayın | 2025 yılı ham OpenAlex JSONL yayın kayıtları |
| **TOPLAM** | **~128.24 MB** | **35.114 yayın** | **6 yıllık tam korunan ham veri seti** |

---

## 3. İşlenmiş Nihai Ağ Verileri (`data/processed/`)

İşlenmiş dosyalar depoda versiyonlanmış ve paylaşıma hazırdır:

| Dosya Yolu | Boyut | Satır / Eleman Sayısı | Açıklama |
| :--- | :---: | :---: | :--- |
| `data/processed/institutions.csv` | ~35 KB | 205 düğüm | Koordinatlar, kategoriler, merkezilikler ve yayın sayaçları |
| `data/processed/edges.csv` | ~260 KB | 3.970 kenar | `source`, `target`, `weight` ağırlıklı ortak yazarlık listesi |
| `data/processed/collaboration.graphml` | ~665 KB | 205 düğüm, 3.970 kenar | Gephi ve NetworkX uyumlu GraphML ağı |
| `data/processed/excluded_works_summary.csv` | ~140 KB | 641 satır | Ağ dışı bırakılan 641 çalışmanın ID ve gerekçeli dökümü |

---

## 4. Dışlanan 641 Çalışmanın Doğrulama Metodolojisi

OpenAlex API seviyesinde `institutions.country_code:TR` filtresi uygulandığı için, yazarları arasında üniversite bulunmayan sanayi, kamu ve sağlık kuruluşları da yanıtta yer almıştır.

Bu 641 çalışmanın analizi:
- `scripts/audit_excluded_works.py` betiği ile yerel ham veriden doğrudan yeniden üretilebilmektedir.
- 641 çalışmanın tamamında yazarlar arasında hiçbir Türk üniversitesi bulunmamakta; ASELSAN, HAVELSAN, TÜBİTAK MAM/BİLGEM veya şehir hastaneleri gibi kuruluşlar yer almaktadır.
- Yıllara göre dağılım:
  - 2020: 69
  - 2021: 76
  - 2022: 106
  - 2023: 132
  - 2024: 106
  - 2025: 152
  - **Toplam: 641 çalışma**

Yeniden denetim çalıştırma komutu:
```bash
python scripts/audit_excluded_works.py
```
