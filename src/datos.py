"""Acceso compatible a las observaciones auditadas."""

from pathlib import Path

from adopcion_pagos.data import load_observations, select_model_series

RAIZ = Path(__file__).resolve().parent.parent
RUTA_CSV = RAIZ / "data" / "nequi_usuarios.csv"


def cargar_datos():
    return load_observations(RUTA_CSV)


def cargar_serie_principal():
    return select_model_series(cargar_datos())
