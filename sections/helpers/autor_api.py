"""
Fetch SIT_AUTOR_DOSSIER authorization dossiers and CAD_BATIMENT_HORSOL
building footprints from SITG ArcGIS REST APIs, then spatial-join them
to produce records keyed by EGID, ready for Supabase insertion.
"""

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Callable

import geopandas as gpd
import requests
from shapely.geometry import MultiPolygon, Point, Polygon

logger = logging.getLogger(__name__)

URL_AUTOR_DOSSIER = (
    "https://vector.sitg.ge.ch/arcgis/rest/services/"
    "SIT_AUTOR_DOSSIER/FeatureServer/0/query"
)
URL_BATIMENT_HORSOL = (
    "https://vector.sitg.ge.ch/arcgis/rest/services/"
    "CAD_BATIMENT_HORSOL/FeatureServer/0/query"
)

_AUTOR_FIELDS = ",".join([
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
])

_BATIMENT_FIELDS = "EGID,COMMUNE"


def _ms_to_iso(ms: int | None) -> str | None:
    if ms is None:
        return None
    try:
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()
    except (OSError, OverflowError, ValueError):
        return None


def _get_count(url: str) -> int:
    resp = requests.get(
        url,
        params={"where": "1=1", "returnCountOnly": "true", "f": "json"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("count", 0)


def _fetch_page(
    url: str,
    offset: int,
    chunk_size: int,
    fields: str,
    with_geometry: bool,
) -> list[dict]:
    for attempt in range(4):
        try:
            r = requests.get(
                url,
                params={
                    "where": "1=1",
                    "outFields": fields,
                    "returnGeometry": "true" if with_geometry else "false",
                    "f": "json",
                    "resultOffset": offset,
                    "resultRecordCount": chunk_size,
                },
                timeout=120,
            )
            r.raise_for_status()
            return r.json().get("features", [])
        except requests.exceptions.RequestException:
            if attempt == 3:
                raise
            wait = 2 ** (attempt + 1)
            logger.warning(f"offset={offset} attempt {attempt + 1}/4, retry in {wait}s")
            time.sleep(wait)
    return []


def _fetch_all_features(
    url: str,
    fields: str,
    with_geometry: bool,
    chunk_size: int = 1000,
    max_workers: int = 3,
    progress_start: float = 0.0,
    progress_end: float = 1.0,
    progress_cb: Callable[[float], None] | None = None,
    status_cb: Callable[[str], None] | None = None,
) -> list[dict]:
    """Paginated parallel fetch from an ArcGIS FeatureServer."""
    total = _get_count(url)
    if status_cb:
        status_cb(f"{total:,} enregistrements trouvés — téléchargement...")

    offsets = list(range(0, max(total, 1), chunk_size))
    completed = 0
    lock = threading.Lock()
    all_features: list[dict] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_fetch_page, url, off, chunk_size, fields, with_geometry): off
            for off in offsets
        }
        for future in as_completed(futures):
            off = futures[future]
            try:
                features = future.result()
            except Exception as e:
                raise RuntimeError(f"Échec offset {off}: {e}") from e
            with lock:
                all_features.extend(features)
                completed += 1
                if progress_cb:
                    frac = progress_start + (completed / len(offsets)) * (
                        progress_end - progress_start
                    )
                    progress_cb(min(frac, progress_end))
                if status_cb:
                    status_cb(f"Téléchargé {len(all_features):,} / ~{total:,}")

    return all_features


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


def fetch_and_join_autorizations(
    url_autor: str = URL_AUTOR_DOSSIER,
    url_batiment: str = URL_BATIMENT_HORSOL,
    chunk_size_autor: int = 1000,
    chunk_size_batiment: int = 500,
    max_workers: int = 3,
    progress_cb: Callable[[float], None] | None = None,
    status_cb: Callable[[str], None] | None = None,
) -> list[dict]:
    """
    Fetch all authorization dossiers and building footprints from SITG,
    spatial-join them by location to assign EGID per dossier.

    Returns a list of dicts with keys matching the `autorizations` DB table.
    Authorization points are buffered by 1m before the join to handle
    edge cases where a point sits exactly on a polygon boundary.
    """
    # Stage 1: Authorization dossiers — points (0–40%)
    if status_cb:
        status_cb("Chargement des dossiers d'autorisation SITG...")
    autor_features = _fetch_all_features(
        url_autor,
        _AUTOR_FIELDS,
        with_geometry=True,
        chunk_size=chunk_size_autor,
        max_workers=max_workers,
        progress_start=0.0,
        progress_end=0.4,
        progress_cb=progress_cb,
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

    # Stage 2: Building polygons (40–80%)
    if status_cb:
        status_cb("Chargement des emprises bâtiments SITG...")
    batiment_features = _fetch_all_features(
        url_batiment,
        _BATIMENT_FIELDS,
        with_geometry=True,
        chunk_size=chunk_size_batiment,
        max_workers=max_workers,
        progress_start=0.4,
        progress_end=0.8,
        progress_cb=progress_cb,
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
        records.append({
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
        })

    if status_cb:
        status_cb(
            f"Jointure terminée — {len(records):,} dossiers liés à un bâtiment"
        )

    return records
