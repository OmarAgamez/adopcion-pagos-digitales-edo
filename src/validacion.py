"""Compatibilidad de métricas y validación con llamadas al modelo central."""

from __future__ import annotations

import numpy as np

from adopcion_pagos.model import LogisticParameters, time_to_fraction


def r_cuadrado(observed, predicted):
    observed = np.asarray(observed, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    total = float(np.sum((observed - observed.mean()) ** 2))
    return float(1.0 - np.sum((observed - predicted) ** 2) / total)


def tiempo_hasta_fraccion(r, K, N0, f):
    parameters = LogisticParameters(K, N0, r)
    return time_to_fraction(parameters, f)


if __name__ == "__main__":
    from adopcion_pagos.pipeline import main
    main()