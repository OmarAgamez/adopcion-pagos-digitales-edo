"""Generación de gráficas en español para el informe académico."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from .model import LogisticParameters
from .simulation import Scenario, SimulationResult


def _save_figure(figure: plt.Figure, output_dir: str | Path, name: str) -> None:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    figure.savefig(destination / f"{name}.png", dpi=300, bbox_inches="tight")
    figure.savefig(destination / f"{name}.pdf", bbox_inches="tight")
    plt.close(figure)


def plot_adoption_comparison(
    result: SimulationResult,
    output_dir: str | Path,
) -> None:
    figure, axis = plt.subplots(figsize=(9, 5.5))
    axis.plot(
        result.time_months,
        result.adoption_analytic,
        color="#145DA0",
        linewidth=2.5,
        label="Solución analítica",
    )
    axis.plot(
        result.time_months,
        result.adoption_numeric,
        color="#F28E2B",
        linestyle="--",
        linewidth=1.8,
        label="Integración numérica (solve_ivp)",
    )
    axis.set_title("Adopción acumulada: solución analítica y numérica")
    axis.set_xlabel("Tiempo (meses)")
    axis.set_ylabel("Adoptantes acumulados (personas)")
    axis.grid(True, alpha=0.25)
    axis.legend()
    _save_figure(figure, output_dir, "comparacion_analitica_numerica")


def plot_adoption_rate(
    result: SimulationResult,
    output_dir: str | Path,
) -> None:
    figure, axis = plt.subplots(figsize=(9, 5.5))
    axis.plot(
        result.time_months,
        result.adoption_rate,
        color="#2E8B57",
        linewidth=2.5,
        label="dA/dt = rA(1 − A/K)",
    )
    axis.set_title("Velocidad de adopción")
    axis.set_xlabel("Tiempo (meses)")
    axis.set_ylabel("Nuevos adoptantes por mes (personas/mes)")
    axis.grid(True, alpha=0.25)
    axis.legend()
    _save_figure(figure, output_dir, "velocidad_adopcion")


def plot_scenarios(
    scenarios: Sequence[Scenario],
    results: dict[str, SimulationResult],
    output_dir: str | Path,
) -> None:
    figure, axis = plt.subplots(figsize=(9, 5.5))
    colors = {"lento": "#4E79A7", "moderado": "#F28E2B", "rápido": "#59A14F"}
    for scenario in scenarios:
        result = results[scenario.name]
        axis.plot(
            result.time_months,
            result.adoption_analytic,
            linewidth=2.4,
            color=colors.get(scenario.name.casefold()),
            label=f"{scenario.name.capitalize()} (r={scenario.parameters.growth_rate:g}/mes)",
        )
    axis.set_title("Escenarios hipotéticos de adopción")
    axis.set_xlabel("Tiempo (meses)")
    axis.set_ylabel("Adoptantes acumulados (personas)")
    axis.grid(True, alpha=0.25)
    axis.legend(title="Tasa de crecimiento")
    _save_figure(figure, output_dir, "escenarios_adopcion")


def plot_sensitivity(
    time_months: np.ndarray,
    curves: dict[str, list[tuple[float, np.ndarray]]],
    parameters: LogisticParameters,
    output_dir: str | Path,
) -> None:
    figure, axes = plt.subplots(1, 3, figsize=(15, 6.2), sharey=True)
    definitions = (
        ("r", "Tasa de crecimiento r (mes⁻¹)", parameters.growth_rate, "Variación de r"),
        ("K", "Capacidad K (personas)", parameters.capacity, "Variación de K"),
        ("A0", "Adopción inicial A₀ (personas)", parameters.initial_adopters, "Variación de A₀"),
    )
    palette = plt.get_cmap("viridis")(np.linspace(0.12, 0.9, 5))
    for axis, (key, legend_title, baseline, title) in zip(axes, definitions, strict=True):
        for color, (value, adoption) in zip(palette, curves[key], strict=True):
            emphasized = np.isclose(value, baseline, rtol=1e-9, atol=1e-12)
            axis.plot(
                time_months,
                adoption,
                color=color,
                linewidth=2.8 if emphasized else 1.8,
                linestyle="-" if emphasized else "--",
                label=f"{value:g}",
            )
        axis.set_title(title)
        axis.set_xlabel("Tiempo (meses)")
        axis.grid(True, alpha=0.25)
        axis.legend(
            title=legend_title,
            fontsize=8,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.18),
            ncol=3,
            frameon=False,
        )
    axes[0].set_ylabel("Adoptantes acumulados (personas)")
    figure.suptitle("Análisis de sensibilidad del modelo logístico", fontsize=14)
    figure.tight_layout(rect=(0, 0.16, 1, 0.94))
    _save_figure(figure, output_dir, "analisis_sensibilidad")
