"""Compatibilidad del ajuste anterior; usa exclusivamente la solución central."""

from __future__ import annotations

import numpy as np
from scipy.optimize import curve_fit

from adopcion_pagos.model import LogisticParameters, analytical_solution


def ajustar_r(t, N, K, N0):
    def curve(time, rate):
        return np.asarray(analytical_solution(time, LogisticParameters(K, N0, rate)))
    (rate,), _ = curve_fit(curve, np.asarray(t, dtype=float), np.asarray(N, dtype=float), p0=[0.5])
    return float(rate)


def ajustar_r_K(t, N, N0):
    values = np.asarray(N, dtype=float)
    def curve(time, rate, capacity):
        return np.asarray(analytical_solution(time, LogisticParameters(capacity, N0, rate)))
    (rate, capacity), _ = curve_fit(
        curve, np.asarray(t, dtype=float), values, p0=[0.5, 30.0],
        bounds=([0.0, float(values.max())], [5.0, 200.0]),
    )
    return float(rate), float(capacity)


def rmse(observed, predicted):
    values = np.asarray(observed, dtype=float) - np.asarray(predicted, dtype=float)
    return float(np.sqrt(np.mean(values**2)))


if __name__ == "__main__":
    from adopcion_pagos.pipeline import main
    main()
