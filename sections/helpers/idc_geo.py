# /sections/helpers/idc_geo.py

import logging
from typing import Dict, List, Tuple

import numpy as np
import pydeck as pdk
import streamlit as st
from pyproj import Transformer


logging.basicConfig(level=logging.WARNING)


# ---------------------------------------------------------------------------
@st.cache_data
def convert_geometry_for_streamlit(data: List[Dict]) -> Tuple:
    """
    Convert polygon rings from LV95 (EPSG:2056) to WGS84 (EPSG:4326).
    Returns a GeoJSON FeatureCollection and the centroid [lon, lat].
    """
    transformer = Transformer.from_crs("EPSG:2056", "EPSG:4326", always_xy=True)
    features = []
    all_points = []

    for item in data:
        if "geometry" not in item or "rings" not in item["geometry"]:
            continue

        new_rings = []
        for ring in item["geometry"]["rings"]:
            new_ring = []
            for x, y in ring:
                lon, lat = transformer.transform(x, y)
                new_ring.append([lon, lat])
                all_points.append([lon, lat])
            new_rings.append(new_ring)

        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": new_rings},
                "properties": item["attributes"],
            }
        )

    geojson = {"type": "FeatureCollection", "features": features}
    centroid = np.mean(all_points, axis=0)
    return geojson, centroid


def show_map(data: List[Dict], centroid: Tuple[float, float]) -> None:
    """Render a PyDeck GeoJSON map centred on the selected buildings."""

    # Couleur dynamique selon IDC : vert (bas) → rouge (élevé)
    # Si IDC absent, fallback sur rouge neutre
    def _idc_to_color(feature: Dict) -> List[int]:
        idc = feature.get("properties", {}).get("indice_calcule", None)
        if idc is None:
            return [200, 100, 100, 200]
        # Normalise entre 0 (≤150) et 1 (≥600)
        t = max(0.0, min(1.0, (idc - 150) / 450))
        r = int(50 + t * 205)  # 50 → 255
        g = int(200 - t * 180)  # 200 → 20
        return [r, g, 50, 200]

    # Injecte la couleur dans chaque feature pour GeoJsonLayer
    colored_data = {
        "type": "FeatureCollection",
        "features": [
            {**f, "properties": {**f["properties"], "_color": _idc_to_color(f)}}
            for f in data["features"]
        ],
    }

    # Zoom adaptatif depuis l'étendue lon/lat des polygones
    all_coords = [
        pt
        for f in data["features"]
        for ring in f["geometry"]["coordinates"]
        for pt in ring
    ]
    if all_coords:
        lons = [c[0] for c in all_coords]
        lats = [c[1] for c in all_coords]
        span = max(max(lons) - min(lons), max(lats) - min(lats))
        # Formule standard : 360° correspond au zoom 0, chaque doublement = +1 zoom
        zoom = max(14, min(19, np.log2(0.2 / (span + 1e-9)) + 16))
    else:
        zoom = 18

    layer = pdk.Layer(
        "GeoJsonLayer",
        colored_data,
        opacity=0.85,
        stroked=True,
        filled=True,
        extruded=False,
        get_fill_color="properties._color",
        get_line_color=[60, 60, 60],
        line_width_min_pixels=1,
        pickable=True,
        auto_highlight=True,
    )

    view_state = pdk.ViewState(
        latitude=centroid[1],
        longitude=centroid[0],
        zoom=zoom,
        pitch=0,  # vue plane — extrusion désactivée
    )

    def _clean_agents(props: Dict) -> Dict:
        cleaned = dict(props)
        for i in (2, 3):
            agent = cleaned.get(f"agent_energetique_{i}")
            qte = cleaned.get(f"quantite_agent_energetique_{i}")
            unite = cleaned.get(f"unite_agent_energetique_{i}", "")
            # Construit un label complet ou chaîne vide
            cleaned[f"_agent_{i}_label"] = (
                f"<b>Agent {i} :</b> {agent} — {qte} {unite or ''}"
                if agent else ""
            )
        return cleaned

    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style="road",  # style intégré PyDeck, pas de token requis
        tooltip={
            "html": (
                "<b>EGID :</b> {egid}<br/>"
                "<b>Adresse :</b> {adresse}<br/>"
                "<b>SRE :</b> {sre} m²<br/>"
                "<b>IDC :</b> {indice} MJ/m² ({annee})<br/>"
                "<b>Agent 1 :</b> {agent_energetique_1} — {quantite_agent_energetique_1} {unite_agent_energetique_1}<br/>"
                "{_agent_2_label}<br/>"
                "{_agent_3_label}"
            ),
            "style": {"backgroundColor": "#1e1e2e", "color": "white", "fontSize": "13px"},
        },
    )
    st.pydeck_chart(deck, use_container_width=True)
