"""Descripción trazable de datos, ecuación, ajuste y alcance."""

from __future__ import annotations

import streamlit as st

from dashboard_pages.common import (
    comparison_events,
    decimal,
    integrated_observations,
    page_intro,
)


page_intro(
    "Datos con fuente y método documentados",
    "Datos y metodología",
    "Esta vista resume cómo se construyó el análisis y qué significado tienen sus cifras. "
    "Los registros se leen de los CSV versionados; la aplicación no los modifica.",
)

st.subheader("Fuentes y naturaleza de las observaciones")
observations = integrated_observations()
observation_rows = [
    {
        "Año": item.year,
        "Métrica reportada": item.metric,
        "Valor": decimal(item.value, 6),
        "Unidad": item.unit,
        "Tipo": item.observation_type.replace("_", " "),
        "En ajuste principal": "Sí" if item.include_primary else "No",
        "En sensibilidad": "Sí" if item.include_sensitivity else "No",
        "Corte": item.cutoff_precision,
    }
    for item in observations
]
st.dataframe(observation_rows, hide_index=True, width="stretch")

source_records = {}
for item in observations:
    source_records.setdefault(item.source_url, (item.source_title, item.source))
st.markdown("**Fuentes registradas en el repositorio:**")
for url, (title, organization) in source_records.items():
    st.markdown(f"- [{title}]({url}) · {organization}")

st.caption(
    "La serie principal estudia una base reportada, no adopciones nuevas por periodo, descargas "
    "ni transacciones. Los valores de 2018–2021 son redondeados; 2022 es una cota inferior; "
    "2023–2024 son conteos de usuarios totales; 2025 se reporta como cuentas."
)

with st.expander("Evento que afecta la comparabilidad de 2025"):
    events = comparison_events()
    for event in events:
        st.markdown(
            f"**{event['anio']} · {event['evento']}**  \n"
            f"El registro indica {event['valor']} {event['unidad']}. "
            "Se usa como contexto y no se suma ni se resta a la serie."
        )
        st.markdown(f"[Fuente: {event['titulo_fuente']}]({event['url_fuente']})")

st.divider()
st.subheader("Ecuación y solución analítica")
st.latex(r"\frac{dN}{dt}=rN\left(1-\frac{N}{K}\right), \qquad N(0)=N_0")
st.markdown("Separación de variables:")
st.latex(r"\frac{dN}{N\left(1-\frac{N}{K}\right)}=r\,dt")
st.markdown("Integración y aplicación de la condición inicial:")
st.latex(r"\ln\left(\frac{N}{K-N}\right)=rt+\ln\left(\frac{N_0}{K-N_0}\right)")
st.latex(
    r"N(t)=\frac{K}{1+\left(\frac{K-N_0}{N_0}\right)e^{-rt}}"
)

columns = st.columns(3)
columns[0].markdown("**N(t)**  \nBase acumulada que representa el modelo.")
columns[1].markdown("**r**  \nTasa por unidad de tiempo; año⁻¹ o mes⁻¹.")
columns[2].markdown("**K**  \nCapacidad asintótica definida para el escenario.")

st.subheader("Ajuste y restricciones de datos")
st.markdown(
    "- La condición histórica se fija en N₀ = 0,816 millones en t=0 (año 2018).\n"
    "- Para observaciones puntuales se minimizan residuos cuadrados; redondeos y aproximaciones "
    "se conservan como valores publicados, sin afirmar precisión adicional.\n"
    "- Para la observación de 2022, el ajuste impone N(4) ≥ 14 M. La cota no se iguala a una "
    "observación exacta y se evalúa por separado de RMSE y R².\n"
    "- Los K=32 M y K=37,1 M son escenarios heredados para comparación. El ajuste con K libre "
    "es diagnóstico y puede aproximarse al último valor disponible.\n"
    "- Las proyecciones prolongan la ecuación bajo parámetros fijos; no son mediciones ni "
    "predicciones validadas para decisiones de mercado."
)

st.subheader("Alcance y límites")
st.warning(
    "Cuentas, usuarios vinculados, usuarios totales y usuarios activos tienen definiciones "
    "diferentes. La fuente de 2025 reporta cuentas y el cambio de composición por A la Mano "
    "limita la comparación con 2023–2024."
)
st.markdown(
    "- Varios hitos antiguos solo indican el año y no un día de corte común.\n"
    "- El R² in-sample describe el ajuste a los puntos usados; no valida la asíntota ni garantiza "
    "capacidad predictiva.\n"
    "- La prueba de RK45 verifica una implementación numérica contra la solución cerrada, no "
    "la adecuación empírica del modelo.\n"
    "- El ajuste histórico de Omar se muestra como reproducción de su método; el análisis "
    "integrado se presenta como una metodología complementaria."
)
st.caption(
    "La bibliografía completa y las notas metodológicas están en docs/referencias.bib, "
    "docs/fuentes_datos.md y docs/decisiones_metodologicas.md."
)
