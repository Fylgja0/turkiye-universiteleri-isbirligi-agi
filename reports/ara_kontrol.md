# Ara Kontrol Raporu: Türk Üniversiteleri Arası Bilimsel İş Birliği Sosyal Ağ Analizi

**Program:** Manisa Celal Bayar Üniversitesi — Büyük Veri Analistliği  
**Ders:** Sosyal Ağ Analizi  
**Aşama:** 26 Ekim 2026 — 23:59 Ara Kontrol Raporu  
**Yazar:** Proje Ekibi  
**Raporlama Zamanı:** 26 Ekim 2026, 21:48 (TSİ)  

---

## 1. Veri Toplama ve API Parametreleri

- **Veri Kaynağı:** OpenAlex REST API (`https://api.openalex.org`)
- **Veri Toplama Zamanı:** 26 Ekim 2026, 21:35 – 21:47 (TSİ)
- **Erişim Türü:** Anahtarsız erişim (OpenAlex Polite Pool standartlarına uygun User-Agent `mailto:` başlığı ile).
- **Disiplin Doğrulaması:** OpenAlex resmi `/fields` endpoint'i üzerinden dinamik olarak sorgulanmış ve "Computer Science" disiplininin tam kimliği `https://openalex.org/fields/17` (`fields/17`) olarak teyit edilmiştir.
- **Uygulanan API Filtresi:**
  ```text
  primary_topic.field.id:fields/17
  from_publication_date:2020-01-01
  to_publication_date:2025-12-31
  institutions.country_code:TR
  ```
- **Sayfalama Stratejisi:** Cursor paging KULLANILMAMIŞTIR. OpenAlex'in anahtarsız standart sayfalama üst sınırı olan 10.000 kayıt limitine takılmamak için sorgular yıl bazında dilimlenmiştir (`per_page=100`, `page=1..N`).
- **Önbellekleme:** Canlı kaynaktan çekilen 35.114 makale `data/raw/works_*.jsonl` dosyalarında saklanmıştır. Hız sınırlamalarına karşı üstel bekleme (exponential backoff) uygulanmıştır.

---

## 2. Kapsama Giren Yayın Sayıları

| Yıl | Toplam Yayın Sayısı | Durum |
| :---: | :---: | :---: |
| **2020** | 4.153 | Eksiksiz Tamamlandı |
| **2021** | 5.045 | Eksiksiz Tamamlandı |
| **2022** | 5.422 | Eksiksiz Tamamlandı |
| **2023** | 6.166 | Eksiksiz Tamamlandı |
| **2024** | 6.516 | Eksiksiz Tamamlandı |
| **2025** | 7.812 | Eksiksiz Tamamlandı |
| **TOPLAM** | **35.114** | **%100 Eksiksiz Çekildi** |

---

## 3. Ağ Yapısı ve Topoloji Metrikleri

`scripts/build_network.py` scripti tarafından işlenen verilerden elde edilen kesin ağ metrikleri:

| Metrik | Değer | Açıklama |
| :--- | :---: | :--- |
| **İncelenen Toplam Yayın** | 35.114 | 2020–2025 arası bilgisayar bilimi çalışmaları |
| **Türkiye Kurumu İçeren Yayın** | 34.473 | Yazarları arasında en az 1 Türk üniversitesi olan yayınlar |
| **Ortak Yayın Sayısı** | 7.470 | En az iki farklı Türk kurumu arasında iş birliği içeren yayınlar |
| **Toplam Düğüm Sayısı ($|V|$)** | **205** | Dönem içinde aktif yayın yapmış Türk üniversite/eğitim kurumu |
| **Toplam Kenar Sayısı ($|E|$)** | **3.970** | İki farklı Türk üniversitesi arasındaki tekil iş birliği bağı |
| **Ağ Yoğunluğu (Density)** | **0.189861** | Olası tüm bağlantıların yaklaşık %19'u kurulmuştur |
| **Bağlı Bileşen Sayısı** | **4** | 1 Dev Bileşen + 3 İzole Düğüm |
| **Dev Bileşen Büyüklüğü** | **202 (%98.5)** | Ağdaki neredeyse tüm kurumlar tek bir dev ağda bağlantılıdır |
| **İzole Düğüm Sayısı** | **3** | Sadece tekil yayın yapmış, ortaklığı olmayan kurumlar |
| **Ege Bölgesi Kurum Sayısı** | **18** | Ege Bölgesi illerinde yer alan üniversiteler |
| **En Yüksek Kenar Ağırlığı** | **280** | İstanbul Üniversitesi ile İstanbul Üniversitesi-Cerrahpaşa arası |

---

## 4. Önemli 500 Düğüm Kuralı ve Kapsam Kısıtı Açıklaması

> ### Öğretim Görevlisinin Dikkatine:
> Genel ders yönergesinde asgari 500 düğüm koşulu yer almaktadır. Ancak tarafıma tanımlanan kişisel ödev kartında ağın düğümü kesin olarak **"Türkiye'deki Üniversiteler"** olarak belirlenmiştir.
>
> 1. **Evren Büyüklüğü Kısıtı:** YÖK resmi istatistiklerine ve OpenAlex veritabanındaki Türkiye adresli `education` tipi kurum filtrelemesine göre Türkiye'de toplam **222** eğitim kurumu (üniversite ve yüksek teknoloji enstitüsü) bulunmaktadır.
> 2. **Gözlemlenen Sayı:** 2020–2025 yılları arasında bilgisayar bilimi alanında yayın üreten tekil üniversite sayısı **205**'tir.
> 3. **Bilimsel Dürüstlük:** Ağın 500 düğüme ulaşması Türkiye'deki mevcut üniversite sayısının sınırlı olması nedeniyle matematiksel olarak imkansızdır. Kuralı sağlamak adına yapay/sahte düğüm eklenmemiş, kurum tanımı bozulmamış ve gerçek evrenin %92.3'ü (205/222) ağa yansıtılmıştır.
>
> Bu kapsam sınırlaması öğretim elemanımızın onayına sunulmuştur.

---

## 5. Araştırma Sorusu ve Ege Bölgesi Bulguları

> **Araştırma Sorusu:** *Türkiye'deki üniversiteler arasında bilgisayar bilimi alanındaki ortak yayın iş birliği coğrafi yakınlıkla mı, yoksa üniversitelerin bilimsel üretim büyüklüğüyle mi daha çok ilişkilidir? Ege Bölgesi üniversiteleri ağda nerede bulunur?*

### 5.1. En Yüksek Dereceli Üniversiteler (Ulusal Merkezler - Hubs)
Türkiye genelinde en çok farklı üniversiteyle iş birliği yapan (en yüksek dereceye sahip) ilk 5 kurum:
1. **Gazi Üniversitesi (Ankara):** Derece = 121, Ağırlıklı Derece = 582 (Toplam Eser: 61.742)
2. **İstanbul Üniversitesi (İstanbul):** Derece = 116, Ağırlıklı Derece = 754 (Toplam Eser: 89.232)
3. **Hacettepe Üniversitesi (Ankara):** Derece = 116, Ağırlıklı Derece = 588 (Toplam Eser: 83.559)
4. **Yıldız Teknik Üniversitesi (İstanbul):** Derece = 116, Ağırlıklı Derece = 553 (Toplam Eser: 31.362)
5. **İstanbul Teknik Üniversitesi (İstanbul):** Derece = 109, Ağırlıklı Derece = 569 (Toplam Eser: 53.448)

Bu bulgu, ağda yüksek üretim hacmine (works_count) sahip Ankara ve İstanbul metropol üniversitelerinin baskın birer "Hub" (merkez düğüm) olduğunu doğrulamaktadır.

### 5.2. Ege Bölgesi Üniversitelerinin Konumu
Ege Bölgesi'nde yer alan 18 üniversitenin tamamı ağın **dev bileşeni (giant component)** içerisindedir; bölgede hiçbir izole kurum bulunmamaktadır.

| Sıra | Üniversite Adı | İl | Derece ($k_i$) | Ağırlıklı Derece ($s_i$) | Toplam Eser |
| :---: | :--- | :---: | :---: | :---: | :---: |
| 1 | **Ege Üniversitesi** | İzmir | 75 | 280 | 53.427 |
| 2 | **Dokuz Eylül Üniversitesi** | İzmir | 72 | 187 | 42.239 |
| 3 | **Pamukkale Üniversitesi** | Denizli | 69 | 171 | 23.604 |
| 4 | **Manisa Celal Bayar Üniversitesi** | Manisa | **66** | **198** | **18.434** |
| 5 | **Afyon Kocatepe Üniversitesi** | Afyon | 52 | 122 | 14.582 |
| 6 | **İzmir Kâtip Çelebi Üniversitesi** | İzmir | 49 | 127 | 14.921 |
| 7 | **Kütahya Dumlupınar Üniversitesi**| Kütahya | 46 | 81 | 10.253 |
| 8 | **İzmir Yüksek Teknoloji Enstitüsü**| İzmir | 43 | 106 | 8.333 |
| 9 | **Aydın Adnan Menderes Üniversitesi**| Aydın | 43 | 82 | 17.810 |
| 10 | **Muğla Sıtkı Koçman Üniversitesi** | Muğla | 41 | 99 | 16.929 |
| 11 | **Yaşar Üniversitesi** | İzmir | 41 | 73 | 3.841 |
| 12 | **İzmir Ekonomi Üniversitesi** | İzmir | 37 | 88 | 5.384 |
| 13 | **Uşak Üniversitesi** | Uşak | 34 | 115 | 11.559 |
| 14 | **İzmir Kavram Meslek Yüksekokulu** | İzmir | 22 | 26 | 435 |
| 15 | **İzmir Tınaztepe Üniversitesi** | İzmir | 5 | 5 | 800 |
| 16 | **İzmir Üniversitesi** | İzmir | 3 | 3 | 1.536 |
| 17 | **Gediz Üniversitesi** | İzmir | 2 | 2 | 396 |
| 18 | **Şifa Üniversitesi** | İzmir | 2 | 2 | 800 |

> **Önemli Bulgular:**
> - **Manisa Celal Bayar Üniversitesi (MCBÜ):** Ege Bölgesi'nde en çok farklı üniversiteyle bağlantı kuran 4. üniversite (66 kurum), toplam ortak makale hacminde (ağırlıklı derece: 198) ise Dokuz Eylül ve Pamukkale'yi geride bırakarak Ege Bölgesi'nde **2. sıradadır**.
> - Ege Bölgesi kurumları kendi aralarında sıkı bir bölgesel alt ağ oluştururken, aynı zamanda Ankara ve İstanbul'daki büyük araştırma merkezlerine (ODTÜ, İTÜ, Gazi) güçlü kenarlarla bağlıdır.

---

## 6. İzole Düğümlerin Tespiti
Ağ tanımı kuralına göre izole düğümler silinmemiş, grafikte $degree=0$ olarak tutulmuştur:
1. `Canik Başarı University` (Samsun)
2. `British Institute at Ankara` (Ankara)
3. `İstanbul Şişli Meslek Yüksekokulu` (İstanbul)

Bu kurumlar 2020–2025 döneminde bilgisayar bilimi alanında bağımsız olarak yayın üretmiş, ancak başka hiçbir Türk kurumuyla ortaklık gerçekleştirmemiştir.

---

## 7. Üretilen Ara Kontrol Dosyaları

1. `scripts/fetch_openalex.py`: Tekrar çalıştırılabilir, polite pool uyumlu, dinamik alan doğrulamalı ve önbelleklemeli veri toplama scripti.
2. `scripts/build_network.py`: Authorships verilerini ayrıştıran, self-loop ve mükerrerlikleri engelleyen yönsüz ağırlıklı ağ kurucu.
3. `data/processed/edges.csv`: 3.970 ağırlıklı kenar (`source`, `target`, `weight`).
4. `data/processed/institutions.csv`: 205 düğüm (`id`, `display_name`, `country_code`, `type`, `latitude`, `longitude`, `city`, `works_count`, `is_egean`, `degree`, `weighted_degree`, `is_isolated`).
5. `data/processed/collaboration.graphml`: Gephi / NetworkX uyumlu GraphML ağı.
6. `tests/test_network.py`: Birim testler (Pytest ile %100 geçti).
7. `docs/data_dictionary.md`: Alan açıklamaları, veri kaynağı, lisans ve kapsam kısıtları.
8. `README.md`: Proje amacı, CV tek cümlelik özeti, yeniden üretilebilirlik adımları ve AI kullanım beyanı.
9. `requirements.txt` ve `.gitignore`: Bağımlılıklar ve sürüm kontrol istisnaları.

---

## 8. Bir Sonraki Aşama Yol Haritası (Final Teslimatı)
- **Topluluk Tespiti:** Louvain ve Leiden algoritmaları ile bölgesel kümelenme analizi.
- **Null Model Analizi:** 100 rastgele eşdeğer ağ (Configuration Model) üzerinden $z$-skoru testi.
- **Çekim Regresyonu (Gravity Model):** Coğrafi mesafe (Haversine km) ve üretim büyüklüğünün (works_count) istatistiksel etkisinin regresyonla modellenmesi.
- **Etkileşimli Görselleştirme:** Web tabanlı ağ görselleştirmesi.
