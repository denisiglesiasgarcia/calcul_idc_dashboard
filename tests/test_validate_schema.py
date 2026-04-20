"""Unit tests for idc_api.validate_schema() — pure function, no I/O."""

from datetime import datetime

import polars as pl
import pytest

from sections.helpers.idc_api import EXPECTED_SCHEMA, validate_schema


@pytest.fixture
def valid_df():
    dt = datetime(2020, 1, 1)
    return pl.DataFrame(
        {
            "egid": pl.Series([1], dtype=pl.Int64),
            "annee": pl.Series([2020], dtype=pl.Int64),
            "indice": pl.Series([300], dtype=pl.Int64),
            "sre": pl.Series([500], dtype=pl.Int64),
            "adresse": pl.Series(["Rue Test 1"], dtype=pl.String),
            "npa": pl.Series([1200], dtype=pl.Int64),
            "commune": pl.Series(["Genève"], dtype=pl.String),
            "destination": pl.Series(["Habitation"], dtype=pl.String),
            "agent_energetique_1": pl.Series(["gaz"], dtype=pl.String),
            "quantite_agent_energetique_1": pl.Series([100.0], dtype=pl.Float64),
            "unite_agent_energetique_1": pl.Series(["kWh"], dtype=pl.String),
            "agent_energetique_2": pl.Series([None], dtype=pl.String),
            "quantite_agent_energetique_2": pl.Series([None], dtype=pl.Float64),
            "unite_agent_energetique_2": pl.Series([None], dtype=pl.String),
            "agent_energetique_3": pl.Series([None], dtype=pl.String),
            "quantite_agent_energetique_3": pl.Series([None], dtype=pl.Float64),
            "unite_agent_energetique_3": pl.Series([None], dtype=pl.String),
            "date_debut_periode": pl.Series([dt]).cast(pl.Datetime("ms")),
            "date_fin_periode": pl.Series([dt]).cast(pl.Datetime("ms")),
            "date_saisie": pl.Series([dt]).cast(pl.Datetime("ms")),
            "indice_moy2": pl.Series([None], dtype=pl.Int64),
            "annees_concernees_moy_2": pl.Series([None], dtype=pl.String),
            "indice_moy3": pl.Series([None], dtype=pl.Int64),
            "annees_concernees_moy_3": pl.Series([None], dtype=pl.String),
            "id_concessionnaire": pl.Series([None], dtype=pl.Int64),
            "nbre_preneur": pl.Series([None], dtype=pl.Int64),
        }
    )


def test_valid_schema_returns_no_errors(valid_df):
    assert validate_schema(valid_df) == []


def test_missing_required_column_reported(valid_df):
    df = valid_df.drop("egid")
    errors = validate_schema(df)
    assert any("egid" in e and "absente" in e for e in errors)


def test_wrong_dtype_on_required_column_reported(valid_df):
    df = valid_df.with_columns(pl.col("egid").cast(pl.Utf8))
    errors = validate_schema(df)
    assert any("egid" in e for e in errors)


def test_datetime_us_accepted_for_ms_column(valid_df):
    df = valid_df.with_columns(pl.col("date_debut_periode").cast(pl.Datetime("us")))
    errors = validate_schema(df)
    assert all("date_debut_periode" not in e for e in errors)


def test_nullable_column_with_null_type_no_error(valid_df):
    df = valid_df.drop("agent_energetique_2").with_columns(
        pl.Series("agent_energetique_2", [None], dtype=pl.Null)
    )
    errors = validate_schema(df)
    assert all("agent_energetique_2" not in e for e in errors)


def test_multiple_missing_columns_all_reported(valid_df):
    df = valid_df.drop(["egid", "annee", "indice"])
    errors = validate_schema(df)
    assert len(errors) >= 3


def test_missing_nullable_column_still_an_error(valid_df):
    df = valid_df.drop("indice_moy3")
    errors = validate_schema(df)
    assert any("indice_moy3" in e and "absente" in e for e in errors)


def test_empty_dataframe_with_correct_schema_no_errors():
    df = pl.DataFrame(schema=EXPECTED_SCHEMA)
    assert validate_schema(df) == []


def test_wrong_dtype_string_instead_of_int64(valid_df):
    df = valid_df.with_columns(pl.col("npa").cast(pl.Utf8))
    errors = validate_schema(df)
    assert any("npa" in e for e in errors)


def test_wrong_dtype_int_instead_of_float(valid_df):
    df = valid_df.with_columns(pl.col("quantite_agent_energetique_1").cast(pl.Int64))
    errors = validate_schema(df)
    assert any("quantite_agent_energetique_1" in e for e in errors)
