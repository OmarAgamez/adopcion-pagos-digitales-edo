"""Compatibilidad con el módulo histórico; delega en el modelo central."""

from adopcion_pagos.model import LogisticParameters, analytical_solution


def logistico(t, r, K, N0):
    """Solución analítica; r y t deben usar unidades recíprocas/coherentes."""
    return analytical_solution(t, LogisticParameters(K, N0, r))
