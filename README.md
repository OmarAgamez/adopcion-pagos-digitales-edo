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

## Dashboard interactivo local

La interfaz Streamlit reutiliza el modelo, los datos auditados y las tablas reproducibles que ya existen en el proyecto. Los controles mensuales son un ejemplo hipotético y permanecen separados del análisis histórico.

En Windows, desde la raíz del repositorio, crea un entorno aislado e instala las dependencias del dashboard:

~~~powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
~~~

Inicia la aplicación local:

~~~powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
~~~

Para usar el comando directo tras activar el entorno virtual:

~~~powershell
.\.venv\Scripts\Activate.ps1
python -m streamlit run app.py --server.address 127.0.0.1
~~~

El archivo raíz **requirements.txt** fija Streamlit y conserva las versiones de SciPy, NumPy y Matplotlib usadas por el análisis científico. La aplicación no usa servicios externos, bases de datos ni autenticación.

La navegación incluye inicio, simulador, análisis histórico, sensibilidad, validación matemática y datos/metodología. La reproducción histórica original de Omar y el ajuste integrado se presentan con tablas, métricas y observaciones independientes.

## Despliegue en Streamlit Community Cloud

La configuración de esta rama para Community Cloud es:

- **Repositorio:** OmarAgamez/adopcion-pagos-digitales-edo
- **Rama:** feat/dashboard-interactivo
- **Main file path:** app.py
- **Python:** 3.13

El archivo raíz **requirements.txt** declara Streamlit 1.67.0 y todas las dependencias científicas fijadas por el proyecto. Community Cloud crea el entorno desde ese archivo y ejecuta la aplicación desde la raíz del repositorio. En el diálogo **Advanced settings**, selecciona Python 3.13 para usar la misma versión que el entorno local.

Para desplegar el repositorio original, el propietario o una cuenta con permisos de administrador debe conectar GitHub a Streamlit Community Cloud y crear la aplicación con el repositorio, la rama y el archivo principal indicados arriba. La guía oficial describe los campos de repositorio, rama y ruta de entrada en [Deploy an app](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy); las dependencias se leen de [requirements.txt](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).

### Alternativa mediante un fork

Si no tienes permisos de administrador sobre el repositorio original:

1. Crea un fork de **OmarAgamez/adopcion-pagos-digitales-edo** en tu cuenta de GitHub.
2. Asegúrate de que el fork contenga la rama **feat/dashboard-interactivo**. Si no aparece automáticamente, publica en tu fork una rama con ese nombre basada en la rama publicada del repositorio original.
3. En Streamlit Community Cloud, selecciona tu fork como repositorio, **feat/dashboard-interactivo** como rama y **app.py** como archivo principal.
4. En **Advanced settings**, selecciona Python 3.13 y despliega. Los cambios de tu fork serán independientes del repositorio de Omar.

Esta documentación prepara los parámetros de despliegue; no afirma que exista una instancia pública desplegada.
