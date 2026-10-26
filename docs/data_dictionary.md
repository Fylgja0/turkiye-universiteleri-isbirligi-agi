# Veri Sözlüğü (Data Dictionary)

**Proje:** Türkiye Üniversiteleri Arası Bilimsel İş Birliği Sosyal Ağ Analizi  
**Kurum:** Manisa Celal Bayar Üniversitesi — Büyük Veri Analistliği  
**Aşama:** 26 Ekim 2026 Ara Kontrol Teslimi  
**Veri Kaynağı:** [OpenAlex API](https://openalex.org/) (CC0 Kamu Malı Lisansı)  
**Veri Toplama Tarihi:** 26 Ekim 2026  

---

## 1. Veri Toplama ve Kapsam Kararları

### 1.1. Disiplin ve Konu Kapsamı (`primary_topic.field.id:fields/17`)
- **Seçim Gerekçesi:** OpenAlex sınıflandırma hiyerarşisinde çalışmalar `Domain` -> `Field` -> `Subfield` -> `Topic` şeklinde yapılandırılmıştır. "Computer Science" alanı resmi `/fields` endpoint'inden sorgulanarak `https://openalex.org/fields/17` (ID: `17`) olarak doğrulanmıştır.
- Çalışmaların yalnızca yan bir anahtar kelime olarak değil, ana eksende bilgisayar bilimi araştırması olduğunu garantilemek için `primary_topic.field.id:fields/17` filtresi kullanılmıştır.

### 1.2. Zaman Aralığı (2020-01-01 ile 2025-12-31)
- 2020-2025 yılları arasındaki 6 yıllık dönemi kapsar. Güncel akademik iş birliği dinamiklerini yansıtır.

### 1.3. Kurum Türü ve Ülke Sınırlaması (`country_code:TR`, `type:education`)
- **Düğüm Tanımı:** Türkiye Cumhuriyeti sınırları içerisindeki yükseköğretim kurumları (üniversiteler ve yüksek teknoloji enstitüleri).
- **Filtreler:** OpenAlex `/institutions` verisindeki `country_code == 'TR'` ve `type == 'education'`.
- **Kapsam İncelemesi:** OpenAlex veritabanında Türkiye'de `type:education` olarak kayıtlı toplam **222** kurum bulunmaktadır. Bu sayı, YÖK (Yükseköğretim Kurulu) bünyesindeki 129 devlet, 75 vakıf üniversitesi, vakıf MYO'ları ve harp akademisi/polis akademisi gibi yükseköğretim kurumları evreniyle tam uyumludur. Sanayi şirketleri (örn. ASELSAN, TUSAŞ), araştırma merkezleri (TÜBİTAK UZAY) veya hastaneler ödev kartındaki "üniversite" tanımı gereği ağ düğümü olarak ayrıştırılmıştır.

### 1.4. Sayfalama ve Anahtarsız Erişim Mimarisi
- OpenAlex anahtarsız polite pool erişimi kullanılmıştır (`User-Agent` içinde `mailto:` etik kuralı).
- Cursor paging KULLANILMAMIŞTIR. Standart `per_page=100` ve `page=1..N` kullanılmıştır.
- OpenAlex standart sayfalama üst sınırı 10.000 kayıt olduğu için, veriler yıl bazında parçalanmış; her yıl 4.000-8.000 arasında kalarak 10.000 sınırına takılmadan eksiksiz biçimde indirilmiştir.

### 1.5. 500 Düğüm Kuralı ve Kapsam Kısıtı Açıklaması
> **Önemli Not:** Genel ders yönergesinde yer alan "en az 500 düğüm" kuralı, bireysel araştırmacı (yazar) iş birliği ağları veya küresel ölçekli ağlar için geçerli bir genel parametredir. Kişisel ödev kartında düğüm tanımı **"Türkiye'deki Üniversiteler"** olarak sınırlandırılmıştır. Türkiye'deki toplam üniversite sayısı doğası gereği ~208 (OpenAlex'te 222) olduğundan, bilgisayar bilimi alanında aktif yayın yapan üniversite sayısı 500'e matematiksel ve fiziksel olarak ulaşamaz. Projede yapay/sahte düğüm eklenmemiş, bilimsel dürüstlük ilkesi gereği gerçek evren büyüklüğü raporlanmıştır.

---

## 2. Veri Dosyaları ve Alan Tanımları

### 2.1. `data/processed/edges.csv`
Ağdaki kurumlar arası ortak yazarlık bağlantılarını içerir (Yönsüz, ağırlıklı kenarlar).

| Sütun Adı | Veri Tipi | Açıklama |
| :--- | :--- | :--- |
| `source` | string (URI) | Birinci kurumun OpenAlex ID'si (Örn: `https://openalex.org/I149218525`) |
| `target` | string (URI) | İkinci kurumun OpenAlex ID'si (Örn: `https://openalex.org/I41641357`) |
| `weight` | integer | İki kurum arasında 2020-2025 döneminde ortak yayımlanan toplam bilgisayar bilimi makalesi sayısı ($\ge 1$) |

*Not:* Ağ yönsüz olduğu için $source < target$ alfabetik sıralaması ile kaydedilmiş, çift yönlü mükerrerlik ve $source == target$ self-loop durumları tamamen elenmiştir.

---

### 2.2. `data/processed/institutions.csv`
Ağdaki düğümleri (kurumları) ve özniteliklerini içerir.

| Sütun Adı | Veri Tipi | Açıklama |
| :--- | :--- | :--- |
| `id` | string (URI) | Kurumun tekil OpenAlex tanımlayıcısı (Örn: `https://openalex.org/I41641357`) |
| `display_name` | string | Kurumun uluslararası veya resmi adı (Örn: `Ege University`) |
| `country_code` | string | Ülke ISO kodu (`TR`) |
| `type` | string | OpenAlex kurum türü (`education`) |
| `latitude` | float / null | Kurumun coğrafi enlemi (OpenAlex `geo.latitude` verisi; eksikse null) |
| `longitude` | float / null | Kurumun coğrafi boylamı (OpenAlex `geo.longitude` verisi; eksikse null) |
| `city` | string | Kurumun bulunduğu şehir |
| `works_count` | integer | Kurumun OpenAlex veritabanındaki tüm zamanlara ait toplam yayın sayısı |
| `is_egean` | boolean | Kurumun Ege Bölgesi'nde yer alıp almadığı (`True` / `False`) |
| `degree` | integer | Üniversitenin ağdaki derece merkeziliği (farklı ortak üniversite sayısı) |
| `weighted_degree`| integer | Üniversitenin ağdaki ağırlıklı derecesi (toplam ortak yayın hacmi) |
| `is_isolated` | boolean | Kurumun dönem içinde ortak yayını bulunmayıp tekil yayın yapmış olması (`degree == 0`) |

---

### 2.3. `data/processed/collaboration.graphml`
Ağın tüm düğüm ve kenar öznitelikleriyle birlikte saklandığı standart XML tabanlı GraphML formatıdır. Gephi, Cytoscape veya NetworkX ile doğrudan açılabilir.
- **Düğüm Öznitelikleri:** `name`, `display_name`, `country_code`, `type`, `city`, `is_egean`, `works_count`, `latitude`, `longitude`.
- **Kenar Öznitelikleri:** `weight` (ortak yayın sayısı).
- **Ağ Tipi:** `undirected` (yönsüz).

---

## 3. Veri Temizleme ve Doğrulama Kuralları
1. **Self-Loop Engelleme:** Aynı üniversiteden birden fazla yazarın yer aldığı tek bir yayında, üniversitenin kendi kendine kenar oluşturması engellenmiştir.
2. **Yayın Başına Tekillik:** Bir yayında $A$ ve $B$ üniversitelerinden kaç yazar olursa olsun, o yayın için $(A, B)$ kenar ağırlığı yalnızca **+1** artırılmıştır.
3. **İzole Düğümlerin Korunması:** Bilgisayar bilimi alanında yayın yapmış fakat başka bir Türk üniversitesiyle ortaklık kurmamış kurumlar ağdan sessizce silinmemiş, $degree=0$ izole düğüm olarak ağa dahil edilmiştir.
