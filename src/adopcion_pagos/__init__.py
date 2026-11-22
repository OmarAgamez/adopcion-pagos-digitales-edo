"""Modelo logístico hipotético para adopción de pagos digitales."""

from .model import LogisticParameters, analytical_solution, logistic_rhs
from .simulation import Scenario, SimulationResult, load_scenarios, simulate

__all__ = [
    "LogisticParameters",
    "Scenario",
    "SimulationResult",
    "analytical_solution",
    "load_scenarios",
    "logistic_rhs",
    "simulate",
]
