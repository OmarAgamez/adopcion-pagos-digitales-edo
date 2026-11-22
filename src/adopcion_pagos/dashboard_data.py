"""Lectura no destructiva de resultados guardados para el dashboard local."""

from __future__ import annotations

import csv
from pathlib import Path

from .model import LogisticParameters


TABLE_FILES = {
    "original_fits": "reproduccion_omar.csv",
    "original_residuals": "reproduccion_omar_residuos.csv",
    "primary_fits": "ajustes_principales.csv",
    "sensitivity_2025": "ajustes_sensibilidad_2025.csv",
    "primary_residuals": "residuos_principales.csv",
    "numerical_comparison": "comparacion_analitica_numerica.csv",
    "holdout": "validacion_holdout.csv",
    "characteristics": "tiempos_caracteristicos.csv",
}


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    """Lee filas versionadas sin modificarlas ni inferir definiciones estadísticas."""

    csv_path = Path(path)
    try:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise ValueError("El archivo CSV no contiene encabezados.")
            return list(reader)
    except OSError as exc:
        raise ValueError(f"No se pudo leer el archivo CSV: {csv_path}") from exc


def load_dashboard_tables(project_root: str | Path) -> dict[str, list[dict[str, str]]]:
    """Carga tablas reproducibles por separado para impedir mezclar metodologías."""

    root = Path(project_root)
    tables_root = root / "outputs" / "tables"
    return {
        name: read_csv_rows(tables_root / filename)
        for name, filename in TABLE_FILES.items()
    }


def parameters_from_fit_row(row: dict[str, str]) -> LogisticParameters:
    """Construye parámetros del modelo desde una fila de resultados históricos."""

    try:
        return LogisticParameters(
            capacity=float(row["K_millones"]),
            initial_adopters=float(row["N0_millones"]),
            growth_rate=float(row["r_por_anio"]),
        )
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise ValueError("La fila de ajuste no contiene parámetros históricos válidos.") from exc
