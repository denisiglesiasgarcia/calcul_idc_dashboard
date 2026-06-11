# /sections/helpers/db.py

import json
import logging
import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import polars as pl
import streamlit as st
from sitg_api import fetch_all

from sections.helpers.autor_api import fetch_and_join_autorizations

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DB_PATH = Path(__file__).parent.parent.parent / "idc_local.db"
_write_lock = threading.Lock()
# The startup refresh runs in a single background daemon thread, decoupled from
# the Streamlit script-run lifecycle. A Streamlit rerun (e.g. the cookie-manager's
# initial rerun) can interrupt the main script mid-refresh; running the work in a
# thread means it keeps going and finishes once. _refresh_lock guards the
# start/attach decision so concurrent runs share the SAME thread instead of each
# launching its own.
_refresh_lock = threading.Lock()
_refresh_thread: threading.Thread | None = None
_refresh_state: dict | None = None
# Minimum gap between refresh attempts when a cache table is empty but the last
# refresh is recent — bounds retries so a persistently-empty source can't trigger
# a full download on every Streamlit rerun.
_EMPTY_RETRY_COOLDOWN = timedelta(minutes=15)


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    # WAL + relaxed durability: safe with WAL and much faster for the bulk
    # truncate/reinsert refresh cycle. busy_timeout avoids "database is locked"
    # errors when several Streamlit sessions touch the WAL concurrently.
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA cache_size=-65536")  # ~64 MB page cache
    conn.execute("PRAGMA mmap_size=268435456")  # 256 MB memory-mapped I/O
    conn.execute("PRAGMA busy_timeout=5000")  # ms
    return conn


# ---------------------------------------------------------------------------
# Schema init — idempotent, called at app startup
# ---------------------------------------------------------------------------


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


def init_idc_table() -> None:
    conn = _get_conn()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS idc_data (
                id                              INTEGER PRIMARY KEY AUTOINCREMENT,
                egid                            INTEGER NOT NULL,
                annee                           INTEGER,
                indice                          INTEGER,
                sre                             INTEGER,
                adresse                         TEXT,
                npa                             INTEGER,
                commune                         TEXT,
                destination                     TEXT,
                agent_energetique_1             TEXT,
                quantite_agent_energetique_1    REAL,
                unite_agent_energetique_1       TEXT,
                agent_energetique_2             TEXT,
                quantite_agent_energetique_2    REAL,
                unite_agent_energetique_2       TEXT,
                agent_energetique_3             TEXT,
                quantite_agent_energetique_3    REAL,
                unite_agent_energetique_3       TEXT,
                date_debut_periode              INTEGER,
                date_fin_periode                INTEGER,
                date_saisie                     INTEGER,
                indice_moy2                     INTEGER,
                annees_concernees_moy_2         TEXT,
                indice_moy3                     INTEGER,
                annees_concernees_moy_3         TEXT,
                id_concessionnaire              INTEGER,
                nbre_preneur                    INTEGER,
                geometry_json                   TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_idc_data_egid ON idc_data (egid)
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
# IDC data cache
# ---------------------------------------------------------------------------

_IDC_COLS = [
    "egid",
    "annee",
    "indice",
    "sre",
    "adresse",
    "npa",
    "commune",
    "destination",
    "agent_energetique_1",
    "quantite_agent_energetique_1",
    "unite_agent_energetique_1",
    "agent_energetique_2",
    "quantite_agent_energetique_2",
    "unite_agent_energetique_2",
    "agent_energetique_3",
    "quantite_agent_energetique_3",
    "unite_agent_energetique_3",
    "date_debut_periode",
    "date_fin_periode",
    "date_saisie",
    "indice_moy2",
    "annees_concernees_moy_2",
    "indice_moy3",
    "annees_concernees_moy_3",
    "id_concessionnaire",
    "nbre_preneur",
]


def refresh_idc_db(
    url: str,
    progress_bar=None,
    status_text=None,
) -> int:
    """
    Fetch all IDC data from SITG SCANE_INDICE_MOYENNES_3_ANS (with geometry)
    and rebuild the local idc_data table.
    Returns the number of records inserted.
    """

    def _status(msg: str) -> None:
        if status_text is not None:
            status_text.caption(msg)
        logger.info(msg)

    def _progress(value: float) -> None:
        if progress_bar is not None:
            progress_bar.progress(value)

    _status("Connexion au SITG — récupération des données IDC...")
    _progress(0.0)

    features = fetch_all(
        url,
        # Request only the columns we store instead of "*": smaller payload,
        # faster JSON parse. Geometry is controlled separately via with_geometry.
        fields=",".join(_IDC_COLS),
        with_geometry=True,
        max_workers=8,
        response_format="pbf",
        progress=False,
        progress_cb=lambda f: _progress(f * 0.9),
        status_cb=_status,
    )

    if not features:
        _status("Aucune donnée IDC récupérée.")
        return 0

    _status(f"Dédoublonnage de {len(features):,} enregistrements IDC...")

    raw_attrs = [f["attributes"] for f in features]
    geometries = [f.get("geometry") for f in features]

    # Deduplicate: keep most recent date_saisie per (egid, annee), preserve original index.
    # infer_schema_length=None scans all rows when inferring dtypes — required because
    # nullable columns (e.g. agent_energetique_2/3) can be null for the first 100+ rows
    # and only later carry a string, which would otherwise raise a schema/append error.
    df = (
        pl.from_dicts(raw_attrs, infer_schema_length=None)
        .select(_IDC_COLS)
        .with_columns(pl.Series("_idx", range(len(raw_attrs))))
        .sort(["egid", "annee", "date_saisie"], descending=[False, False, True])
        .unique(subset=["egid", "annee"], keep="first")
    )

    rows = []
    for row in df.to_dicts():
        orig_idx = row.pop("_idx")
        geom = geometries[orig_idx]
        rows.append(
            (
                row["egid"],
                row["annee"],
                row["indice"],
                row["sre"],
                row["adresse"],
                row["npa"],
                row["commune"],
                row["destination"],
                row["agent_energetique_1"],
                row["quantite_agent_energetique_1"],
                row["unite_agent_energetique_1"],
                row["agent_energetique_2"],
                row["quantite_agent_energetique_2"],
                row["unite_agent_energetique_2"],
                row["agent_energetique_3"],
                row["quantite_agent_energetique_3"],
                row["unite_agent_energetique_3"],
                row["date_debut_periode"],
                row["date_fin_periode"],
                row["date_saisie"],
                row["indice_moy2"],
                row["annees_concernees_moy_2"],
                row["indice_moy3"],
                row["annees_concernees_moy_3"],
                row["id_concessionnaire"],
                row["nbre_preneur"],
                json.dumps(geom) if geom else None,
            )
        )

    _status(f"Écriture de {len(rows):,} enregistrements IDC en base...")

    conn = _get_conn()
    try:
        with _write_lock:
            conn.execute("DELETE FROM idc_data")
            conn.commit()

            chunk = 1000
            total_chunks = (len(rows) + chunk - 1) // chunk
            for idx, i in enumerate(range(0, len(rows), chunk)):
                conn.executemany(
                    """
                    INSERT INTO idc_data (
                        egid, annee, indice, sre, adresse, npa, commune, destination,
                        agent_energetique_1, quantite_agent_energetique_1, unite_agent_energetique_1,
                        agent_energetique_2, quantite_agent_energetique_2, unite_agent_energetique_2,
                        agent_energetique_3, quantite_agent_energetique_3, unite_agent_energetique_3,
                        date_debut_periode, date_fin_periode, date_saisie,
                        indice_moy2, annees_concernees_moy_2, indice_moy3, annees_concernees_moy_3,
                        id_concessionnaire, nbre_preneur, geometry_json
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    rows[i : i + chunk],
                )
                conn.commit()
                _progress(0.9 + ((idx + 1) / total_chunks) * 0.1)
                _status(
                    f"Écriture en base : {min(i + chunk, len(rows)):,} / {len(rows):,} enregistrements IDC"
                )
    finally:
        conn.close()

    _progress(1.0)
    _status(f"Terminé — {len(rows):,} enregistrements IDC enregistrés.")
    return len(rows)


@st.cache_data(ttl=3600)
def load_idc_by_egids(
    egids: tuple[int, ...],
) -> tuple[list[dict] | None, list[dict] | None]:
    """
    Load IDC data and geometry from local SQLite for the given EGIDs.
    Returns (geometry_records, data_records) matching the fetch_idc_data interface.
    """
    if not egids:
        return None, None

    conn = _get_conn()
    try:
        placeholders = ",".join(["?"] * len(egids))
        cur = conn.execute(
            f"SELECT {', '.join(_IDC_COLS)}, geometry_json "
            f"FROM idc_data WHERE egid IN ({placeholders}) ORDER BY egid, annee",
            list(egids),
        )
        rows = cur.fetchall()
        col_names = [d[0] for d in cur.description]
    finally:
        conn.close()

    if not rows:
        return None, None

    geometry_records = []
    data_attrs = []
    for r in rows:
        d = dict(zip(col_names, r))
        geom_json = d.pop("geometry_json", None)
        geom = json.loads(geom_json) if geom_json else None
        geometry_records.append({"attributes": dict(d), "geometry": geom})
        data_attrs.append(d)

    try:
        # infer_schema_length=None: same nullable-column inference guard as refresh_idc_db.
        df = pl.from_dicts(data_attrs, infer_schema_length=None).with_columns(
            [
                pl.col("date_debut_periode").cast(pl.Datetime("ms")),
                pl.col("date_fin_periode").cast(pl.Datetime("ms")),
                pl.col("date_saisie").cast(pl.Datetime("ms")),
                pl.col("npa").cast(pl.Int64),
                pl.col("quantite_agent_energetique_1").cast(pl.Float64),
                pl.col("quantite_agent_energetique_2").cast(pl.Float64),
                pl.col("quantite_agent_energetique_3").cast(pl.Float64),
            ]
        )
        return geometry_records, df.to_dicts()
    except Exception as exc:
        logger.error("load_idc_by_egids: failed to build DataFrame: %s", exc)
        return None, None


# ---------------------------------------------------------------------------
# Address cache
# ---------------------------------------------------------------------------


def refresh_adresses_db(
    url: str | None = None,
    progress_bar=None,
    status_text=None,
) -> int:
    """
    Rebuild the adresses_egid table from the local idc_data table.

    Addresses come from the same SITG layer (SCANE_INDICE_MOYENNES_3_ANS) as the
    IDC data, so they are derived locally from idc_data after refresh_idc_db has
    populated it — avoiding a second full download of the layer. ``url`` is kept
    for backwards compatibility but is no longer used.
    """

    def _status(msg: str) -> None:
        if status_text is not None:
            status_text.caption(msg)
        logger.info(msg)

    def _progress(value: float) -> None:
        if progress_bar is not None:
            progress_bar.progress(value)

    _status("Construction des adresses depuis les données IDC locales...")
    _progress(0.0)

    conn = _get_conn()
    try:
        unique_records = conn.execute(
            "SELECT DISTINCT egid, adresse FROM idc_data "
            "WHERE egid IS NOT NULL AND adresse IS NOT NULL AND adresse <> '' "
            "ORDER BY adresse"
        ).fetchall()

        with _write_lock:
            conn.execute("DELETE FROM adresses_egid")
            conn.executemany(
                "INSERT OR IGNORE INTO adresses_egid (egid, adresse) VALUES (?,?)",
                unique_records,
            )
            conn.commit()
    finally:
        conn.close()

    _progress(1.0)
    _status(f"Terminé — {len(unique_records):,} adresses uniques enregistrées.")
    return len(unique_records)


def _refresh_needed(refresh_interval: timedelta) -> bool:
    """True if any cache table is empty or the last full refresh is stale."""
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
        idc_empty = conn.execute("SELECT 1 FROM idc_data LIMIT 1").fetchone() is None
    finally:
        conn.close()

    last_refresh = None
    if row and row[0]:
        try:
            last_refresh = datetime.fromisoformat(row[0])
            if last_refresh.tzinfo is None:
                last_refresh = last_refresh.replace(tzinfo=timezone.utc)
        except ValueError:
            logger.warning("Invalid last_full_refresh_utc value in app_metadata.")

    # No refresh attempt on record yet → always run (first/cold start).
    if last_refresh is None:
        logger.info("Refresh needed: no last_full_refresh_utc recorded.")
        return True

    age = datetime.now(timezone.utc) - last_refresh

    # Stale → run the regular daily refresh.
    if age >= refresh_interval:
        logger.info("Refresh needed: last refresh is stale (age=%s).", age)
        return True

    # A table is empty despite a recent attempt (e.g. a source layer returned no
    # rows, or a stage failed). Retry — but at most once per cooldown, NOT on every
    # rerun, otherwise adding an address would re-trigger the full download.
    any_empty = addr_empty or autor_empty or idc_empty
    if any_empty and age >= _EMPTY_RETRY_COOLDOWN:
        logger.info(
            "Refresh needed: empty table past cooldown "
            "(addr_empty=%s autor_empty=%s idc_empty=%s age=%s).",
            addr_empty,
            autor_empty,
            idc_empty,
            age,
        )
        return True

    return False


def _split_progress(bar, offset: float, span: float):
    """Return a progress proxy mapping local [0,1] into global [offset, offset+span]."""
    if bar is None:
        return None

    class _Bar:
        def progress(self, v):
            bar.progress(min(offset + v * span, 1.0))

    return _Bar()


class _StateBar:
    """progress_bar-like proxy that records progress into a shared state dict."""

    def __init__(self, state: dict):
        self._state = state

    def progress(self, v: float) -> None:
        self._state["progress"] = max(0.0, min(v, 1.0))


class _StateStatus:
    """status_text-like proxy that records the latest message into a state dict."""

    def __init__(self, state: dict):
        self._state = state

    def caption(self, msg: str) -> None:
        self._state["message"] = msg


def _do_full_refresh(addresses_url: str, state: dict) -> None:
    """Run the three refreshes + timestamp write. Executes in a background thread.

    Must not call any st.* UI functions (no ScriptRunContext here): progress is
    reported through the shared ``state`` dict, which the main script mirrors
    into the real Streamlit widgets.
    """
    bar = _StateBar(state)
    status = _StateStatus(state)
    idc_bar = _split_progress(bar, 0.0, 1 / 3)
    autor_bar = _split_progress(bar, 1 / 3, 1 / 3)
    addr_bar = _split_progress(bar, 2 / 3, 1 / 3)

    # Each stage is isolated: a failure in one (e.g. autorizations) must NOT skip
    # the timestamp write, otherwise last_full_refresh_utc stays unset and the gate
    # re-triggers a full refresh on EVERY rerun (the empty-retry cooldown only
    # applies once a timestamp exists). A persistently-failing stage instead leaves
    # its table empty and is retried at the bounded cooldown cadence.
    errors: list[str] = []

    # IDC first — the addresses table is derived from idc_data.
    try:
        refresh_idc_db(addresses_url, progress_bar=idc_bar, status_text=status)
        load_idc_by_egids.clear()
    except Exception as exc:
        logger.warning("IDC refresh failed: %s", exc)
        errors.append(f"idc: {exc}")

    try:
        refresh_autorizations_db(progress_bar=autor_bar, status_text=status)
        load_autorizations_by_egids.clear()
    except Exception as exc:
        logger.warning("Autorizations refresh failed: %s", exc)
        errors.append(f"autor: {exc}")

    try:
        refresh_adresses_db(addresses_url, progress_bar=addr_bar, status_text=status)
        get_all_addresses.clear()
    except Exception as exc:
        logger.warning("Adresses refresh failed: %s", exc)
        errors.append(f"adresses: {exc}")

    # Always record the attempt time, even on partial failure.
    try:
        now = datetime.now(timezone.utc)
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
    except Exception as exc:
        logger.warning("Failed to record refresh timestamp: %s", exc)
        errors.append(f"timestamp: {exc}")

    state["error"] = "; ".join(errors) if errors else None
    state["progress"] = 1.0
    state["done"] = True


def refresh_db_at_startup_if_needed(
    addresses_url: str,
    refresh_interval: timedelta = timedelta(days=1),
    progress_bar=None,
    status_text=None,
) -> bool:
    """
    Refresh local caches at startup if they are empty or stale.
    Returns True if a refresh ran (successfully) this call, False otherwise.

    The heavy download runs in a single background daemon thread so that a
    Streamlit rerun (notably the cookie-manager's initial rerun) cannot interrupt
    it half-way and trigger a second full refresh. Concurrent/re-entrant script
    runs attach to the SAME thread and just mirror its progress; the timestamp is
    written by the thread on completion, so the next run sees the cache as fresh.
    """
    global _refresh_thread, _refresh_state

    init_metadata_table()

    # Fast path, no lock: already fresh → nothing to do.
    if not _refresh_needed(refresh_interval):
        return False

    with _refresh_lock:
        if _refresh_thread is not None and _refresh_thread.is_alive():
            # A refresh is already running (started by an earlier/concurrent run).
            thread, state = _refresh_thread, _refresh_state
        elif _refresh_needed(refresh_interval):
            _refresh_state = {
                "progress": 0.0,
                "message": "",
                "done": False,
                "error": None,
            }
            _refresh_thread = threading.Thread(
                target=_do_full_refresh,
                args=(addresses_url, _refresh_state),
                daemon=True,
            )
            _refresh_thread.start()
            thread, state = _refresh_thread, _refresh_state
        else:
            # Another thread finished refreshing while we waited for the lock.
            return False

    # Mirror the background thread's progress into this run's widgets until done.
    while thread.is_alive():
        if progress_bar is not None:
            progress_bar.progress(state["progress"])
        if status_text is not None:
            status_text.caption(state["message"])
        time.sleep(0.2)
    thread.join()

    if progress_bar is not None:
        progress_bar.progress(1.0)
    return state.get("error") is None


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


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
