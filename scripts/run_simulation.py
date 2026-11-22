"""Genera tablas y figuras reproducibles del modelo logístico."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from adopcion_pagos.model import analytical_solution
from adopcion_pagos.plotting import (
    plot_adoption_comparison,
    plot_adoption_rate,
    plot_scenarios,
    plot_sensitivity,
)
from adopcion_pagos.simulation import load_scenarios, sensitivity_curves, simulate


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Simula la adopción hipotética de pagos digitales con una EDO logística."
    )
    parser.add_argument(
        "--parameters",
        type=Path,
        default=PROJECT_ROOT / "data" / "parameters.csv",
        help="Ruta al CSV configurable de parámetros y escenarios.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "outputs",
        help="Directorio de salida para tablas y figuras.",
    )
    parser.add_argument(
        "--points",
        type=int,
        default=241,
        help="Cantidad de puntos de evaluación en cada curva (mínimo 2).",
    )
    return parser


def main() -> int:
    arguments = _build_parser().parse_args()
    scenarios = load_scenarios(arguments.parameters)
    duration = scenarios[0].duration_months
    tables_dir = arguments.output_dir / "tables"
    figures_dir = arguments.output_dir / "figures"

    results = {
        scenario.name: simulate(scenario.parameters, duration, arguments.points)
        for scenario in scenarios
    }
    moderate = next(s for s in scenarios if s.name.casefold() == "moderado")
    baseline_result = results[moderate.name]

    comparison_rows = [
        {
            "time_months": time,
            "adopters_analytic_people": analytic,
            "adopters_numeric_people": numeric,
            "adoption_rate_people_per_month": rate,
            "absolute_error_people": error,
        }
        for time, analytic, numeric, rate, error in zip(
            baseline_result.time_months,
            baseline_result.adoption_analytic,
            baseline_result.adoption_numeric,
            baseline_result.adoption_rate,
            baseline_result.absolute_error,
            strict=True,
        )
    ]
    _write_csv(
        tables_dir / "model_comparison.csv",
        [
            "time_months",
            "adopters_analytic_people",
            "adopters_numeric_people",
            "adoption_rate_people_per_month",
            "absolute_error_people",
        ],
        comparison_rows,
    )

    scenario_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    for scenario in scenarios:
        result = results[scenario.name]
        parameters = scenario.parameters
        scenario_rows.extend(
            {
                "scenario": scenario.name,
                "description": scenario.description,
                "time_months": time,
                "capacity_people": parameters.capacity,
                "initial_adopters_people": parameters.initial_adopters,
                "growth_rate_per_month": parameters.growth_rate,
                "adopters_analytic_people": analytic,
                "adopters_numeric_people": numeric,
                "adoption_rate_people_per_month": rate,
                "absolute_error_people": error,
            }
            for time, analytic, numeric, rate, error in zip(
                result.time_months,
                result.adoption_analytic,
                result.adoption_numeric,
                result.adoption_rate,
                result.absolute_error,
                strict=True,
            )
        )
        peak_month = np.log(
            (parameters.capacity - parameters.initial_adopters)
            / parameters.initial_adopters
        ) / parameters.growth_rate
        final_adopters = float(analytical_solution(scenario.duration_months, parameters))
        summary_rows.append(
            {
                "scenario": scenario.name,
                "description": scenario.description,
                "capacity_people": parameters.capacity,
                "initial_adopters_people": parameters.initial_adopters,
                "growth_rate_per_month": parameters.growth_rate,
                "duration_months": scenario.duration_months,
                "adopters_at_end_people": final_adopters,
                "capacity_reached_percent": 100.0 * final_adopters / parameters.capacity,
                "peak_adoption_rate_people_per_month": (
                    parameters.growth_rate * parameters.capacity / 4.0
                ),
                "inflection_month": peak_month,
                "inflection_within_simulation": 0 <= peak_month <= scenario.duration_months,
                "maximum_absolute_error_people": float(np.max(result.absolute_error)),
            }
        )

    _write_csv(
        tables_dir / "scenario_comparison.csv",
        [
            "scenario",
            "description",
            "time_months",
            "capacity_people",
            "initial_adopters_people",
            "growth_rate_per_month",
            "adopters_analytic_people",
            "adopters_numeric_people",
            "adoption_rate_people_per_month",
            "absolute_error_people",
        ],
        scenario_rows,
    )
    _write_csv(
        tables_dir / "summary.csv",
        [
            "scenario",
            "description",
            "capacity_people",
            "initial_adopters_people",
            "growth_rate_per_month",
            "duration_months",
            "adopters_at_end_people",
            "capacity_reached_percent",
            "peak_adoption_rate_people_per_month",
            "inflection_month",
            "inflection_within_simulation",
            "maximum_absolute_error_people",
        ],
        summary_rows,
    )

    times, sensitivity = sensitivity_curves(
        moderate.parameters,
        duration_months=duration,
        points=arguments.points,
    )
    sensitivity_rows: list[dict[str, object]] = []
    sensitivity_labels = {
        "r": "growth_rate_per_month",
        "K": "capacity_people",
        "A0": "initial_adopters_people",
    }
    for parameter_name, curves in sensitivity.items():
        for varied_value, adoption in curves:
            for time, adopters in zip(times, adoption, strict=True):
                sensitivity_rows.append(
                    {
                        "varied_parameter": sensitivity_labels[parameter_name],
                        "varied_value": varied_value,
                        "time_months": time,
                        "adopters_analytic_people": adopters,
                    }
                )
    _write_csv(
        tables_dir / "sensitivity.csv",
        [
            "varied_parameter",
            "varied_value",
            "time_months",
            "adopters_analytic_people",
        ],
        sensitivity_rows,
    )

    plot_adoption_comparison(baseline_result, figures_dir)
    plot_adoption_rate(baseline_result, figures_dir)
    plot_scenarios(scenarios, results, figures_dir)
    plot_sensitivity(times, sensitivity, moderate.parameters, figures_dir)

    print(f"Escenarios simulados: {len(scenarios)} (valores hipotéticos).")
    print(f"Tiempo: 0 a {duration:g} meses; puntos por curva: {arguments.points}.")
    print(
        "Error absoluto máximo analítico-numérico (moderado): "
        f"{np.max(baseline_result.absolute_error):.6g} personas."
    )
    print(f"Tablas CSV: {tables_dir.resolve()}")
    print(f"Figuras PNG y PDF: {figures_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
