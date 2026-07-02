"""
Fetch SIT_AUTOR_DOSSIER authorization dossiers and CAD_BATIMENT_HORSOL
building footprints from SITG ArcGIS REST APIs, then spatial-join them
to produce records keyed by EGID, ready for Supabase insertion.
"""

import logging
from datetime import datetime, timezone
from typing import Callable

import geopandas as gpd
from shapely.geometry import MultiPolygon, Point, Polygon
from sitg_api import fetch_all, stage_progress

logger = logging.getLogger(__name__)

URL_AUTOR_DOSSIER = (
    "https://vector.sitg.ge.ch/arcgis/rest/services/"
    "SIT_AUTOR_DOSSIER/FeatureServer/0/query"
)
URL_BATIMENT_HORSOL = (
    "https://vector.sitg.ge.ch/arcgis/rest/services/"
    "CAD_BATIMENT_HORSOL/FeatureServer/0/query"
)

_AUTOR_FIELDS = ",".join(
    [
        "ID_DOSSIER",
        "TYPE_DOSSIER",
        "TYPE_OPERATION",
        "NOM_DOSSIER",
        "NO_DOSSIER",
        "NO_COMPLEMENTAIRE",
        "STATUT",
        "DATE_DEPOT",
        "DESCRIPTION",
        "OPERATION",
        "LIEN_SAD",
        "DATE_MAJ_2",
    ]
)

_BATIMENT_FIELDS = "EGID,COMMUNE"

# Descriptive building attributes surfaced in the dashboard (no geometry needed —
# the map reuses the IDC layer polygons). NB: ANNEE_TRANSFORNATION is the SITG
# field name, misspelled at source; we expose it as `annee_transformation`.
_BATIMENT_DETAIL_FIELDS = ",".join(
    [
        "EGID",
        "COMMUNE",
        "NO_BATIMENT",
        "NOMBAT",
        "DESTINATION",
        "NOMENCLATURE",
        "NOMEN_CLASSE",
        "EPOQUE_CONSTRUCTION",
        "ANNEE_CONSTRUCTION",
        "ANNEE_TRANSFORNATION",
        "NIVEAUX_HORSOL",
        "NIVEAUX_SSOL",
        "HAUTEUR",
        "SURFACE",
    ]
)


def _ms_to_iso(ms: int | None) -> str | None:
    if ms is None:
        return None
    try:
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()
    except (OSError, OverflowError, ValueError):
        return None


def _parse_point(geo: dict | None) -> Point | None:
    if not geo:
        return None
    try:
        return Point(geo["x"], geo["y"])
    except (KeyError, TypeError):
        return None


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


def fetch_batiment_footprints(
    url_batiment: str = URL_BATIMENT_HORSOL,
    progress_cb: Callable[[float], None] | None = None,
    status_cb: Callable[[str], None] | None = None,
) -> list[dict]:
    """
    Fetch CAD_BATIMENT_HORSOL once, with full detail fields AND geometry.

    This is the single, shared source for building characteristics
    (fetch_batiments) and the two spatial joins (fetch_and_join_autorizations,
    fetch_reseau_thermique) — passing its result into those functions avoids
    downloading the ~240k-feature building layer three separate times per
    refresh.
    """
    if status_cb:
        status_cb("Chargement des bâtiments SITG (CAD_BATIMENT_HORSOL)...")

    return fetch_all(
        url_batiment,
        fields=_BATIMENT_DETAIL_FIELDS,
        with_geometry=True,
        max_workers=8,
        response_format="pbf",
        progress=False,
        progress_cb=progress_cb,
        status_cb=status_cb,
    )


def fetch_batiments(
    batiment_features: list[dict] | None = None,
    url_batiment: str = URL_BATIMENT_HORSOL,
    progress_cb: Callable[[float], None] | None = None,
    status_cb: Callable[[str], None] | None = None,
) -> list[dict]:
    """
    Derive CAD_BATIMENT_HORSOL building characteristics keyed by EGID.

    Geometry is ignored here: the dashboard reuses the IDC layer polygons for
    mapping, so this layer only contributes descriptive attributes (construction
    period, levels, height, footprint area, destination…). When several polygons
    share an EGID, the one with the largest SURFACE is kept.

    ``batiment_features`` may be a previously-fetched result of
    fetch_batiment_footprints() to avoid a second network fetch; if omitted,
    this fetches it directly (useful for standalone/test usage).

    Returns a list of dicts with keys matching the `batiments` DB table.
    """
    if batiment_features is None:
        batiment_features = fetch_batiment_footprints(
            url_batiment, progress_cb=progress_cb, status_cb=status_cb
        )
    elif progress_cb:
        progress_cb(1.0)

    if not batiment_features:
        logger.warning("Aucun bâtiment retourné par le SITG")
        return []

    by_egid: dict[int, dict] = {}
    for f in batiment_features:
        a = f["attributes"]
        egid = a.get("EGID")
        if egid is None:
            continue
        surface = a.get("SURFACE") or 0
        existing = by_egid.get(egid)
        # Keep the largest footprint when several polygons share an EGID.
        if existing is not None and (existing.get("surface") or 0) >= surface:
            continue
        by_egid[egid] = {
            "egid": egid,
            "commune": a.get("COMMUNE"),
            "no_batiment": a.get("NO_BATIMENT"),
            "nombat": a.get("NOMBAT"),
            "destination": a.get("DESTINATION"),
            "nomenclature": a.get("NOMENCLATURE"),
            "nomen_classe": a.get("NOMEN_CLASSE"),
            "epoque_construction": a.get("EPOQUE_CONSTRUCTION"),
            "annee_construction": a.get("ANNEE_CONSTRUCTION"),
            "annee_transformation": a.get("ANNEE_TRANSFORNATION"),
            "niveaux_horsol": a.get("NIVEAUX_HORSOL"),
            "niveaux_ssol": a.get("NIVEAUX_SSOL"),
            "hauteur": a.get("HAUTEUR"),
            "surface": a.get("SURFACE"),
        }

    records = list(by_egid.values())
    if status_cb:
        status_cb(f"{len(records):,} bâtiments chargés depuis le SITG.")
    return records


def fetch_and_join_autorizations(
    batiment_features: list[dict] | None = None,
    url_autor: str = URL_AUTOR_DOSSIER,
    url_batiment: str = URL_BATIMENT_HORSOL,
    progress_cb: Callable[[float], None] | None = None,
    status_cb: Callable[[str], None] | None = None,
) -> list[dict]:
    """
    Fetch all authorization dossiers from SITG and spatial-join them against
    building footprints by location to assign EGID per dossier.

    ``batiment_features`` may be a previously-fetched result of
    fetch_batiment_footprints() to avoid a second network fetch; if omitted,
    this fetches it directly (useful for standalone/test usage).

    Returns a list of dicts with keys matching the `autorizations` DB table.
    Authorization points are buffered by 1m before the join to handle
    edge cases where a point sits exactly on a polygon boundary.
    """
    fetch_span = 0.4 if batiment_features is None else 0.8

    # Stage 1: Authorization dossiers — points (0–40%, or 0–80% when the
    # building footprints are already provided)
    if status_cb:
        status_cb("Chargement des dossiers d'autorisation SITG...")
    autor_features = fetch_all(
        url_autor,
        fields=_AUTOR_FIELDS,
        with_geometry=True,
        max_workers=8,
        response_format="pbf",
        progress=False,
        progress_cb=stage_progress(progress_cb, 0.0, fetch_span),
        status_cb=status_cb,
    )

    if not autor_features:
        logger.warning("Aucun dossier d'autorisation retourné par le SITG")
        return []

    gdf_autor = gpd.GeoDataFrame(
        [f["attributes"] for f in autor_features],
        geometry=[_parse_point(f.get("geometry")) for f in autor_features],
        crs="EPSG:2056",
    ).dropna(subset=["geometry"])

    # Stage 2: Building polygons — reuse if provided, else fetch (40–80%)
    if batiment_features is None:
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
    elif progress_cb:
        progress_cb(0.8)

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
        status_cb("Jointure spatiale autorisation ↔ bâtiment...")

    gdf_buf = gdf_autor.copy()
    gdf_buf["geometry"] = gdf_autor.buffer(1)

    gdf_joined = gpd.sjoin(
        gdf_buf,
        gdf_batiment[["EGID", "COMMUNE", "geometry"]],
        how="inner",
        predicate="intersects",
    ).drop(columns=["geometry", "index_right"], errors="ignore")

    if progress_cb:
        progress_cb(0.9)

    # Stage 4: Normalize column names and convert timestamps
    records = []
    for row in gdf_joined.to_dict(orient="records"):
        records.append(
            {
                "egid": row.get("EGID"),
                "commune": row.get("COMMUNE"),
                "id_dossier": row.get("ID_DOSSIER"),
                "type_dossier": row.get("TYPE_DOSSIER"),
                "type_operation": row.get("TYPE_OPERATION"),
                "nom_dossier": row.get("NOM_DOSSIER"),
                "statut": row.get("STATUT"),
                "date_depot": _ms_to_iso(row.get("DATE_DEPOT")),
                "description": row.get("DESCRIPTION"),
                "operation": row.get("OPERATION"),
                "lien_sad": row.get("LIEN_SAD"),
                "date_maj": _ms_to_iso(row.get("DATE_MAJ_2")),
            }
        )

    if status_cb:
        status_cb(f"Jointure terminée — {len(records):,} dossiers liés à un bâtiment")

    return records
