# Resultados reproducibles de la integración

Generados por el pipeline desde los CSV versionados; unidades históricas en millones y tasas por año. Las cifras se deben regenerar con `python scripts/run_analysis.py`.

## Referencia: método original

La reproducción de los scripts anteriores usa las ocho filas originales como puntos, incluidos 2022 y 2023 (que en realidad se describían como aproximación/cota), además de 21,4 M para 2024 y 27,4 M para 2025.

| Escenario original | K (M) | r/año | RMSE (M) | R² in-sample |
|---|---:|---:|---:|---:|
| K fijo 37,1 | 37,1 | 0,729322 | 2,126270 | 0,944345 |
| K fijo 32 | 32 | 0,787847 | 1,607432 | 0,968192 |
| K libre | 27,438799 | 0,866401 | 1,281783 | 0,979775 |

La estimación libre reproduce la cota inferior original (K geq max(N)) y queda junto al último punto. Estos números sirven para cotejar la implementación histórica; no constituyen el ajuste académico auditado.

## Ajuste integrado principal: 2018–2024

La condición inicial es (N_0=0{,}816) M, el ajuste usa seis puntos y respeta la cota 2022 (N(4)geq14) M como desigualdad. RMSE y R² se calculan solo con los seis puntos; la cota se valida aparte.

| Escenario | K (M) | r/año | RMSE puntos (M) | R² in-sample | N̂ 2028 (M) |
|---|---:|---:|---:|---:|---:|
| K fijo 32 | 32 | 0,847983 | 2,226132 | 0,921655 | 31,748107 |
| K fijo 37,1 | 37,1 | 0,823486 | 3,185984 | 0,839529 | 36,667532 |
| K libre, diagnóstico | 22,398572 | 1,001082 | 0,277025 | 0,998787 | 22,371997 |

Los K fijos se conservan de la versión previa del proyecto como escenarios comparativos; no se han estimado a partir de una población elegible ni se ha verificado que sean techos de mercado. El K libre queda solo 1,08 M por encima de 2024 y produce una asíntota temprana. El alto R² de este ajuste no valida esa asíntota ni demuestra predicción futura.

La desigualdad de 2022 queda activa para K=32 y K=37,1: ambos modelos predicen 14 M en (t=4). Para K libre predice aproximadamente 15,11 M. El corte exacto de la cifra de 2022 no está especificado por la fuente; el eje anual es una aproximación.

## Sensibilidad que incorpora 2025

La observación agregada en esta corrida es 27,4 M **cuentas**, no el mismo rótulo estadístico que la tabla de usuarios totales 2023–2024. Además, Grupo Cibest reporta la incorporación durante 2025 de más de 3,2 M de antiguos clientes de Bancolombia A la Mano. No se resta esa cantidad.

| Escenario | K ajustado/fijado (M) | r/año | RMSE puntos (M) | R² in-sample |
|---|---:|---:|---:|---:|
| K fijo 32 | 32 | 0,847983 | 2,154878 | 0,950181 |
| K fijo 37,1 | 37,1 | 0,823486 | 3,535715 | 0,865877 |
| K libre, diagnóstico | 27,400003 | 0,881863 | 1,331225 | 0,980987 |

Con K fijo, la desigualdad activa de 2022 mantiene r en el mismo valor; el residuo 2025 se agrega a las métricas. El ajuste libre se pega al límite inferior (K>27{,}4) introducido para que una capacidad no quede por debajo del máximo observado. Por esto, los estadísticos de la corrida 2025 no deben compararse directamente con los del periodo principal ni interpretarse como estimación de saturación.

## Validación temporal reservada

Ajustando hasta 2023 con la metodología integrada, la corrida de K=32 predice 25,89 M para 2024 frente a 21,32 M publicados (residuo observado menos predicho −4,57 M). K=37,1 predice 28,15 M (residuo −6,83 M). Para 2025, las proyecciones serían 29,06 M y 32,56 M, frente a 27,4 M cuentas, pero esa comparación mezcla definiciones y el cambio de composición descrito arriba.

El holdout original de Omar, que trata también las cifras antiguas como puntos y usa 21,4 M/27,4 M, predijo para K=32: 25,23 M y 28,63 M (errores −3,83 M y −1,23 M); para K=37,1: 26,76 M y 31,57 M (errores −5,36 M y −4,17 M). El error en 2024 refuerza que el buen ajuste in-sample no basta para sostener proyecciones.

## Simulación didáctica y controles

Para el escenario hipotético moderado (K=10.000 personas, N₀=500, r=0,35/mes), el error absoluto máximo entre la solución analítica y solve_ivp (RK45, tolerancias (10^{-12})) fue (6{,}419	imes10^{-8}) personas en 241 puntos. Las pruebas de la Fase 1 incluyen monotonicidad, acotamiento, condición inicial, parámetros y reproducibilidad. Se agregaron pruebas para fuentes, tipos de observación, separación de métricas, cotas y ajuste.
