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
  Yalnızca `country_code: TR` ve `type: education` olan kurumlar ağın düğümleri olarak tanımlanmıştır. OpenAlex'te Türkiye kayıtlı toplam 222 eğitim kurumu yer almakta olup, bu liste YÖK bünyesindeki tüm devlet ve vakıf üniversitelerini tam kapsamaktadır.
- **Sayfalama Yöntemi:**
  Cursor paging kullanılmamış; `per_page=100` ile standart `page` sayfalaması yapılmıştır. OpenAlex'in 10.000 kayıt sınırı nedeniyle veriler yıl bazlı sorgulanmıştır.

---

## 3. Önemli Kapsam Değerlendirmesi: "500 Düğüm Kuralı"
Genel ders yönergesi en az 500 düğümlü bir ağ istemektedir. Ancak bu kişisel ödev kartında düğüm **"Türkiye'deki Üniversiteler"** olarak tanımlanmıştır:
1. Türkiye'de YÖK sistemine kayıtlı toplam üniversite sayısı yaklaşık 208'dir (OpenAlex veritabanında `education` tipi kurum sayısı 222'dir).
2. Bilgisayar bilimi (2020–2025) alanında yayın yapan Türkiye üniversiteleri sayısı bu evrenin alt kümesidir.
3. **Bilimsel Dürüstlük İlkesi:** 500 sayısına ulaşmak amacıyla yapay/sahte düğüm eklenmemiş ya da kurum tanımı bozulmamıştır. İlgili kısıt öğretim elemanının değerlendirmesine sunulmak üzere ara kontrol raporunda ve dokümantasyonda açıkça belgelenmiştir.

---

## 4. Ağ Tanımı ve Topoloji
- **Düğüm (Node):** Türkiye'deki uygun üniversite / eğitim kurumu.
- **Kenar (Edge):** İki farklı Türk üniversitesinin araştırmacılarının aynı yayında ortak yazar olarak yer alması.
- **Ağırlık (Weight):** İki kurum arasında dönem boyunca yayımlanan toplam ortak makale sayısı.
- **Yönsüz ve Ağırlıklı Ağ:** Ortaklık karşılıklı bir ilişki olduğu için ağ yönsüzdür ($G=(V, E, W)$).
- **Self-Loop ve Enflasyon Engelleme:** Aynı yayında aynı üniversiteden birden çok yazar bulunması durumunda kendi kendine kenar (self-loop) açılmaz; her iki farklı üniversite çifti için yayından gelen katkı +1 sayılır.
- **İzole Düğümlerin Korunması:** Dönem içinde yayın yapmış fakat başka bir Türk üniversitesiyle ortaklık kurmamış kurumlar ağdan silinmemiş, izole düğüm ($degree=0$) olarak korunmuştur.

### 4.1. Doğrulanmış Ağ İstatistikleri (Ara Kontrol Verisi)
- **İncelenen Toplam Yayın:** 35.114 (2020–2025)
- **Ortak Yayın Sayısı (İki veya daha çok Türk kurumu):** 7.470
- **Düğüm Sayısı ($|V|$):** 205 üniversite / yükseköğretim kurumu
- **Kenar Sayısı ($|E|$):** 3.970 ağırlıklı iş birliği kenarı
- **Ağ Yoğunluğu (Density):** 0.189861
- **Bağlı Bileşen Sayısı:** 4 (1 Dev Bileşen [202 düğüm, %98.5] + 3 İzole Düğüm)
- **Ege Bölgesi Üniversite Sayısı:** 18 (Tamamı dev bileşende, en yüksek merkezilik Ege Üni [75] ve MCBÜ [66])

---

## 5. Proje Dizin Yapısı

```text
turkiye-universiteleri-isbirligi-agi/
├── .gitignore
├── requirements.txt
├── README.md
├── docs/
│   └── data_dictionary.md          # Veri sözlüğü ve alan açıklamaları
├── reports/
│   └── ara_kontrol.md              # Ara kontrol istatistikleri ve metrik raporu
├── scripts/
│   ├── __init__.py
│   ├── fetch_openalex.py           # Tekrar çalıştırılabilir veri toplama scripti
│   └── build_network.py            # Ham veriden ağ kurma scripti
├── tests/
│   └── test_network.py             # Birim testler ve kural doğrulamaları
└── data/
    ├── raw/                        # OpenAlex'ten çekilen ham json/jsonl dosyaları
    │   ├── institutions_tr.json
    │   └── works_*.jsonl
    └── processed/                  # İşlenmiş nihai ağ çıktıları
        ├── edges.csv               # source, target, weight
        ├── institutions.csv        # Düğüm üstverileri ve merkezilikler
        └── collaboration.graphml   # NetworkX GraphML ağ dosyası
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
PYTHONPATH=. pytest tests/test_network.py -v
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

---

## 7. Yapay Zekâ (AI) Kullanım Beyanı
Bu projenin veri toplama boru hattı mimarisinin kurgulanması (`fetch_openalex.py`), ağ oluşturma algoritmasının optimize edilmesi (`build_network.py`), birim test senaryolarının yazılması (`test_network.py`) ve dokümantasyon taslaklarının hazırlanmasında **Google Antigravity** yapay zekâ kodlama asistanından faydalanılmıştır. API istekleri, veri doğrulama testleri ve üretilen ağ metrikleri yerel terminal ortamında canlı olarak çalıştırılmış ve sonuçların doğruluğu teyit edilmiştir.