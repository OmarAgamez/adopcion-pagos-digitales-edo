"""Lectura y validación de observaciones históricas con trazabilidad de fuentes."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


OBSERVATION_TYPES = {"exacta", "redondeada", "aproximada", "cota_inferior"}
REQUIRED_COLUMNS = {
    "id", "anio", "t_anios_desde_2018", "fecha_corte", "precision_corte",
    "metrica", "valor", "unidad", "tipo_observacion", "fuente",
    "titulo_fuente", "url_fuente", "serie_modelo",
    "incluir_ajuste_principal", "incluir_ajuste_sensibilidad", "notas",
}


@dataclass(frozen=True)
class HistoricObservation:
    observation_id: str
    year: int
    time_years: float
    cutoff_date: str
    cutoff_precision: str
    metric: str
    value: float
    unit: str
    observation_type: str
    source: str
    source_title: str
    source_url: str
    model_series: str
    include_primary: bool
    include_sensitivity: bool
    notes: str


def _parse_bool(value: str, row_number: int, column: str) -> bool:
    normalized = value.strip().casefold()
    if normalized not in {"true", "false"}:
        raise ValueError(f"Fila {row_number}: {column} debe ser true o false.")
    return normalized == "true"


def load_observations(path: str | Path) -> list[HistoricObservation]:
    """Carga la tabla de observaciones sin combinar métricas distintas."""

    csv_path = Path(path)
    try:
        handle = csv_path.open("r", encoding="utf-8-sig", newline="")
    except OSError as exc:
        raise ValueError(f"No se pudo abrir el archivo de observaciones: {csv_path}") from exc

    observations: list[HistoricObservation] = []
    with handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
            missing = sorted(REQUIRED_COLUMNS - set(reader.fieldnames or []))
            raise ValueError(f"Faltan columnas requeridas: {', '.join(missing)}")
        ids: set[str] = set()
        for row_number, row in enumerate(reader, start=2):
            try:
                obs_id = (row["id"] or "").strip()
                year = int(row["anio"])
                time_years = float(row["t_anios_desde_2018"])
                value = float(row["valor"])
                kind = (row["tipo_observacion"] or "").strip()
                if not obs_id or obs_id in ids:
                    raise ValueError("id vacío o duplicado.")
                if year < 2018 or not (year - 2018 == time_years):
                    raise ValueError("año o tiempo no concuerda con t = año - 2018.")
                if value < 0:
                    raise ValueError("el valor no puede ser negativo.")
                if kind not in OBSERVATION_TYPES:
                    raise ValueError(f"tipo_observacion no reconocido: {kind}.")
                url = (row["url_fuente"] or "").strip()
                if not url.startswith("https://"):
                    raise ValueError("la fuente debe incluir una URL HTTPS.")
                item = HistoricObservation(
                    observation_id=obs_id,
                    year=year,
                    time_years=time_years,
                    cutoff_date=(row["fecha_corte"] or "").strip(),
                    cutoff_precision=(row["precision_corte"] or "").strip(),
                    metric=(row["metrica"] or "").strip(),
                    value=value,
                    unit=(row["unidad"] or "").strip(),
                    observation_type=kind,
                    source=(row["fuente"] or "").strip(),
                    source_title=(row["titulo_fuente"] or "").strip(),
                    source_url=url,
                    model_series=(row["serie_modelo"] or "").strip(),
                    include_primary=_parse_bool(row["incluir_ajuste_principal"], row_number, "incluir_ajuste_principal"),
                    include_sensitivity=_parse_bool(row["incluir_ajuste_sensibilidad"], row_number, "incluir_ajuste_sensibilidad"),
                    notes=(row["notas"] or "").strip(),
                )
                if not all((item.cutoff_date, item.cutoff_precision, item.metric, item.unit, item.source_title, item.model_series)):
                    raise ValueError("faltan metadatos de corte, métrica, unidad o fuente.")
            except (KeyError, TypeError, ValueError, OverflowError) as exc:
                raise ValueError(f"Observación inválida en fila {row_number}: {exc}") from exc
            ids.add(obs_id)
            observations.append(item)
    if not observations:
        raise ValueError("El CSV debe contener al menos una observación.")
    return observations


def select_model_series(
    observations: list[HistoricObservation],
    *,
    include_2025: bool = False,
) -> list[HistoricObservation]:
    """Selecciona la serie de base reportada; 2025 entra solo en sensibilidad."""

    selected = []
    for item in observations:
        allowed = item.include_sensitivity if include_2025 else item.include_primary
        if item.model_series == "base_nequi_reportada" and allowed:
            selected.append(item)
    if not selected:
        raise ValueError("No hay observaciones elegibles para la serie solicitada.")
    return sorted(selected, key=lambda item: item.time_years)


def point_observations(observations: list[HistoricObservation]) -> list[HistoricObservation]:
    """Las cotas inferiores se conservan como restricciones, no como puntos exactos."""

    return [item for item in observations if item.observation_type != "cota_inferior"]
