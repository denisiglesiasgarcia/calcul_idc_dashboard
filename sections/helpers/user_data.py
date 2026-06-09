# sections/helpers/user_data.py
"""
History and favourites backed by browser cookies via extra-streamlit-components.

Data is stored as JSON strings in two cookies:
  "idc_history"   → list of {ts: str, labels: list[str]}  (newest first)
  "idc_favorites" → list of {name: str, labels: list[str]} (sorted by name)

Each record is returned with a positional "id" (int) that callers use to
identify entries for deletion; it is stable within a single page render.

Call init_cookie_manager() ONCE at the top of main.py on every render
before any read/write operation.
"""

import json
from datetime import datetime, timedelta, timezone

import streamlit as st
from extra_streamlit_components import CookieManager

_COOKIE_HISTORY = "idc_history"
_COOKIE_FAVORITES = "idc_favorites"
_MAX_HISTORY = 20
_EXPIRY = datetime.now() + timedelta(days=3650)  # ~10 years


def init_cookie_manager() -> None:
    """Render the CookieManager component and cache it for this render cycle.

    Must be called once per page render, before any read/write call.
    """
    st.session_state["_idc_cm"] = CookieManager(key="idc_user_data")


def _cm() -> CookieManager:
    if "_idc_cm" not in st.session_state:
        init_cookie_manager()
    return st.session_state["_idc_cm"]


def _next_write_key() -> str:
    """Return a unique Streamlit widget key for each CookieManager.set() call."""
    n = st.session_state.get("_idc_wk", 0) + 1
    st.session_state["_idc_wk"] = n
    return f"idc_write_{n}"


def _load(cookie_name: str) -> list:
    raw = _cm().get(cookie_name)
    if not raw:
        return []
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
        return parsed if isinstance(parsed, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def _save(cookie_name: str, data: list) -> None:
    _cm().set(
        cookie_name,
        json.dumps(data, ensure_ascii=False),
        key=_next_write_key(),
        expires_at=_EXPIRY,
    )


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


def load_history(n: int = 20) -> list[dict]:
    """Return the n most recent history entries, each with a positional id."""
    entries = _load(_COOKIE_HISTORY)
    return [{"id": i, **e} for i, e in enumerate(entries[:n])]


def save_history_entry(selected_options: list[str]) -> None:
    """Append a new history entry; skips exact duplicates; caps list at _MAX_HISTORY."""
    labels = sorted(selected_options)
    entries = _load(_COOKIE_HISTORY)
    if any(e.get("labels") == labels for e in entries):
        return
    ts = datetime.now(timezone.utc).isoformat()
    entries.insert(0, {"ts": ts, "labels": labels})
    _save(_COOKIE_HISTORY, entries[:_MAX_HISTORY])


def delete_history_entry(entry_id: int) -> None:
    """Remove the entry at positional index entry_id."""
    entries = _load(_COOKIE_HISTORY)
    if 0 <= entry_id < len(entries):
        entries.pop(entry_id)
    _save(_COOKIE_HISTORY, entries)


# ---------------------------------------------------------------------------
# Favourites
# ---------------------------------------------------------------------------


def load_favorites() -> list[dict]:
    """Return all favourites sorted by name, each with a positional id."""
    favs = _load(_COOKIE_FAVORITES)
    return [
        {"id": i, "name": f["name"], "labels": f["labels"]} for i, f in enumerate(favs)
    ]


def save_favorite(name: str, labels: list[str]) -> bool:
    """
    Save a favourite. Returns False (without saving) if the name already exists
    or an identical label set is already saved.
    """
    favs = _load(_COOKIE_FAVORITES)
    labels_sorted = sorted(labels)
    if any(f["name"] == name or f.get("labels") == labels_sorted for f in favs):
        return False
    favs.append({"name": name, "labels": labels_sorted})
    favs.sort(key=lambda f: f["name"])
    _save(_COOKIE_FAVORITES, favs)
    return True


def delete_favorite(fav_id: int) -> None:
    """Remove the favourite at positional index fav_id."""
    favs = _load(_COOKIE_FAVORITES)
    if 0 <= fav_id < len(favs):
        favs.pop(fav_id)
    _save(_COOKIE_FAVORITES, favs)
