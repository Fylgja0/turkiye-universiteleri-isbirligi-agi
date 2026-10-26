# Ara Kontrol Raporu: Türk Üniversiteleri Arası Bilimsel İş Birliği Sosyal Ağ Analizi

**Program:** Manisa Celal Bayar Üniversitesi — Büyük Veri Analistliği  
**Ders:** Sosyal Ağ Analizi  
**Aşama:** 26 Ekim 2026 — 23:59 Ara Kontrol Raporu (Bilimsel Denetim ve Doğrulama Sürümü)  
**Yazar:** Proje Ekibi  
**Raporlama Zamanı:** 26 Ekim 2026, 22:36 (TSİ)  

---

## 1. Veri Toplama, API Parametreleri ve 641 Kayıt Farkının Analizi

### 1.1. API Parametreleri ve Veri İndirme
- **Veri Kaynağı:** OpenAlex REST API (`https://api.openalex.org`)
- **Doğrulanan Alan:** `/fields` endpoint'i üzerinden dinamik sorguyla doğrulanmış `fields/17` ("Computer Science").
- **Tarih Aralığı:** `from_publication_date:2020-01-01` ile `to_publication_date:2025-12-31`.
- **API Filtresi:** `primary_topic.field.id:fields/17,from_publication_date:2020-01-01,to_publication_date:2025-12-31,institutions.country_code:TR`.
- **Sayfalama:** Cursor paging kullanılmamış; `per_page=100`, `page=1..N` ile yıllık dilimler halinde toplam **35.114 yayın** indirilmiştir.

### 1.2. 35.114 İndirilen Yayın vs. 34.473 İşlenen Yayın (641 Kayıt Farkı)
API sorgusu sonucunda inen 35.114 kayıt ile ağ algoritmasının işlediği 34.473 yayın arasındaki **641 kayıtlık fark**, ham verilerin satır satır incelenmesiyle doğrulanmıştır:

| Yıl | (1) İndirilen Ham Yayın | (2) Türkiye Eğitim Kurumu İçeren | (3) Fark (Salt Sanayi/Kamu/Sağlık) | (4) Ortak Yayın (En Az 2 Türk Kurumu) |
| :---: | :---: | :---: | :---: | :---: |
| **2020** | 4.153 | 4.084 | 69 | 851 |
| **2021** | 5.045 | 4.969 | 76 | 1.059 |
| **2022** | 5.422 | 5.316 | 106 | 1.144 |
| **2023** | 6.166 | 6.034 | 132 | 1.282 |
| **2024** | 6.516 | 6.410 | 106 | 1.408 |
| **2025** | 7.812 | 7.660 | 152 | 1.726 |
| **TOPLAM** | **35.114** | **34.473** | **641** | **7.470** |

**641 Farkın Nedeni ve Sektörel Dökümü:**
API düzeyinde `institutions.country_code:TR` filtresi uygulandığı için Türkiye'de yerleşik şirketler, bakanlıklar ve kamu araştırma merkezleri de yanıta dahil olmuştur. Bu 641 çalışmada yazarlar arasında **hiçbir üniversite veya eğitim kurumu yer almamakta**, yalnızca sanayi/kamu/sağlık kuruluşları bulunmaktadır:
- `company` (Özel sektör: ASELSAN, HAVELSAN, Turkcell vb.): **315 çalışma** (Örn: `W3040579653`)
- `government` (Kamu Ar-Ge: TÜBİTAK BİLGEM, TÜBİTAK MAM vb.): **290 çalışma** (Örn: `W3045322569`, `W3080667067`)
- `healthcare` (Eğitim Araştırma ve Şehir Hastaneleri): **22 çalışma** (Örn: `W3029272675`, `W3090128481`)
- `facility`: **4 çalışma**
- `company + government` karma: **3 çalışma**
- `nonprofit`: **3 çalışma**
- `other`: **2 çalışma**
- `facility + government`: **1 çalışma**
- `no_TR_country_institutions` (OpenAlex veri entegrasyonu kaynaklı): **1 çalışma**

Eğitim kurumu niteliği taşımayan bu 641 yayın kapsam kararı gereği ağ dışı bırakılmıştır.

---

## 2. Kurum Sınıflandırması ve Düğüm Evreni Karşılaştırması

OpenAlex'teki `country_code:TR` ve `type:education` filtrelemesine uyan 205 kurum ROR kimlikleri, mevzuat statüleri, `raw_status` verileri ve Resmî Gazete kayıtları üzerinden incelenmiş ve sınıflandırılmıştır:

1. **Halen Aktif Üniversiteler (`active_university`):** **186 kurum** (Devlet ve Vakıf üniversiteleri, İYTE ve Gebze Teknik).
2. **2016 KHK ile Kapatılan Tarihsel Üniversiteler (`closed_2016_khk`):** **7 kurum**
   - `Turgut Özal University` (Ankara, `https://openalex.org/I6573832`)
   - `Fatih University` (İstanbul, `https://openalex.org/I32462889`)
   - `Gediz University` (İzmir, `https://openalex.org/I149028718`)
   - `Şifa University` (İzmir, `https://openalex.org/I334480368`)
   - `Bursa Orhangazi University` (Bursa, `https://openalex.org/I3003364`)
   - `Canik Başarı University` (Samsun, `https://openalex.org/I264664839` - İzole)
   - `Izmir University` (İzmir, `https://openalex.org/I132257509` - 667 sayılı KHK ile kapatılmıştır; önceki active_university yanlış ataması düzeltilmiştir).  
   *(Not: 2018'de 7141 sayılı kanunla kurulan aktif devlet üniversitesi 'Malatya Turgut Özal Üniversitesi' (`I4210110665`) ile 'Fatih Sultan Mehmet Vakıf Üniversitesi' (`I4210146544`) kapatılan adaşlarından ID bazında ayrıştırılarak aktif üniversite olarak korunmuştur).*
3. **Bağımsız Meslek Yüksekokulları (`vocational_college`):** **2 kurum** (`İzmir Kavram Meslek Yüksekokulu`, `İstanbul Şişli Meslek Yüksekokulu`).
4. **Harp/Polis Okulları ve Yabancı Enstitüler (`academy_or_institute`):** **5 kurum** (`Naval Academy`, `Turkish Air Force Academy`, `Turkish Military Academy`, `Police Academy`, `British Institute at Ankara`).
5. **Sağlık/İdari Merkezler (`hospital_or_other`):** **3 kurum** (`Istanbul Provincial Directorate of National Education`, `SBÜ Beyhekim Training and Research Hospital`, `Research Center for Built Environment and Design`).
6. **Doğrulanmamış / Özel Kısıtlı Kurumlar (`unverified`):** **2 kurum**
   - `European University of Lefke` (`https://openalex.org/I116528569`): OpenAlex kaydında `country_code: TR` olarak yer almasına karşın Kuzey Kıbrıs Türk Cumhuriyeti'nde (KKTC) yer almaktadır; YÖK Türkiye üniversiteleri listesinde değil, KKTC üniversiteleri statüsündedir.
   - `Istanbul Şehir University` (`https://openalex.org/I13419840`): OpenAlex `raw_status` verisinde `active` görünmesine karşın, 30 Haziran 2020 tarihli ve 2814 sayılı Cumhurbaşkanı Kararı ile faaliyet izni kaldırılarak kapatılmış ve Marmara Üniversitesi'ne devredilmiştir.

> [!NOTE] **Sınıflandırma Metodolojisi ve Güvenirlik Ayrımı:**  
> Kapatılan 7 üniversite ve özel kısıtlı 2 kurum OpenAlex ID bazında kesin olarak doğrulanmıştır. `active_university` kategorisindeki atamalar ise OpenAlex `raw_status` kontrolü (`inactive/closed/defunct` olmama) ve kurum adındaki "university/universite/institute of technology" kelime eşleşmesine dayalı algoritmik kural tabanlı bir sınıflamadır. OpenAlex/ROR `status` alanı (genellikle 'active' kalmaktadır) Türkiye'deki güncel hukuki yükseköğretim statüsünü tek başına kanıtlamadığından, bu ayrım raporda açıkça belirtilmiştir.

**Toplam Düğüm Sayısı:** 186 + 7 + 2 + 5 + 3 + 2 = **205 kurum** (tam tutarlı).

### 2.1. Karşılaştırmalı Ağ Topolojisi Tablosu

| Metrik | Kapsam A (Tüm Education Kurumları) | Kapsam B (Üniversiteler - Tarihsel Dahil) | Kapsam B1 (Yalnızca Halen Aktif Üniversiteler) |
| :--- | :---: | :---: | :---: |
| **Düğüm Sayısı ($|V|$)** | **205** | **193** | **186** |
| **Kenar Sayısı ($|E|$)** | **3.970** | **3.883** | **3.848** |
| **Ağ Yoğunluğu (Density)** | 0.189861 | 0.209575 | **0.223656** |
| **Bağlı Bileşen Sayısı** | 4 | 2 | **1** |
| **İzole Düğüm Sayısı** | 3 | 1 (Canik Başarı Üni) | **0** |
| **Dev Bileşen Büyüklüğü** | 202 (%98.5) | 192 (%99.5) | **186 (%100.0)** |

> **Metodolojik Çıkarım:**
> Kapsam B1'e (halen aktif üniversitelere) odaklanıldığında Türkiye'deki tüm üniversiteler **tek bir dev bileşen** içinde toplanmakta, hiçbir üniversite izole kalmamaktadır ($density = 0.223656$).

---

## 3. Kurumsal Üretim Hacmi Düzeltmesi (All-time vs. Period CS Works)

OpenAlex `works_count` verisi tüm zamanlara ve tüm disiplinlere aittir. Bilgisayar bilimi alanındaki 2020–2025 dönem üretim hacmi (`period_cs_works_count`) indirilen gerçek yayınlardan ayrı bir sütun olarak hesaplanmıştır:

### En Çok CS Yayını Üreten İlk 10 Üniversite (2020–2025 Dönemi)

| Sıra | Üniversite Adı | İl | 2020–2025 CS Eser Sayısı | Tüm Zamanlar Eser Sayısı | Derece ($k_i$) | Ağırlıklı Derece ($s_i$) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| 1 | **İstanbul Teknik Üniversitesi** | İstanbul | **1.670** | 53.448 | 109 | 569 |
| 2 | **Orta Doğu Teknik Üniversitesi** | Ankara | **1.320** | 50.160 | 91 | 408 |
| 3 | **Fırat Üniversitesi** | Elazığ | **1.173** | 30.163 | 94 | 538 |
| 4 | **Gazi Üniversitesi** | Ankara | **1.170** | 61.742 | 121 | 582 |
| 5 | **Yıldız Teknik Üniversitesi** | İstanbul | **1.043** | 31.362 | 116 | 553 |
| 6 | **Hacettepe Üniversitesi** | Ankara | **1.019** | 83.559 | 116 | 588 |
| 7 | **Boğaziçi Üniversitesi** | İstanbul | **785** | 24.497 | 71 | 322 |
| 8 | **İstanbul Üniversitesi** | İstanbul | **712** | 89.232 | 116 | 754 |
| 9 | **Ankara Üniversitesi** | Ankara | **700** | 71.659 | 106 | 440 |
| 10 | **Ege Üniversitesi** | İzmir | **670** | 53.427 | 75 | 280 |
| ... | **Manisa Celal Bayar Üniversitesi**| Manisa | **322** | 18.434 | 66 | 198 |

---

## 4. Ege Bölgesi Kurumlarının Ağdaki Yeri (Kategori Bazlı Döküm)

Ege Bölgesi'nde yer alan toplam 18 kurum bulunmaktadır. Bu kurumlar niteliklerine göre ayrıştırılmış; meslek yüksekokulları üniversite gibi sunulmamış, kapatılan kurumlar aktif üniversiteye dahil edilmemiştir:

### 4.1. Halen Aktif Ege Bölgesi Üniversiteleri (14 Kurum)

| Sıra | Üniversite Adı | İl | 2020–25 CS Eser | Derece ($k_i$) | Ağırlıklı Derece ($s_i$) | Tüm Zamanlar Eser |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| 1 | **Ege Üniversitesi** | İzmir | **670** | 75 | 280 | 53.427 |
| 2 | **Dokuz Eylül Üniversitesi** | İzmir | **517** | 72 | 187 | 42.239 |
| 3 | **Manisa Celal Bayar Üniversitesi** | Manisa | **322** | **66** | **198** | **18.434** |
| 4 | **Muğla Sıtkı Koçman Üniversitesi** | Muğla | **279** | 41 | 99 | 16.929 |
| 5 | **İzmir Yüksek Teknoloji Enstitüsü** | İzmir | **260** | 43 | 106 | 8.333 |
| 6 | **Kütahya Dumlupınar Üniversitesi** | Kütahya | **250** | 46 | 81 | 10.253 |
| 7 | **İzmir Kâtip Çelebi Üniversitesi** | İzmir | **249** | 49 | 127 | 14.921 |
| 8 | **Pamukkale Üniversitesi** | Denizli | **244** | 69 | 171 | 23.604 |
| 9 | **Afyon Kocatepe Üniversitesi** | Afyon | **212** | 52 | 122 | 14.582 |
| 10 | **İzmir Ekonomi Üniversitesi** | İzmir | **173** | 37 | 88 | 5.384 |
| 11 | **Aydın Adnan Menderes Üniversitesi**| Aydın | **153** | 43 | 82 | 17.810 |
| 12 | **Yaşar Üniversitesi** | İzmir | **146** | 41 | 73 | 3.841 |
| 13 | **Uşak Üniversitesi** | Uşak | **140** | 34 | 115 | 11.559 |
| 14 | **İzmir Tınaztepe Üniversitesi** | İzmir | **2** | 5 | 5 | 800 |

### 4.2. 2016 KHK ile Kapatılan Tarihsel Ege Üniversiteleri (3 Kurum)
*Geçmiş yayınların geç taranması/düzeltilmesi kaynaklı dönem verisinde yer almaktadır; aktif üniversite sayılmamaktadır:*
1. **İzmir Üniversitesi** (İzmir) - 4 CS eseri, Derece: 3, Ağırlıklı Derece: 3, Tüm Zamanlar: 1.536
2. **Gediz Üniversitesi** (İzmir) - 2 CS eseri, Derece: 2, Ağırlıklı Derece: 2, Tüm Zamanlar: 396
3. **Şifa Üniversitesi** (İzmir) - 1 CS eseri, Derece: 2, Ağırlıklı Derece: 2, Tüm Zamanlar: 800

### 4.3. Bağımsız Meslek Yüksekokulu (1 Kurum)
*Üniversite statüsünde olmayıp vakıf MYO niteliğindedir:*
1. **İzmir Kavram Meslek Yüksekokulu** (İzmir) - 13 CS eseri, Derece: 22, Ağırlıklı Derece: 26, Tüm Zamanlar: 435

> **Özet Bulgu:**  
> Manisa Celal Bayar Üniversitesi, aktif Ege üniversiteleri arasında hem 2020–2025 CS yayın üretiminde (322 eser) hem de derece merkeziliğinde ($k_i=66$), Ege ve Dokuz Eylül'ün ardından **3. sırada** yer almaktadır. Ağdaki toplam iş birliği hacmini temsil eden ağırlıklı derecede ise ($s_i=198$), Dokuz Eylül Üniversitesi'ni (187) de geride bırakarak Ege Üniversitesi'nden (280) sonra **bölgede 2. sırada** yer almaktadır.

---

## 5. Çekim Modeli (Gravity Model) ve Tekrarlanan Koordinatlar Sorunu

> [!CAUTION] **Tekrarlanan Koordinatlar ve $\ln(0)$ Problemi:**
> OpenAlex'ten çekilen koordinatlar incelendiğinde, 205 kurum için ham float hassasiyetinde **122 tekil koordinat**, 4 ondalık basamağa yuvarlandığında (şehir merkezi seviyesinde) ise **112 tekil koordinat** bulunduğu tespit edilmiştir:
> - **İstanbul:** 49 kuruma `(41.0138, 28.9497)` şehir merkezi koordinatı atanmıştır.
> - **Ankara:** 20 kuruma `(39.9199, 32.8543)` merkez koordinatı atanmıştır.
> - **İzmir:** 9 kuruma `(38.4127, 27.1384)` merkez koordinatı atanmıştır.
>
> **Metodolojik Sorun:** Aynı ilde yer alan iki üniversite arasındaki coğrafi mesafe formülle hesaplandığında $d_{ij} = 0\text{ km}$ çıkmaktadır. Çekim modelindeki standart formülasyon olan $\ln(d_{ij})$ terimi hesaplandığında $\ln(0) = -\infty$ tanımsızlığı ortaya çıkmaktadır.
>
> **Dönem Sonu Çözüm Planı:** Çekim modeli regresyonunda mesafe terimi için ya $d_{ij} + 1\text{ km}$ taban düzeltmesi kullanılacak ya da yerleşke bazlı hassas koordinatlar harici coğrafi API'lerle (OpenStreetMap Nominatim vb.) zenginleştirilecektir.

---

## 6. Önemli "500 Düğüm Kuralı" Kapsam Açıklaması

> **Öğretim Görevlisinin Değerlendirmesine:**  
> Genel ders izlencesi en az 500 düğümlü bir ağ talep etmektedir. Ancak tarafıma iletilen ödev kartında düğüm **"Türkiye'deki Üniversiteler"** olarak sınırlandırılmıştır.  
> 
> 1. [YÖK Resmî İstatistikleri](https://www.yok.gov.tr/universiteler/universitelerimiz) verilerine göre Türkiye'de güncel olarak **208 üniversite** bulunmaktadır (129 Devlet Üniversitesi, 75 Vakıf Üniversitesi; 4 bağımsız Vakıf Meslek Yüksekokulu hariç. MYO'lar dahil edildiğinde 212 yükseköğretim kurumudur).  
> 2. OpenAlex veritabanında ise `country_code: TR` ve `type: education` filtresinde toplam **222 kurum** yer almaktadır (Bu sayı üniversitelerin yanı sıra askeri okulları, kapatılan kurumları, bağımsız MYO'ları ve KKTC'deki Lefke Avrupa Üniversitesi gibi kurumları da içerir).  
> 3. Bilgisayar bilimi alanında 2020–2025'te yayın yapan tekil eğitim kurumu sayısı **205** (Kapsam A), üniversite niteliğindeki kurum sayısı **193** (Kapsam B - tarihsel dahil), halen hukuken aktif üniversite sayısı ise **186** (Kapsam B1)'dir.  
> 
> Ağın 500 düğüme ulaşması evrenin fiziksel sınırlılığı nedeniyle imkansızdır. Sahte veri üretilmemiş, bilimsel dürüstlük ilkesi gereği gerçek sayılar raporlanmıştır.

---

## 7. Üretilen Ara Kontrol Dosyaları
- `scripts/fetch_openalex.py`: Canlı veri toplama scripti.
- `scripts/build_network.py`: Çoklu kapsam analizli, dönem CS eser sayaçlı ağ kurucu.
- `data/processed/edges.csv`: 3.970 ağırlıklı kenar listesi.
- `data/processed/institutions.csv`: 205 kurumun koordinatları, `all_time_works_count`, `period_cs_works_count`, `category`, `is_university` ve merkezilikleri.
- `data/processed/collaboration.graphml`: Düğüm öznitelikleriyle zenginleştirilmiş GraphML.
- `tests/test_network.py`: 6 birim test (Pytest ile 6/6 PASSED).
- `docs/data_dictionary.md`: Ayrıntılı veri sözlüğü.
- `README.md`: Proje amacı, CV özeti, çalıştırma adımları ve AI kullanım beyanı.
