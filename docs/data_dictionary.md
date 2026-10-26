# Veri Sözlüğü (Data Dictionary)

**Proje:** Türkiye Üniversiteleri Arası Bilimsel İş Birliği Sosyal Ağ Analizi  
**Kurum:** Manisa Celal Bayar Üniversitesi — Büyük Veri Analistliği  
**Aşama:** 26 Ekim 2026 Ara Kontrol Denetimi ve Bilimsel Tutarlılık Güncellemesi  
**Veri Kaynağı:** [OpenAlex API](https://openalex.org/) (CC0 Kamu Malı Lisansı)  
**Veri Toplama Tarihi:** 26 Ekim 2026  

---

## 1. Veri Toplama ve Kapsam Kararları

### 1.1. Disiplin ve Konu Kapsamı (`primary_topic.field.id:fields/17`)
- **Seçim Gerekçesi:** OpenAlex sınıflandırma hiyerarşisinde çalışmalar `Domain` -> `Field` -> `Subfield` -> `Topic` şeklinde yapılandırılmıştır. "Computer Science" alanı resmi `/fields` endpoint'inden canlı olarak sorgulanarak `https://openalex.org/fields/17` (ID: `17`) olarak doğrulanmıştır.
- Çalışmaların yalnızca yan bir anahtar kelime olarak değil, ana eksende bilgisayar bilimi araştırması olduğunu garantilemek için `primary_topic.field.id:fields/17` filtresi kullanılmıştır.

### 1.2. Zaman Aralığı (2020-01-01 ile 2025-12-31)
- 2020-2025 yılları arasındaki 6 yıllık dönemi kapsar. Yıllara göre dağılım:
  - 2020: 4.153 yayın
  - 2021: 5.045 yayın
  - 2022: 5.422 yayın
  - 2023: 6.166 yayın
  - 2024: 6.516 yayın
  - 2025: 7.812 yayın
  - **Toplam İndirilen:** **35.114 çalışma**

### 1.3. 641 Kayıt Farkının Bilimsel Açıklaması (İndirilen vs. Ağda Yer Alan Yayınlar)
OpenAlex API'den indirilen toplam 35.114 yayın ile ağ kurma scriptinin (`build_network.py`) işlediği 34.473 yayın arasında **641 kayıtlık bir fark** bulunmaktadır. Ham verilerin incelenmesi sonucunda bu farkın nedeni şöyledir:
- API seviyesinde uygulanan `institutions.country_code:TR` filtresi, yazarları arasında Türkiye adresli *herhangi bir kurum* (şirket, kamu kurumu, hastane, eğitim kurumu) bulunan yayınları getirmektedir.
- Ağ modellemesinde ise yalnızca yükseköğretim ve üniversite niteliği taşıyan eğitim kurumları (`type:education`) kapsama alınmıştır.
- 641 çalışmada yazarların tamamı özel sektör veya kamu kurumlarına bağlıdır ve **hiçbir Türk üniversitesi yazarı yer almamaktadır**:
  - `company` (Özel sektör AR-GE: ASELSAN, HAVELSAN, Turkcell vb.): **315 çalışma**
  - `government` (Kamu araştırma: TÜBİTAK BİLGEM, TÜBİTAK MAM vb.): **290 çalışma**
  - `healthcare` (Eğitim ve Araştırma Hastaneleri, Şehir Hastaneleri): **22 çalışma**
  - `facility`: **4 çalışma**
  - `company + government` karma: **3 çalışma**
  - `nonprofit`: **3 çalışma**
  - `other`: **2 çalışma**
  - `facility + government`: **1 çalışma**
  - `country_code değişikliği / affiliation eşleşmesi`: **1 çalışma**
- Bu 641 çalışma, üniversiteler arası iş birliği ağının düğüm tanımına uymadığı için ağ dışı kalmıştır.

### 1.4. YÖK Kurumsal Evreni ve Düğüm Kapsamları (Kapsam A vs. Kapsam B vs. Kapsam B1)
- **Resmî YÖK Evreni:** [YÖK Resmî İstatistikleri](https://www.yok.gov.tr/universiteler/universitelerimiz) (2025–2026 / 2026 Güz) verilerine göre Türkiye'de **129 Devlet Üniversitesi** ve **75 Vakıf Üniversitesi** olmak üzere toplam **204 üniversite** ve ayrıca **4 Bağımsız Vakıf Meslek Yüksekokulu** (toplam **208 yükseköğretim kurumu**) yer almaktadır.
- **OpenAlex `type:education` Evreni:** API'de TR koduyla 222 kurum yer almakta olup, askeri/polis akademileri, kapatılan kurumlar, bağımsız MYO'lar ve KKTC'deki Lefke Avrupa Üniversitesi'ni de içerir.
- **Kapsam A (Geniş Eğitim Kurumu Kapsamı):** 2020–2025 döneminde bilgisayar bilimi yayını bulunan tüm kurumlar (205 düğüm, 3.970 kenar).
- **Kapsam B (186 Kural Tabanlı Aktif + 7 KHK Kurumu, 193 Düğüm):** Yükseköğretim kurumları içinden bağımsız MYO'lar (2), askeri/polis okulları (5), idari/sağlık birimleri (3) ve kısıtlı/doğrulanmamış kurumlar (2: KKTC merkezli Lefke Avrupa Üniversitesi ve 2020 CBK ile kapatılmış olan İstanbul Şehir Üniversitesi bu kapsama dahil edilmemiştir) çıkarılarak elde edilen; 186 kural tabanlı aktif üniversite ile 2016'da 667 KHK ile kapatılan 7 tarihsel üniversitenin toplamından oluşan **193 üniversite** (3.883 kenar).
- **Kapsam B1 (Kural Tabanlı Aktif Üniversiteler):** 2016'da 667 KHK ile kapatılmış 7 tarihsel üniversite (Turgut Özal, Fatih, Gediz, Şifa, Bursa Orhangazi, Canik Başarı, İzmir Üniversitesi) çıkarıldığında geriye kalan ve algoritmik kural tabanlı ad/durum filtresiyle belirlenen **186 aktif üniversite** (3.848 kenar).

---

## 2. Veri Dosyaları ve Alan Tanımları

### 2.1. `data/processed/edges.csv`
Ağdaki kurumlar arası ortak yazarlık bağlantılarını içerir (Yönsüz, ağırlıklı kenarlar).

| Sütun Adı | Veri Tipi | Açıklama |
| :--- | :--- | :--- |
| `source` | string (URI) | Birinci kurumun OpenAlex ID'si (Örn: `https://openalex.org/I149218525`) |
| `target` | string (URI) | İkinci kurumun OpenAlex ID'si (Örn: `https://openalex.org/I41641357`) |
| `weight` | integer | İki kurum arasında 2020-2025 döneminde ortak yayımlanan toplam bilgisayar bilimi makalesi sayısı ($\ge 1$) |

---

### 2.2. `data/processed/institutions.csv`
Ağdaki düğümleri (kurumları) ve hem tüm zamanlar hem de dönem bazlı üretim metriklerini içerir.

| Sütun Adı | Veri Tipi | Açıklama |
| :--- | :--- | :--- |
| `id` | string (URI) | Kurumun tekil OpenAlex tanımlayıcısı (Örn: `https://openalex.org/I41641357`) |
| `display_name` | string | Kurumun uluslararası veya resmi adı (Örn: `Ege University`) |
| `country_code` | string | Ülke ISO kodu (`TR`) |
| `type` | string | OpenAlex kurum türü (`education`) |
| `category` | string | Kurum kategorisi (`active_university`, `closed_2016_khk`, `vocational_college`, `academy_or_institute`, `hospital_or_other`, `unverified`) |
| `is_university` | boolean | Kurumun üniversite niteliği taşıyıp taşımadığı (`True` / `False`) |
| `latitude` | float / null | Kurumun coğrafi enlemi (OpenAlex `geo.latitude` verisi; eksikse null) |
| `longitude` | float / null | Kurumun coğrafi boylamı (OpenAlex `geo.longitude` verisi; eksikse null) |
| `city` | string | Kurumun bulunduğu şehir |
| `all_time_works_count` | integer | Kurumun OpenAlex veritabanındaki tüm zamanlara ve tüm disiplinlere ait toplam yayın sayısı |
| `period_cs_works_count`| integer | **Kurumun 2020–2025 döneminde bilgisayar bilimi alanında ürettiği gerçek yayın sayısı** |
| `works_count` | integer | Geriye dönük uyumluluk için `all_time_works_count` ile eşdeğer tutulmuştur |
| `is_egean` | boolean | Kurumun Ege Bölgesi'nde yer alıp almadığı (`True` / `False`) |
| `degree` | integer | Üniversitenin ağdaki derece merkeziliği (farklı ortak üniversite sayısı) |
| `weighted_degree`| integer | Üniversitenin ağdaki ağırlıklı derecesi (toplam ortak yayın hacmi) |
| `is_isolated` | boolean | Kurumun dönem içinde ortak yayını bulunmayıp tekil yayın yapmış olması (`degree == 0`) |

---

## 3. Coğrafi Koordinatlar ve Çekim Modeli (Gravity Model) Kısıtı

> [!WARNING] **Coğrafi Koordinat Tekrarı ve $\ln(0)$ Problemi:**
> OpenAlex veri tabanında yer alan coğrafi koordinatlar (`latitude`, `longitude`), kampüsün kesin konumundan ziyade genellikle ilgili şehrin merkez koordinatını temsil etmektedir:
> - İncelenen 205 kurum için ham float hassasiyetinde **122 tekil koordinat**, `round(4)` yöntemiyle 4 ondalık basamağa yuvarlandığında (şehir merkezi seviyesinde) ise **112 tekil koordinat** bulunmaktadır.
> - **İstanbul:** 49 farklı kuruma tek bir merkez koordinatı verilmiştir `(41.0138, 28.9497)`.
> - **Ankara:** 20 farklı kuruma tek bir merkez koordinatı verilmiştir `(39.9199, 32.8543)`.
> - **İzmir:** 9 farklı kuruma tek bir merkez koordinatı verilmiştir `(38.4127, 27.1384)`.
> 
> **Metodolojik Etki:** Çekim modeli (Gravity Model) regresyonunda mesafe formülü uygulandığında, aynı şehirdeki iki üniversite arasındaki mesafe $d_{ij} = 0\text{ km}$ çıkmaktadır. Çekim modelindeki logaritmik dönüşümde $\ln(d_{ij}) = \ln(0) = -\infty$ tanımsızlığı oluşur.
> 
> **Çözüm Stratejisi (Final Aşaması İçin):**
> 1. Şehir içi mesafeler için $d_{ij} + 1\text{ km}$ düzeltmesi yapılmalıdır, veya
> 2. OpenStreetMap / Google Geocoding API ile üniversitelerin rektörlük/ana yerleşke koordinatları ayrıştırılmalıdır.
