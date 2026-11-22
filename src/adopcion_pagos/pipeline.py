"""Pipeline reproducible para ajuste, validación, sensibilidad y figuras."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

import numpy as np
from scipy.optimize import curve_fit

from .data import HistoricObservation, load_observations, select_model_series
from .fit import FitResult, fit_logistic
from .model import LogisticParameters, analytical_solution, inflection_time, time_to_fraction
from .plotting import (
    plot_didactic_scenarios,
    plot_numerical_comparison,
    plot_parameter_sensitivity,
    plot_primary_fit,
    plot_residuals,
    plot_sensitivity_including_2025,
)
from .simulation import load_scenarios, simulate


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _r_squared(observed: np.ndarray, predicted: np.ndarray) -> float:
    ss_res = float(np.sum((observed - predicted) ** 2))
    ss_total = float(np.sum((observed - observed.mean()) ** 2))
    return 1.0 - ss_res / ss_total if ss_total > 0 else float("nan")


def reproduce_original_omar(project_root: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Reproduce curve_fit y las hipótesis puntuales usadas en los scripts originales."""

    raw_path = project_root / "data" / "nequi_usuarios_original.csv"
    with raw_path.open("r", encoding="utf-8-sig", newline="") as handle:
        records = list(csv.DictReader(handle))
    time = np.asarray([float(row["t"]) for row in records], dtype=np.float64)
    values = np.asarray([float(row["usuarios_millones"]) for row in records], dtype=np.float64)
    initial = float(values[0])

    fitted: list[tuple[str, float, float]] = []
    for capacity in (37.1, 32.0):
        def fixed_curve(x: np.ndarray, rate: float) -> np.ndarray:
            return np.asarray(analytical_solution(
                x, LogisticParameters(capacity, initial, rate)
            ))
        (rate,), _ = curve_fit(fixed_curve, time, values, p0=[0.5])
        fitted.append((f"K fijo {capacity:g}", float(rate), capacity))

    def free_curve(x: np.ndarray, rate: float, capacity: float) -> np.ndarray:
        return np.asarray(analytical_solution(
            x, LogisticParameters(capacity, initial, rate)
        ))
    (free_rate, free_capacity), _ = curve_fit(
        free_curve, time, values, p0=[0.5, 30.0],
        bounds=([0.0, float(values.max())], [5.0, 200.0]),
    )
    fitted.append(("K libre", float(free_rate), float(free_capacity)))

    metric_rows: list[dict[str, object]] = []
    residual_rows: list[dict[str, object]] = []
    for label, rate, capacity in fitted:
        params = LogisticParameters(capacity, initial, rate)
        predictions = np.asarray(analytical_solution(time, params))
        residuals = values - predictions
        score = _r_squared(values, predictions)
        row: dict[str, object] = {
            "escenario": label,
            "K_millones": capacity,
            "r_por_anio": rate,
            "N0_millones": initial,
            "n_observaciones": len(values),
            "RMSE_millones": float(np.sqrt(np.mean(residuals**2))),
            "R2_in_sample": score,
            "pred_2026_millones": float(analytical_solution(8.0, params)),
            "pred_2027_millones": float(analytical_solution(9.0, params)),
            "pred_2028_millones": float(analytical_solution(10.0, params)),
            "advertencia": "Reproducción fiel: 2022 cota y 2023 cota se trataron como puntos; 2024=21.4 y 2025=27.4 como puntos.",
        }
        if capacity in (37.1, 32.0):
            training_time, training_values = time[:6], values[:6]
            def holdout_curve(x: np.ndarray, holdout_rate: float) -> np.ndarray:
                return np.asarray(analytical_solution(
                    x, LogisticParameters(capacity, initial, holdout_rate)
                ))
            (holdout_rate,), _ = curve_fit(
                holdout_curve, training_time, training_values, p0=[0.5]
            )
            holdout_params = LogisticParameters(capacity, initial, float(holdout_rate))
            holdout_predictions = np.asarray(analytical_solution(time[6:], holdout_params))
            row.update({
                "r_holdout_hasta_2023": float(holdout_rate),
                "holdout_pred_2024": float(holdout_predictions[0]),
                "holdout_pred_2025": float(holdout_predictions[1]),
                "holdout_residuo_2024": float(values[6] - holdout_predictions[0]),
                "holdout_residuo_2025": float(values[7] - holdout_predictions[1]),
            })
        else:
            row.update({
                "r_holdout_hasta_2023": "",
                "holdout_pred_2024": "",
                "holdout_pred_2025": "",
                "holdout_residuo_2024": "",
                "holdout_residuo_2025": "",
            })
        metric_rows.append(row)
        for record, observed, predicted, residual in zip(records, values, predictions, residuals):
            residual_rows.append({
                "escenario": label,
                "anio": record["anio"],
                "observado_millones": observed,
                "predicho_millones": float(predicted),
                "residuo_millones": float(residual),
                "tipo_original": record["tipo_dato"],
                "nota": "Supuesto puntual del script original, incluso para observaciones no puntuales.",
            })
    return metric_rows, residual_rows


def _fit_rows(fits: list[tuple[str, FitResult]], period: str) -> list[dict[str, object]]:
    rows = []
    for label, fit in fits:
        bound_excess = max(fit.lower_bound_violations.values(), default=0.0)
        if bound_excess < 1e-10:
            bound_excess = 0.0
        rows.append({
            "periodo": period,
            "escenario": label,
            "K_millones": fit.parameters.capacity,
            "K_modo": fit.capacity_mode,
            "r_por_anio": fit.parameters.growth_rate,
            "N0_millones": fit.parameters.initial_adopters,
            "puntos_usados_en_metricas": fit.point_count,
            "cotas_inferiores": fit.lower_bound_count,
            "RMSE_puntos_millones": fit.rmse_millions,
            "R2_puntos_in_sample": fit.r_squared,
            "maximo_incumplimiento_cota_millones": bound_excess,
        })
    return rows


def _fit_scenarios(observations: list[HistoricObservation]) -> list[tuple[str, FitResult]]:
    fits = [
        (f"K = {capacity:g} M (escenario fijo)",
         fit_logistic(observations, capacity=capacity, label=f"K={capacity:g}"))
        for capacity in (32.0, 37.1)
    ]
    fits.append((
        "K libre (diagnóstico)",
        fit_logistic(observations, capacity=None, label="K libre"),
    ))
    return fits


def run_pipeline(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).resolve()
    outputs = root / "outputs"
    figures = outputs / "figures"
    tables = outputs / "tables"
    figures.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)

    observations = load_observations(root / "data" / "nequi_usuarios.csv")
    primary = select_model_series(observations)
    sensitivity = select_model_series(observations, include_2025=True)
    primary_fits = _fit_scenarios(primary)
    sensitivity_fits = _fit_scenarios(sensitivity)

    _write_csv(
        tables / "ajustes_principales.csv",
        ["periodo", "escenario", "K_millones", "K_modo", "r_por_anio", "N0_millones",
         "puntos_usados_en_metricas", "cotas_inferiores", "RMSE_puntos_millones",
         "R2_puntos_in_sample", "maximo_incumplimiento_cota_millones"],
        _fit_rows(primary_fits, "2018-2024"),
    )
    _write_csv(
        tables / "ajustes_sensibilidad_2025.csv",
        ["periodo", "escenario", "K_millones", "K_modo", "r_por_anio", "N0_millones",
         "puntos_usados_en_metricas", "cotas_inferiores", "RMSE_puntos_millones",
         "R2_puntos_in_sample", "maximo_incumplimiento_cota_millones"],
        _fit_rows(sensitivity_fits, "2018-2025; 2025 = cuentas y con migración"),
    )

    residual_rows = []
    for label, fit in primary_fits:
        for item in primary:
            if item.observation_id in fit.residuals:
                residual_rows.append({
                    "escenario": label,
                    "anio": item.year,
                    "id_observacion": item.observation_id,
                    "observado_millones": item.value,
                    "predicho_millones": fit.predictions[item.observation_id],
                    "residuo_millones": fit.residuals[item.observation_id],
                    "tipo_observacion": item.observation_type,
                })
            else:
                residual_rows.append({
                    "escenario": label,
                    "anio": item.year,
                    "id_observacion": item.observation_id,
                    "observado_millones": item.value,
                    "predicho_millones": fit.predictions[item.observation_id],
                    "residuo_millones": "",
                    "tipo_observacion": "cota_inferior; violacion="
                    + str(fit.lower_bound_violations[item.observation_id]),
                })
    _write_csv(
        tables / "residuos_principales.csv",
        ["escenario", "anio", "id_observacion", "observado_millones",
         "predicho_millones", "residuo_millones", "tipo_observacion"],
        residual_rows,
    )

    prediction_rows = []
    forecast_times = np.arange(0.0, 13.0, 1.0)
    for label, fit in primary_fits:
        for time in forecast_times:
            prediction_rows.append({
                "escenario": label,
                "anio": int(2018 + time),
                "t_anios": int(time),
                "prediccion_millones": float(analytical_solution(time, fit.parameters)),
                "clasificacion": "ajuste/historia" if time <= 6 else "proyeccion",
                "K_millones": fit.parameters.capacity,
                "r_por_anio": fit.parameters.growth_rate,
            })
    _write_csv(
        tables / "proyecciones_anuales.csv",
        ["escenario", "anio", "t_anios", "prediccion_millones",
         "clasificacion", "K_millones", "r_por_anio"],
        prediction_rows,
    )

    # Evaluación temporal reservada: parámetros entrenados solo hasta 2023.
    train = [item for item in primary if item.year <= 2023]
    held_out = [item for item in sensitivity if item.year in (2024, 2025)]
    holdout_rows = []
    for capacity in (32.0, 37.1):
        label = f"K = {capacity:g} M (fijo)"
        fit = fit_logistic(train, capacity=capacity, label=label)
        for item in held_out:
            predicted = float(analytical_solution(item.time_years, fit.parameters))
            holdout_rows.append({
                "escenario": label,
                "anio_entrenamiento_hasta": 2023,
                "anio_evaluado": item.year,
                "observado_millones": item.value,
                "metrica_observada": item.metric,
                "predicho_millones": predicted,
                "residuo_observado_menos_predicho": item.value - predicted,
                "comparabilidad": (
                    "Comparable en definición general de usuarios totales reportados"
                    if item.year == 2024 else
                    "No plenamente comparable: cuentas en 2025, incorporación de A la Mano y cambio de definición"
                ),
            })
    _write_csv(
        tables / "validacion_holdout.csv",
        ["escenario", "anio_entrenamiento_hasta", "anio_evaluado",
         "observado_millones", "metrica_observada", "predicho_millones",
         "residuo_observado_menos_predicho", "comparabilidad"],
        holdout_rows,
    )

    original_rows, original_residuals = reproduce_original_omar(root)
    original_columns = list(original_rows[0])
    _write_csv(tables / "reproduccion_omar.csv", original_columns, original_rows)
    _write_csv(
        tables / "reproduccion_omar_residuos.csv",
        ["escenario", "anio", "observado_millones", "predicho_millones",
         "residuo_millones", "tipo_original", "nota"],
        original_residuals,
    )

    # Sensibilidad explícita de K (r se reajusta) y r (K fijo, sin reajuste).
    sensitivity_rows = []
    for capacity in (30.0, 32.0, 37.1, 45.0, 60.0):
        fit = fit_logistic(primary, capacity=capacity, label=f"K={capacity:g}")
        sensitivity_rows.append({
            "tipo_variacion": "K; r reajustado",
            "valor": capacity,
            "unidad": "millones",
            "r_por_anio": fit.parameters.growth_rate,
            "RMSE_puntos_millones": fit.rmse_millions,
            "R2_puntos_in_sample": fit.r_squared,
            "prediccion_2028_millones": float(analytical_solution(10.0, fit.parameters)),
        })
    base_k32 = next(fit for label, fit in primary_fits if label.startswith("K = 32"))
    for multiplier in (0.8, 1.0, 1.2):
        params = LogisticParameters(
            base_k32.parameters.capacity,
            base_k32.parameters.initial_adopters,
            base_k32.parameters.growth_rate * multiplier,
        )
        predictions = np.asarray(analytical_solution(
            np.asarray([item.time_years for item in primary]), params
        ))
        point_values = np.asarray([item.value for item in primary
                                   if item.observation_type != "cota_inferior"])
        point_predictions = np.asarray([
            float(analytical_solution(item.time_years, params))
            for item in primary if item.observation_type != "cota_inferior"
        ])
        sensitivity_rows.append({
            "tipo_variacion": "r; K fijo y sin reajuste",
            "valor": multiplier,
            "unidad": "multiplicador de r ajustada con K=32",
            "r_por_anio": params.growth_rate,
            "RMSE_puntos_millones": float(np.sqrt(np.mean((point_values - point_predictions)**2))),
            "R2_puntos_in_sample": _r_squared(point_values, point_predictions),
            "prediccion_2028_millones": float(analytical_solution(10.0, params)),
        })
    _write_csv(
        tables / "sensibilidad_parametros.csv",
        ["tipo_variacion", "valor", "unidad", "r_por_anio",
         "RMSE_puntos_millones", "R2_puntos_in_sample",
         "prediccion_2028_millones"],
        sensitivity_rows,
    )

    characteristic_rows = []
    for period, fits in (("2018-2024", primary_fits), ("incluye 2025", sensitivity_fits)):
        for label, fit in fits:
            parameters = fit.parameters
            t_inflection = inflection_time(parameters)
            characteristic_rows.append({
                "periodo": period,
                "escenario": label,
                "K_millones": parameters.capacity,
                "r_por_anio": parameters.growth_rate,
                "N0_millones": parameters.initial_adopters,
                "t_inflexion_desde_2018_anios": t_inflection,
                "anio_inflexion_modelado": 2018.0 + t_inflection,
                "N_inflexion_millones": parameters.capacity / 2.0,
                "t_90_por_ciento_K_desde_2018_anios": time_to_fraction(parameters, 0.9),
                "tasa_maxima_millones_por_anio": parameters.growth_rate * parameters.capacity / 4.0,
            })
    _write_csv(
        tables / "tiempos_caracteristicos.csv",
        ["periodo", "escenario", "K_millones", "r_por_anio", "N0_millones",
         "t_inflexion_desde_2018_anios", "anio_inflexion_modelado",
         "N_inflexion_millones", "t_90_por_ciento_K_desde_2018_anios",
         "tasa_maxima_millones_por_anio"],
        characteristic_rows,
    )

    # Comparación numérica del caso didáctico moderado.
    scenarios = load_scenarios(root / "data" / "escenarios_didacticos.csv")
    moderate = next(item for item in scenarios if item.name == "moderado")
    numeric = simulate(moderate.parameters, moderate.duration_months, points=241)
    _write_csv(
        tables / "comparacion_analitica_numerica.csv",
        ["t_meses", "analitica_personas", "solve_ivp_personas",
         "tasa_numerica_personas_por_mes", "error_absoluto_personas"],
        [{
            "t_meses": float(t),
            "analitica_personas": float(a),
            "solve_ivp_personas": float(n),
            "tasa_numerica_personas_por_mes": float(rate),
            "error_absoluto_personas": float(error),
        } for t, a, n, rate, error in zip(
            numeric.time_months, numeric.adoption_analytic,
            numeric.adoption_numeric, numeric.adoption_rate, numeric.absolute_error
        )],
    )
    didactic_rows = []
    for scenario in scenarios:
        for month in (0, 6, 12, 18, 24):
            didactic_rows.append({
                "escenario": scenario.name,
                "mes": month,
                "capacidad_personas": scenario.parameters.capacity,
                "N0_personas": scenario.parameters.initial_adopters,
                "r_por_mes": scenario.parameters.growth_rate,
                "adopcion_analitica_personas": float(analytical_solution(month, scenario.parameters)),
                "descripcion": scenario.description,
                "estatus": "hipotético; no son datos de Nequi",
            })
    _write_csv(
        tables / "escenarios_didacticos.csv",
        ["escenario", "mes", "capacidad_personas", "N0_personas", "r_por_mes",
         "adopcion_analitica_personas", "descripcion", "estatus"],
        didactic_rows,
    )

    plot_primary_fit(primary, primary_fits, figures / "ajuste_nequi_principal.png")
    plot_residuals(primary, primary_fits, figures / "residuos_nequi_principal.png")
    k_fits = [
        (capacity, fit_logistic(primary, capacity=capacity, label=f"K={capacity:g}"))
        for capacity in (30.0, 32.0, 37.1, 45.0, 60.0)
    ]
    plot_parameter_sensitivity(primary, base_k32, k_fits,
                               figures / "sensibilidad_parametros_nequi.png")
    plot_sensitivity_including_2025(
        observations, primary_fits, sensitivity_fits, figures / "sensibilidad_incluye_2025.png"
    )
    plot_didactic_scenarios(scenarios, figures / "escenarios_didacticos.png")
    plot_numerical_comparison(numeric, figures / "comparacion_analitica_numerica.png")

    return {
        "primary_fits": primary_fits,
        "sensitivity_fits": sensitivity_fits,
        "original_rows": original_rows,
        "numeric_max_error": float(np.max(numeric.absolute_error)),
        "output_root": outputs,
    }


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    result = run_pipeline(project_root)
    print("Ajustes principales (datos 2018-2024):")
    for label, fit in result["primary_fits"]:
        print(
            f"  {label}: r={fit.parameters.growth_rate:.6f}/año, "
            f"K={fit.parameters.capacity:.6f} M, "
            f"RMSE={fit.rmse_millions:.6f} M, R2={fit.r_squared:.6f}"
        )
    print("Sensibilidad incluyendo cuentas 2025:")
    for label, fit in result["sensitivity_fits"]:
        print(
            f"  {label}: r={fit.parameters.growth_rate:.6f}/año, "
            f"K={fit.parameters.capacity:.6f} M, "
            f"RMSE={fit.rmse_millions:.6f} M, R2={fit.r_squared:.6f}"
        )
    print(f"Error máximo analítico-numérico del caso didáctico: {result['numeric_max_error']:.3e}")
    print(f"Resultados reproducibles: {result['output_root']}")


if __name__ == "__main__":
    main()
