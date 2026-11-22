# Fuentes, métricas y trazabilidad

Fecha de consulta: 22 de noviembre de 2026.

## Fuentes primarias

1. **Nequi, “Somos Nequi”** — reseña histórica institucional. Reporta, entre otros hitos, 816.000 usuarios al cierre de 2018, 1,8 millones en 2019, 4,8 millones en 2020, 10 millones en 2021, más de 14 millones en 2022, más de 18 millones al cierre de 2023 y más de 27 millones en 2025. La página distingue además usuarios activos en hitos antiguos y, por ello, se conserva el texto y la métrica específica de cada cifra.
   - <https://www.nequi.com.co/conocenos/somos-nequi>

2. **Bancolombia, Informe anual 2024**, sección Nequi y tabla histórica. La tabla reporta usuarios totales: 18.598.442 (2023) y 21.320.389 (2024); usuarios activos por mes: 13.399.397 y 16.499.498, respectivamente. Son métricas diferentes.
   - <https://www.sec.gov/Archives/edgar/data/1071371/000107137125000062/ex991-annualreportofbancol.htm>

3. **Grupo Cibest, resultados del cuarto trimestre de 2025**, presentado ante la SEC. Informa que al 31 de diciembre de 2025 había 27,4 millones de cuentas en Nequi, de las cuales 21,9 millones estaban activas. En la frase consultada no se define una ventana temporal para “activas”.
   - <https://www.sec.gov/Archives/edgar/data/2058897/000205889726000013/grupocibestsa6-kpr4q25.htm>

4. **Grupo Cibest, Informe anual 2025**, sección de Nequi. Indica que Nequi cerró 2025 con más de 27 millones de clientes y durante el año incorporó más de 3,2 millones de clientes que antes usaban Bancolombia A la Mano.
   - <https://www.sec.gov/Archives/edgar/data/2058897/000205889726000132/ex99-annualreportofgrupoci.htm>

## Criterios de registro

- Los conteos de 2018–2021 se toman de la secuencia publicada por Nequi y se marcan como redondeados. Para 2019–2021, la fuente da el año del hito, no un día de corte.
- “Más de 14 millones” de 2022 se registra como límite inferior de 14, no como observación puntual.
- Para 2023–2024 se priorizan los conteos tabulados del informe anual frente a las descripciones redondeadas de la página institucional. Los valores activos mensuales se mantienen en filas aparte.
- Se mantiene la cifra original de 2024 (21,4 M) y la clasificación original de 2022–2025 en **data/nequi_usuarios_original.csv**; el CSV auditado usa la publicación primaria más precisa disponible para 2023–2024 y corrige la tipología de los valores redondeados.
- 2025 se registra como “cuentas” y solo participa en sensibilidad. La migración de más de 3,2 millones desde A la Mano se documenta en **data/eventos_comparabilidad.csv**, sin ajuste aritmético.
- Las cifras exactas de 2023–2024 se registran como conteos exactos **según lo publicado**. El informe es anual; la fecha ISO de corte se interpreta como cierre de cada ejercicio financiero y se documenta así en el campo precision_corte.
- La fuente no mide adopciones nuevas por periodo ni transacciones. El estudio modela la evolución de un stock reportado, no una tasa observada de descargas ni la actividad financiera.
