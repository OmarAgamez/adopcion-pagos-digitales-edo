# Modelado de la curva de adopción de aplicaciones móviles de pagos digitales mediante ecuaciones diferenciales de primer orden

**Caso aplicado:** cifras públicas de base reportada de Nequi en Colombia.

Proyecto académico independiente de La Exclusiva para la asignatura Ecuaciones Diferenciales.

**Integrantes:**
- Omar David Agamez Pérez
- Carlos Eduardo Camelo Montaño
- Santiago Daniel Galviz Silva

El proyecto estudia si una curva logística de primer orden puede describir, de forma exploratoria, la evolución de las cifras públicas reportadas de Nequi en Colombia.

## Pregunta y modelo

Se considera el modelo autónomo

\[
\frac{dN}{dt}=rN\left(1-\frac{N}{K}\right), \qquad N(0)=N_0,
\]

cuya solución analítica es

\[
N(t)=\frac{K}{1+\left(\frac{K-N_0}{N_0}\right)e^{-rt}}.
\]

Para la serie histórica, N se mide en millones de personas o cuentas reportadas, t en años desde 2018 y r en año⁻¹. En el ejercicio didáctico se usan personas, meses y una tasa mensual; esos datos hipotéticos se mantienen separados.

## Datos y comparabilidad

- **data/nequi_usuarios_original.csv** conserva sin cambios la tabla que estaba en origin/main.
- **data/nequi_usuarios.csv** agrega fecha/corte reportado, precisión, definición de la métrica, tipo de observación, fuente primaria y notas.
- El ajuste principal usa cifras 2018–2024. La cifra de 2022 se publica como “más de 14 millones” y entra al ajuste como una **cota inferior** y se impone N(4) ≥ 14, sin igualar el valor de la función a 14.
- Para 2023–2024 se usan los conteos “total users” del informe anual de Bancolombia. Los usuarios activos por mes están registrados aparte y no se combinan con el total.
- El dato de 2025 se reporta como cuentas en Nequi y solo se incluye en sensibilidad. Grupo Cibest reporta además que incorporó más de 3,2 millones de clientes que usaban Bancolombia A la Mano. Esa migración limita la comparabilidad; el proyecto no la resta ni la corrige arbitrariamente.
- Las cifras 2018–2021 son cifras redondeadas divulgadas por Nequi. Los cortes exactos de varias cifras históricas no aparecen en la fuente; se documenta esa precisión en el CSV.
- **data/eventos_comparabilidad.csv** mantiene el evento de migración como contexto, no como observación de la serie.

Las fuentes y sus definiciones se describen en [docs/fuentes_datos.md](docs/fuentes_datos.md); las decisiones de modelado, en [docs/decisiones_metodologicas.md](docs/decisiones_metodologicas.md).

## Ajuste y validación

El módulo central **src/adopcion_pagos/model.py** contiene la ecuación, su solución estable y el lado derecho de la EDO. **simulation.py** compara la solución cerrada con solve_ivp; **fit.py** ajusta r con K fijado o libre y distingue cotas inferiores; **pipeline.py** centraliza residuos, RMSE, R², sensibilidad, proyecciones, tablas y gráficas.

Se conservan K=32 y K=37,1 millones como escenarios hipotéticos exploratorios, no estimaciones demostradas del mercado. El ajuste libre es diagnóstico: una serie corta y cambios de definición no identifican con fiabilidad la saturación. El R² in-sample describe el ajuste a los puntos usados y no prueba la capacidad predictiva; por eso también se guarda una validación temporal reservada y se señalan sus límites.

Las filas de métricas en tablas de ajuste, RMSE y R² usan observaciones puntuales. Las cotas se evalúan por separado como restricciones unilaterales. Las proyecciones se etiquetan como tales y no son datos observados.

## Reproducibilidad

Requisito verificado: Python 3.13.3. Las versiones exactas de dependencias directas y transitivas usadas están fijadas en **requirements.txt**.

Desde la raíz del proyecto:

~~~powershell
python -m pip install -r requirements.txt
python scripts/run_analysis.py
python -m pytest
~~~

El script crea tablas CSV en **outputs/tables/** y figuras PNG en **outputs/figures/**. No modifica las figuras históricas en **report/figures/**. Para regenerar las salidas se usa el mismo CSV auditado y los mismos parámetros guardados en el repositorio.

## Estructura

- **data/**: serie original preservada, datos auditados y escenarios didácticos.
- **src/adopcion_pagos/**: implementación central de modelo, carga, ajuste, simulación, análisis y figuras.
- **src/modelo.py**, **src/ajuste.py**, **src/validacion.py**, **src/datos.py**: adaptadores delgados para nombres históricos.
- **scripts/run_analysis.py**: punto de entrada reproducible.
- **tests/**: 23 pruebas adaptadas de la Fase 1 y pruebas nuevas del tratamiento de datos y ajustes.
- **docs/**: fuentes, decisiones metodológicas e informe de integración del manuscrito LaTeX del equipo.
- **outputs/**: tablas y figuras generadas.

## Informe y póster

El informe original de Omar está integrado en **report/main.tex** y se conserva como documento principal, con sus tablas y resultados históricos. Las mejoras metodológicas de la integración se documentan por separado y no sustituyen automáticamente sus resultados. El diseño original de Canva no se modificó; no había integración disponible para crear una copia independiente.
