from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from adopcion_pagos.data import load_observations, select_model_series
from adopcion_pagos.fit import fit_logistic
from adopcion_pagos.model import (
    LogisticParameters,
    analytical_solution,
    inflection_time,
    time_to_fraction,
)


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def primary():
    return select_model_series(
        load_observations(ROOT / "data" / "nequi_usuarios.csv")
    )


def test_fixed_capacity_fit_reports_point_metrics_and_bound_separately(primary):
    result = fit_logistic(primary, capacity=32.0, label="K=32")
    assert result.parameters.capacity == pytest.approx(32.0)
    assert result.parameters.initial_adopters == pytest.approx(0.816)
    assert result.parameters.growth_rate > 0
    assert result.point_count == 6
    assert result.lower_bound_count == 1
    assert result.rmse_millions >= 0
    assert np.isfinite(result.r_squared)
    assert result.lower_bound_violations["nequi_2022_min"] == pytest.approx(0.0, abs=1e-8)


def test_a_satisfied_lower_bound_is_not_fitted_as_a_point(primary):
    satisfied_bound = [
        replace(item, value=1.0) if item.observation_type == "cota_inferior" else item
        for item in primary
    ]
    with_bound = fit_logistic(satisfied_bound, capacity=32.0, label="with bound")
    without_bound = [
        item for item in primary if item.observation_type != "cota_inferior"
    ]
    without = fit_logistic(without_bound, capacity=32.0, label="without bound")
    assert with_bound.parameters.growth_rate == pytest.approx(
        without.parameters.growth_rate, rel=1e-7
    )
    assert with_bound.rmse_millions == pytest.approx(without.rmse_millions)


def test_free_capacity_fit_exceeds_all_point_and_lower_bound_values(primary):
    result = fit_logistic(primary, capacity=None, label="K libre")
    assert result.parameters.capacity > max(item.value for item in primary)
    assert result.parameters.capacity < 200
    assert result.capacity_mode == "libre"
    assert result.parameters.growth_rate > 0


def test_2025_sensitivity_uses_a_different_observation_set(primary):
    full = select_model_series(
        load_observations(ROOT / "data" / "nequi_usuarios.csv"),
        include_2025=True,
    )
    primary_fit = fit_logistic(primary, capacity=32.0, label="2018-24")
    sensitivity_fit = fit_logistic(full, capacity=32.0, label="incluye-2025")
    assert sensitivity_fit.point_count == primary_fit.point_count + 1
    assert "cuentas_nequi_2025" in sensitivity_fit.residuals
    assert "cuentas_nequi_2025" not in primary_fit.residuals
    assert sensitivity_fit.rmse_millions != pytest.approx(primary_fit.rmse_millions)


def test_fixed_capacity_below_a_reported_value_is_rejected(primary):
    with pytest.raises(ValueError, match="superar"):
        fit_logistic(primary, capacity=20.0, label="K demasiado bajo")


def test_inflection_time_maps_to_half_capacity():
    parameters = LogisticParameters(10_000, 500, 0.35)
    time = inflection_time(parameters)
    assert analytical_solution(time, parameters) == pytest.approx(5_000.0)


def test_time_to_fraction_reaches_requested_share():
    parameters = LogisticParameters(10_000, 500, 0.35)
    time = time_to_fraction(parameters, 0.9)
    assert analytical_solution(time, parameters) == pytest.approx(9_000.0)


@pytest.mark.parametrize("fraction", [0.0, 1.0, float("nan")])
def test_invalid_capacity_fraction_is_rejected(fraction):
    with pytest.raises(ValueError):
        time_to_fraction(LogisticParameters(10_000, 500, 0.35), fraction)
