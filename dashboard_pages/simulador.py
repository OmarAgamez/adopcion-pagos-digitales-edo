"""Simulador mensual del escenario hipotético usando el modelo central existente."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from adopcion_pagos.model import LogisticParameters, analytical_solution, inflection_time, logistic_rhs
from adopcion_pagos.simulation import load_scenarios, simulate
from dashboard_pages.common import PROJECT_ROOT, configure_axes, decimal, page_intro


DEFAULTS = {
    "sim_k": 10_000,
    "sim_n0": 500,
    "sim_r": 0.35,
    "sim_duration": 24,
    "sim_query_time": 12,
}


def _clamp_initial_population() -> None:
    capacity = int(st.session_state.get("sim_k", DEFAULTS["sim_k"]))
    initial = int(st.session_state.get("sim_n0", DEFAULTS["sim_n0"]))
    if initial >= capacity:
        st.session_state["sim_n0"] = max(1, int(capacity * 0.05))


def _clamp_query_time() -> None:
    duration = int(st.session_state.get("sim_duration", DEFAULTS["sim_duration"]))
    query_time = int(st.session_state.get("sim_query_time", DEFAULTS["sim_query_time"]))
    if query_time > duration:
        st.session_state["sim_query_time"] = duration


for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value)

page_intro(
    "Simulación hipotética · unidades mensuales",
    "Simulador logístico",
    "Ajusta los controles para observar cómo cambian la solución analítica y la integración numérica. "
    "Estos valores son didácticos y no provienen de un ajuste de datos de Nequi.",
)

scenario_file = PROJECT_ROOT / "data" / "escenarios_didacticos.csv"
reference = next(item for item in load_scenarios(scenario_file) if item.name == "moderado")

button_area, note_area = st.columns([1, 3])
if button_area.button("Restablecer valores", type="secondary", width="stretch"):
    for key, value in DEFAULTS.items():
        st.session_state[key] = value
    st.rerun()
note_area.caption("El escenario de referencia usa los parámetros moderados guardados en el CSV didáctico.")

with st.container(border=True):
    first_row = st.columns(2)
    capacity = first_row[0].slider(
        "Capacidad K (personas)",
        min_value=1_000,
        max_value=100_000,
        step=500,
        key="sim_k",
        on_change=_clamp_initial_population,
        help="Asíntota matemática del escenario; no es una estimación de mercado.",
    )
    initial = first_row[1].slider(
        "Población inicial N₀ (personas)",
        min_value=1,
        max_value=int(capacity) - 1,
        step=1,
        key="sim_n0",
        help="Se mantiene estrictamente menor que K.",
    )
    second_row = st.columns(2)
    rate = second_row[0].slider(
        "Tasa de crecimiento r (mes⁻¹)",
        min_value=0.01,
        max_value=1.50,
        step=0.01,
        key="sim_r",
    )
    duration = second_row[1].slider(
        "Horizonte de simulación (meses)",
        min_value=1,
        max_value=60,
        step=1,
        key="sim_duration",
        on_change=_clamp_query_time,
    )
    query_time = st.slider(
        "Mes para consultar N(t)",
        min_value=0,
        max_value=int(duration),
        step=1,
        key="sim_query_time",
    )

if not (0 < initial < capacity):
    st.error("Los parámetros deben cumplir 0 < N₀ < K.")
    st.stop()

parameters = LogisticParameters(
    capacity=float(capacity),
    initial_adopters=float(initial),
    growth_rate=float(rate),
)
result = simulate(parameters, duration_months=float(duration), points=duration * 10 + 1)
adoption_at_time = float(analytical_solution(float(query_time), parameters))
instantaneous_rate = float(logistic_rhs(float(query_time), adoption_at_time, parameters))
inflection = inflection_time(parameters)

metric_columns = st.columns(4)
metric_columns[0].metric(
    f"N({query_time})", f"{decimal(adoption_at_time, 1)} personas"
)
metric_columns[1].metric(
    "Tasa instantánea",
    f"{decimal(instantaneous_rate, 1)} personas/mes",
)
metric_columns[2].metric(
    "Punto de inflexión",
    f"{decimal(inflection, 1)} meses",
    help="Tiempo medido desde N₀ hasta N=K/2; puede ser negativo si ya ocurrió.",
)
metric_columns[3].metric(
    "Máximo error analítico–RK45",
    f"{decimal(float(np.max(result.absolute_error)), 8)} personas",
)

if inflection < 0:
    st.caption(
        f"El punto de inflexión quedó {decimal(abs(inflection), 2)} meses antes del inicio, "
        "porque la población inicial ya supera K/2."
    )
else:
    st.caption(
        f"En el punto de inflexión, N = K/2 = {decimal(capacity / 2, 1)} personas "
        "y la tasa de crecimiento es máxima."
    )

show_reference = st.checkbox("Comparar con el escenario moderado de referencia", value=True)
figure, axis = plt.subplots(figsize=(10.5, 5.3))
axis.plot(
    result.time_months,
    result.adoption_analytic,
    color="#087E8B",
    linewidth=2.8,
    label="Solución analítica",
)
axis.plot(
    result.time_months,
    result.adoption_numeric,
    color="#17324D",
    linewidth=1.6,
    linestyle="--",
    label="solve_ivp · RK45",
)
axis.scatter(
    [query_time],
    [adoption_at_time],
    color="#E08A42",
    edgecolor="white",
    linewidth=0.9,
    s=80,
    zorder=5,
    label=f"Consulta en t={query_time} meses",
)
if show_reference:
    reference_times = np.linspace(0.0, duration, duration * 10 + 1)
    reference_values = analytical_solution(reference_times, reference.parameters)
    axis.plot(
        reference_times,
        reference_values,
        color="#8A6BBE",
        linewidth=1.8,
        linestyle=":",
        label="Referencia moderada (parámetros CSV)",
    )
axis.set_xlabel("Tiempo (meses)")
axis.set_ylabel("Adoptantes hipotéticos (personas)")
axis.set_title("Curva logística: escenario hipotético")
axis.legend(frameon=False, ncol=2)
configure_axes(axis)
figure.tight_layout()
st.pyplot(figure, width="stretch")
plt.close(figure)

with st.expander("Lectura matemática de la simulación"):
    st.latex(r"\frac{dN}{dt}=rN\left(1-\frac{N}{K}\right)")
    st.write(
        "Para 0 < N < K y r > 0, la solución crece, se aproxima a K y cambia más rápido "
        "cuando N=K/2. La línea RK45 integra la misma ecuación diferencial; su coincidencia "
        "con la solución cerrada verifica la implementación numérica para estos parámetros."
    )
