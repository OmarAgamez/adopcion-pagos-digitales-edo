"""Integración numérica, escenarios y lectura de parámetros CSV."""

from __future__ import annotations

import csv
from dataclasses import dataclass, replace
import math
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from scipy.integrate import solve_ivp

from .model import LogisticParameters, analytical_solution, logistic_rhs


@dataclass(frozen=True)
class Scenario:
    name: str
    parameters: LogisticParameters
    duration_months: float
    description: str


@dataclass(frozen=True)
class SimulationResult:
    time_months: NDArray[np.float64]
    adoption_analytic: NDArray[np.float64]
    adoption_numeric: NDArray[np.float64]
    adoption_rate: NDArray[np.float64]
    absolute_error: NDArray[np.float64]


def _positive_duration(value: float) -> float:
    try:
        duration = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("La duración debe ser un número finito mayor que cero.") from exc
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("La duración debe ser un número finito mayor que cero.")
    return duration


def load_scenarios(csv_path: str | Path) -> list[Scenario]:
    """Lee y valida el CSV editable de escenarios hipotéticos."""

    required = {
        "scenario",
        "capacity_people",
        "initial_adopters_people",
        "growth_rate_per_month",
        "duration_months",
        "description",
    }
    path = Path(csv_path)
    try:
        handle = path.open("r", encoding="utf-8-sig", newline="")
    except OSError as exc:
        raise ValueError(f"No se pudo abrir el archivo de parámetros: {path}") from exc

    scenarios: list[Scenario] = []
    with handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            missing = sorted(required - set(reader.fieldnames or []))
            raise ValueError(f"Faltan columnas requeridas en el CSV: {', '.join(missing)}")
        for row_number, row in enumerate(reader, start=2):
            name = (row.get("scenario") or "").strip()
            description = (row.get("description") or "").strip()
            if not name:
                raise ValueError(f"El escenario de la fila {row_number} no tiene nombre.")
            if not description:
                raise ValueError(f"El escenario {name} requiere una descripción.")
            try:
                parameters = LogisticParameters(
                    capacity=float(row["capacity_people"]),
                    initial_adopters=float(row["initial_adopters_people"]),
                    growth_rate=float(row["growth_rate_per_month"]),
                )
                duration = _positive_duration(float(row["duration_months"]))
            except (TypeError, ValueError, OverflowError) as exc:
                raise ValueError(f"Parámetros inválidos en la fila {row_number}: {exc}") from exc
            scenarios.append(Scenario(name, parameters, duration, description))

    if not scenarios:
        raise ValueError("El CSV debe contener al menos un escenario.")
    names = [scenario.name.casefold() for scenario in scenarios]
    if len(names) != len(set(names)):
        raise ValueError("Los nombres de escenarios deben ser únicos.")
    if not {"lento", "moderado", "rápido"}.issubset(set(names)):
        raise ValueError("El CSV debe incluir los escenarios lento, moderado y rápido.")
    if len({scenario.duration_months for scenario in scenarios}) != 1:
        raise ValueError("Todos los escenarios deben usar la misma duración.")
    return scenarios


def simulate(
    parameters: LogisticParameters,
    duration_months: float = 24,
    points: int = 241,
) -> SimulationResult:
    """Resuelve la EDO con solve_ivp y la compara con la solución analítica."""

    duration = _positive_duration(duration_months)
    if isinstance(points, bool) or not isinstance(points, (int, np.integer)) or points < 2:
        raise ValueError("points debe ser un entero mayor o igual que 2.")

    times = np.linspace(0.0, duration, int(points), dtype=np.float64)

    def derivative(time: float, state: NDArray[np.float64]) -> NDArray[np.float64]:
        return np.asarray([logistic_rhs(time, state[0], parameters)], dtype=np.float64)

    numerical = solve_ivp(
        derivative,
        (0.0, duration),
        [parameters.initial_adopters],
        t_eval=times,
        method="RK45",
        rtol=1e-12,
        atol=1e-12,
    )
    if not numerical.success:
        raise RuntimeError(f"Falló solve_ivp: {numerical.message}")

    analytic_values = np.asarray(analytical_solution(times, parameters), dtype=np.float64)
    numeric_values = numerical.y[0]
    rates = np.asarray(logistic_rhs(times, numeric_values, parameters), dtype=np.float64)
    return SimulationResult(
        time_months=times,
        adoption_analytic=analytic_values,
        adoption_numeric=numeric_values,
        adoption_rate=rates,
        absolute_error=np.abs(analytic_values - numeric_values),
    )


def sensitivity_values(parameters: LogisticParameters) -> dict[str, NDArray[np.float64]]:
    """Devuelve cinco valores alrededor de cada parámetro base."""

    capacity_values = np.linspace(
        max(0.8 * parameters.capacity, 1.01 * parameters.initial_adopters),
        1.2 * parameters.capacity,
        5,
    )
    initial_upper = min(1.5 * parameters.initial_adopters, 0.99 * parameters.capacity)
    if initial_upper <= parameters.initial_adopters:
        initial_upper = parameters.initial_adopters + 0.5 * (
            parameters.capacity - parameters.initial_adopters
        )
    return {
        "r": np.linspace(0.5 * parameters.growth_rate, 1.5 * parameters.growth_rate, 5),
        "K": capacity_values,
        "A0": np.linspace(0.5 * parameters.initial_adopters, initial_upper, 5),
    }


def sensitivity_curves(
    parameters: LogisticParameters,
    duration_months: float = 24,
    points: int = 241,
) -> tuple[NDArray[np.float64], dict[str, list[tuple[float, NDArray[np.float64]]]]]:
    """Calcula curvas analíticas al variar r, K y A0 de forma independiente."""

    duration = _positive_duration(duration_months)
    if isinstance(points, bool) or not isinstance(points, (int, np.integer)) or points < 2:
        raise ValueError("points debe ser un entero mayor o igual que 2.")
    times = np.linspace(0.0, duration, int(points), dtype=np.float64)
    curves: dict[str, list[tuple[float, NDArray[np.float64]]]] = {}

    for parameter_name, values in sensitivity_values(parameters).items():
        parameter_curves: list[tuple[float, NDArray[np.float64]]] = []
        for value in values:
            if parameter_name == "r":
                varied = replace(parameters, growth_rate=float(value))
            elif parameter_name == "K":
                varied = replace(parameters, capacity=float(value))
            else:
                varied = replace(parameters, initial_adopters=float(value))
            adoption = np.asarray(analytical_solution(times, varied), dtype=np.float64)
            parameter_curves.append((float(value), adoption))
        curves[parameter_name] = parameter_curves
    return times, curves
