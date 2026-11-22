"""Figuras del estudio; todos los cálculos provienen de los módulos centrales."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .data import HistoricObservation
from .fit import FitResult
from .model import LogisticParameters, analytical_solution
from .simulation import Scenario, SimulationResult


def _year_axis(ax: plt.Axes) -> None:
    ax.set_xlabel("Año")
    ax.set_xticks(np.arange(2018, 2031, 2))
    ax.grid(alpha=0.25)


def plot_primary_fit(
    observations: list[HistoricObservation],
    fits: list[tuple[str, FitResult]],
    output: str | Path,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    types = {
        "redondeada": ("o", "Cifras redondeadas"),
        "exacta": ("s", "Conteos publicados"),
        "aproximada": ("D", "Cifras aproximadas"),
        "cota_inferior": ("v", "Cota inferior (mínimo reportado)"),
    }
    seen: set[str] = set()
    for item in observations:
        marker, label = types[item.observation_type]
        ax.scatter(
            item.year, item.value, marker=marker, s=62, color="black",
            facecolors="none" if item.observation_type == "cota_inferior" else "black",
            label=label if label not in seen else None, zorder=4,
        )
        seen.add(label)
        if item.observation_type == "cota_inferior":
            ax.annotate("≥", (item.year, item.value), xytext=(5, 5),
                        textcoords="offset points", fontsize=10)
    dense_time = np.linspace(0.0, 12.0, 500)
    for index, (label, result) in enumerate(fits):
        params = result.parameters
        prediction = np.asarray(analytical_solution(dense_time, params))
        years = 2018 + dense_time
        color = f"C{index}"
        observed_part = years <= 2024
        ax.plot(years[observed_part], prediction[observed_part], color=color,
                linewidth=2, label=label)
        ax.plot(years[~observed_part], prediction[~observed_part], color=color,
                linewidth=2, linestyle="--")
    ax.axvline(2024, color="gray", linestyle=":", linewidth=1.2,
               label="Fin del periodo principal")
    ax.set_ylabel("Base reportada (millones)")
    ax.set_title("Ajuste logístico de la serie reportada de Nequi")
    _year_axis(ax)
    ax.set_xlim(2018, 2030)
    ax.legend(frameon=False, fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_residuals(
    observations: list[HistoricObservation],
    fits: list[tuple[str, FitResult]],
    output: str | Path,
) -> None:
    points = [item for item in observations if item.observation_type != "cota_inferior"]
    x = np.asarray([item.year for item in points], dtype=float)
    fig, ax = plt.subplots(figsize=(10, 5))
    width = 0.75 / max(1, len(fits))
    for index, (label, result) in enumerate(fits):
        values = [result.residuals[item.observation_id] for item in points]
        ax.bar(x + (index - (len(fits) - 1) / 2) * width, values,
               width=width, label=label)
    ax.axhline(0.0, color="black", linewidth=0.9)
    ax.set_xticks(x, [str(item.year) for item in points])
    ax.set_xlabel("Año")
    ax.set_ylabel("Residuo puntual: observado − modelo (millones)")
    ax.set_title("Residuos sobre observaciones puntuales")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_parameter_sensitivity(
    observations: list[HistoricObservation],
    base: FitResult,
    k_fits: list[tuple[float, FitResult]],
    output: str | Path,
) -> None:
    point_items = [item for item in observations if item.observation_type != "cota_inferior"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.3), sharey=True)
    time = np.linspace(0.0, 10.0, 300)
    for capacity, result in k_fits:
        values = analytical_solution(time, result.parameters)
        axes[0].plot(2018 + time, values, label=f"K={capacity:g}; r={result.parameters.growth_rate:.2f}")
    axes[0].scatter([item.year for item in point_items], [item.value for item in point_items],
                    color="black", s=28, zorder=4)
    axes[0].set_title("K fijado; r reajustado")
    axes[0].legend(frameon=False, fontsize=7)

    for multiplier, style in zip((0.8, 1.0, 1.2), (":", "-", "--")):
        parameters = LogisticParameters(
            base.parameters.capacity,
            base.parameters.initial_adopters,
            base.parameters.growth_rate * multiplier,
        )
        axes[1].plot(2018 + time, analytical_solution(time, parameters),
                     linestyle=style, label=f"r × {multiplier:.1f}")
    axes[1].scatter([item.year for item in point_items], [item.value for item in point_items],
                    color="black", s=28, zorder=4)
    axes[1].set_title(f"Sensibilidad de r con K={base.parameters.capacity:g}")
    axes[1].legend(frameon=False, fontsize=8)
    for ax in axes:
        _year_axis(ax)
        ax.set_xlim(2018, 2028)
    axes[0].set_ylabel("Base reportada (millones)")
    fig.suptitle("Sensibilidad estructural de los escenarios logísticos", y=1.02)
    fig.tight_layout()
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_sensitivity_including_2025(
    observations: list[HistoricObservation],
    primary_fits: list[tuple[str, FitResult]],
    sensitivity_fits: list[tuple[str, FitResult]],
    output: str | Path,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.8))
    time = np.linspace(0.0, 9.0, 350)
    for (label, primary), (_, sensitivity) in zip(primary_fits, sensitivity_fits):
        ax.plot(2018 + time, analytical_solution(time, primary.parameters),
                linestyle="--", linewidth=1.8, label=f"{label}: ajuste hasta 2024")
        ax.plot(2018 + time, analytical_solution(time, sensitivity.parameters),
                linestyle="-", linewidth=1.8, label=f"{label}: incluye 2025")

    series = [
        item for item in observations
        if item.model_series == "base_nequi_reportada" and item.include_sensitivity
    ]
    historic = [item for item in series if item.year <= 2024]
    points = [item for item in historic if item.observation_type != "cota_inferior"]
    bounds = [item for item in historic if item.observation_type == "cota_inferior"]
    accounts_2025 = [item for item in series if item.year == 2025]
    ax.scatter([item.year for item in points], [item.value for item in points],
               color="black", s=34, label="Usuarios totales reportados hasta 2024", zorder=4)
    for item in bounds:
        ax.scatter(item.year, item.value, marker="v", facecolors="none",
                   edgecolors="black", s=55,
                   label="Cota inferior (mínimo reportado)", zorder=4)
    for item in accounts_2025:
        ax.scatter(item.year, item.value, marker="*", color="darkred", s=110,
                   label=f"{item.value:g} M cuentas (definición distinta)", zorder=5)
    ax.axvline(2024, color="gray", linestyle=":", linewidth=1)
    ax.set_ylabel("Base reportada (millones)")
    ax.set_title("Sensibilidad al incorporar el dato de cuentas de 2025")
    ax.set_xlim(2018, 2027)
    ax.set_xticks(range(2018, 2028, 1))
    ax.tick_params(axis="x", labelrotation=45)
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_didactic_scenarios(
    scenarios: list[Scenario],
    output: str | Path,
) -> None:
    fig, ax = plt.subplots(figsize=(9, 5.5))
    colors = {"lento": "C0", "moderado": "C1", "rápido": "C2"}
    for item in scenarios:
        time = np.linspace(0.0, item.duration_months, 241)
        values = analytical_solution(time, item.parameters)
        ax.plot(time, values, linewidth=2.2, color=colors.get(item.name, None),
                label=f"{item.name.capitalize()} (r={item.parameters.growth_rate:g}/mes)")
    ax.set_xlabel("Tiempo (meses)")
    ax.set_ylabel("Adoptantes hipotéticos (personas)")
    ax.set_title("Escenario didáctico hipotético: K=10.000, N₀=500")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)


def plot_numerical_comparison(
    result: SimulationResult,
    output: str | Path,
) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True,
                             gridspec_kw={"height_ratios": [2, 1]})
    axes[0].plot(result.time_months, result.adoption_analytic, label="Analítica", linewidth=2)
    axes[0].plot(result.time_months, result.adoption_numeric, "--",
                 label="solve_ivp (RK45)", linewidth=1.6)
    axes[0].set_ylabel("Adoptantes hipotéticos")
    axes[0].set_title("Verificación numérica frente a la solución cerrada")
    axes[0].legend(frameon=False)
    axes[1].plot(result.time_months, result.absolute_error, color="C3")
    axes[1].set_xlabel("Tiempo (meses)")
    axes[1].set_ylabel("Error absoluto")
    for ax in axes:
        ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)
