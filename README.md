# Türk Üniversiteleri Arası Bilimsel İş Birliği Sosyal Ağ Analizi

> **CV için Proje Özeti:** 2020–2025 yılları arasında Türkiye'deki üniversitelerin bilgisayar bilimi alanındaki 35.000'i aşkın bilimsel yayınını OpenAlex API üzerinden modelleyerek; akademik iş birliklerinde coğrafi yakınlık ve üretim hacmi etkilerini ortaya koyan yönsüz ve ağırlıklı bir Sosyal Ağ Analizi (SNA) projesi.

**Ders / Program:** Manisa Celal Bayar Üniversitesi — Büyük Veri Analistliği  
**Dönem:** 2026–2027 Güz / Sosyal Ağ Analizi  
**Öncelikli Aşama:** 26 Ekim 2026 — 23:59 Ara Kontrol Teslimi  

---

## 1. Araştırma Sorusu
> *Türkiye'deki üniversiteler arasında bilgisayar bilimi alanındaki ortak yayın iş birliği coğrafi yakınlıkla mı, yoksa üniversitelerin bilimsel üretim büyüklüğüyle mi daha çok ilişkilidir? Ege Bölgesi üniversiteleri ağda nerede bulunur?*

Bu araştırma, Türkiye yükseköğretim ekosistemindeki bilgisayar bilimi araştırmacılarının kurumlar arası iş birliği eğilimlerini incelemeyi amaçlar. Üniversitelerin coğrafi olarak birbirine yakın olmaları mı (bölgesel kümelenme), yoksa araştırma hacmi ve atıf kapasitesi yüksek olan büyük metropol üniversiteleriyle (tercihli bağlanma - preferential attachment) ortaklık kurmaları mı daha belirleyicidir? Ayrıca Manisa Celal Bayar Üniversitesi'nin de içinde bulunduğu Ege Bölgesi üniversitelerinin bu ağdaki yapısal pozisyonu ve merkeziliği analiz edilmektedir.

---

## 2. Veri Kaynağı ve Kapsam Kararları

- **Veri Sağlayıcı:** [OpenAlex API](https://openalex.org/) (Açık erişimli, CC0 lisanslı bilimsel katalog).
- **Zaman Aralığı:** `2020-01-01` ile `2025-12-31` tarihleri arasında yayımlanan çalışmalar.
- **Alan Doğrulaması (`primary_topic.field.id`):**
  OpenAlex resmi `/fields` endpoint'i taranarak "Computer Science" disiplininin tam kimliği `https://openalex.org/fields/17` (`fields/17`) olarak teyit edilmiştir. Yayınların ana ekseninin bilgisayar bilimi olduğunu garanti etmek amacıyla `primary_topic.field.id:fields/17` filtresi kullanılmıştır.
- **Kurum Türü ve Ülke Sınırlaması:**
  OpenAlex API seviyesinde `country_code: TR` ve `type: education` filtresi kullanılmıştır. Ancak OpenAlex `education` türü üniversitelerin yanı sıra askeri/polis akademilerini, bağımsız meslek yüksekokullarını (MYO), hastane eğitim birimlerini ve kapatılmış tarihsel kurumları da içeren geniş bir sınıftır. Bu projede kurumlar OpenAlex üstveri analizi ve kural tabanlı algoritmik filtreleme (ad ve durum kontrolü) ile sınıflandırılmış; 2016 KHK ile kapatılan kurumlar ise ID bazında doğrulanmıştır. Analizler hem geniş eğitim kurumu (Kapsam A) hem de kural tabanlı üniversiteler (Kapsam B/B1) düzeyinde modellenmiştir.
- **Sayfalama Yöntemi:**
  Cursor paging kullanılmamış; `per_page=100` ile standart `page` sayfalaması yapılmıştır. OpenAlex'in 10.000 kayıt sınırı nedeniyle veriler yıl bazlı sorgulanmıştır.

---

## 3. Önemli Kapsam Değerlendirmesi: "500 Düğüm Kuralı"
Genel ders yönergesi en az 500 düğümlü bir ağ istemektedir. Ancak bu kişisel ödev kartında düğüm **"Türkiye'deki Üniversiteler"** olarak tanımlanmıştır:
1. [YÖK Resmî Web Portalı](https://www.yok.gov.tr/universiteler/universitelerimiz) (erişim: 26 Ekim 2026) verilerine göre Türkiye'de:
   - **129 Devlet Üniversitesi**
   - **75 Vakıf Üniversitesi**
   - Toplam **204 Üniversite**
   - Ayrıca **4 Bağımsız Vakıf Meslek Yüksekokulu** (Ataşehir Adıgüzel MYO, İstanbul Şişli MYO, İzmir Kavram MYO, Avrupa MYO)
   bulunmaktadır. Dolayısıyla Türkiye'deki toplam yükseköğretim kurumu sayısı **208** (204 üniversite + 4 vakıf MYO)'dir.
2. OpenAlex veritabanında `country_code: TR` ve `type: education` sorgusunda ise toplam **222 kurum** yer almaktadır (Bu sayı üniversitelerin yanı sıra askeri okulları, kapatılan kurumları, bağımsız MYO'ları ve KKTC'deki Lefke Avrupa Üniversitesi gibi kurumları da kapsar).
3. Bilgisayar bilimi (2020–2025) alanında yayın yapan Türkiye üniversiteleri sayısı bu evrenin alt kümesidir: Kapsam B'de **194 üniversite** (186 kural tabanlı aktif üniversite + 2016 KHK ile kapatılan 7 tarihsel vakıf üniversitesi + 2020'de 2708 sayılı CBK ile kapatılan İstanbul Şehir Üniversitesi; KKTC merkezli Lefke Avrupa Üniversitesi Türkiye kurumsal kapsamı dışındadır), kural tabanlı aktif olan Kapsam B1'de ise **186 üniversite**dir.
4. **Bilimsel Dürüstlük İlkesi:** 500 sayısına ulaşmak amacıyla yapay/sahte düğüm eklenmemiş ya da kurum tanımı bozulmamıştır. İlgili kısıt öğretim elemanının değerlendirmesine sunulmak üzere ara kontrol raporunda ve dokümantasyonda açıkça belgelenmiştir.

---

## 4. Ağ Tanımı ve Topoloji
- **Düğüm (Node):** Türkiye'deki uygun üniversite / eğitim kurumu.
- **Kenar (Edge):** İki farklı Türk üniversitesinin araştırmacılarının aynı yayında ortak yazar olarak yer alması.
- **Ağırlık (Weight):** İki kurum arasında dönem boyunca yayımlanan toplam ortak makale sayısı.
- **Yönsüz ve Ağırlıklı Ağ:** Ortaklık karşılıklı bir ilişki olduğu için ağ yönsüzdür ($G=(V, E, W)$).
- **Self-Loop ve Enflasyon Engelleme:** Aynı yayında aynı üniversiteden birden çok yazar bulunması durumunda kendi kendine kenar (self-loop) açılmaz; her iki farklı üniversite çifti için yayından gelen katkı +1 sayılır.
- **İzole Düğümlerin Korunması:** Dönem içinde yayın yapmış fakat başka bir Türk üniversitesiyle ortaklık kurmamış kurumlar ağdan silinmemiş, izole düğüm ($degree=0$) olarak korunmuştur.

### 4.1. Doğrulanmış Ağ İstatistikleri ve Kapsam Karşılaştırması (Ara Kontrol Verisi)

- **İndirilen Toplam Çalışma (2020–2025):** 35.114 yayın (Yerel ham boyutu: 128.229.572 bayt / 122,29 MiB; SHA-256 hash'leri `docs/data_manifest.md` dosyasındadır).
- **Türkiye Eğitim Kurumu İçeren Çalışma:** 34.473 yayın (*641 yayın farkı: 640 yayın Türkiye bağlantılı fakat education türünde olmayan kurumlar [ASELSAN, TÜBİTAK vb.]; 1 yayın ise yazar üstverisinde Türkiye kurumu bulunmayan kayıttır*).
- **En Az İki Türk Kurumu Arasında Ortak Yayın:** 7.470 yayın

| Metrik | Kapsam A (Tüm 205 Education Kurumu) | Kapsam B (186 Aktif + 7 KHK + 1 CBK Kapatılan, 194 Düğüm) | Kapsam B1 (186 Kural Tabanlı Aktif Üniversite) |
| :--- | :---: | :---: | :---: |
| **Düğüm Sayısı (N)** | **205** | **194** | **186** |
| **Kenar Sayısı (M)** | **3.970** | **3.887** | **3.848** |
| **Ağ Yoğunluğu (Density)** | 0.189861 | **0.207628** | **0.223656** |
| **Bağlı Bileşen Sayısı** | 4 | **2** | **1** |
| **İzole Düğüm Sayısı** | 3 | **1** (Canik Başarı Üni) | **0** |
| **Dev Bileşen Büyüklüğü** | 202 (%98.5) | **193 (%99.5)** | **186 (%100.0)** |

---

## 5. Proje Dizin Yapısı

```text
turkiye-universiteleri-isbirligi-agi/
├── .gitignore
├── requirements.txt
├── README.md
├── docs/
│   ├── data_dictionary.md          # Veri sözlüğü ve alan açıklamaları
│   └── data_manifest.md            # Veri manifestosu, ham veri hash ve boyutları
├── notebooks/
│   └── final_analysis.ipynb        # Final teslimi interaktif analiz ve görselleştirme notebook'u
├── reports/
│   ├── ara_kontrol.md              # Ara kontrol istatistikleri ve metrik raporu
│   └── generated/                  # Final analizi çıktıları (JSON, CSV, PNG, HTML)
│       ├── network_topology_summary.json
│       ├── centrality_metrics.csv
│       ├── centrality_top10_comparison.csv
│       ├── centrality_spearman_correlation.csv
│       ├── powerlaw_fit_results.json
│       ├── degree_distribution_powerlaw.png
│       ├── community_detection_summary.json
│       ├── community_assignments.csv
│       ├── community_top_clusters.csv
│       ├── null_model_comparison.json
│       ├── null_model_comparison.csv
│       ├── gravity_model_results.json
│       ├── gravity_model_summary.csv
│       ├── gravity_model_dyadic_sample.csv
│       └── turkey_collaboration_map.html
├── scripts/
│   ├── __init__.py
│   ├── fetch_openalex.py           # Tekrar çalıştırılabilir veri toplama scripti
│   ├── build_network.py            # Ham veriden ağ kurma scripti
│   ├── audit_excluded_works.py     # 641 dışlanan yayını denetleme ve doğrulama scripti
│   ├── analysis_metrics.py         # Temel ağ ölçüleri ve merkeziyet modülü
│   ├── analysis_powerlaw.py        # Derece dağılımı ve güç yasası modülü
│   ├── analysis_community.py       # Louvain/Leiden (10 seed) topluluk modülü
│   ├── analysis_null_model.py      # 100 rastgele ağ null model modülü
│   ├── analysis_gravity.py         # Çekim modeli Poisson & NegBinomial GLM modülü
│   ├── visualize_map.py            # Folium coğrafi iş birliği haritası modülü
│   └── run_final_analysis.py       # Tüm final analiz hattını çalıştıran orkestratör
├── tests/
│   ├── test_network.py             # Veri ve ara kontrol doğrulama testleri (14 test)
│   └── test_final_analysis.py      # Final analiz hattı birim testleri (10 test)
└── data/
    ├── raw/                        # Yerel ham json/jsonl dosyaları (.gitignore ile korunur)
    │   ├── institutions_tr.json
    │   └── works_*.jsonl
    └── processed/                  # İşlenmiş nihai ağ çıktıları
        ├── edges.csv               # source, target, weight
        ├── institutions.csv        # Düğüm üstverileri ve merkezilikler
        ├── collaboration.graphml   # NetworkX GraphML ağ dosyası
        └── excluded_works_summary.csv # Dışlanan 641 çalışmanın ID ve gerekçeleri
```

---

## 6. Kurulum ve Yeniden Üretilebilirlik Adımları

### 6.1. Gereksinimler ve Sanal Ortam Kurulumu
```bash
# Depoyu klonlayın ve dizine girin
cd turkiye-universiteleri-isbirligi-agi

# Python 3.10+ sanal ortamı oluşturun ve aktif edin
python3 -m venv venv
source venv/bin/activate

# Gerekli bağımlılıkları yükleyin
pip install -r requirements.txt
```

### 6.2. Testlerin Çalıştırılması (Birim Doğrulama)
```bash
# Tüm birim ve entegrasyon testlerini (24 test) çalıştırın:
PYTHONPATH=. pytest -v
```

### 6.3. Veri Toplama (Canlı OpenAlex API)
```bash
# 2020-2025 aralığındaki tüm verileri çeker (yerel önbellekleme destekler):
python scripts/fetch_openalex.py --start-year 2020 --end-year 2025

# Yalnızca sayıları kontrol etmek için (dry-run):
python scripts/fetch_openalex.py --dry-run
```

### 6.4. Ağın Kurulması ve Çıktıların Üretilmesi
```bash
python scripts/build_network.py
```
Bu komut sonucunda `data/processed/` altında `edges.csv`, `institutions.csv` ve `collaboration.graphml` dosyaları üretilir.

### 6.5. Final Analiz Hattının Çalıştırılması (30 Ekim 2026 Teslimi)
```bash
# Temel metrikler, güç yasası, topluluk tespiti, null model, çekim modeli ve coğrafi haritayı üretir:
python scripts/run_final_analysis.py
```
Tüm nihai analiz tabloları, JSON özetleri, grafikler ve etkileşimli HTML haritası `reports/generated/` dizinine kaydedilir. Ayrıca `notebooks/final_analysis.ipynb` üzerinden tüm adımlar interaktif olarak incelenebilir.

---

## 7. Yapay Zekâ (AI) Kullanım Beyanı
Bu projenin veri toplama boru hattı mimarisinin kurgulanması (`fetch_openalex.py`), ağ oluşturma algoritmasının optimize edilmesi (`build_network.py`), birim test senaryolarının yazılması (`test_network.py`) ve dokümantasyon taslaklarının hazırlanmasında **Google Antigravity** yapay zekâ kodlama asistanından faydalanılmıştır. API istekleri, veri doğrulama testleri ve üretilen ağ metrikleri yerel terminal ortamında canlı olarak çalıştırılmış ve sonuçların doğruluğu teyit edilmiştir.