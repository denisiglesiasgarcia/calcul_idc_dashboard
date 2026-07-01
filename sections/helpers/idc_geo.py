# /sections/helpers/idc_geo.py

import logging
from typing import Dict, List, Optional, Tuple

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


def show_map(
    data: Dict,
    centroid: Tuple[float, float],
    batiments_by_egid: Optional[Dict] = None,
) -> None:
    """Render a PyDeck GeoJSON map centred on the selected buildings.

    ``batiments_by_egid`` optionally maps EGID → CAD_BATIMENT_HORSOL record;
    when provided, its descriptive attributes are added to the hover tooltip.
    """
    batiments_by_egid = batiments_by_egid or {}

    # Couleur dynamique selon IDC : vert (bas) → rouge (élevé)
    # Si IDC absent, fallback sur rouge neutre
    def _idc_to_color(feature: Dict) -> List[int]:
        idc = feature.get("properties", {}).get("indice", None)
        if idc is None:
            return [200, 100, 100, 200]
        # Normalise entre 0 (≤150) et 1 (≥600)
        t = max(0.0, min(1.0, (idc - 150) / 450))
        r = int(50 + t * 205)  # 50 → 255
        g = int(200 - t * 180)  # 200 → 20
        return [r, g, 50, 200]

    # Construit le bloc HTML des caractéristiques bâtiment (CAD_BATIMENT_HORSOL)
    # pour l'infobulle, ou une chaîne vide si l'EGID n'a pas de fiche bâtiment.
    def _batiment_html(props: Dict) -> str:
        egid = props.get("egid")
        bat = batiments_by_egid.get(egid) or batiments_by_egid.get(str(egid))
        if not bat:
            return ""
        parts = []
        annee = bat.get("annee_construction")
        epoque = bat.get("epoque_construction")
        if annee:
            parts.append(f"<b>Construction :</b> {annee}")
        elif epoque:
            parts.append(f"<b>Construction :</b> {epoque}")
        if bat.get("annee_transformation"):
            parts.append(f"<b>Transformation :</b> {bat['annee_transformation']}")
        niv_hs = bat.get("niveaux_horsol")
        niv_ss = bat.get("niveaux_ssol")
        if niv_hs is not None or niv_ss is not None:
            parts.append(
                f"<b>Niveaux :</b> {niv_hs if niv_hs is not None else '?'} h-sol"
                f" / {niv_ss if niv_ss is not None else '?'} s-sol"
            )
        if bat.get("hauteur"):
            parts.append(f"<b>Hauteur :</b> {bat['hauteur']:.1f} m")
        if bat.get("surface"):
            parts.append(f"<b>Emprise :</b> {bat['surface']} m²")
        if bat.get("destination"):
            parts.append(f"<b>Destination :</b> {bat['destination']}")
        if not parts:
            return ""
        return "<hr style='margin:4px 0'/>" + "<br/>".join(parts)

    # Construit les labels agent 2 / agent 3 pour l'infobulle, ou une chaîne
    # vide si l'agent correspondant est absent.
    def _clean_agents(props: Dict) -> Dict:
        cleaned = {}
        for i in (2, 3):
            agent = props.get(f"agent_energetique_{i}")
            qte = props.get(f"quantite_agent_energetique_{i}")
            unite = props.get(f"unite_agent_energetique_{i}", "")
            cleaned[f"_agent_{i}_label"] = (
                f"<b>Agent {i} :</b> {agent} — {qte} {unite or ''}" if agent else ""
            )
        return cleaned

    # Injecte la couleur et les infos bâtiment dans chaque feature pour GeoJsonLayer
    colored_data = {
        "type": "FeatureCollection",
        "features": [
            {
                **f,
                "properties": {
                    **f["properties"],
                    "_color": _idc_to_color(f),
                    "_batiment_info": _batiment_html(f["properties"]),
                    **_clean_agents(f["properties"]),
                },
            }
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
        zoom = max(14, min(19, np.log2(0.2 / (span + 1e-9)) + 16)) - 2
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
                "{_batiment_info}"
            ),
            "style": {
                "backgroundColor": "#1e1e2e",
                "color": "white",
                "fontSize": "13px",
            },
        },
    )
    st.pydeck_chart(deck, width="stretch")
