# Türk Üniversiteleri Arası Bilimsel İş Birliği Sosyal Ağ Analizi

> **CV için Proje Özeti:** 2020–2025 yılları arasında Türkiye'deki üniversitelerin bilgisayar bilimi alanındaki 35.000'i aşkın bilimsel yayınını OpenAlex API üzerinden modelleyerek; akademik iş birliklerinde coğrafi yakınlık ve üretim hacmi etkilerini ortaya koyan yönsüz ve ağırlıklı bir Sosyal Ağ Analizi (SNA) projesi.

**Ders / Program:** Manisa Celal Bayar Üniversitesi — Büyük Veri Analistliği  
**Dönem:** 2026–2027 Güz / Sosyal Ağ Analizi  
**Öncelikli Aşama:** 30 Ekim 2026 — 23:59 Final Teslimi (26 Ekim Ara Kontrolü Tamamlandı)  

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

### 4.1. Doğrulanmış Ağ İstatistikleri ve Kapsam Karşılaştırması

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
| **Ortalama En Kısa Yol (L)** | Tanımsız (Bağlantısız) | LCC: 1.8731 (Tüm Ağ: Tanımsız) | **1.8290 (Tek Bileşen)** |
| **Ağ Çapı (Diameter)** | 4 | LCC: 4 | **4** |
| **Ortalama Kümelenme (C)** | 0.4357 | 0.4477 | **0.4433** |
| **Derece Benzeşimi (r)** | -0.1062 | -0.0983 | **-0.0992** |

> **Metodolojik Not:** 26 Ekim ara kontrol raporundaki veriler tarihsel bir kayıt olarak korunmuştur. Final analiz hattında ise topolojik ve istatistiksel modellerin matematiksel tutarlılığı için tek bağlı bileşene sahip ve izole düğüm içermeyen **Kapsam B1 (186 aktif üniversite)** birincil analiz ekseni olarak seçilmiş; Kapsam B ise duyarlılık (sensitivity) kıyaslaması olarak raporlanmıştır.

---

## 5. Final Analiz Hattı ve Bilimsel Bulgular (30 Ekim 2026 Teslimi)

Final tesliminde uygulanan tüm ileri yöntemler `scripts/run_final_analysis.py` betiği üzerinden otomatik olarak çalıştırılabilmekte ve çıktıları `reports/generated/` altında saklanmaktadır.

### 5.1. Derece Dağılımı ve Güç Yasası (Power Law)
- **Tahmin Edilen Parametreler:** $\alpha = 2.8989$, $x_{min} = 29.0$, $\sigma = 0.1653$ (düğümlerin %71'i eşiğin üzerindedir).
- **Log-Likelihood Karşılaştırma Testleri:**
  - Üstel Dağılıma Karşı: $R = -5.140$, $p = 2.74 \times 10^{-7}$ (Üstel modeli tercih eder).
  - Log-Normal Dağılıma Karşı: $R = -3.537$, $p = 0.0004$ (Log-normal modeli tercih eder).
- **Bilimsel Sınırlılık Notu:** $N=186$ gibi dar derece aralığına sahip sonlu makro ağlarda saf bir "ölçeksiz (scale-free) güç yasası" iddiasında bulunmak istatistiksel olarak yanıltıcıdır; veriler ağır kuyruklu log-normal davranış sergilemektedir (`degree_distribution_powerlaw.png`).

### 5.2. Louvain ve Leiden Topluluk Tespiti (10 Sabit Tohum Kararlılığı)
- **Ortak Modülerlik Ölçümü ve Optimizasyon Hedefi:** Leiden ve Louvain sonuçları aynı ağırlıklı NetworkX grafiği ve `nx.community.modularity(..., weight='weight')` formülüyle ortak bir ölçekte karşılaştırılmıştır. Leiden algoritmasında optimize edilen ağırlıklı modülerlik hedef fonksiyonu olan `partition.quality()` değeri NetworkX sonucuyla makine hassasiyetinde birebir uyuşmaktadır ($Q = 0.3420$). `leidenalg` kütüphanesinin `igraph.VertexClustering` mirasından gelen `partition.modularity` değeri ise varsayılan olarak ağırlıkları hesaba katmayan farklı bir ölçeklendirme kullandığından daha düşük çıkmaktadır (~$0.1416$).
- **Louvain:** Ortalama $6.5$ topluluk, Modülerlik $Q = 0.3394 \pm 0.0015$, NMI kararlılığı $= 0.8171$, ARI kararlılığı $= 0.8032$.
- **Leiden:** Ortalama $6.6$ topluluk, Ortak Modülerlik / partition.quality $Q = 0.3420 \pm 0.0009$, NMI kararlılığı $= 0.8378$, ARI kararlılığı $= 0.8374$ (Leiden'ın ham `partition.modularity` değeri $0.1416 \pm 0.0025$ olarak saklanmıştır).
- **Çapraz Mutabakat:** İki bağımsız algoritma arasında $NMI = 0.7845$, $ARI = 0.7589$ düzeyinde yüksek mutabakat tespit edilmiştir.

### 5.3. Null Model (Derece Korumalı 100 Rastgele Ağ)
- **Ağırlıksız Topolojik Model:** Deneyin amacı derece dizisinin getirdiği topolojik kısıtları test etmek olduğundan, gözlenen ağ ve 100 rastgele ağ (`connected_double_edge_swap`) tamamen ağırlıksız topolojik basit grafik (`weight=None`) olarak modellenmiştir.
- **Kümelenme ($C$):** Gözlenen $= 0.4433$, Null Ortalama $= 0.3898$, $Z = 12.00$, $p = 0.0099$ (sağ kuyruklu test).
- **En Kısa Yol ($L$):** Gözlenen $= 1.8290$, Null Ortalama $= 1.8079$, $Z = 6.05$, $p = 0.0198$ (iki kuyruklu test).
- **Modülerlik ($Q$):** Gözlenen $= 0.1684$, Null Ortalama $= 0.0962$, $Z = 23.05$, $p = 0.0099$ (sağ kuyruklu test).
- **Küçük Dünya (Small-Worldness):** $\gamma = 1.1373$, $\lambda = 1.0117 \implies \sigma = 1.1242 > 1.0$. Bu değer kesin bir küçük-dünya kanıtı olarak değil, seçilen derece korumalı null model altında sınırlı/hafif bir küçük-dünya sinyali olarak yorumlanmalıdır; ampirik ağın kümelenme katsayısı derece eşdeğeri rastgele ağlardan belirgin şekilde yüksektir ancak ortalama yol uzunluğu rastgele ağ seviyesine çok yakındır.

### 5.4. Zorunlu İleri Yöntem: Çekim (Gravity) Modeli Regresyonu
- **Veri Yapısı:** $\binom{186}{2} = 17.205$ ikili üniversite çifti ($w=0$ sıfır iş birliği çiftleri eksiksiz dahil, %77.63 kurumsal seyreklik).
- **Mesafe ve Sıfır Mesafesi:** Haversine büyük daire mesafesi kullanılmış; aynı şehirdeki kurumların merkez koordinat çakışmasından doğan $\ln(0)$ tanımsızlığı $d_{eff} = d_{raw} + 1.0\text{ km}$ intra-city ofset düzeltmesiyle giderilmiştir.
- **Aşırı Yayılım (Overdispersion):** Poisson modelinde Pearson dispersiyon oranı $4.67 \gg 1.0$ bulunmuş; veriden $\alpha = 2.6511$ ($p < 10^{-248}$) parametresini serbest tahmin eden ayrık Negatif Binom (NB2) modeli esas model olarak seçilmiştir (AIC: Poisson 38.293, Negatif Binom 27.700).
- **Esas Model Katsayıları ve Ekonometrik Yorum:**
  - $\ln(\text{dist}_{eff})$: $\beta = -0.3010$ ($p < 0.001$, %95 GA: [-0.3205, -0.2814]). Bu değer bir **esneklik (elasticity)** katsayısıdır; kilometre başına doğrusal azalış değildir. Coğrafi mesafe %1 arttığında iki üniversite arasındaki iş birliği beklentisi yaklaşık %0.30 azalmaktadır (mesafe iki katına çıktığında $2^{-0.3010} \approx 0.812$ katına, yani %18.8 azalış).
  - $\ln(\text{size}_i)$ ve $\ln(\text{size}_j)$: $\beta_i = 0.7390$, $\beta_j = 0.7780$ ($p < 0.001$). Kurumların CS yayın üretim hacmi çekim kuvvetini katlamaktadır.
  - $BothEgean$: $\beta = 0.7899$ ($p = 5.74 \times 10^{-5}$, %95 GA: [0.4051, 1.1747], $\exp(\beta) = 2.203$). Diğer faktörler sabit tutulduğunda her iki kurumun da Ege'de olması beklenen ortak yayın hacmini yaklaşık **2.20 katına** çıkarmaktadır.
  - **Nedensellik Uyarısı:** Bulgular çekim modeli spesifikasyonuna dayalı kurumsal-coğrafi ilişkileri ve istatistiksel çekim kuvvetini göstermektedir; doğrudan tek yönlü bir nedensellik olarak yorumlanmamalıdır.

---

## 6. Proje Dizin Yapısı

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
│   ├── ara_kontrol.md              # 26 Ekim ara kontrol istatistikleri ve tarihsel rapor
│   └── generated/                  # Final analizi çıktıları (15 adet JSON, CSV, PNG, HTML)
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
│   └── test_final_analysis.py      # Final analiz hattı birim testleri (13 test)
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

## 7. Kurulum ve Yeniden Üretilebilirlik Adımları

### 7.1. Gereksinimler ve Sanal Ortam Kurulumu
```bash
# Depoyu klonlayın ve dizine girin
cd turkiye-universiteleri-isbirligi-agi

# Python 3.10+ sanal ortamı oluşturun ve aktif edin
python3 -m venv venv
source venv/bin/activate

# Gerekli bağımlılıkları yükleyin
pip install -r requirements.txt
```

### 7.2. Testlerin Çalıştırılması (Birim ve Entegrasyon Doğrulama)
```bash
# Tüm birim ve entegrasyon testlerini (27 test) çalıştırın:
PYTHONPATH=. pytest -v
```

### 7.3. Final Analiz Hattının Çalıştırılması (30 Ekim 2026 Teslimi)
```bash
# Temel metrikler, güç yasası, topluluk tespiti, null model, çekim modeli ve coğrafi haritayı üretir:
python scripts/run_final_analysis.py
```
Tüm nihai analiz tabloları, JSON özetleri, grafikler ve etkileşimli HTML haritası `reports/generated/` dizinine kaydedilir. Ayrıca `notebooks/final_analysis.ipynb` üzerinden tüm adımlar interaktif olarak incelenebilir.

### 7.4. Veri Toplama (Canlı OpenAlex API - İsteğe Bağlı)
```bash
# 2020-2025 aralığındaki tüm verileri çeker (yerel önbellekleme destekler):
python scripts/fetch_openalex.py --start-year 2020 --end-year 2025

# Yalnızca sayıları kontrol etmek için (dry-run):
python scripts/fetch_openalex.py --dry-run
```

---

## 8. Veri ve Metodoloji Sınırlılıkları (Limitations)

1. **500 Düğüm Kuralı:** Genel yönerge 500 düğümlü ağ beklerken Türkiye'deki toplam üniversite sayısı 204'tür (YÖK 2026). Bilimsel dürüstlük gereği yapay/sahte düğüm eklenmemiştir.
2. **Coğrafi Koordinat Yığılması:** OpenAlex'te aynı şehirdeki üniversiteler çoğunlukla il merkez koordinatına atanmıştır (İstanbul 49, Ankara 20, İzmir 9 kurum). Bu durum haritada açısal dağıtım (jitter) ile, çekim modelinde ise $+1.0\text{ km}$ efektif mesafe ofsetiyle çözülmüştür.
3. **Örneklem Boyutu ve Güç Yasası:** $N=186$ gibi dar bir derece spektrumunda saf bir güç yasası (scale-free) iddia edilemez; veriler ağır kuyruklu log-normal modele uymaktadır.
4. **Sıfır Enflasyonu ve Aşırı Yayılım:** 17.205 ikili çiftin %77.63'ünde ortak yayın bulunmamaktadır ($w=0$). Bu aşırı yayılım Poisson varsayımlarını geçersiz kıldığından ayrık Negatif Binom (NB2) modeli esas alınmıştır.
5. **İlişkisellik vs Nedensellik:** Çekim modeli regresyon katsayıları kurumsal ve bölgesel çekim ilişkilerini göstermektedir; doğrudan tek yönlü bir nedensel etki olarak yorumlanmamalıdır.
6. **İkili Çiftlerde Ağ Bağımlılığı (Network Dyadic Dependence):** Çekim modelindeki 17.205 ikili gözlem bağımsız değildir; aynı üniversiteleri ortaklaşa paylaşmaktadır (örneğin her bir kurum 185 farklı ikili çiftte yer alır). Bu durum standart GLM regresyonlarındaki gözlemlerin bağımsız ve özdeş dağıldığı (i.i.d.) varsayımını sınırlar; elde edilen standart hatalar ve anlamlılık düzeyleri ağ bağımlılığı göz önüne alınarak temkinli değerlendirilmelidir.

---

## 9. Yapay Zekâ (AI) Kullanım Beyanı
Bu projenin veri toplama boru hattı mimarisinin kurgulanması (`fetch_openalex.py`), ağ oluşturma algoritmasının optimize edilmesi (`build_network.py`), ileri analiz modellerinin geliştirilmesi (`scripts/analysis_*.py`), birim test senaryolarının yazılması (`tests/test_*.py`) ve dokümantasyon taslaklarının hazırlanmasında **Google Antigravity** yapay zekâ kodlama asistanından faydalanılmıştır. Tüm analizler, model tahminleri ve testler yerel terminal ortamında canlı olarak çalıştırılmış ve sonuçların doğruluğu teyit edilmiştir.