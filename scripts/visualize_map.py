"""
scripts/visualize_map.py

Türkiye Coğrafi İş Birliği Haritası Görselleştirme Modülü:
- Folium kütüphanesi ile etkileşimli, açılabilir HTML haritası (turkey_collaboration_map.html).
- Şehir merkez koordinat çakışmalarını (İstanbul, Ankara, İzmir vb.) ayrıştırmak için
  sembolik açısal dağıtım (jitter / spiderfy offset) algoritması.
- Düğüm yarıçaplarının derece merkeziliği ile orantılandırılması.
- Ege Bölgesi kurumlarının renk vurgusu ile ayrıştırılması.
- Güçlü iş birliği kenarlarının (weight >= edge_weight_threshold) harita okunabilirliği için filtrelenmesi.
- Kapsamlı HTML lejantı, metrik açıklamaları ve metodolojik sınırlılık notları.
"""

import math
import logging
from typing import Dict, Any, List, Tuple, Optional
import networkx as nx
import pandas as pd
import folium

logger = logging.getLogger(__name__)


def generate_collaboration_map(
    G: nx.Graph,
    inst_metadata_df: pd.DataFrame,
    output_html_path: str = "reports/generated/turkey_collaboration_map.html",
    edge_weight_threshold: int = 5
) -> folium.Map:
    """
    Türkiye üniversiteleri iş birliği ağını interaktif bir Folium haritası olarak üretir.
    """
    # Türkiye coğrafi merkezi
    m = folium.Map(
        location=[39.0, 35.2],
        zoom_start=6,
        tiles="CartoDB positron",
        control_scale=True
    )

    meta_dict = {}
    for _, r in inst_metadata_df.iterrows():
        meta_dict[r["id"]] = r.to_dict()

    nodes = list(G.nodes())

    # 1. Koordinat Çakışması Analizi ve Sembolik Jitter
    coord_groups: Dict[Tuple[float, float], List[str]] = {}
    for n in nodes:
        meta = meta_dict.get(n, {})
        lat = meta.get("latitude")
        lon = meta.get("longitude")
        if lat is not None and lon is not None:
            # 3 ondalık hassasiyetle grupla
            key = (round(float(lat), 3), round(float(lon), 3))
            coord_groups.setdefault(key, []).append(n)

    # Her düğüm için harita koordinatını belirle
    node_map_coords: Dict[str, Tuple[float, float]] = {}
    for (lat, lon), group_nodes in coord_groups.items():
        k = len(group_nodes)
        if k == 1:
            node_map_coords[group_nodes[0]] = (lat, lon)
        else:
            # Açısal olarak merkez etrafına dağıt (yaklaşık 1.5 - 3.5 km yarıçapında)
            # Düğüm sayısına göre kademeli yarıçap
            for idx, nid in enumerate(group_nodes):
                angle = (2.0 * math.pi * idx) / k
                # İstanbul gibi yoğun yerlerde k>20 için yarıçap 0.025 derece
                radius_deg = 0.015 if k <= 10 else (0.025 if k <= 30 else 0.035)
                adj_lat = lat + radius_deg * math.sin(angle)
                adj_lon = lon + (radius_deg / math.cos(math.radians(lat))) * math.cos(angle)
                node_map_coords[nid] = (adj_lat, adj_lon)

    # 2. Kenarları Çiz (Eşik Filtrelemeli)
    plotted_edges_count = 0
    total_network_edges = G.number_of_edges()

    for u, v, d in G.edges(data=True):
        w = int(d.get("weight", 1))
        if w >= edge_weight_threshold:
            if u in node_map_coords and v in node_map_coords:
                coord_u = node_map_coords[u]
                coord_v = node_map_coords[v]

                # Ağırlığa göre çizgi kalınlığı ve opaklık
                line_weight = min(6.0, 1.2 + math.log(w) * 1.1)
                line_opacity = min(0.85, 0.35 + (w / 40.0))

                # Ege içi kenarlar için özel renk vurgusu
                is_ege_u = meta_dict.get(u, {}).get("is_egean", False)
                is_ege_v = meta_dict.get(v, {}).get("is_egean", False)
                if is_ege_u and is_ege_v:
                    edge_color = "#D84315"  # Turuncu/Kırmızı
                else:
                    edge_color = "#37474F"  # Koyu Gri

                popup_text = f"<b>İş Birliği:</b> {meta_dict.get(u, {}).get('display_name', u)} - {meta_dict.get(v, {}).get('display_name', v)}<br><b>Ortak Eser Sayısı:</b> {w}"

                folium.PolyLine(
                    locations=[coord_u, coord_v],
                    color=edge_color,
                    weight=line_weight,
                    opacity=line_opacity,
                    popup=folium.Popup(popup_text, max_width=300)
                ).add_to(m)
                plotted_edges_count += 1

    # 3. Düğümleri (Üniversiteleri) Çiz
    max_degree = max([d for _, d in G.degree()] or [1])

    for n in nodes:
        if n not in node_map_coords:
            continue
        coord = node_map_coords[n]
        meta = meta_dict.get(n, {})
        deg = G.degree(n)
        wdeg = G.degree(n, weight="weight")
        cs_works = meta.get("period_cs_works_count", 0)
        is_egean = meta.get("is_egean", False)
        disp_name = meta.get("display_name", n)
        city = meta.get("city", "")

        # Yarıçap (derece merkeziliği ile orantılı)
        radius = 4.0 + 11.0 * (deg / max_degree)

        if is_egean:
            fill_color = "#FF6F00"  # Canlı Ege Turuncusu
            stroke_color = "#B71C1C"
        else:
            fill_color = "#1E88E5"  # Türkiye Mavisi
            stroke_color = "#0D47A1"

        popup_html = f"""
        <div style="font-family: sans-serif; font-size: 12px; width: 240px;">
            <h4 style="margin: 0 0 6px 0; color: {'#B71C1C' if is_egean else '#0D47A1'};">{disp_name}</h4>
            <b>Şehir:</b> {city}<br>
            <b>Bölge:</b> {'Ege Bölgesi' if is_egean else 'Diğer'}<br>
            <b>2020–25 CS Eseri:</b> {cs_works}<br>
            <b>Derece (Ortak Üniversite):</b> {deg}<br>
            <b>Ağırlıklı Derece:</b> {wdeg}<br>
        </div>
        """

        folium.CircleMarker(
            location=coord,
            radius=radius,
            color=stroke_color,
            weight=1.5,
            fill=True,
            fill_color=fill_color,
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"{disp_name} (Derece={deg}, Ortak Yayın={wdeg})"
        ).add_to(m)

    # 4. Açıklayıcı HTML Bilgi Kutusu (Legend)
    legend_html = f"""
    <div style="
        position: fixed; 
        bottom: 25px; left: 25px; width: 330px; 
        background-color: white; 
        border: 2px solid #90A4AE; 
        border-radius: 8px;
        z-index: 9999; 
        font-family: Arial, sans-serif; 
        font-size: 11px; 
        padding: 12px; 
        box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
        line-height: 1.4;
    ">
        <h4 style="margin: 0 0 8px 0; font-size: 13px; color: #263238;">Türk Üniversiteleri Bilgisayar Bilimi Ağı</h4>
        <div><i style="background: #FF6F00; border: 1px solid #B71C1C; width: 12px; height: 12px; display: inline-block; border-radius: 50%; margin-right: 5px;"></i> <b>Ege Bölgesi Üniversiteleri</b></div>
        <div><i style="background: #1E88E5; border: 1px solid #0D47A1; width: 12px; height: 12px; display: inline-block; border-radius: 50%; margin-right: 5px;"></i> <b>Diğer Üniversiteler</b></div>
        <div><i style="background: #D84315; width: 18px; height: 3px; display: inline-block; margin-right: 5px; vertical-align: middle;"></i> Ege İçi Güçlü İş Birliği (w ≥ {edge_weight_threshold})</div>
        <div><i style="background: #37474F; width: 18px; height: 2px; display: inline-block; margin-right: 5px; vertical-align: middle;"></i> Ulusal Güçlü İş Birliği (w ≥ {edge_weight_threshold})</div>
        <hr style="margin: 6px 0; border: 0; border-top: 1px solid #CFD8DC;">
        <span style="color: #455A64;">
            <b>Düğüm Boyutu:</b> Derece merkeziliği ile orantılı.<br>
            <b>Harita Filtresi:</b> Toplam {total_network_edges} kenardan en güçlü {plotted_edges_count} kenar (w ≥ {edge_weight_threshold}) gösterilmektedir.<br>
            <b>Metodolojik Not:</b> OpenAlex koordinatları şehir düzeyinde olduğundan aynı şehirdeki kurumlar açısal ofset (jitter) ile ayrıştırılmıştır.
        </span>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    m.save(output_html_path)
    logger.info(f"Etkileşimli harita kaydedildi -> {output_html_path}")
    return m
