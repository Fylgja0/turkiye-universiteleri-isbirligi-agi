# Veri Kaynakları ve Kullanım Koşulları (Data Sources & Terms of Use)

Bu belge, **"Türk Üniversiteleri Arası Bilimsel İş Birliği Sosyal Ağ Analizi"** (`turkiye-universiteleri-isbirligi-agi`) projesinde kullanılan veri kaynaklarını, bu kaynakların yasal lisans statülerini, harici yazılım bileşenlerini ve kullanım koşullarını açıklamaktadır.

---

## 1. Lisans Kapsamı ve Fikri Mülkiyet Sınırları

- **Özgün Kaynak Kod ve Dokümantasyon:** Bu depoda yer alan analiz kodları, veri işleme boru hatları, test senaryoları ve Ahmetcan Bağlı tarafından hazırlanan dokümantasyon metinleri [MIT Lisansı](LICENSE) ile korunmaktadır.
- **Veri ve Harici Kaynaklar:** MIT Lisansı, projede kullanılan harici veri setlerini, kamuya açık mevzuat kayıtlarını veya üçüncü taraf kütüphaneleri **kapsamaz**. Her veri kaynağı ve kütüphane, kendi sağlayıcısının belirlediği lisans ve kullanım koşullarına tabidir. Projede belgelenmemiş veya doğrulanmamış hiçbir telif hakkı ya da kullanım izni varsayılmamıştır.

---

## 2. Birincil Veri Kaynağı: OpenAlex

Projede kullanılan bilimsel yayınlar, yazar bilgileri ve kurumsal üstveriler **OpenAlex** veri tabanından REST API aracılığıyla temin edilmiştir.

- **Veri Sağlayıcı:** OurResearch (OpenAlex)
- **Web Sitesi:** [https://openalex.org/](https://openalex.org/)
- **API Endpoint:** [https://api.openalex.org/](https://api.openalex.org/)
- **Lisans:** **Creative Commons CC0 1.0 Universal (CC0 1.0) Kamu Malı Feragatnamesi**
- **Resmî Lisans Bildirimi:** [https://docs.openalex.org/about-the-data/licensing-and-privacy](https://docs.openalex.org/about-the-data/licensing-and-privacy)
- **CC0 1.0 Lisans Metni:** [https://creativecommons.org/publicdomain/zero/1.0/](https://creativecommons.org/publicdomain/zero/1.0/)
- **Akademik Kaynak Gösterimi:**
  > Priem, J., Piwowar, H., & Orr, R. (2022). *OpenAlex: A fully-open index of scholarly works, authors, venues, institutions, and concepts*. arXiv. [https://arxiv.org/abs/2205.01833](https://arxiv.org/abs/2205.01833)

### Veri Kullanım Şartları ve Kapsamı
OpenAlex verileri CC0 1.0 lisansı gereğince kamu malı (Public Domain) olup telif kısıtlaması bulunmaksızın ticari, bilimsel veya kişisel amaçlarla serbestçe kullanılabilir, paylaşılabilir ve işlenebilir. Projede şu filtreler kullanılmıştır:
- Disiplin: Computer Science (`primary_topic.field.id:fields/17`)
- Dönem: 2020–2025 (`from_publication_date:2020-01-01,to_publication_date:2025-12-31`)
- Ülke ve Kurum Türü: Türkiye adresli eğitim kurumları (`institutions.country_code:TR`, `type:education`)

---

## 3. Kurumsal Doğrulama Kaynağı: YÖK (Yükseköğretim Kurulu)

Türkiye'deki üniversitelerin güncel sayısı, statüleri (devlet / vakıf) ve bağımsız meslek yüksekokulları verisi, T.C. Yükseköğretim Kurulu (YÖK) resmi web portalından doğrulanmıştır.

- **Kaynak Kuruluş:** T.C. Yükseköğretim Kurulu
- **Web Adresi:** [https://www.yok.gov.tr/universiteler/universitelerimiz](https://www.yok.gov.tr/universiteler/universitelerimiz)
- **Erişim Tarihi:** 26 Ekim 2026
- **Kullanım Amacı:** Türkiye'deki 129 devlet üniversitesi, 75 vakıf üniversitesi (toplam 204 üniversite) ve 4 bağımsız vakıf meslek yüksekokulunun kurumsal mevcudiyetinin doğrulanması.
- **Yasal Statü:** Kamuya açık resmi bilgilendirme verisidir.

---

## 4. Hukuki Mevzuat ve Resmî Gazete Kayıtları

Tarihsel süreçte kapatılan veya statüsü değişen kurumların nesnel sınıflandırması için aşağıdaki kamuya açık resmi mevzuat kayıtları referans alınmıştır:

- **2016 Tarihli 667 Sayılı KHK:** 23 Temmuz 2016 tarihli ve 29779 sayılı Resmî Gazete'de yayımlanan Olağanüstü Hal Kapsamında Alınan Tedbirlere İlişkin Kanun Hükmünde Kararname (Kapatılan 7 tarihsel vakıf üniversitesi için).
- **2020 Tarihli 2708 Sayılı Cumhurbaşkanı Kararı:** 29 Haziran 2020 tarihli karar; 30 Haziran 2020 tarihli ve 31171 sayılı Resmî Gazete'de yayımlanmıştır (İstanbul Şehir Üniversitesi'nin faaliyet izninin kaldırılması).
- **Yasal Statü:** T.C. Resmî Gazete'de yayımlanan kamuya açık resmi mevzuat metinleridir.

---

## 5. Üçüncü Taraf Yazılım Bağımlılıkları ve Kütüphaneler

Projenin yürütülmesi için `requirements.txt` kapsamında kullanılan harici Python kütüphaneleri ve lisansları şunlardır:

| Kütüphane | Kullanım Amacı | Lisans | Resmî Web / Depo |
| :--- | :--- | :--- | :--- |
| **networkx** | Ağ modelleme ve topoloji analizleri | BSD 3-Clause | [https://networkx.org/](https://networkx.org/) |
| **pandas** | Tablosal veri analizi ve CSV yönetimi | BSD 3-Clause | [https://pandas.pydata.org/](https://pandas.pydata.org/) |
| **numpy** | Sayısal hesaplamalar ve matris işlemleri | BSD 3-Clause | [https://numpy.org/](https://numpy.org/) |
| **scipy** | Bilimsel ve istatistiksel hesaplamalar | BSD 3-Clause | [https://scipy.org/](https://scipy.org/) |
| **statsmodels** | GLM çekim modeli regresyon analizleri | BSD 3-Clause | [https://www.statsmodels.org/](https://www.statsmodels.org/) |
| **powerlaw** | Derece dağılımı güç yasası fiti | Apache 2.0 | [https://github.com/jeffalstott/powerlaw](https://github.com/jeffalstott/powerlaw) |
| **python-igraph**| Ağ topluluk algoritmaları altyapısı | GNU GPL v2+ | [https://igraph.org/python/](https://igraph.org/python/) |
| **leidenalg** | Leiden topluluk tespiti algoritması | GNU GPL v3 | [https://github.com/vtraag/leidenalg](https://github.com/vtraag/leidenalg) |
| **folium** | Coğrafi iş birliği haritası görselleştirmesi | MIT | [https://python-visualization.github.io/folium/](https://python-visualization.github.io/folium/) |
| **requests** | HTTP tabanlı OpenAlex API istemcisi | Apache 2.0 | [https://requests.readthedocs.io/](https://requests.readthedocs.io/) |
| **pytest** | Birim ve entegrasyon test takımı | MIT | [https://docs.pytest.org/](https://docs.pytest.org/) |

Bu kütüphanelerin telif hakları ilgili proje geliştiricilerine aittir.

---

## 6. Sorumluluk Reddi (Disclaimer)

Veriler ilgili sağlayıcılardan temin edildiği tarihteki (Ekim 2026) haliyle işlenmiştir. Sağlayıcıların veri tabanlarındaki olası güncellemeler, isim değişiklikleri veya üstveri revizyonları sağlayıcının sorumluluğundadır.
