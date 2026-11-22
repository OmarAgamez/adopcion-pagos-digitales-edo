# Modelado de la curva de adopción de aplicaciones móviles de pagos digitales mediante ecuaciones diferenciales de primer orden

## Información académica

- **Universidad:** Universidad Popular del Cesar
- **Programa:** Ingeniería de Sistemas
- **Asignatura:** Ecuaciones Diferenciales
- **Grupo:** 03
- **Docente:** Daniel Meza
- **Periodo:** 2026-II
- **Integrantes:**
  - Omar David Agemes Pérez
  - Santiago Daniel Galviz Silva
  - Carlos Eduardo Camelo Montaño

## Descripción

Este proyecto académico estudia una curva hipotética de adopción de aplicaciones móviles de pagos digitales mediante una ecuación diferencial ordinaria de primer orden. El programa compara su solución analítica con una integración numérica, genera escenarios y analiza la sensibilidad a los parámetros.

Los valores incluidos sirven únicamente para explicar y reproducir la simulación. No son observaciones ni estimaciones de Colombia, de la Universidad Popular del Cesar ni de una aplicación real.

## Modelo matemático

La cantidad acumulada de adoptantes A(t) se representa con la ecuación logística:

    dA/dt = r A (1 - A/K),      A(0) = A0

Su solución analítica es:

    A(t) = K / (1 + ((K - A0) / A0) exp(-r t))

El tiempo t se mide en meses; A(t), A0 y K en personas; y r en mes⁻¹. Para el modelo de adopción se requiere 0 < A0 < K y r > 0. La solución se aproxima a K cuando el tiempo crece. La velocidad es dA/dt = r A (1 - A/K) y alcanza su máximo, rK/4, en el punto de inflexión A = K/2.

### Supuestos

- A(t) representa personas que han adoptado acumulativamente; no mide transacciones ni usuarios activos recurrentes.
- La población potencial K permanece constante y no hay pérdida de adoptantes.
- La tasa r es positiva y constante durante cada escenario.
- La población se modela de forma agregada, sin representar diferencias individuales o geográficas.
- Los valores del CSV son hipótesis ilustrativas elegidas para mostrar las curvas, no datos observados.

### Parámetros hipotéticos iniciales

| Escenario | K (personas) | A0 (personas) | r (mes⁻¹) | Duración |
|---|---:|---:|---:|---:|
| Lento | 10.000 | 500 | 0,20 | 24 meses |
| Moderado (base) | 10.000 | 500 | 0,35 | 24 meses |
| Rápido | 10.000 | 500 | 0,50 | 24 meses |

Los parámetros pueden editarse en data/parameters.csv. Las descripciones de cada fila identifican los escenarios como hipotéticos.

## Estructura

    data/parameters.csv             Parámetros y escenarios editables
    src/adopcion_pagos/model.py     EDO, validación y solución analítica
    src/adopcion_pagos/simulation.py
                                    Lectura CSV, solve_ivp y sensibilidad
    src/adopcion_pagos/plotting.py  Figuras en español (PNG y PDF)
    scripts/run_simulation.py       Ejecución y exportación de resultados
    tests/                          Pruebas automáticas con pytest
    outputs/tables/                 CSV generados por la simulación
    outputs/figures/                Figuras PNG y PDF generadas

## Requisitos e instalación en Windows

Se requiere Python 3.13.3. Desde PowerShell, situado en la carpeta del proyecto:

1. Comprueba la versión:

        python --version

2. Crea el entorno virtual:

        python -m venv .venv

3. Instala las dependencias fijadas en requirements.txt:

        .\.venv\Scripts\python.exe -m pip install -r requirements.txt

No es necesario activar el entorno; los comandos siguientes invocan su intérprete directamente.

## Ejecución

Genera las tablas y las figuras con los parámetros del CSV:

    .\.venv\Scripts\python.exe scripts\run_simulation.py

El número de puntos, el archivo de parámetros y el directorio de salida pueden cambiarse:

    .\.venv\Scripts\python.exe scripts\run_simulation.py --parameters data\parameters.csv --output-dir outputs --points 241

--points debe ser un entero mayor o igual que 2. Todos los escenarios deben tener la misma duración; los nombres requeridos son lento, moderado y rápido.

## Resultados generados

En outputs/tables/ se escriben:

- model_comparison.csv: solución analítica, integración numérica, velocidad y error absoluto para el escenario moderado.
- scenario_comparison.csv: curvas de los tres escenarios, con sus parámetros y discrepancia numérica.
- sensitivity.csv: curvas al variar independientemente r, K y A0.
- summary.csv: adopción al final del periodo, porcentaje de la capacidad, velocidad máxima, mes de inflexión y error máximo.

En outputs/figures/ se guardan cuatro figuras, cada una en PNG y PDF: comparación analítica-numérica, velocidad de adopción, escenarios y análisis de sensibilidad. Las gráficas tienen títulos, leyendas y ejes en español con unidades.

La integración se realiza con scipy.integrate.solve_ivp (método RK45). El CSV de comparación permite revisar la discrepancia entre ambas soluciones. La sensibilidad se calcula con la solución analítica, variando un parámetro a la vez alrededor del escenario moderado.

## Pruebas

Ejecuta la suite automática desde la raíz del repositorio:

    .\.venv\Scripts\python.exe -m pytest

Las pruebas verifican condición inicial, monotonía y acotación de la curva, límite de saturación, derivada logística, concordancia analítica-numérica, entradas inválidas, variaciones de sensibilidad y reproducibilidad determinista.

## Limitaciones

La curva logística es una simplificación determinista: presupone una tasa constante, una capacidad fija y ausencia de abandono. No modela campañas, cambios regulatorios, acceso a internet, diferencias socioeconómicas, efectos de red ni competencia entre aplicaciones. Los escenarios actuales no se ajustaron a una serie empírica y no permiten concluir cómo se adoptan realmente los pagos digitales en Colombia.

## Continuación académica

La Fase 1 deja los CSV y figuras listos para reutilizar en el documento y el póster. Para la Fase 2 se deben seleccionar datos y fuentes académicas verificables, describir la procedencia de cualquier serie observada y separar claramente esos datos de estas hipótesis. Este repositorio todavía no incluye documento LaTeX, bibliografía ni póster.
