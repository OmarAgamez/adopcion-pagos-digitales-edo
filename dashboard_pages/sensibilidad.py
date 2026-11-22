"""Exploración de parámetros y sensibilidad separada al dato de 2025."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from adopcion_pagos.dashboard_data import parameters_from_fit_row
from adopcion_pagos.model import LogisticParameters, analytical_solution, inflection_time
from dashboard_pages.common import (
    configure_axes,
    dashboard_tables,
    decimal,
    integrated_observations,
    page_intro,
)


tables = dashboard_tables()
page_intro(
    "Exploración de escenarios · no una estimación del techo de mercado",
    "Sensibilidad de la curva",
    "Compara el escenario integrado de K=32 M con los valores que elijas para K y r. "
    "Después revisa, en un bloque separado, qué cambia al agregar el dato de cuentas de 2025.",
)

base_row = next(
    row for row in tables["primary_fits"] if row["escenario"] == "K = 32 M (escenario fijo)"
)
base_parameters = parameters_from_fit_row(base_row)
st.subheader("Explorar K y r")
st.caption(
    "Las dos curvas parten de la misma condición inicial. La base fija K=32 M y r ajustada "
    "para 2018–2024; el escenario explorado cambia K y r sin reajustarlos con los datos."
)

if "sensitivity_k" not in st.session_state:
    st.session_state["sensitivity_k"] = 32.0
if "sensitivity_r" not in st.session_state:
    st.session_state["sensitivity_r"] = base_parameters.growth_rate

controls = st.columns(2)
capacity = controls[0].slider(
    "Capacidad K (millones)",
    min_value=23.0,
    max_value=60.0,
    step=0.5,
    key="sensitivity_k",
    help="K es una capacidad matemática del escenario, no una cifra observada.",
)
rate = controls[1].slider(
    "Tasa r (año⁻¹)",
    min_value=0.20,
    max_value=1.50,
    step=0.01,
    key="sensitivity_r",
)
explored_parameters = LogisticParameters(
    capacity=capacity,
    initial_adopters=base_parameters.initial_adopters,
    growth_rate=rate,
)

years = np.linspace(2018.0, 2032.0, 421)
base_curve = analytical_solution(years - 2018.0, base_parameters)
explored_curve = analytical_solution(years - 2018.0, explored_parameters)
figure, axis = plt.subplots(figsize=(10.5, 5.2))
axis.plot(
    years,
    base_curve,
    color="#17324D",
    linewidth=2.6,
    label=f"Base K=32 M, r={decimal(base_parameters.growth_rate, 3)} año⁻¹",
)
axis.plot(
    years,
    explored_curve,
    color="#087E8B",
    linewidth=2.6,
    linestyle="--",
    label=f"Explorado K={decimal(capacity, 1)} M, r={decimal(rate, 2)} año⁻¹",
)
axis.axvline(2024, color="#8B9BA5", linestyle=":", linewidth=1.2, label="Fin del ajuste principal")
axis.set_xlim(2018, 2032)
axis.set_xticks(np.arange(2018, 2033, 2))
axis.set_xlabel("Año")
axis.set_ylabel("Base modelada (millones)")
axis.set_title("Efecto de cambiar capacidad y tasa")
axis.legend(frameon=False)
configure_axes(axis)
figure.tight_layout()
st.pyplot(figure, width="stretch")
plt.close(figure)

base_inflection = 2018 + inflection_time(base_parameters)
explored_inflection = 2018 + inflection_time(explored_parameters)
metric_columns = st.columns(4)
metric_columns[0].metric("Base: inflexión modelada", decimal(base_inflection, 2))
metric_columns[1].metric(
    "Explorado: inflexión modelada", decimal(explored_inflection, 2)
)
metric_columns[2].metric(
    "Explorado: N(2028)",
    f"{decimal(float(analytical_solution(10.0, explored_parameters)), 2)} M",
)
metric_columns[3].metric("Nivel de inflexión", f"{decimal(capacity / 2, 2)} M")
st.caption(
    "Al variar r cambia la rapidez de crecimiento; al variar K cambia el nivel de saturación "
    "matemática. El punto de inflexión ocurre en N=K/2. Estas curvas no reajustan el modelo."
)

st.divider()
st.subheader("Sensibilidad integrada al incorporar 2025")
st.warning(
    "El valor de 2025 corresponde a cuentas en Nequi; 2023–2024 usa usuarios totales. "
    "Además, Grupo Cibest reporta que se incorporaron más de 3,2 M de antiguos clientes de "
    "A la Mano durante 2025. La comparación es exploratoria y no corrige ni resta esa migración."
)

main_rows = tables["primary_fits"]
sensitivity_rows = tables["sensitivity_2025"]
by_scenario_main = {row["escenario"]: row for row in main_rows}
by_scenario_2025 = {row["escenario"]: row for row in sensitivity_rows}
comparison_rows = []
for scenario_name in by_scenario_main:
    before = by_scenario_main[scenario_name]
    after = by_scenario_2025.get(scenario_name)
    if after is None:
        continue
    comparison_rows.append(
        {
            "Escenario": scenario_name,
            "K 2018–2024 (M)": decimal(float(before["K_millones"]), 3),
            "K con 2025 (M)": decimal(float(after["K_millones"]), 3),
            "r 2018–2024 (año⁻¹)": decimal(float(before["r_por_anio"]), 4),
            "r con 2025 (año⁻¹)": decimal(float(after["r_por_anio"]), 4),
            "RMSE principal (M)": decimal(float(before["RMSE_puntos_millones"]), 3),
            "RMSE con 2025 (M)": decimal(float(after["RMSE_puntos_millones"]), 3),
            "Puntos": f"{before['puntos_usados_en_metricas']} → {after['puntos_usados_en_metricas']}",
            "Cotas": f"{before['cotas_inferiores']} → {after['cotas_inferiores']}",
        }
    )
st.dataframe(comparison_rows, hide_index=True, width="stretch")

free_main = next(row for row in main_rows if row["K_modo"] == "libre")
free_with_2025 = next(row for row in sensitivity_rows if row["K_modo"] == "libre")
parameters_main = parameters_from_fit_row(free_main)
parameters_with_2025 = parameters_from_fit_row(free_with_2025)
history = integrated_observations()
base_series = [item for item in history if item.include_primary and item.year <= 2024]
account_2025 = next(item for item in history if item.year == 2025 and item.metric == "cuentas en Nequi")

years = np.linspace(2018.0, 2030.0, 361)
figure, axis = plt.subplots(figsize=(10.5, 5.1))
axis.plot(
    years,
    analytical_solution(years - 2018.0, parameters_main),
    color="#17324D",
    linewidth=2.4,
    label="K libre diagnóstico · ajuste principal 2018–2024",
)
axis.plot(
    years,
    analytical_solution(years - 2018.0, parameters_with_2025),
    color="#C76750",
    linewidth=2.4,
    linestyle="--",
    label="K libre diagnóstico · sensibilidad con 2025",
)
axis.scatter(
    [item.year for item in base_series],
    [item.value for item in base_series],
    color="#172F46",
    s=42,
    zorder=4,
    label="Observaciones de base 2018–2024",
)
axis.scatter(
    [account_2025.year],
    [account_2025.value],
    marker="*",
    color="#B34842",
    s=150,
    edgecolor="white",
    linewidth=0.8,
    zorder=5,
    label="2025 · cuentas, definición distinta",
)
axis.axvline(2024.5, color="#8B9BA5", linestyle=":", linewidth=1.1)
axis.set_xlim(2018, 2030)
axis.set_xticks(np.arange(2018, 2031, 1))
axis.set_xlabel("Año")
axis.set_ylabel("Base modelada (millones)")
axis.set_title("Diagnóstico de K libre: resultados de dos periodos distintos")
axis.legend(frameon=False, fontsize=8)
configure_axes(axis)
figure.tight_layout()
st.pyplot(figure, width="stretch")
plt.close(figure)

st.caption(
    "La incorporación de 2025 no transforma el dato en una medición homogénea. El ajuste "
    "libre tiende a situar K cerca del último valor incluido; por tanto, no identifica por sí "
    "solo una saturación real."
)
