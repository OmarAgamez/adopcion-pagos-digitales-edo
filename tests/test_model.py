import numpy as np
import pytest

from adopcion_pagos.model import (
    LogisticParameters,
    analytical_solution,
    logistic_rhs,
)


@pytest.fixture
def parameters():
    return LogisticParameters(capacity=10_000, initial_adopters=500, growth_rate=0.35)


def test_analytical_solution_satisfies_initial_condition(parameters):
    assert analytical_solution(0, parameters) == pytest.approx(500)


def test_adoption_curve_is_monotonic_and_bounded(parameters):
    time = np.linspace(0, 24, 241)
    adoption = analytical_solution(time, parameters)

    assert np.all(np.diff(adoption) > 0)
    assert np.all(adoption < parameters.capacity)
    assert np.all(adoption > 0)


def test_solution_approaches_saturation_limit(parameters):
    adoption = analytical_solution(200, parameters)
    assert adoption == pytest.approx(parameters.capacity, rel=1e-12)


def test_rhs_matches_expected_initial_growth_rate(parameters):
    expected = 0.35 * 500 * (1 - 500 / 10_000)
    assert logistic_rhs(0, 500, parameters) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("capacity", "initial_adopters", "growth_rate"),
    [
        (0, 10, 0.2),
        (10, 0, 0.2),
        (10, 10, 0.2),
        (10, 11, 0.2),
        (10, 2, 0),
        (10, 2, -0.2),
        (10, float("nan"), 0.2),
        (10, 2, float("inf")),
    ],
)
def test_invalid_parameters_are_rejected(capacity, initial_adopters, growth_rate):
    with pytest.raises(ValueError):
        LogisticParameters(capacity, initial_adopters, growth_rate)


def test_negative_or_nonfinite_time_is_rejected(parameters):
    with pytest.raises(ValueError):
        analytical_solution(-1, parameters)
    with pytest.raises(ValueError):
        analytical_solution(float("nan"), parameters)
