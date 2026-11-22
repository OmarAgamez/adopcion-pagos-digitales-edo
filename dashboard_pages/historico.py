"""Visualización separada de la reproducción original y el ajuste integrado."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from adopcion_pagos.data import select_model_series
from adopcion_pagos.dashboard_data import parameters_from_fit_row
from adopcion_pagos.model import analytical_solution, inflection_time
from dashboard_pages.common import (
    configure_axes,
    dashboard_tables,
    decimal,
    integrated_observations,
    original_observations,
    page_intro,
)


tables = dashboard_tables()
page_intro(
    "Serie histórica · métodos presentados por separado",
    "Análisis histórico de Nequi",
    "Selecciona una metodología para visualizar únicamente su conjunto de observaciones, "
    "sus parámetros y sus métricas. Las proyecciones son condicionadas a la ecuación logística.",
)

method = st.radio(
    "Metodología",
    ["Reproducción histórica de Omar", "Análisis integrado con cotas"],
    horizontal=True,
    key="historical_method",
)

if method == "Reproducción histórica de Omar":
    fits = tables["original_fits"]
    observations = original_observations()
    integrated = False
    with st.container(border=True):
        st.warning(
            "Reproducción fiel del CSV histórico: sus ocho valores se ajustaron como puntos. "
            "Esto incluye la cifra aproximada de 2022, la cota de 2023 y los valores originales "
            "de 21,4 M (2024) y 27,4 M (2025). No es el ajuste académico integrado."
        )
    fit_labels = [row["escenario"] for row in fits]
    fit_label = st.selectbox("Escenario de capacidad", fit_labels, key="historical_original_fit")
    selected_fit = next(row for row in fits if row["escenario"] == fit_label)
    years = np.asarray([int(row["anio"]) for row in observations], dtype=float)
    values = np.asarray([float(row["usuarios_millones"]) for row in observations], dtype=float)
    kinds = [row["tipo_dato"] for row in observations]
    fit_end = 2025.0
    rmse = float(selected_fit["RMSE_millones"])
    r_squared = float(selected_fit["R2_in_sample"])
    point_count = int(selected_fit["n_observaciones"])
    bound_count = 0
else:
    fits = tables["primary_fits"]
    series = select_model_series(integrated_observations())
    integrated = True
    with st.container(border=True):
        st.info(
            "Ajuste integrado 2018–2024: seis observaciones puntuales y una restricción "
            "unilateral N(4) ≥ 14 M. Las cuentas publicadas para 2025 se reservan para "
            "sensibilidad por la diferencia de definición y la migración desde A la Mano."
        )
    fit_labels = [row["escenario"] for row in fits]
    fit_label = st.selectbox("Escenario de capacidad", fit_labels, key="historical_integrated_fit")
    selected_fit = next(row for row in fits if row["escenario"] == fit_label)
    years = np.asarray([float(item.year) for item in series], dtype=float)
    values = np.asarray([item.value for item in series], dtype=float)
    kinds = [item.observation_type for item in series]
    fit_end = 2024.0
    rmse = float(selected_fit["RMSE_puntos_millones"])
    r_squared = float(selected_fit["R2_puntos_in_sample"])
    point_count = int(selected_fit["puntos_usados_en_metricas"])
    bound_count = int(selected_fit["cotas_inferiores"])

parameters = parameters_from_fit_row(selected_fit)
predicted_2028 = float(analytical_solution(10.0, parameters))
inflection_year = 2018.0 + inflection_time(parameters)

metrics = st.columns(5)
metrics[0].metric("K del escenario", f"{decimal(parameters.capacity, 3)} M")
metrics[1].metric("r ajustada", f"{decimal(parameters.growth_rate, 4)} año⁻¹")
metrics[2].metric("RMSE", f"{decimal(rmse, 3)} M")
metrics[3].metric("R² in-sample", decimal(r_squared, 4))
metrics[4].metric("Puntos / cotas", f"{point_count} / {bound_count}")

st.caption(
    f"Punto de inflexión modelado: año {decimal(inflection_year, 2)} · "
    f"proyección condicionada para 2028: {decimal(predicted_2028, 2)} M."
)

figure, axis = plt.subplots(figsize=(11, 5.7))
model_years = np.linspace(2018.0, 2030.0, 361)
model_values = analytical_solution(model_years - 2018.0, parameters)
historical_mask = model_years <= fit_end
future_mask = model_years >= fit_end
axis.plot(
    model_years[historical_mask],
    model_values[historical_mask],
    color="#087E8B",
    linewidth=2.7,
    label="Ajuste dentro del periodo usado",
)
axis.plot(
    model_years[future_mask],
    model_values[future_mask],
    color="#087E8B",
    linewidth=2.3,
    linestyle="--",
    label="Proyección condicionada al modelo",
)

marker_labels = {
    "exacto": ("o", "Conteo exacto publicado"),
    "exacta": ("o", "Conteo exacto publicado"),
    "redondeada": ("s", "Cifra redondeada"),
    "aproximado": ("D", "Aproximación histórica"),
    "aproximada": ("D", "Aproximación histórica"),
    "cota_inferior": ("v", "Cota inferior reportada"),
}
seen_labels: set[str] = set()
for kind in sorted(set(kinds)):
    marker, label = marker_labels.get(kind, ("o", kind.replace("_", " ").capitalize()))
    if not integrated and kind == "cota_inferior":
        label = "Cota tratada como punto en la reproducción de Omar"
    indices = [index for index, item_kind in enumerate(kinds) if item_kind == kind]
    axis.scatter(
        years[indices],
        values[indices],
        marker=marker,
        s=70,
        color="#172F46" if kind not in {"cota_inferior", "aproximado", "aproximada"} else "#D47B38",
        edgecolor="white",
        linewidth=0.8,
        zorder=4,
        label=label if label not in seen_labels else None,
    )
    seen_labels.add(label)

if integrated:
    account_2025 = next(
        item
        for item in integrated_observations()
        if item.year == 2025 and item.metric == "cuentas en Nequi"
    )
    axis.scatter(
        [account_2025.year],
        [account_2025.value],
        marker="*",
        s=145,
        color="#B34842",
        edgecolor="white",
        linewidth=0.8,
        zorder=5,
        label=f"2025 · {decimal(account_2025.value, 1)} M cuentas (solo contexto)",
    )
    axis.axvline(2024.5, color="#8B9BA5", linestyle=":", linewidth=1.2)
else:
    axis.axvline(2025.5, color="#8B9BA5", linestyle=":", linewidth=1.2)
axis.set_xlim(2018, 2030)
axis.set_xticks(np.arange(2018, 2031, 1))
axis.set_xlabel("Año")
axis.set_ylabel("Base reportada (millones)")
axis.set_title("Observaciones y curva logística")
axis.legend(frameon=False, ncol=2)
configure_axes(axis)
figure.tight_layout()
st.pyplot(figure, width="stretch")
plt.close(figure)

st.subheader("Resultados de la metodología seleccionada")
if integrated:
    display_rows = [
        {
            "Escenario": row["escenario"],
            "K (M)": decimal(float(row["K_millones"]), 3),
            "r (año⁻¹)": decimal(float(row["r_por_anio"]), 5),
            "Puntos": row["puntos_usados_en_metricas"],
            "Cotas": row["cotas_inferiores"],
            "RMSE en puntos (M)": decimal(float(row["RMSE_puntos_millones"]), 4),
            "R² en puntos": decimal(float(row["R2_puntos_in_sample"]), 5),
        }
        for row in fits
    ]
else:
    display_rows = [
        {
            "Escenario": row["escenario"],
            "K (M)": decimal(float(row["K_millones"]), 3),
            "r (año⁻¹)": decimal(float(row["r_por_anio"]), 5),
            "Puntos": row["n_observaciones"],
            "RMSE (M)": decimal(float(row["RMSE_millones"]), 4),
            "R² in-sample": decimal(float(row["R2_in_sample"]), 5),
        }
        for row in fits
    ]
st.dataframe(display_rows, hide_index=True, width="stretch")

with st.expander("Cómo leer los resultados"):
    if integrated:
        st.write(
            "El RMSE y el R² se calculan solo sobre los puntos incluidos. La cota inferior se "
            "evalúa como desigualdad y no aporta un residuo simétrico ni entra en esas métricas. "
            "El dato de 2025 no participa en este ajuste."
        )
    else:
        st.write(
            "Esta vista reproduce el supuesto de ajuste original. La etiqueta de cota recuerda "
            "que 2023 se describía como un mínimo, aunque la reproducción histórica lo ajusta "
            "como valor puntual. Su RMSE y R² pertenecen únicamente a esta reproducción."
        )
    st.write(
        "La línea discontinua es una extrapolación matemática bajo los parámetros elegidos. "
        "No es una cifra observada ni una predicción validada del mercado."
    )
