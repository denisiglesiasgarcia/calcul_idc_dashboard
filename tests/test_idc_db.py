"""Unit tests for idc_data SQLite cache: init, refresh, and load functions."""

import sqlite3

import polars as pl
import pytest

from sections.helpers import db

_TS = 1_672_531_200_000  # 2023-01-01 00:00:00 UTC as ms epoch
_TS_OLD = 1_000_000_000_000
_TS_NEW = 1_672_531_200_000


def _make_feature(
    egid: int = 100,
    annee: int = 2022,
    saisie_ts: int = _TS,
    indice: int = 300,
) -> dict:
    return {
        "attributes": {
            "egid": egid,
            "annee": annee,
            "indice": indice,
            "sre": 500,
            "adresse": f"Rue Test {egid}",
            "npa": 1201,
            "commune": "Genève",
            "destination": "Habitation",
            "agent_energetique_1": "gaz",
            "quantite_agent_energetique_1": 100.0,
            "unite_agent_energetique_1": "kWh",
            "agent_energetique_2": None,
            "quantite_agent_energetique_2": None,
            "unite_agent_energetique_2": None,
            "agent_energetique_3": None,
            "quantite_agent_energetique_3": None,
            "unite_agent_energetique_3": None,
            "date_debut_periode": saisie_ts,
            "date_fin_periode": saisie_ts,
            "date_saisie": saisie_ts,
            "indice_moy2": None,
            "annees_concernees_moy_2": None,
            "indice_moy3": None,
            "annees_concernees_moy_3": None,
            "id_concessionnaire": None,
            "nbre_preneur": None,
        },
    }


@pytest.fixture(autouse=True)
def _clear_cache():
    db.load_idc_by_egids.clear()
    yield
    db.load_idc_by_egids.clear()


class TestInitIdcTable:
    def test_creates_idc_data_table(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_idc_table()

        conn = sqlite3.connect(db.DB_PATH)
        try:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='idc_data'"
            ).fetchone()
        finally:
            conn.close()

        assert row is not None

    def test_creates_egid_index(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_idc_table()

        conn = sqlite3.connect(db.DB_PATH)
        try:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_idc_data_egid'"
            ).fetchone()
        finally:
            conn.close()

        assert row is not None

    def test_is_idempotent(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_idc_table()
        db.init_idc_table()  # must not raise


class TestRefreshIdcDb:
    def test_inserts_records(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_idc_table()
        monkeypatch.setattr(db, "fetch_all", lambda *a, **kw: [_make_feature()])

        count = db.refresh_idc_db("http://fake")

        assert count == 1

    def test_data_stored_in_db(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_idc_table()
        monkeypatch.setattr(db, "fetch_all", lambda *a, **kw: [_make_feature(egid=42)])

        db.refresh_idc_db("http://fake")

        conn = sqlite3.connect(db.DB_PATH)
        try:
            row = conn.execute(
                "SELECT egid, indice FROM idc_data WHERE egid = 42"
            ).fetchone()
        finally:
            conn.close()

        assert row == (42, 300)

    def test_deduplicates_keeps_most_recent_saisie(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_idc_table()
        monkeypatch.setattr(
            db,
            "fetch_all",
            lambda *a, **kw: [
                _make_feature(egid=1, annee=2022, saisie_ts=_TS_OLD, indice=100),
                _make_feature(egid=1, annee=2022, saisie_ts=_TS_NEW, indice=200),
            ],
        )

        count = db.refresh_idc_db("http://fake")

        assert count == 1
        conn = sqlite3.connect(db.DB_PATH)
        try:
            row = conn.execute("SELECT indice FROM idc_data WHERE egid=1").fetchone()
        finally:
            conn.close()
        assert row[0] == 200  # most recent saisie wins

    def test_different_years_not_deduplicated(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_idc_table()
        monkeypatch.setattr(
            db,
            "fetch_all",
            lambda *a, **kw: [
                _make_feature(egid=1, annee=2021),
                _make_feature(egid=1, annee=2022),
            ],
        )

        count = db.refresh_idc_db("http://fake")

        assert count == 2

    def test_truncates_before_insert(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_idc_table()

        monkeypatch.setattr(db, "fetch_all", lambda *a, **kw: [_make_feature(egid=1)])
        db.refresh_idc_db("http://fake")

        monkeypatch.setattr(db, "fetch_all", lambda *a, **kw: [_make_feature(egid=2)])
        db.refresh_idc_db("http://fake")

        conn = sqlite3.connect(db.DB_PATH)
        try:
            rows = conn.execute("SELECT egid FROM idc_data").fetchall()
        finally:
            conn.close()

        egids = [r[0] for r in rows]
        assert egids == [2]

    def test_returns_zero_on_empty_features(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_idc_table()
        monkeypatch.setattr(db, "fetch_all", lambda *a, **kw: [])

        count = db.refresh_idc_db("http://fake")

        assert count == 0

    def test_calls_fetch_all_with_idc_fields_and_no_geometry(
        self, tmp_path, monkeypatch
    ):
        # Geometry is deliberately not requested: the same polygon would
        # otherwise be downloaded once per (egid, annee) row. The map instead
        # sources building polygons from the batiments table.
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_idc_table()

        captured = {}

        def _fake_fetch_all(url, **kwargs):
            captured.update(kwargs)
            return []

        monkeypatch.setattr(db, "fetch_all", _fake_fetch_all)
        db.refresh_idc_db("http://fake")

        # Explicit outFields (only the stored columns), not "*"
        assert captured.get("fields") == ",".join(db._IDC_COLS)
        assert captured.get("with_geometry") is False


class TestLoadIdcByEgids:
    def _insert_feature(self, path, feature: dict) -> None:
        a = feature["attributes"]
        conn = sqlite3.connect(path)
        try:
            conn.execute(
                """
                INSERT INTO idc_data (
                    egid, annee, indice, sre, adresse, npa, commune, destination,
                    agent_energetique_1, quantite_agent_energetique_1, unite_agent_energetique_1,
                    agent_energetique_2, quantite_agent_energetique_2, unite_agent_energetique_2,
                    agent_energetique_3, quantite_agent_energetique_3, unite_agent_energetique_3,
                    date_debut_periode, date_fin_periode, date_saisie,
                    indice_moy2, annees_concernees_moy_2, indice_moy3, annees_concernees_moy_3,
                    id_concessionnaire, nbre_preneur
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    a["egid"],
                    a["annee"],
                    a["indice"],
                    a["sre"],
                    a["adresse"],
                    a["npa"],
                    a["commune"],
                    a["destination"],
                    a["agent_energetique_1"],
                    a["quantite_agent_energetique_1"],
                    a["unite_agent_energetique_1"],
                    a["agent_energetique_2"],
                    a["quantite_agent_energetique_2"],
                    a["unite_agent_energetique_2"],
                    a["agent_energetique_3"],
                    a["quantite_agent_energetique_3"],
                    a["unite_agent_energetique_3"],
                    a["date_debut_periode"],
                    a["date_fin_periode"],
                    a["date_saisie"],
                    a["indice_moy2"],
                    a["annees_concernees_moy_2"],
                    a["indice_moy3"],
                    a["annees_concernees_moy_3"],
                    a["id_concessionnaire"],
                    a["nbre_preneur"],
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def test_returns_none_for_empty_tuple(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_idc_table()

        data = db.load_idc_by_egids(())

        assert data is None

    def test_returns_none_for_unknown_egid(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_idc_table()

        data = db.load_idc_by_egids((99999,))

        assert data is None

    def test_data_records_contain_all_idc_columns(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_idc_table()
        self._insert_feature(db.DB_PATH, _make_feature(egid=1))

        data = db.load_idc_by_egids((1,))

        row = data[0]
        for col in db._IDC_COLS:
            assert col in row, f"Missing column: {col}"

    def test_date_columns_cast_to_datetime(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_idc_table()
        self._insert_feature(db.DB_PATH, _make_feature(egid=1))

        data = db.load_idc_by_egids((1,))

        df = pl.from_dicts(data)
        assert isinstance(df["date_saisie"].dtype, pl.Datetime)
        assert isinstance(df["date_debut_periode"].dtype, pl.Datetime)
        assert isinstance(df["date_fin_periode"].dtype, pl.Datetime)

    def test_multiple_egids_returned(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_idc_table()
        self._insert_feature(db.DB_PATH, _make_feature(egid=1))
        self._insert_feature(db.DB_PATH, _make_feature(egid=2))

        data = db.load_idc_by_egids((1, 2))

        assert len(data) == 2

    def test_filters_by_egid(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_idc_table()
        self._insert_feature(db.DB_PATH, _make_feature(egid=1))
        self._insert_feature(db.DB_PATH, _make_feature(egid=2))

        data = db.load_idc_by_egids((1,))

        assert len(data) == 1
        assert data[0]["egid"] == 1

    def test_multiple_years_per_egid_all_returned(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_idc_table()
        self._insert_feature(db.DB_PATH, _make_feature(egid=1, annee=2021))
        self._insert_feature(db.DB_PATH, _make_feature(egid=1, annee=2022))

        data = db.load_idc_by_egids((1,))

        annees = sorted(r["annee"] for r in data)
        assert annees == [2021, 2022]

    def test_result_ordered_by_egid_and_annee(self, tmp_path, monkeypatch):
        monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
        db.init_idc_table()
        self._insert_feature(db.DB_PATH, _make_feature(egid=2, annee=2022))
        self._insert_feature(db.DB_PATH, _make_feature(egid=1, annee=2021))
        self._insert_feature(db.DB_PATH, _make_feature(egid=1, annee=2022))

        data = db.load_idc_by_egids((1, 2))

        egids = [r["egid"] for r in data]
        assert egids == sorted(egids)
