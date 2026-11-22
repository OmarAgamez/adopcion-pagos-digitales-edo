from pathlib import Path

import numpy as np
import pytest

from adopcion_pagos.model import LogisticParameters
from adopcion_pagos.simulation import (
    load_scenarios,
    sensitivity_curves,
    simulate,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_analytic_and_numerical_solutions_agree():
    parameters = LogisticParameters(10_000, 500, 0.35)
    result = simulate(parameters)

    np.testing.assert_allclose(
        result.adoption_numeric,
        result.adoption_analytic,
        rtol=1e-9,
        atol=1e-7,
    )
    assert np.all(np.diff(result.adoption_numeric) > 0)
    assert np.all(result.adoption_numeric < parameters.capacity)


def test_simulation_is_reproducible():
    parameters = LogisticParameters(10_000, 500, 0.35)
    first = simulate(parameters, duration_months=24, points=101)
    second = simulate(parameters, duration_months=24, points=101)

    np.testing.assert_array_equal(first.time_months, second.time_months)
    np.testing.assert_array_equal(first.adoption_analytic, second.adoption_analytic)
    np.testing.assert_array_equal(first.adoption_numeric, second.adoption_numeric)
    np.testing.assert_array_equal(first.adoption_rate, second.adoption_rate)
    np.testing.assert_array_equal(first.absolute_error, second.absolute_error)


@pytest.mark.parametrize(
    ("duration", "points"),
    [
        (0, 10),
        (-1, 10),
        (float("inf"), 10),
        (24, 1),
        (24, 2.5),
        (24, True),
    ],
)
def test_invalid_simulation_options_are_rejected(duration, points):
    parameters = LogisticParameters(10_000, 500, 0.35)
    with pytest.raises(ValueError):
        simulate(parameters, duration_months=duration, points=points)


def test_parameter_csv_loads_three_hypothetical_scenarios():
    scenarios = load_scenarios(PROJECT_ROOT / "data" / "escenarios_didacticos.csv")
    assert {scenario.name for scenario in scenarios} == {"lento", "moderado", "rápido"}
    assert all(scenario.duration_months == 24 for scenario in scenarios)
    assert all("hipotético" in scenario.description for scenario in scenarios)


def test_sensitivity_varies_each_parameter_independently():
    base = LogisticParameters(10_000, 500, 0.35)
    times, curves = sensitivity_curves(base, duration_months=24, points=21)

    assert times.size == 21
    assert set(curves) == {"r", "K", "A0"}
    assert all(len(parameter_curves) == 5 for parameter_curves in curves.values())
    for value, adoption in curves["r"]:
        assert 0.0 < value
        assert adoption.shape == times.shape
    for value, adoption in curves["K"]:
        assert value > base.initial_adopters
        assert adoption.shape == times.shape
    for value, adoption in curves["A0"]:
        assert 0.0 < value < base.capacity
        assert adoption.shape == times.shape
