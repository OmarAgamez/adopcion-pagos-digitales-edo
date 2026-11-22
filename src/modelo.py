import numpy as np


def logistico(t, r, K, N0):
    """Solución analítica de dN/dt = r*N*(1 - N/K) con N(0) = N0."""
    return K / (1 + ((K - N0) / N0) * np.exp(-r * t))