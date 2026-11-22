"""Verificación numérica y revisión de residuos por metodología."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from adopcion_pagos.simulation import load_scenarios, simulate
from dashboard_pages.common import (
    PROJECT_ROOT,
    configure_axes,
    dashboard_tables,
    decimal,
    page_intro,
)


tables = dashboard_tables()
page_intro(
    "Verificación numérica ≠ validación empírica",
    "Validación matemática",
    "La comparación entre dos soluciones verifica el cálculo numérico para un escenario. "
    "Los residuos históricos describen el ajuste disponible, pero no prueban que la curva "
    "represente el comportamiento futuro.",
)

numeric_tab, residual_tab = st.tabs(["Solución analítica y RK45", "Residuos históricos"])

with numeric_tab:
    scenarios = load_scenarios(PROJECT_ROOT / "data" / "escenarios_didacticos.csv")
    moderate = next(item for item in scenarios if item.name == "moderado")
    computed = simulate(moderate.parameters, moderate.duration_months, points=241)

    saved = tables["numerical_comparison"]
    saved_error = max(float(row["error_absoluto_personas"]) for row in saved)
    recomputed_error = float(np.max(computed.absolute_error))

    st.latex(r"N(t)=\frac{K}{1+\left(\frac{K-N_0}{N_0}\right)e^{-rt}}")
    st.write(
        "La solución cerrada y solve_ivp (RK45) usan los mismos parámetros y unidades "
        "del escenario moderado: personas, meses y tasa mensual."
    )
    metric_columns = st.columns(4)
    metric_columns[0].metric("Puntos de integración", f"{len(computed.time_months)}")
    metric_columns[1].metric("Error máximo recalculado", f"{recomputed_error:.2e} personas")
    metric_columns[2].metric("Error máximo guardado", f"{saved_error:.2e} personas")
    metric_columns[3].metric(
        "Tolerancias RK45",
        "1×10⁻¹²",
        help="Tolerancias usadas por la función simulate del proyecto.",
    )

    figure, axes = plt.subplots(
        2,
        1,
        figsize=(10.5, 7.0),
        sharex=True,
        gridspec_kw={"height_ratios": [2, 1]},
    )
    axes[0].plot(
        computed.time_months,
        computed.adoption_analytic,
        color="#087E8B",
        linewidth=2.5,
        label="Solución analítica",
    )
    axes[0].plot(
        computed.time_months,
        computed.adoption_numeric,
        color="#17324D",
        linestyle="--",
        linewidth=1.8,
        label="RK45 · solve_ivp",
    )
    axes[0].set_ylabel("Adoptantes (personas)")
    axes[0].set_title("Solución cerrada y solución numérica")
    axes[0].legend(frameon=False)
    axes[1].plot(
        computed.time_months,
        computed.absolute_error,
        color="#C76750",
        linewidth=1.5,
    )
    axes[1].set_xlabel("Tiempo (meses)")
    axes[1].set_ylabel("Error absoluto")
    for axis in axes:
        configure_axes(axis)
    figure.tight_layout()
    st.pyplot(figure, width="stretch")
    plt.close(figure)

    with st.expander("Muestra de la tabla numérica versionada"):
        st.dataframe(saved[::24], hide_index=True, width="stretch")

with residual_tab:
    residual_method = st.radio(
        "Conjunto de residuos",
        ["Reproducción de Omar", "Análisis integrado"],
        horizontal=True,
        key="residual_method",
    )
    if residual_method == "Reproducción de Omar":
        rows = tables["original_residuals"]
        fit_rows = tables["original_fits"]
        fit_name_key = "escenario"
        method_fit_key = "escenario"
        rmse_key = "RMSE_millones"
        r2_key = "R2_in_sample"
        count_key = "n_observaciones"
        bound_count = 0
        footnote = (
            "La reproducción trata como puntos los valores que el CSV original registraba "
            "como aproximación o cota; los residuos reflejan ese supuesto histórico."
        )
    else:
        rows = tables["primary_residuals"]
        fit_rows = tables["primary_fits"]
        fit_name_key = "escenario"
        method_fit_key = "escenario"
        rmse_key = "RMSE_puntos_millones"
        r2_key = "R2_puntos_in_sample"
        count_key = "puntos_usados_en_metricas"
        footnote = (
            "La cota inferior de 2022 se valida como desigualdad y no tiene residuo "
            "simétrico. Por eso no aparece como barra ni entra en RMSE o R²."
        )

    labels = [row[fit_name_key] for row in fit_rows]
    fit_label = st.selectbox("Escenario para los indicadores", labels, key="residual_fit")
    selected_fit = next(row for row in fit_rows if row[method_fit_key] == fit_label)
    selected_residuals = [
        row
        for row in rows
        if row["escenario"] == fit_label and row.get("residuo_millones", "") != ""
    ]

    columns = st.columns(4)
    columns[0].metric("RMSE", f"{decimal(float(selected_fit[rmse_key]), 3)} M")
    columns[1].metric("R² in-sample", decimal(float(selected_fit[r2_key]), 4))
    columns[2].metric("Puntos en métricas", str(selected_fit[count_key]))
    columns[3].metric(
        "Cotas inferiores",
        str(selected_fit.get("cotas_inferiores", bound_count)),
    )

    residual_years = np.asarray([int(row["anio"]) for row in selected_residuals])
    residual_values = np.asarray(
        [float(row["residuo_millones"]) for row in selected_residuals]
    )
    figure, axis = plt.subplots(figsize=(10.5, 4.8))
    axis.axhline(0, color="#697E8C", linewidth=1.1)
    axis.vlines(
        residual_years,
        0,
        residual_values,
        color="#087E8B",
        linewidth=2.4,
        alpha=0.8,
    )
    axis.scatter(residual_years, residual_values, color="#087E8B", s=55, zorder=3)
    axis.set_xticks(residual_years)
    axis.set_xlabel("Año")
    axis.set_ylabel("Observado − predicho (M)")
    axis.set_title(f"Residuos: {fit_label}")
    configure_axes(axis)
    figure.tight_layout()
    st.pyplot(figure, width="stretch")
    plt.close(figure)

    st.caption(footnote)
    with st.expander("Ver las filas de residuos usadas"):
        st.dataframe(selected_residuals, hide_index=True, width="stretch")

st.warning(
    "Una diferencia numérica pequeña entre RK45 y la solución analítica no valida los datos "
    "ni la estructura logística. Los ajustes históricos dependen de cifras heterogéneas, "
    "supuestos de K y cambios de definición."
)
