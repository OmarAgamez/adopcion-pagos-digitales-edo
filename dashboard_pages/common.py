"""Elementos compartidos de presentación; la lógica matemática permanece en src."""

from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from adopcion_pagos.dashboard_data import load_dashboard_tables, read_csv_rows  # noqa: E402
from adopcion_pagos.data import load_observations  # noqa: E402


@st.cache_data(show_spinner=False)
def dashboard_tables() -> dict[str, list[dict[str, str]]]:
    return load_dashboard_tables(PROJECT_ROOT)


@st.cache_data(show_spinner=False)
def integrated_observations():
    return load_observations(PROJECT_ROOT / "data" / "nequi_usuarios.csv")


@st.cache_data(show_spinner=False)
def original_observations() -> list[dict[str, str]]:
    return read_csv_rows(PROJECT_ROOT / "data" / "nequi_usuarios_original.csv")


@st.cache_data(show_spinner=False)
def comparison_events() -> list[dict[str, str]]:
    return read_csv_rows(PROJECT_ROOT / "data" / "eventos_comparabilidad.csv")


def page_intro(eyebrow: str, title: str, description: str) -> None:
    st.markdown(f'<div class="eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.title(title)
    st.write(description)


def decimal(value: float, places: int = 2) -> str:
    """Formato español con punto de millares y coma decimal."""

    formatted = f"{value:,.{places}f}"
    return formatted.replace(",", "§").replace(".", ",").replace("§", ".")


def configure_axes(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.22, linewidth=0.8)
    ax.set_axisbelow(True)
