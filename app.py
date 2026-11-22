"""Aplicación local de demostración del proyecto de Ecuaciones Diferenciales."""

from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

st.set_page_config(
    page_title="Adopción Nequi · Proyecto EDO",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2.6rem; max-width: 1320px; }
    .eyebrow { color: #0b8586; font-size: 0.76rem; font-weight: 750;
               letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 0.25rem; }
    .app-banner { display: flex; align-items: center; justify-content: space-between;
                  gap: 1rem; border-bottom: 1px solid #dbe6eb; padding: 0.15rem 0 0.8rem;
                  margin-bottom: 1.3rem; color: #476071; font-size: 0.84rem; }
    .app-banner strong { color: #102b43; }
    [data-testid="stMetric"] { background: #ffffff; border: 1px solid #dbe6eb;
                              border-radius: 14px; padding: 0.8rem 1rem; }
    [data-testid="stMetricLabel"] { color: #567080; }
    [data-testid="stSidebar"] { border-right: 1px solid #dbe6eb; }
    .sidebar-brand { background: #102b43; color: #f6fbfd; border-radius: 16px;
                     padding: 1rem; margin: 0.3rem 0 1rem; }
    .sidebar-brand small { color: #9ce8df; letter-spacing: 0.1em; font-weight: 700; }
    .sidebar-brand h3 { color: #ffffff; margin: 0.35rem 0 0.25rem; }
    .sidebar-brand p { color: #d0e1e9; margin: 0; font-size: 0.82rem; }
    div[data-testid="stAlert"] { border-radius: 12px; }
    @media (max-width: 720px) {
      .block-container { padding-left: 1rem; padding-right: 1rem; }
      .app-banner { align-items: flex-start; flex-direction: column; gap: 0.2rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
          <small>PROYECTO ACADÉMICO · EDO</small>
          <h3>Adopción digital</h3>
          <p>Modelo logístico · Caso Nequi Colombia</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Universidad Popular del Cesar")
    st.caption("Ingeniería de Sistemas · Grupo 03")
    st.divider()
    st.caption("Omar David Agamez Pérez")
    st.caption("Santiago Daniel Galviz Silva")
    st.caption("Carlos Eduardo Camelo Montaño")
    st.divider()
    st.caption("Docente: Daniel Meza · 2026-II")

st.markdown(
    '<div class="app-banner"><span><strong>UPC</strong> · Ingeniería de Sistemas · '
    'Ecuaciones Diferenciales</span><span>Grupo 03 · 2026-II</span></div>',
    unsafe_allow_html=True,
)

navigation = st.navigation(
    {
        "Proyecto": [
            st.Page("dashboard_pages/inicio.py", title="Inicio", icon="🏠", default=True),
        ],
        "Explorar el modelo": [
            st.Page("dashboard_pages/simulador.py", title="Simulador", icon="🎛️"),
            st.Page("dashboard_pages/historico.py", title="Análisis histórico", icon="📊"),
            st.Page("dashboard_pages/sensibilidad.py", title="Sensibilidad", icon="🧭"),
        ],
        "Método": [
            st.Page("dashboard_pages/validacion.py", title="Validación matemática", icon="🧮"),
            st.Page("dashboard_pages/metodologia.py", title="Datos y metodología", icon="📚"),
        ],
    }
)
navigation.run()
