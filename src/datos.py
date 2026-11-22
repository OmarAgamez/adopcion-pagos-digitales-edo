from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
RUTA_CSV = RAIZ / "data" / "nequi_usuarios.csv"
RUTA_FIGURA = RAIZ / "report" / "figures" / "datos_nequi.png"


def cargar_datos():
    return pd.read_csv(RUTA_CSV)


def graficar(df):
    exactos = df[df["tipo_dato"] == "exacto"]
    cotas = df[df["tipo_dato"] != "exacto"]

    plt.figure(figsize=(7, 4))
    plt.plot(df["anio"], df["usuarios_millones"], color="gray", alpha=0.4)
    plt.scatter(exactos["anio"], exactos["usuarios_millones"], label="Dato exacto")
    plt.scatter(cotas["anio"], cotas["usuarios_millones"],
                facecolors="none", edgecolors="red", label="Aproximado o 'más de'")
    plt.xlabel("Año (cierre de diciembre)")
    plt.ylabel("Usuarios vinculados (millones)")
    plt.title("Usuarios de Nequi, 2018-2025")
    plt.legend()
    plt.grid(alpha=0.3)

    RUTA_FIGURA.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(RUTA_FIGURA, dpi=200, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    datos = cargar_datos()
    print(datos)
    graficar(datos)