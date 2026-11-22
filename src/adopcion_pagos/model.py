"""Ecuación diferencial logística y solución analítica."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.special import expit


@dataclass(frozen=True)
class LogisticParameters:
    """Parámetros del modelo, con tiempo medido en meses."""

    capacity: float
    initial_adopters: float
    growth_rate: float

    def __post_init__(self) -> None:
        validate_parameters(self.capacity, self.initial_adopters, self.growth_rate)
        object.__setattr__(self, "capacity", float(self.capacity))
        object.__setattr__(self, "initial_adopters", float(self.initial_adopters))
        object.__setattr__(self, "growth_rate", float(self.growth_rate))


def _finite_number(value: float, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} debe ser un número real finito.") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} debe ser un número real finito.")
    return result


def validate_parameters(capacity: float, initial_adopters: float, growth_rate: float) -> None:
    """Valida 0 < A0 < K y r > 0, supuestos del modelo de adopción."""

    capacity_value = _finite_number(capacity, "K")
    initial_value = _finite_number(initial_adopters, "A0")
    rate_value = _finite_number(growth_rate, "r")

    if capacity_value <= 0:
        raise ValueError("K debe ser mayor que cero.")
    if not 0 < initial_value < capacity_value:
        raise ValueError("A0 debe cumplir 0 < A0 < K.")
    if rate_value <= 0:
        raise ValueError("r debe ser mayor que cero.")


def logistic_rhs(
    time_months: ArrayLike,
    adopters: ArrayLike,
    parameters: LogisticParameters,
) -> float | NDArray[np.float64]:
    """Evalúa dA/dt = r*A*(1 - A/K), en personas por mes."""

    times = np.asarray(time_months, dtype=np.float64)
    if not np.all(np.isfinite(times)):
        raise ValueError("El tiempo debe contener únicamente valores finitos.")
    values = np.asarray(adopters, dtype=np.float64)
    if not np.all(np.isfinite(values)):
        raise ValueError("A(t) debe contener únicamente valores finitos.")
    result = parameters.growth_rate * values * (1.0 - values / parameters.capacity)
    if result.ndim == 0:
        return float(result)
    return result


def analytical_solution(
    time_months: ArrayLike,
    parameters: LogisticParameters,
) -> float | NDArray[np.float64]:
    """Calcula A(t) mediante la solución logística cerrada.

    La expresión se evalúa con una función logística numéricamente estable,
    equivalente a K / (1 + ((K-A0)/A0) * exp(-r*t)).
    """

    times = np.asarray(time_months, dtype=np.float64)
    if not np.all(np.isfinite(times)):
        raise ValueError("El tiempo debe contener únicamente valores finitos.")
    if np.any(times < 0):
        raise ValueError("El tiempo de simulación no puede ser negativo.")

    log_odds = math.log(parameters.capacity - parameters.initial_adopters) - math.log(
        parameters.initial_adopters
    )
    values = parameters.capacity * expit(parameters.growth_rate * times - log_odds)
    if values.ndim == 0:
        return float(values)
    return values
