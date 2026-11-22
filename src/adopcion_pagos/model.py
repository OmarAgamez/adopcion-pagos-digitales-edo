"""Modelo logístico central: dN/dt = r N (1 - N/K)."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.special import expit


def _finite_number(value: float, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} debe ser un número real finito.") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} debe ser un número real finito.")
    return result


@dataclass(frozen=True)
class LogisticParameters:
    """Parámetros en unidades coherentes: K y N0 comparten unidad; r es 1/tiempo."""

    capacity: float
    initial_adopters: float
    growth_rate: float

    def __post_init__(self) -> None:
        capacity = _finite_number(self.capacity, "K")
        initial = _finite_number(self.initial_adopters, "N0")
        rate = _finite_number(self.growth_rate, "r")
        if capacity <= 0:
            raise ValueError("K debe ser mayor que cero.")
        if not 0 < initial < capacity:
            raise ValueError("N0 debe cumplir 0 < N0 < K.")
        if rate <= 0:
            raise ValueError("r debe ser mayor que cero.")
        object.__setattr__(self, "capacity", capacity)
        object.__setattr__(self, "initial_adopters", initial)
        object.__setattr__(self, "growth_rate", rate)


def logistic_rhs(
    time: ArrayLike,
    adopters: ArrayLike,
    parameters: LogisticParameters,
) -> float | NDArray[np.float64]:
    """Evalúa dN/dt; la salida tiene unidades de población por unidad de tiempo."""

    times = np.asarray(time, dtype=np.float64)
    values = np.asarray(adopters, dtype=np.float64)
    if not np.all(np.isfinite(times)):
        raise ValueError("El tiempo debe contener únicamente valores finitos.")
    if not np.all(np.isfinite(values)):
        raise ValueError("N(t) debe contener únicamente valores finitos.")
    result = parameters.growth_rate * values * (1.0 - values / parameters.capacity)
    if result.ndim == 0:
        return float(result)
    return result


def analytical_solution(
    time: ArrayLike,
    parameters: LogisticParameters,
) -> float | NDArray[np.float64]:
    """Solución cerrada y estable, válida para tiempo no negativo."""

    times = np.asarray(time, dtype=np.float64)
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


def time_to_fraction(parameters: LogisticParameters, fraction: float) -> float:
    """Tiempo desde N0 para alcanzar una fracción de K, 0 < fraction < 1."""

    target = _finite_number(fraction, "fracción")
    if not 0 < target < 1:
        raise ValueError("La fracción debe estar estrictamente entre cero y uno.")
    odds_target = target / (1.0 - target)
    odds_initial = parameters.initial_adopters / (
        parameters.capacity - parameters.initial_adopters
    )
    return math.log(odds_target / odds_initial) / parameters.growth_rate


def inflection_time(parameters: LogisticParameters) -> float:
    """Tiempo desde N0 hasta el punto de inflexión N=K/2."""

    return time_to_fraction(parameters, 0.5)
