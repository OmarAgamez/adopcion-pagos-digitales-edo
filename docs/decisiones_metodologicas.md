# Decisiones de modelado y validación

## Variable y condición inicial

La variable histórica se interpreta como base acumulada reportada, en millones. El eje temporal se define como t = año − 2018, de modo que N₀ = 0,816 millones en t = 0. Las fechas de algunos hitos solo se conocen a nivel de año; la escala anual es una aproximación documentada, no un día de corte común garantizado.

## Ecuación y parámetros

[
\frac{dN}{dt}=rN\left(1-\frac{N}{K}\right), \qquad
N(t)=\frac{K}{1+\left(\frac{K-N_0}{N_0}\right)e^{-rt}}.
]

r se expresa por año para la serie real. K y N se expresan en millones. En el escenario hipotético didáctico, K=10.000, N₀=500, tiempo en meses y r por mes.

La solución cerrada y la función del lado derecho están centralizadas en **src/adopcion_pagos/model.py**. La integración numérica llama a esa misma función.

## Cotas y tipo de dato

Para observaciones puntuales, el ajuste usa el residuo Nᵢ − N̂ᵢ. Para una cota inferior Lᵢ, impone la restricción N̂ᵢ ≥ Lᵢ en el problema de optimización. Así, el modelo respeta “más de 14” sin tratar 14 como conteo exacto. El RMSE y R² se calculan solo sobre observaciones puntuales y las violaciones de cota se informan aparte.

Cifras redondeadas se ajustan a su valor publicado como aproximación puntual, sin atribuirles precisión mayor que la indicada. Se reporta esa limitación.

## Escenarios de capacidad

K=32 M y K=37,1 M se conservan de la versión previa del proyecto como escenarios de capacidad fija para mostrar sensibilidad. Las fuentes auditadas no demuestran que sean límites del mercado colombiano y no se presentan como estimaciones empíricas. Se incluye un ajuste con K libre como diagnóstico, pero un buen ajuste en una serie corta no demuestra que la asíntota haya sido identificada. La tabla de sensibilidad reajusta r para varios K y también varía r sin reajustarlo.

## Periodos y evaluación predictiva

- **Ajuste principal:** cifras de base reportada entre 2018 y 2024, con observaciones de usuarios y una cota de usuarios. El año 2025 se reserva.
- **Sensibilidad 2025:** incorpora 27,4 millones de cuentas reportadas para 2025, manteniendo la advertencia de que la definición varía y que Grupo Cibest reportó la incorporación de más de 3,2 millones de usuarios de A la Mano.
- **Holdout temporal:** se ajusta hasta 2023 y se compara con la publicación de 2024. También se muestra 2025 como contraste exploratorio, aunque no plenamente comparable.

RMSE cuantifica el error típico en millones para los puntos usados. R² in-sample compara la suma de cuadrados del residuo con la variación de esos mismos puntos. Ninguna de las dos métricas, por sí sola, demuestra generalización. El holdout es pequeño, las observaciones históricas son heterogéneas y la reserva de 2025 contiene un cambio de población/definición.

## Separación didáctica

Los tres escenarios de 10.000 personas están en **data/escenarios_didacticos.csv** y son hipotéticos. No son muestras ni subconjuntos de la serie Nequi y no intervienen en el ajuste histórico.
