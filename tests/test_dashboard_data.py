from pathlib import Path

import pytest

from adopcion_pagos.dashboard_data import (
    load_dashboard_tables,
    parameters_from_fit_row,
)


ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_adapter_reads_original_and_integrated_results_separately():
    tables = load_dashboard_tables(ROOT)

    original = next(
        row for row in tables["original_fits"] if row["escenario"] == "K fijo 32"
    )
    integrated = next(
        row
        for row in tables["primary_fits"]
        if row["escenario"] == "K = 32 M (escenario fijo)"
    )

    assert int(original["n_observaciones"]) == 8
    assert int(integrated["puntos_usados_en_metricas"]) == 6
    assert int(integrated["cotas_inferiores"]) == 1
    assert "advertencia" in original
    assert "maximo_incumplimiento_cota_millones" in integrated


def test_fit_row_adapter_reuses_validated_logistic_parameters():
    row = {
        "K_millones": "32.0",
        "N0_millones": "0.816",
        "r_por_anio": "0.8479829096255819",
    }

    parameters = parameters_from_fit_row(row)

    assert parameters.capacity == pytest.approx(32.0)
    assert parameters.initial_adopters == pytest.approx(0.816)
    assert parameters.growth_rate == pytest.approx(0.8479829096255819)


def test_fit_row_adapter_rejects_missing_or_invalid_parameters():
    with pytest.raises(ValueError, match="parámetros históricos válidos"):
        parameters_from_fit_row({"K_millones": "32", "N0_millones": "0.816"})

    with pytest.raises(ValueError, match="parámetros históricos válidos"):
        parameters_from_fit_row(
            {"K_millones": "0.5", "N0_millones": "0.816", "r_por_anio": "1"}
        )
