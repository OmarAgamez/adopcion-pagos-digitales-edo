import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

from datos import RAIZ, cargar_datos
from modelo import logistico

RUTA_FIGURA = RAIZ / "report" / "figures" / "ajuste_logistico.png"


def ajustar_r(t, N, K, N0):
    """K fijo: solo se busca r."""
    def f(t, r):
        return logistico(t, r, K, N0)
    (r,), _ = curve_fit(f, t, N, p0=[0.5])
    return r


def ajustar_r_K(t, N, N0):
    """K libre: se buscan r y K."""
    def f(t, r, K):
        return logistico(t, r, K, N0)
    (r, K), _ = curve_fit(f, t, N, p0=[0.5, 30], bounds=([0, N.max()], [5, 200]))
    return r, K


def rmse(N, N_modelo):
    """Error típico del modelo, en millones de usuarios."""
    return float(np.sqrt(np.mean((N - N_modelo) ** 2)))


if __name__ == "__main__":
    df = cargar_datos()
    t = df["t"].to_numpy(dtype=float)
    N = df["usuarios_millones"].to_numpy(dtype=float)
    N0 = N[0]

    escenarios = {}
    for K in (37.1, 32.0):
        escenarios[f"K = {K} (fijo)"] = (ajustar_r(t, N, K, N0), K)
    r_libre, K_libre = ajustar_r_K(t, N, N0)
    escenarios[f"K = {K_libre:.1f} (libre)"] = (r_libre, K_libre)

    tt = np.linspace(0, 12, 300)
    plt.figure(figsize=(8, 5))
    plt.scatter(t, N, color="black", zorder=3, label="Datos Nequi")
    for nombre, (r, K) in escenarios.items():
        error = rmse(N, logistico(t, r, K, N0))
        print(f"{nombre}: r = {r:.3f} por año, RMSE = {error:.2f} millones")
        plt.plot(tt, logistico(tt, r, K, N0), label=f"{nombre}, r={r:.2f}")
    plt.xlabel("t (años desde dic. 2018)")
    plt.ylabel("Usuarios (millones)")
    plt.legend()
    plt.grid(alpha=0.3)
    RUTA_FIGURA.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(RUTA_FIGURA, dpi=200, bbox_inches="tight")
    plt.show()