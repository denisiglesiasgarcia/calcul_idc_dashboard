# /sections/helpers/db.py

import json
import logging
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

import polars as pl
import requests
import streamlit as st

from sections.helpers.autor_api import fetch_and_join_autorizations

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DB_PATH = Path(__file__).parent.parent.parent / "idc_local.db"
_write_lock = threading.Lock()


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


# ---------------------------------------------------------------------------
# Schema init — idempotent, called at app startup
# ---------------------------------------------------------------------------


def init_history_table() -> None:
    conn = _get_conn()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS consultation_history (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                ts     TEXT NOT NULL,
                labels TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_ts
            ON consultation_history (ts DESC)
        """)
        conn.commit()
    finally:
        conn.close()


def init_favorites_table() -> None:
    conn = _get_conn()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS adresses_favorites (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                name   TEXT NOT NULL,
                labels TEXT NOT NULL UNIQUE
            )
        """)
        conn.commit()
    finally:
        conn.close()


def init_adresses_table() -> None:
    conn = _get_conn()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS adresses_egid (
                egid    INTEGER,
                adresse TEXT,
                PRIMARY KEY (egid, adresse)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_adresses_adresse
            ON adresses_egid (adresse)
        """)
        conn.commit()
    finally:
        conn.close()


def init_autorizations_table() -> None:
    conn = _get_conn()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS autorizations (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                egid           INTEGER NOT NULL,
                commune        TEXT,
                id_dossier     TEXT,
                type_dossier   TEXT,
                type_operation TEXT,
                nom_dossier    TEXT,
                statut         TEXT,
                date_depot     TEXT,
                description    TEXT,
                operation      TEXT,
                lien_sad       TEXT,
                date_maj       TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_autorizations_egid ON autorizations (egid)
        """)
        conn.commit()
    finally:
        conn.close()


def init_metadata_table() -> None:
    conn = _get_conn()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS app_metadata (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Authorization dossiers cache
# ---------------------------------------------------------------------------


def refresh_autorizations_db(
    progress_bar=None,
    status_text=None,
) -> int:
    """
    Full ETL: fetch SIT_AUTOR_DOSSIER + CAD_BATIMENT_HORSOL from SITG,
    spatial-join to get EGID per dossier, then truncate/insert into local SQLite.
    Returns the number of records inserted.
    """

    def _status(msg: str) -> None:
        if status_text is not None:
            status_text.caption(msg)
        logger.info(msg)

    def _progress(value: float) -> None:
        if progress_bar is not None:
            progress_bar.progress(value)

    records = fetch_and_join_autorizations(
        progress_cb=lambda f: _progress(f * 0.9),
        status_cb=_status,
    )

    if not records:
        _status("Aucun dossier d'autorisation récupéré.")
        return 0

    _status(f"Écriture de {len(records):,} dossiers en base...")

    rows = [
        (
            r["egid"],
            r["commune"],
            r["id_dossier"],
            r["type_dossier"],
            r["type_operation"],
            r["nom_dossier"],
            r["statut"],
            r["date_depot"],
            r["description"],
            r["operation"],
            r["lien_sad"],
            r["date_maj"],
        )
        for r in records
    ]

    conn = _get_conn()
    try:
        with _write_lock:
            conn.execute("DELETE FROM autorizations")
            conn.commit()

            chunk = 1000
            total_chunks = (len(rows) + chunk - 1) // chunk
            for idx, i in enumerate(range(0, len(rows), chunk)):
                conn.executemany(
                    """
                    INSERT INTO autorizations
                        (egid, commune, id_dossier, type_dossier, type_operation,
                         nom_dossier, statut, date_depot, description, operation,
                         lien_sad, date_maj)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    rows[i : i + chunk],
                )
                conn.commit()
                _progress(0.9 + ((idx + 1) / total_chunks) * 0.1)
                _status(
                    f"Écriture en base : {min(i + chunk, len(rows)):,} / {len(rows):,} dossiers"
                )
    finally:
        conn.close()

    _progress(1.0)
    _status(f"Terminé — {len(rows):,} dossiers d'autorisation enregistrés.")
    return len(rows)


@st.cache_data(ttl=600)
def load_autorizations_by_egids(egids: tuple) -> list[dict]:
    """Load authorization records for a set of EGIDs, most recent first."""
    if not egids:
        return []
    conn = _get_conn()
    try:
        placeholders = ",".join(["?"] * len(egids))
        cur = conn.execute(
            f"""
            SELECT egid, commune, id_dossier, type_dossier, type_operation,
                   nom_dossier, statut, date_depot, description, operation,
                   lien_sad, date_maj
            FROM autorizations
            WHERE egid IN ({placeholders})
            ORDER BY date_depot DESC
            """,
            list(egids),
        )
        rows = cur.fetchall()
    finally:
        conn.close()
    cols = [
        "egid",
        "commune",
        "id_dossier",
        "type_dossier",
        "type_operation",
        "nom_dossier",
        "statut",
        "date_depot",
        "description",
        "operation",
        "lien_sad",
        "date_maj",
    ]
    return [dict(zip(cols, r)) for r in rows]


# ---------------------------------------------------------------------------
# Address cache
# ---------------------------------------------------------------------------


def refresh_adresses_db(
    url: str,
    chunk_size: int = 2000,
    max_workers: int = 3,
    progress_bar=None,
    status_text=None,
) -> int:
    """
    Fetch all address/EGID pairs from SITG and rebuild the local SQLite table.
    Strategy: parallel fetch with retry, then bulk insert in chunks of 1000.
    """

    def _status(msg: str) -> None:
        if status_text is not None:
            status_text.caption(msg)
        logger.info(msg)

    def _progress(value: float) -> None:
        if progress_bar is not None:
            progress_bar.progress(value)

    _status("Connexion au SITG — récupération du nombre total d'adresses...")
    _progress(0.0)

    resp = requests.get(
        url,
        params={
            "where": "1=1",
            "outFields": "adresse,egid",
            "returnDistinctValues": "true",
            "returnGeometry": "false",
            "returnCountOnly": "true",
            "f": "json",
        },
        timeout=30,
    )
    resp.raise_for_status()
    total_count = resp.json().get("count", 0)
    _status(f"{total_count:,} adresses trouvées — téléchargement...")

    offsets = list(range(0, total_count, chunk_size))
    completed_pages = 0
    lock = threading.Lock()
    all_records: list[tuple] = []

    def fetch_page(offset: int) -> list[tuple]:
        for attempt in range(4):
            try:
                r = requests.get(
                    url,
                    params={
                        "where": "1=1",
                        "outFields": "adresse,egid",
                        "returnDistinctValues": "true",
                        "returnGeometry": "false",
                        "f": "json",
                        "resultOffset": offset,
                        "resultRecordCount": chunk_size,
                    },
                    timeout=60,
                )
                r.raise_for_status()
                features = r.json().get("features", [])
                return [
                    (f["attributes"]["egid"], f["attributes"]["adresse"])
                    for f in features
                    if f["attributes"].get("egid") and f["attributes"].get("adresse")
                ]
            except requests.exceptions.RequestException:
                if attempt == 3:
                    raise
                wait = 2 ** (attempt + 1)
                logger.warning(
                    f"offset={offset} attempt {attempt + 1}/4 failed, retry in {wait}s"
                )
                time.sleep(wait)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_page, off): off for off in offsets}
        for future in as_completed(futures):
            offset = futures[future]
            try:
                records = future.result()
            except Exception as e:
                raise RuntimeError(f"Échec offset {offset}: {e}") from e
            with lock:
                all_records.extend(records)
                completed_pages += 1
                frac = completed_pages / len(offsets)
                _progress(frac * 0.9)
                _status(f"Téléchargé {len(all_records):,} / ~{total_count:,} adresses")

    _status("Dédoublonnage et écriture en base...")
    df = (
        pl.DataFrame(
            {
                "egid": [r[0] for r in all_records],
                "adresse": [r[1] for r in all_records],
            }
        )
        .unique()
        .sort("adresse")
    )
    unique_records = df.rows()

    conn = _get_conn()
    try:
        with _write_lock:
            conn.execute("DELETE FROM adresses_egid")
            conn.commit()

            chunk = 1000
            total_chunks = (len(unique_records) + chunk - 1) // chunk
            for idx, i in enumerate(range(0, len(unique_records), chunk)):
                conn.executemany(
                    "INSERT OR IGNORE INTO adresses_egid (egid, adresse) VALUES (?,?)",
                    unique_records[i : i + chunk],
                )
                conn.commit()
                write_frac = (idx + 1) / total_chunks
                _progress(0.9 + write_frac * 0.1)
                _status(
                    f"Écriture en base : {min(i + chunk, len(unique_records)):,} / {len(unique_records):,} adresses"
                )
    finally:
        conn.close()

    _progress(1.0)
    _status(f"Terminé — {len(unique_records):,} adresses uniques enregistrées.")
    return len(unique_records)


def refresh_db_at_startup_if_needed(
    addresses_url: str,
    refresh_interval: timedelta = timedelta(days=1),
) -> bool:
    """
    Refresh local caches at startup if they are empty or stale.
    Returns True if a refresh was executed, False otherwise.
    """
    init_metadata_table()

    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT value FROM app_metadata WHERE key = ?",
            ("last_full_refresh_utc",),
        ).fetchone()
        addr_empty = (
            conn.execute("SELECT 1 FROM adresses_egid LIMIT 1").fetchone() is None
        )
        autor_empty = (
            conn.execute("SELECT 1 FROM autorizations LIMIT 1").fetchone() is None
        )
    finally:
        conn.close()

    now = datetime.now(timezone.utc)
    last_refresh = None
    if row and row[0]:
        try:
            last_refresh = datetime.fromisoformat(row[0])
            if last_refresh.tzinfo is None:
                last_refresh = last_refresh.replace(tzinfo=timezone.utc)
        except ValueError:
            logger.warning("Invalid last_full_refresh_utc value in app_metadata.")

    is_stale = last_refresh is None or (now - last_refresh) >= refresh_interval
    needs_refresh = addr_empty or autor_empty or is_stale
    if not needs_refresh:
        return False

    try:
        refresh_adresses_db(addresses_url)
        get_all_addresses.clear()
        refresh_autorizations_db()
        load_autorizations_by_egids.clear()
    except Exception as exc:
        logger.warning("Automatic startup DB refresh failed: %s", exc)
        return False

    conn = _get_conn()
    try:
        with _write_lock:
            conn.execute(
                """
                INSERT INTO app_metadata (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                ("last_full_refresh_utc", now.isoformat()),
            )
            conn.commit()
    finally:
        conn.close()
    return True


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


def save_history_entry(selected_options: list[str]) -> None:
    labels_json = json.dumps(sorted(selected_options), ensure_ascii=False)
    conn = _get_conn()
    try:
        with _write_lock:
            cur = conn.execute(
                "SELECT id FROM consultation_history WHERE labels = ?", (labels_json,)
            )
            if cur.fetchone() is None:
                conn.execute(
                    "INSERT INTO consultation_history (ts, labels) VALUES (?,?)",
                    (datetime.utcnow().isoformat(), labels_json),
                )
                conn.commit()
    finally:
        conn.close()
    load_history.clear()


@st.cache_data(ttl=120)
def load_history(n: int = 20) -> list[dict]:
    conn = _get_conn()
    try:
        cur = conn.execute(
            "SELECT id, ts, labels FROM consultation_history ORDER BY ts DESC LIMIT ?",
            (n,),
        )
        rows = cur.fetchall()
    finally:
        conn.close()
    return [{"id": r[0], "ts": r[1], "labels": json.loads(r[2])} for r in rows]


def delete_history_entry(entry_id: int) -> None:
    conn = _get_conn()
    try:
        with _write_lock:
            conn.execute("DELETE FROM consultation_history WHERE id = ?", (entry_id,))
            conn.commit()
    finally:
        conn.close()
    load_history.clear()


# ---------------------------------------------------------------------------
# Favorites
# ---------------------------------------------------------------------------


def save_favorite(name: str, labels: list[str]) -> bool:
    labels_json = json.dumps(sorted(labels), ensure_ascii=False)
    conn = _get_conn()
    try:
        with _write_lock:
            conn.execute(
                "INSERT INTO adresses_favorites (name, labels) VALUES (?,?)",
                (name, labels_json),
            )
            conn.commit()
        load_favorites.clear()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


@st.cache_data(ttl=120)
def load_favorites() -> list[dict]:
    conn = _get_conn()
    try:
        cur = conn.execute(
            "SELECT id, name, labels FROM adresses_favorites ORDER BY name"
        )
        rows = cur.fetchall()
    finally:
        conn.close()
    return [{"id": r[0], "name": r[1], "labels": json.loads(r[2])} for r in rows]


def delete_favorite(fav_id: int) -> None:
    conn = _get_conn()
    try:
        with _write_lock:
            conn.execute("DELETE FROM adresses_favorites WHERE id = ?", (fav_id,))
            conn.commit()
    finally:
        conn.close()
    load_favorites.clear()


# ---------------------------------------------------------------------------
# Address selector
# ---------------------------------------------------------------------------


@st.cache_resource
def get_all_addresses() -> pl.DataFrame:
    """Load address/EGID pairs from local SQLite, sorted by address."""
    conn = _get_conn()
    try:
        cur = conn.execute(
            "SELECT DISTINCT adresse, egid FROM adresses_egid ORDER BY adresse"
        )
        rows = cur.fetchall()
    except Exception as e:
        logger.error(f"get_all_addresses failed: {e}")
        return pl.DataFrame(
            {
                "adresse": pl.Series([], dtype=pl.Utf8),
                "egid": pl.Series([], dtype=pl.Utf8),
            }
        )
    finally:
        conn.close()
    if not rows:
        return pl.DataFrame(
            {
                "adresse": pl.Series([], dtype=pl.Utf8),
                "egid": pl.Series([], dtype=pl.Utf8),
            }
        )
    return pl.DataFrame({"adresse": [r[0] for r in rows], "egid": [r[1] for r in rows]})
