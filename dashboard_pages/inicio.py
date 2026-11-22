"""Página de bienvenida y panorama de resultados sin mezclar ajustes."""

from __future__ import annotations

import streamlit as st

from adopcion_pagos.dashboard_data import parameters_from_fit_row
from adopcion_pagos.model import analytical_solution
from dashboard_pages.common import dashboard_tables, decimal, page_intro


tables = dashboard_tables()
page_intro(
    "Universidad Popular del Cesar · Ecuaciones Diferenciales",
    "¿Cómo crece la adopción de una aplicación?",
    "Exploramos si una ecuación logística puede describir una base reportada de usuarios "
    "a través del tiempo, y usamos un escenario hipotético para explicar cada parámetro.",
)

st.latex(r"\frac{dN}{dt}=rN\left(1-\frac{N}{K}\right)")

st.markdown(
    "La tasa de cambio depende de la población alcanzada y de la distancia matemática "
    "respecto a la capacidad elegida. En este proyecto, los escenarios didácticos y el "
    "estudio histórico son ejercicios distintos."
)

variable_columns = st.columns(3)
variable_content = [
    ("N(t)", "Base acumulada modelada en el tiempo", "Personas en el simulador; millones en el análisis histórico."),
    ("r", "Tasa intrínseca de crecimiento", "Por mes en el ejercicio didáctico; por año en los ajustes históricos."),
    ("K", "Capacidad asintótica del modelo", "Parámetro matemático; los escenarios no demuestran un techo real de mercado."),
]
for column, (symbol, meaning, unit) in zip(variable_columns, variable_content):
    with column, st.container(border=True):
        st.subheader(symbol)
        st.write(meaning)
        st.caption(unit)

st.subheader("Resultados que se presentan por separado")
st.caption(
    "Cada bloque conserva su propio conjunto de datos y procedimiento; sus métricas no se comparan directamente."
)

original = next(row for row in tables["original_fits"] if row["escenario"] == "K fijo 32")
integrated = next(
    row for row in tables["primary_fits"] if row["escenario"] == "K = 32 M (escenario fijo)"
)
left, right = st.columns(2)
with left, st.container(border=True):
    st.markdown("#### Reproducción histórica del método de Omar")
    st.caption("CSV histórico original · 8 observaciones usadas como puntos · 2018–2025.")
    metrics = st.columns(2)
    metrics[0].metric("K del escenario", f"{decimal(float(original['K_millones']), 1)} M")
    metrics[1].metric("Tasa ajustada", f"{decimal(float(original['r_por_anio']), 3)} año⁻¹")
    metrics[0].metric("RMSE", f"{decimal(float(original['RMSE_millones']), 3)} M")
    metrics[1].metric("R² in-sample", decimal(float(original["R2_in_sample"]), 3))
    st.caption(
        "Reproducción de los supuestos originales: los valores de 2022 y 2023 se tratan "
        "como puntos, junto con 21,4 M en 2024 y 27,4 M en 2025."
    )

with right, st.container(border=True):
    st.markdown("#### Análisis integrado")
    st.caption("Datos de base reportada · seis puntos y una cota inferior · 2018–2024.")
    metrics = st.columns(2)
    metrics[0].metric("K del escenario", f"{decimal(float(integrated['K_millones']), 1)} M")
    metrics[1].metric("Tasa ajustada", f"{decimal(float(integrated['r_por_anio']), 3)} año⁻¹")
    metrics[0].metric("RMSE en puntos", f"{decimal(float(integrated['RMSE_puntos_millones']), 3)} M")
    metrics[1].metric("R² in-sample", decimal(float(integrated["R2_puntos_in_sample"]), 3))
    st.caption(
        "2022 se impone como cota inferior (N(4) ≥ 14 M); 2025 queda fuera del ajuste principal."
    )

st.info(
    "El escenario interactivo inicial (K=10.000, N₀=500, r=0,35/mes) es hipotético. "
    "No es una estimación de la adopción real de Nequi."
)

with st.expander("¿Qué puedo explorar en esta demostración?"):
    st.markdown(
        "- Cambiar K, r, N₀ y el horizonte mensual, y ver la curva actualizarse.\n"
        "- Comparar la solución analítica con la integración RK45.\n"
        "- Consultar por separado la reproducción histórica y el ajuste integrado.\n"
        "- Revisar residuos, sensibilidad, datos, fuentes y limitaciones."
    )
