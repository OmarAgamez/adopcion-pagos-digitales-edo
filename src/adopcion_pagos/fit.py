"""Ajuste logístico con observaciones puntuales y cotas inferiores."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
from scipy.optimize import minimize

from .data import HistoricObservation
from .model import LogisticParameters, analytical_solution


@dataclass(frozen=True)
class FitResult:
    label: str
    parameters: LogisticParameters
    capacity_mode: str
    point_count: int
    lower_bound_count: int
    rmse_millions: float
    r_squared: float
    predictions: dict[str, float]
    residuals: dict[str, float]
    lower_bound_violations: dict[str, float]
    optimizer_cost: float


def _parameters(vector: np.ndarray, initial: float, fixed_capacity: float | None) -> LogisticParameters:
    if fixed_capacity is None:
        rate, capacity = map(float, vector)
    else:
        rate, capacity = float(vector[0]), fixed_capacity
    return LogisticParameters(capacity, initial, rate)


def fit_logistic(
    observations: list[HistoricObservation],
    *,
    capacity: float | None,
    label: str,
    initial_adopters: float | None = None,
    maximum_capacity: float = 200.0,
) -> FitResult:
    """Ajusta por mínimos cuadrados con restricciones duras N(t_i) >= L_i.

    Los valores puntuales generan la función objetivo. Cada cota inferior L_i
    impone la desigualdad N(t_i) >= L_i y nunca se ajusta como si N(t_i)=L_i.
    """

    if len(observations) < 3:
        raise ValueError("Se requieren al menos tres observaciones para el ajuste.")
    ordered = sorted(observations, key=lambda item: item.time_years)
    if any(item.time_years < 0 for item in ordered):
        raise ValueError("Los tiempos de ajuste no pueden ser negativos.")
    point_items = [item for item in ordered if item.observation_type != "cota_inferior"]
    bound_items = [item for item in ordered if item.observation_type == "cota_inferior"]
    if len(point_items) < 2:
        raise ValueError("Se requieren al menos dos observaciones puntuales.")
    initial = float(initial_adopters if initial_adopters is not None else point_items[0].value)
    if not np.isfinite(initial) or initial <= 0:
        raise ValueError("La condición inicial N0 debe ser finita y positiva.")

    free_capacity = capacity is None
    if free_capacity:
        capacity_floor = max(initial, max(item.value for item in ordered)) * (1.0 + 1e-7)
        if not np.isfinite(maximum_capacity) or maximum_capacity <= capacity_floor:
            raise ValueError("maximum_capacity debe superar todas las observaciones.")
        starting_capacity = min(maximum_capacity * 0.5, max(30.0, capacity_floor * 1.2))
        starting_capacity = max(starting_capacity, capacity_floor * 1.01)
        if starting_capacity >= maximum_capacity:
            starting_capacity = (capacity_floor + maximum_capacity) / 2
        candidate_capacity = starting_capacity
    else:
        candidate_capacity = float(capacity)
        if not np.isfinite(candidate_capacity) or candidate_capacity <= initial:
            raise ValueError("La capacidad fija K debe ser finita y mayor que N0.")
        if candidate_capacity <= max(item.value for item in ordered):
            raise ValueError("La capacidad fija K debe superar las observaciones reportadas.")
        capacity_floor = candidate_capacity

    # Para una solución inicial factible, calcula r mínimo requerido por las cotas.
    minimum_rate = 1e-8
    for item in bound_items:
        if item.value <= initial:
            continue
        if item.time_years <= 0 or item.value >= candidate_capacity:
            raise ValueError(f"La cota {item.observation_id} no es factible con K elegido.")
        odds_initial = initial / (candidate_capacity - initial)
        odds_bound = item.value / (candidate_capacity - item.value)
        required_rate = math.log(odds_bound / odds_initial) / item.time_years
        minimum_rate = max(minimum_rate, required_rate)
    starting_rate = max(0.7, minimum_rate + 1e-4)
    if starting_rate >= 5.0:
        raise ValueError("Las cotas requieren una tasa r fuera del intervalo permitido.")

    def objective(vector: np.ndarray) -> float:
        parameters = _parameters(vector, initial, None if free_capacity else candidate_capacity)
        residuals = [
            item.value - float(analytical_solution(item.time_years, parameters))
            for item in point_items
        ]
        return 0.5 * float(np.dot(residuals, residuals))

    constraints = []
    for item in bound_items:
        def lower_bound_constraint(vector: np.ndarray, observation=item) -> float:
            parameters = _parameters(vector, initial, None if free_capacity else candidate_capacity)
            return float(analytical_solution(observation.time_years, parameters)) - observation.value
        constraints.append({"type": "ineq", "fun": lower_bound_constraint})

    if free_capacity:
        initial_vector = np.asarray([starting_rate, starting_capacity])
        bounds = [(1e-8, 5.0), (capacity_floor, maximum_capacity)]
    else:
        initial_vector = np.asarray([starting_rate])
        bounds = [(1e-8, 5.0)]

    optimized = minimize(
        objective,
        initial_vector,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"ftol": 1e-12, "maxiter": 20_000},
    )
    if not optimized.success:
        raise RuntimeError(f"No convergió el ajuste {label}: {optimized.message}")

    parameters = _parameters(
        np.asarray(optimized.x, dtype=np.float64),
        initial,
        None if free_capacity else candidate_capacity,
    )
    predictions = {
        item.observation_id: float(analytical_solution(item.time_years, parameters))
        for item in ordered
    }
    residuals = {
        item.observation_id: item.value - predictions[item.observation_id]
        for item in point_items
    }
    point_errors = np.asarray(list(residuals.values()), dtype=np.float64)
    observed_points = np.asarray([item.value for item in point_items], dtype=np.float64)
    rmse = float(np.sqrt(np.mean(point_errors**2)))
    total = float(np.sum((observed_points - observed_points.mean()) ** 2))
    r_squared = float(1.0 - np.sum(point_errors**2) / total) if total > 0 else float("nan")
    violations = {
        item.observation_id: max(item.value - predictions[item.observation_id], 0.0)
        for item in bound_items
    }
    return FitResult(
        label=label,
        parameters=parameters,
        capacity_mode="libre" if free_capacity else "fija",
        point_count=len(point_items),
        lower_bound_count=len(bound_items),
        rmse_millions=rmse,
        r_squared=r_squared,
        predictions=predictions,
        residuals=residuals,
        lower_bound_violations=violations,
        optimizer_cost=float(optimized.fun),
    )
