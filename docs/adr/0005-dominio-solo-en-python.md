# 0005. El dominio vive solo en Python

- **Estado:** Aceptada
- **Fecha:** 2026-10-29
- **Fuente:** [docs/producto.md](../producto.md#31-principios)

## Contexto

Las reglas de negocio (R1–R17) y los indicadores (I1–I8) se implementan en el pipeline. El tablero está escrito en TypeScript, y con un equipo acostumbrado a modelar dominios es tentador volver a modelar parte del dominio ahí: calcular una proporción, un promedio o una diferencia directamente en un componente.

Tres compromisos del proyecto chocan con esa tentación:

- **Trazabilidad (R16):** cualquier cifra del tablero debe poder reconstruirse desde las fuentes con el pipeline.
- **Privacidad (R13):** ninguna cifra desagregada sobre menos de 5 contratos puede llegar al público. Si el tablero calculara a partir de datos más finos, esos datos tendrían que publicarse y la supresión se podría deshacer.
- **Una sola implementación por regla:** dos implementaciones de la misma regla en dos lenguajes divergen con el tiempo, y las pruebas solo cubren una.

## Decisión

- Todas las reglas e indicadores se implementan solo en Python, en el pipeline.
- **El tablero solo puede:** formatear valores, ordenar y seleccionar filas ya publicadas (por indicador, año o secretaría) y dibujarlas.
- **El tablero no puede:** sumar, promediar, calcular proporciones o diferencias, aplicar umbrales, decidir la supresión ni derivar ninguna cifra nueva.
- `data/outputs/` trae todo lo que las pantallas necesitan, ya calculado: el promedio del Distrito en el explorador, las cifras de la frase del hallazgo y las diferencias que se mencionen en un texto.
- Las celdas suprimidas llegan marcadas desde el pipeline. El tablero solo las muestra como «datos insuficientes».

## Consecuencias

- Toda cifra visible se reconstruye con `veeduria run --from-snapshot`; no hay lógica escondida en el frontend.
- Las reglas se prueban en un solo lugar, con pytest. El tablero casi no necesita pruebas de lógica.
- `data/outputs/` crece con valores precalculados. Con 28 secretarías, 5 años y 5 indicadores son pocos miles de filas, sin impacto en la carga.
- Un gráfico nuevo que necesite una cifra nueva exige cambiar primero el pipeline y el contrato (ver [0004](0004-contrato-pydantic-json-schema-ts.md)). Es más lento, pero mantiene la regla.
- El explorador solo puede mostrar combinaciones que el pipeline publicó. Un filtro libre sobre contratos individuales queda descartado, lo que coincide con el alcance del producto.

## Alternativas

| Criterio | Dominio solo en Python (elegida) | Dominio duplicado en TypeScript | Cálculo en el navegador sobre datos finos |
|---|---|---|---|
| Implementaciones por regla | Una | Dos | Una, en TypeScript |
| Trazabilidad (R16) | Completa desde el pipeline | Depende de que ambas coincidan | Solo desde el navegador |
| Supresión de celdas (R13) | Garantizada antes de publicar | Garantizada si se respeta | Se puede deshacer con los datos publicados |
| Flexibilidad del explorador | Combinaciones precalculadas | Combinaciones precalculadas | Filtros libres |

- **Dominio duplicado en TypeScript:** descartada. Dos implementaciones de cada regla duplican el trabajo y divergen sin que ninguna prueba lo detecte.
- **Cálculo en el navegador sobre datos finos:** descartada. Exige publicar datos por contrato, que permiten reconstruir las celdas suprimidas y contradicen el principio de patrones, no personas.