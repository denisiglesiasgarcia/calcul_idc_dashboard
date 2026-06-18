"""Unit tests for the CAD_BATIMENT_HORSOL (`batiments`) SQLite cache and fetch."""

import sqlite3

import pytest

from sections.helpers import autor_api, db


def _make_batiment(egid: int = 100, surface: int = 250) -> dict:
    return {
        "egid": egid,
        "commune": "Genève",
        "no_batiment": f"B{egid}",
        "nombat": f"Bâtiment {egid}",
        "destination": "Habitation",
        "nomenclature": "Logement",
        "nomen_classe": "A",
        "epoque_construction": "1971-1980",
        "annee_construction": 1975,
        "annee_transformation": 2005,
        "niveaux_horsol": 5,
        "niveaux_ssol": 1,
        "hauteur": 15.4,
        "surface": surface,
    }


@pytest.fixture(autouse=True)
def _clear_cache():
    db.load_batiments_by_egids.clear()
    yield
    db.load_batiments_by_egids.clear()


class TestInitBatimentsTable:
    def test_creates_batiments_table(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_batiments_table()

        conn = sqlite3.connect(db.DB_PATH)
        try:
            row = conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='batiments'"
            ).fetchone()
        finally:
            conn.close()

        assert row is not None

    def test_is_idempotent(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_batiments_table()
        db.init_batiments_table()  # must not raise


class TestRefreshBatimentsDb:
    def test_inserts_records(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_batiments_table()
        monkeypatch.setattr(db, "fetch_batiments", lambda **kw: [_make_batiment()])

        assert db.refresh_batiments_db() == 1

    def test_data_stored_in_db(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_batiments_table()
        monkeypatch.setattr(
            db, "fetch_batiments", lambda **kw: [_make_batiment(egid=42)]
        )

        db.refresh_batiments_db()

        conn = sqlite3.connect(db.DB_PATH)
        try:
            row = conn.execute(
                "SELECT egid, annee_construction, niveaux_horsol, surface "
                "FROM batiments WHERE egid = 42"
            ).fetchone()
        finally:
            conn.close()

        assert row == (42, 1975, 5, 250)

    def test_truncates_before_insert(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_batiments_table()

        monkeypatch.setattr(
            db, "fetch_batiments", lambda **kw: [_make_batiment(egid=1)]
        )
        db.refresh_batiments_db()

        monkeypatch.setattr(
            db, "fetch_batiments", lambda **kw: [_make_batiment(egid=2)]
        )
        db.refresh_batiments_db()

        conn = sqlite3.connect(db.DB_PATH)
        try:
            egids = [r[0] for r in conn.execute("SELECT egid FROM batiments")]
        finally:
            conn.close()

        assert egids == [2]

    def test_returns_zero_on_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_batiments_table()
        monkeypatch.setattr(db, "fetch_batiments", lambda **kw: [])

        assert db.refresh_batiments_db() == 0


class TestLoadBatimentsByEgids:
    def _insert(self, path, bat: dict) -> None:
        conn = sqlite3.connect(path)
        try:
            placeholders = ",".join(["?"] * len(db._BATIMENT_COLS))
            conn.execute(
                f"INSERT INTO batiments ({', '.join(db._BATIMENT_COLS)}) "
                f"VALUES ({placeholders})",
                tuple(bat[c] for c in db._BATIMENT_COLS),
            )
            conn.commit()
        finally:
            conn.close()

    def test_returns_empty_for_empty_tuple(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_batiments_table()

        assert db.load_batiments_by_egids(()) == []

    def test_returns_empty_for_unknown_egid(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_batiments_table()

        assert db.load_batiments_by_egids((99999,)) == []

    def test_returns_record_with_all_columns(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_batiments_table()
        self._insert(db.DB_PATH, _make_batiment(egid=1))

        records = db.load_batiments_by_egids((1,))

        assert len(records) == 1
        for col in db._BATIMENT_COLS:
            assert col in records[0]
        assert records[0]["egid"] == 1

    def test_filters_by_egid(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_batiments_table()
        self._insert(db.DB_PATH, _make_batiment(egid=1))
        self._insert(db.DB_PATH, _make_batiment(egid=2))

        records = db.load_batiments_by_egids((1,))

        assert [r["egid"] for r in records] == [1]


class TestFetchBatiments:
    def _feature(self, egid: int, surface: int) -> dict:
        return {
            "attributes": {
                "EGID": egid,
                "COMMUNE": "Genève",
                "NO_BATIMENT": "B1",
                "NOMBAT": "Test",
                "DESTINATION": "Habitation",
                "NOMENCLATURE": "Logement",
                "NOMEN_CLASSE": "A",
                "EPOQUE_CONSTRUCTION": "1971-1980",
                "ANNEE_CONSTRUCTION": 1975,
                "ANNEE_TRANSFORNATION": 2005,
                "NIVEAUX_HORSOL": 5,
                "NIVEAUX_SSOL": 1,
                "HAUTEUR": 15.4,
                "SURFACE": surface,
            }
        }

    def test_maps_source_typo_field(self, monkeypatch):
        monkeypatch.setattr(
            autor_api, "fetch_all", lambda *a, **kw: [self._feature(1, 100)]
        )

        records = autor_api.fetch_batiments()

        assert len(records) == 1
        # SITG ships the field misspelled as ANNEE_TRANSFORNATION.
        assert records[0]["annee_transformation"] == 2005

    def test_requests_without_geometry(self, monkeypatch):
        captured = {}

        def _fake(url, **kwargs):
            captured.update(kwargs)
            return []

        monkeypatch.setattr(autor_api, "fetch_all", _fake)
        autor_api.fetch_batiments()

        assert captured.get("with_geometry") is False
        assert captured.get("fields") == autor_api._BATIMENT_DETAIL_FIELDS

    def test_dedupes_keeping_largest_surface(self, monkeypatch):
        monkeypatch.setattr(
            autor_api,
            "fetch_all",
            lambda *a, **kw: [self._feature(1, 100), self._feature(1, 400)],
        )

        records = autor_api.fetch_batiments()

        assert len(records) == 1
        assert records[0]["surface"] == 400
