# Ara Kontrol Raporu: Türk Üniversiteleri Arası Bilimsel İş Birliği Sosyal Ağ Analizi

**Program:** Manisa Celal Bayar Üniversitesi — Büyük Veri Analistliği  
**Ders:** Sosyal Ağ Analizi  
**Aşama:** 26 Ekim 2026 — 23:59 Ara Kontrol Raporu (Bilimsel Denetim ve Doğrulama Sürümü)  
**Yazar:** Proje Ekibi  
**Raporlama Zamanı:** 26 Ekim 2026, 22:12 (TSİ)  

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

| Yıl | İndirilen Ham Yayın | Üniversite/Eğitim İçeren | Fark (Yalnızca Sanayi/Kamu) |
| :---: | :---: | :---: | :---: |
| **2020** | 4.153 | 4.084 | 69 |
| **2021** | 5.045 | 4.969 | 76 |
| **2022** | 5.422 | 5.316 | 106 |
| **2023** | 6.166 | 6.034 | 132 |
| **2024** | 6.516 | 6.410 | 106 |
| **2025** | 7.812 | 7.660 | 152 |
| **TOPLAM** | **35.114** | **34.473** | **641** |

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
- `no_TR_country_institutions` (veri entegrasyonu kaynaklı): **1 çalışma**

Üniversiteler arası iş birliği ağı kurulurken eğitim kurumu niteliği taşımayan bu 641 yayın kapsam dışı bırakılmıştır.

---

## 2. Kurum Sınıflandırması ve Düğüm Evreni Karşılaştırması

OpenAlex'teki `country_code:TR` ve `type:education` filtrelemesine uyan 205 kurum ROR kimlikleri, mevzuat statüleri ve tarihsel durumları üzerinden incelenmiş ve 5 kategoriye ayrılmıştır:

1. **Halen Aktif Üniversiteler (`active_university`):** **189 kurum** (Devlet ve Vakıf üniversiteleri, İYTE ve Gebze Teknik Enstitüleri).
2. **2016 KHK ile Kapatılmış Tarihsel Üniversiteler (`closed_2016_khk`):** **6 kurum** (Turgut Özal, Fatih, Gediz, Şifa, Bursa Orhangazi, Canik Başarı Üniversiteleri). Bu kurumlar, geçmiş çalışmaların atıf/düzeltme veya geç taranan kayıtları nedeniyle veri tabanında yer almaktadır.
3. **Bağımsız Meslek Yüksekokulları (`vocational_college`):** **2 kurum** (İzmir Kavram MYO, İstanbul Şişli MYO).
4. **Harp/Polis Akademileri ve Yabancı Enstitüler (`academy_or_institute`):** **6 kurum** (Deniz, Hava, Kara Harp Okulları, Polis Akademisi, British Institute at Ankara).
5. **Sağlık/İdari Merkezler (`hospital_or_other`):** **2 kurum** (İstanbul İl MEM, SBÜ Beyhekim EAH).

### 2.1. Karşılaştırmalı Ağ Topolojisi Tablosu

| Metrik | Kapsam A (Tüm Education Kurumları) | Kapsam B (Üniversiteler - Tarihsel Dahil) | Kapsam B1 (Yalnızca Halen Aktif Üniversiteler) |
| :--- | :---: | :---: | :---: |
| **Düğüm Sayısı ($|V|$)** | **205** | **195** | **189** |
| **Kenar Sayısı ($|E|$)** | **3.970** | **3.896** | **3.864** |
| **Ağ Yoğunluğu (Density)** | 0.189861 | 0.205974 | 0.217494 |
| **Bağlı Bileşen Sayısı** | 4 | 2 | 1 |
| **İzole Düğüm Sayısı** | 3 | 1 (Canik Başarı Üni) | **0** |
| **Dev Bileşen Büyüklüğü** | 202 (%98.5) | 194 (%99.5) | **189 (%100.0)** |

> **Metodolojik Çıkarım:**
> Kapsam B1'e (aktif üniversitelere) odaklanıldığında Türkiye'deki tüm üniversiteler **tek bir dev bileşen** oluşturmakta, hiçbir üniversite izole kalmamaktadır ($density = 0.217$). Bu durum Türkiye akademik ağının yüksek derecede bütünleşik olduğunu göstermektedir.

---

## 3. Kurumsal Üretim Hacmi Düzeltmesi (All-time vs. Period CS Works)

Önceki taslakta yer alan "Toplam Eser" sütunu OpenAlex'in tüm zamanlara ve tüm disiplinlere ait `works_count` verisiydi. Bilgisayar bilimi alanındaki 2020–2025 dönem üretim hacmi (`period_cs_works_count`) gerçek verilerden ayrı bir değişken olarak hesaplanmış ve netleştirilmiştir:

### En Çok CS Yayını Üreten İlk 10 Üniversite (2020–2025 Dönemi)

| Sıra | Üniversite Adı | İl | 2020–2025 CS Eser Sayısı | Tüm Zamanlar Eser Sayısı | Derece ($k_i$) | Ağırlıklı Derece ($s_i$) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| 1 | **İstanbul Teknik Üniversitesi** | İstanbul | **1.670** | 53.448 | 109 | 569 |
| 2 | **Orta Doğu Teknik Üniversitesi** | Ankara | **1.320** | 47.925 | 92 | 471 |
| 3 | **Fırat Üniversitesi** | Elazığ | **1.173** | 30.163 | 94 | 538 |
| 4 | **Gazi Üniversitesi** | Ankara | **1.170** | 61.742 | 121 | 582 |
| 5 | **Yıldız Teknik Üniversitesi** | İstanbul | **1.043** | 31.362 | 116 | 553 |
| 6 | **Hacettepe Üniversitesi** | Ankara | **1.019** | 83.559 | 116 | 588 |
| 7 | **Boğaziçi Üniversitesi** | İstanbul | **785** | 30.297 | 64 | 258 |
| 8 | **İstanbul Üniversitesi** | İstanbul | **712** | 89.232 | 116 | 754 |
| 9 | **Ankara Üniversitesi** | Ankara | **700** | 71.659 | 106 | 440 |
| 10 | **Ege Üniversitesi** | İzmir | **670** | 53.427 | 75 | 280 |
| ... | **Manisa Celal Bayar Üniversitesi**| Manisa | **322** | 18.434 | 66 | 198 |

*Not:* Tüm zamanlar toplamında en yüksek olan İstanbul Üniversitesi (89k) ve Hacettepe (83k), tıp ve fen bilimleri ağırlıklı iken; bilgisayar biliminde İTÜ (1.670), ODTÜ (1.320) ve Fırat Üniversitesi (1.173) lider konumdadır.

---

## 4. Ege Bölgesi Üniversitelerinin Ağdaki Yeri

Ege Bölgesi'nde yer alan 18 üniversitenin tamamı ağın dev bileşeni içindedir:

| Sıra | Üniversite | İl | Statü | 2020–25 CS Eser | Derece ($k_i$) | Ağırlıklı Derece ($s_i$) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| 1 | **Ege Üniversitesi** | İzmir | Aktif | 670 | 75 | 280 |
| 2 | **Dokuz Eylül Üniversitesi** | İzmir | Aktif | 436 | 72 | 187 |
| 3 | **Pamukkale Üniversitesi** | Denizli | Aktif | 345 | 69 | 171 |
| 4 | **Manisa Celal Bayar Üniversitesi** | Manisa | Aktif | **322** | **66** | **198** |
| 5 | **Afyon Kocatepe Üniversitesi** | Afyon | Aktif | 215 | 52 | 122 |
| 6 | **İzmir Kâtip Çelebi Üniversitesi** | İzmir | Aktif | 195 | 49 | 127 |
| 7 | **Kütahya Dumlupınar Üniversitesi** | Kütahya | Aktif | 148 | 46 | 81 |
| 8 | **İzmir Yüksek Teknoloji Enstitüsü** | İzmir | Aktif | 260 | 43 | 106 |
| 9 | **Aydın Adnan Menderes Üniversitesi**| Aydın | Aktif | 161 | 43 | 82 |
| 10 | **Muğla Sıtkı Koçman Üniversitesi** | Muğla | Aktif | 178 | 41 | 99 |
| 11 | **Yaşar Üniversitesi** | İzmir | Aktif | 152 | 41 | 73 |
| 12 | **İzmir Ekonomi Üniversitesi** | İzmir | Aktif | 145 | 37 | 88 |
| 13 | **Uşak Üniversitesi** | Uşak | Aktif | 144 | 34 | 115 |
| 14 | **İzmir Kavram Meslek Yüksekokulu** | İzmir | MYO | 33 | 22 | 26 |
| 15 | **İzmir Tınaztepe Üniversitesi** | İzmir | Aktif | 14 | 5 | 5 |
| 16 | **İzmir Üniversitesi** | İzmir | Kapatılan | 2 | 3 | 3 |
| 17 | **Gediz Üniversitesi** | İzmir | Kapatılan | 3 | 2 | 2 |
| 18 | **Şifa Üniversitesi** | İzmir | Kapatılan | 4 | 2 | 2 |

> **Bulgu:** Manisa Celal Bayar Üniversitesi, Ege Bölgesi'nde en çok ortaklık kuran 4. üniversitedir. Ağırlıklı derecede ise (198) Dokuz Eylül ve Pamukkale'nin önünde, Ege Üniversitesi'nden sonra **2. sıradadır**.

---

## 5. Çekim Modeli (Gravity Model) ve Coğrafi Mesafe Metodolojik Kısıtı

> [!CAUTION] **Tekrarlanan Koordinatlar ve $\ln(0)$ Problemi:**
> OpenAlex'ten çekilen koordinatlar incelendiğinde, 205 kurum için yalnızca **112 tekil koordinat** bulunduğu tespit edilmiştir:
> - **İstanbul:** 49 kuruma `(41.0138, 28.9497)` şehir merkezi koordinatı verilmiştir.
> - **Ankara:** 20 kuruma `(39.9199, 32.8543)` merkez koordinatı atanmıştır.
> - **İzmir:** 9 kuruma `(38.4127, 27.1384)` merkez koordinatı atanmıştır.
>
> **Sorun:** Aynı ilde yer alan iki üniversite arasındaki coğrafi mesafe $d_{ij} = 0\text{ km}$ çıkmaktadır. Çekim modelindeki standart formülasyon olan $\ln(d_{ij})$ hesaplandığında $\ln(0) = -\infty$ tanımsızlığı ortaya çıkmaktadır.
>
> **Dönem Sonu Çözüm Planı:** Çekim modeli regresyonunda mesafe terimi için ya $d_{ij} + 1\text{ km}$ taban düzeltmesi kullanılacak ya da yerleşke bazlı hassas koordinatlar harici coğrafi API'lerle zenginleştirilecektir.

---

## 6. Önemli "500 Düğüm Kuralı" Kapsam Açıklaması

> **Öğretim Görevlisinin Değerlendirmesine:**  
> Genel ders izlencesi en az 500 düğümlü bir ağ talep etmektedir. Ancak tarafıma iletilen ödev kartında düğüm **"Türkiye'deki Üniversiteler"** olarak sınırlandırılmıştır.  
> 
> YÖK resmi istatistiklerinde ve OpenAlex veritabanında Türkiye'deki toplam üniversite sayısı **222**'dir. Bilgisayar bilimi alanında 2020–2025'te yayın yapan tekil üniversite sayısı **195** (halen aktif olanlar **189**)'dur.  
> 
> Ağın 500 düğüme ulaşması evrenin fiziksel sınırlılığı nedeniyle imkansızdır. Sahte veri üretilmemiş, bilimsel dürüstlük ilkesi gereği gerçek sayılar raporlanmıştır.

---

## 7. Üretilen Ara Kontrol Dosyaları
- `scripts/fetch_openalex.py`: Canlı veri toplama scripti.
- `scripts/build_network.py`: Çoklu kapsam analizli, dönem CS eser sayaçlı ağ kurucu.
- `data/processed/edges.csv`: 3.970 ağırlıklı kenar listesi.
- `data/processed/institutions.csv`: 205 kurumun koordinatları, `all_time_works_count`, `period_cs_works_count`, kategori ve merkezilikleri.
- `data/processed/collaboration.graphml`: Düğüm öznitelikleriyle zenginleştirilmiş GraphML.
- `tests/test_network.py`: Birim testler (Pytest ile 3/3 PASSED).
- `docs/data_dictionary.md`: Ayrıntılı veri sözlüğü.
- `README.md`: Proje amacı, CV özeti, çalıştırma adımları ve AI kullanım beyanı.
