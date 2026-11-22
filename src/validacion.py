import matplotlib.pyplot as plt
import numpy as np

from ajuste import ajustar_r, rmse
from datos import RAIZ, cargar_datos
from modelo import logistico

RUTA_FIGURA = RAIZ / "report" / "figures" / "residuos.png"
ESCENARIOS = (37.1, 32.0)


def r_cuadrado(N, N_modelo):
    """Qué tanto de la variación de los datos explica el modelo (1 = perfecto)."""
    ss_res = np.sum((N - N_modelo) ** 2)
    ss_tot = np.sum((N - N.mean()) ** 2)
    return float(1 - ss_res / ss_tot)


def tiempo_hasta_fraccion(r, K, N0, f):
    """Tiempo t en que N alcanza la fracción f del techo K."""
    return float(np.log(f / (1 - f) * (K - N0) / N0) / r)


if __name__ == "__main__":
    df = cargar_datos()
    t = df["t"].to_numpy(dtype=float)
    N = df["usuarios_millones"].to_numpy(dtype=float)
    N0 = N[0]

    fig, ax = plt.subplots(figsize=(8, 4))
    ancho = 0.35
    for i, K in enumerate(ESCENARIOS):
        r = ajustar_r(t, N, K, N0)
        N_mod = logistico(t, r, K, N0)
        resid = N - N_mod
        print(f"\n=== K = {K} ===  r = {r:.3f}")
        print("Residuos (dato - modelo, millones):", np.round(resid, 2))
        print(f"RMSE = {rmse(N, N_mod):.2f}  |  R2 = {r_cuadrado(N, N_mod):.3f}")
        print(f"Punto de inflexión (N = K/2): t = {tiempo_hasta_fraccion(r, K, N0, 0.5):.2f}")
        print(f"N alcanza 90% de K en t = {tiempo_hasta_fraccion(r, K, N0, 0.9):.2f}")
        print("Predicción t=8,9,10 (2026-2028):",
              np.round(logistico(np.array([8, 9, 10.0]), r, K, N0), 1))
        print(f"Predicción mayo 2026 (t=7.42): {logistico(7.42, r, K, N0):.1f} (dato aprox. 28)")

        # Prueba con datos "escondidos": ajustar con 2018-2023 y predecir 2024-2025
        r_h = ajustar_r(t[:6], N[:6], K, N0)
        pred = logistico(t[6:], r_h, K, N0)
        print(f"Hold-out: r={r_h:.3f}, pred 2024-25 = {np.round(pred, 1)}, real = {N[6:]}, "
              f"error = {np.round(N[6:] - pred, 1)}")

        ax.bar(df["anio"] + (i - 0.5) * ancho, resid, ancho, label=f"K = {K}")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Año")
    ax.set_ylabel("Residuo: dato - modelo (millones)")
    ax.legend()
    ax.grid(alpha=0.3)
    RUTA_FIGURA.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(RUTA_FIGURA, dpi=200, bbox_inches="tight")
    plt.show()