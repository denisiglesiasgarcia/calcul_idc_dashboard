# /sections/helpers/idc_geo.py

import logging
from typing import Dict, List, Tuple

import numpy as np
import pydeck as pdk
import streamlit as st
from pyproj import Transformer


logging.basicConfig(level=logging.DEBUG)


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


# NOTE: @st.cache_data intentionally omitted — renders a Streamlit widget
def show_map(data: List[Dict], centroid: Tuple[float, float]) -> None:
    """Render a PyDeck GeoJSON map centred on the selected buildings."""
    layer = pdk.Layer(
        "GeoJsonLayer",
        data,
        opacity=0.8,
        stroked=False,
        filled=True,
        extruded=False,
        get_fill_color=[255, 0, 0, 200],
        get_line_color=[0, 0, 0],
        pickable=True,
        auto_highlight=True,
    )
    view_state = pdk.ViewState(
        latitude=centroid[1],
        longitude=centroid[0],
        zoom=17,
        pitch=45,
    )
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/light-v9",
        tooltip={
            "html": "<b>EGID:</b> {egid}<br/><b>Adresse:</b> {adresse}<br/><b>SRE:</b> {sre} m²",
            "style": {"backgroundColor": "steelblue", "color": "white"},
        },
    )
    st.pydeck_chart(deck)
