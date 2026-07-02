"""
Fetch OCEN_RTS_2030_2040_2050 (zones de développement des réseaux thermiques
structurants — GeniLac, GeniTerre, etc.) and CAD_BATIMENT_HORSOL from SITG
ArcGIS REST APIs, then spatial-join them to flag which EGID sits in which
network zone.
"""

import logging
from typing import Callable

import geopandas as gpd
from shapely.geometry import MultiPolygon, Polygon
from sitg_api import fetch_all, stage_progress

from sections.helpers.autor_api import URL_BATIMENT_HORSOL

logger = logging.getLogger(__name__)

URL_RESEAU_THERMIQUE = (
    "https://vector.sitg.ge.ch/arcgis/rest/services/"
    "OCEN_RTS_2030_2040_2050/FeatureServer/0/query"
)

_RTS_FIELDS = "RTS_ID,FLUIDE,HORIZON"
_BATIMENT_FIELDS = "EGID,COMMUNE"


def _parse_polygon(geo: dict | None) -> Polygon | MultiPolygon | None:
    if not geo:
        return None
    try:
        rings = geo.get("rings", [])
        polys = [Polygon(ring) for ring in rings if len(ring) >= 3]
        if not polys:
            return None
        return MultiPolygon(polys) if len(polys) > 1 else polys[0]
    except (TypeError, ValueError):
        return None


def fetch_reseau_thermique(
    url_rts: str = URL_RESEAU_THERMIQUE,
    url_batiment: str = URL_BATIMENT_HORSOL,
    progress_cb: Callable[[float], None] | None = None,
    status_cb: Callable[[str], None] | None = None,
) -> list[dict]:
    """
    Fetch the structuring thermal network development zones (OCEN_RTS_2030_2040_2050)
    and building footprints from SITG, spatial-join them to assign each zone's
    EGID membership.

    A building can intersect several zones (e.g. a "Chaud" zone at horizon 2030
    and a "Chaud-Froid" zone at horizon 2050), so this returns one record per
    (egid, rts_id) match rather than a single row per building.

    Returns a list of dicts with keys matching the `reseau_thermique` DB table.
    """
    # Stage 1: Thermal network zone polygons (0–40%)
    if status_cb:
        status_cb("Chargement des zones réseaux thermiques SITG...")
    rts_features = fetch_all(
        url_rts,
        fields=_RTS_FIELDS,
        with_geometry=True,
        max_workers=8,
        response_format="pbf",
        progress=False,
        progress_cb=stage_progress(progress_cb, 0.0, 0.4),
        status_cb=status_cb,
    )

    if not rts_features:
        logger.warning("Aucune zone de réseau thermique retournée par le SITG")
        return []

    gdf_rts = gpd.GeoDataFrame(
        [f["attributes"] for f in rts_features],
        geometry=[_parse_polygon(f.get("geometry")) for f in rts_features],
        crs="EPSG:2056",
    ).dropna(subset=["geometry", "RTS_ID"])

    # Stage 2: Building polygons (40–80%)
    if status_cb:
        status_cb("Chargement des emprises bâtiments SITG...")
    batiment_features = fetch_all(
        url_batiment,
        fields=_BATIMENT_FIELDS,
        with_geometry=True,
        max_workers=8,
        response_format="pbf",
        progress=False,
        progress_cb=stage_progress(progress_cb, 0.4, 0.8),
        status_cb=status_cb,
    )

    if not batiment_features:
        logger.warning("Aucun bâtiment retourné par le SITG")
        return []

    gdf_batiment = gpd.GeoDataFrame(
        [f["attributes"] for f in batiment_features],
        geometry=[_parse_polygon(f.get("geometry")) for f in batiment_features],
        crs="EPSG:2056",
    ).dropna(subset=["geometry", "EGID"])

    # Stage 3: Spatial join (80–90%)
    if status_cb:
        status_cb("Jointure spatiale bâtiment ↔ zone réseau thermique...")

    gdf_joined = gpd.sjoin(
        gdf_batiment[["EGID", "geometry"]],
        gdf_rts[["RTS_ID", "FLUIDE", "HORIZON", "geometry"]],
        how="inner",
        predicate="intersects",
    ).drop(columns=["geometry", "index_right"], errors="ignore")

    if progress_cb:
        progress_cb(0.9)

    # Stage 4: Normalize column names, one record per (egid, rts_id) match
    records = [
        {
            "egid": row.get("EGID"),
            "rts_id": row.get("RTS_ID"),
            "fluide": row.get("FLUIDE"),
            "horizon": row.get("HORIZON"),
        }
        for row in gdf_joined.to_dict(orient="records")
    ]

    if status_cb:
        status_cb(
            f"Jointure terminée — {len(records):,} zones réseau thermique liées à un bâtiment"
        )

    return records
