from pathlib import Path
import csv

import pytest

from adopcion_pagos.data import (
    load_observations,
    point_observations,
    select_model_series,
)


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def observations():
    return load_observations(ROOT / "data" / "nequi_usuarios.csv")


def test_audited_dataset_has_complete_source_and_cutoff_metadata(observations):
    assert all(item.cutoff_date and item.cutoff_precision for item in observations)
    assert all(item.source_url.startswith("https://") for item in observations)
    assert all(item.source_title for item in observations)
    assert all(item.metric and item.unit for item in observations)


def test_2022_is_stored_as_a_lower_bound(observations):
    item = next(row for row in observations if row.observation_id == "nequi_2022_min")
    assert item.value == pytest.approx(14.0)
    assert item.observation_type == "cota_inferior"
    assert item.include_primary


def test_primary_series_excludes_2025_and_keeps_2022_bound(observations):
    series = select_model_series(observations)
    assert len(series) == 7
    assert max(item.year for item in series) == 2024
    assert any(item.observation_type == "cota_inferior" for item in series)


def test_sensitivity_series_includes_2025_accounts_only_as_flagged(observations):
    series = select_model_series(observations, include_2025=True)
    assert len(series) == 8
    last = series[-1]
    assert last.year == 2025
    assert last.metric == "cuentas en Nequi"
    assert "A la Mano" in last.notes


def test_active_user_metrics_do_not_enter_base_series(observations):
    active = [item for item in observations if "activ" in item.metric]
    assert len(active) == 3
    assert all(item.model_series == "actividad_nequi" for item in active)
    assert all(not item.include_primary and not item.include_sensitivity for item in active)


def test_point_filter_does_not_turn_lower_bound_into_exact_value(observations):
    series = select_model_series(observations)
    points = point_observations(series)
    assert len(points) == 6
    assert all(item.observation_type != "cota_inferior" for item in points)


def test_original_dataset_is_retained_with_2024_rounded_value():
    path = ROOT / "data" / "nequi_usuarios_original.csv"
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 8
    assert next(row for row in rows if row["anio"] == "2024")["usuarios_millones"] == "21.4"
    assert next(row for row in rows if row["anio"] == "2025")["usuarios_millones"] == "27.4"


def test_migration_event_is_context_and_not_an_observation():
    path = ROOT / "data" / "eventos_comparabilidad.csv"
    with path.open(encoding="utf-8-sig", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert row["valor"] == "3.2"
    assert "no se resta ni se suma" in row["uso"]
