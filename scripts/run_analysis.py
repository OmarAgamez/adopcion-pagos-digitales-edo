"""Ejecuta el análisis reproducible desde la raíz del repositorio."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from adopcion_pagos.pipeline import main


if __name__ == "__main__":
    main()
