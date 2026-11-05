# 0038. La conciliación R15 se publica sin supresión de celdas pequeñas

- **Estado:** Aceptada
- **Fecha:** 2026-11-05
- **Fuente:** [docs/reglas.md](../reglas.md#4-reglas) (R13, R15), [ADR 0031](0031-conciliacion-secop-medata.md)

## Contexto

La tabla `reconciliation` (ADR 0031) se calculaba en `build()` pero no se escribía en `data/outputs/`, así que el tablero no podía advertir los meses con menos del 80 % de contratos en ambas fuentes. R13 suprime los indicadores desagregados con menos de 5 contratos; la conciliación se publica por mes, y había que decidir si R13 le aplica.

## Decisión

- **Salida `quality.json`** (`publish/quality.py`, modelo `Quality`): `reconciliation.threshold` y una fila por mes con `secop_count`, `medata_count`, `shared_count`, `union_count`, `shared_share`, `secop_coverage`, `medata_coverage` y `below_threshold`. Es la salida «Calidad de datos» de `docs/reglas.md`, sección 7; por ahora solo trae la conciliación.
- **R13 no se aplica a la conciliación.** R13 protege los indicadores desagregados. Estos conteos son de contratos públicos, sin ningún atributo de personas ni de proveedores, y ADR 0031 pide mostrar el conteo junto a la advertencia porque con pocos contratos un contrato de diferencia mueve mucho el porcentaje.
- **Guarda:** `test_adr_0038_no_month_has_fewer_than_5_contracts` falla si algún mes baja de 5 contratos en alguna fuente. Hoy el mínimo es 5. Si falla, esta decisión se revisa; no se oculta la cifra en silencio.
- **El umbral viaja en la salida.** El tablero lee `threshold` y no escribe «80 %» a mano (el dominio vive en Python).

## Consecuencias

- `run --from-snapshot` escribe `quality.json` junto a `indicators.json` y `metadata.json`, de forma atómica.
- MEData no se actualiza y cubre hasta junio de 2023, así que los 18 meses publicados no cambian con una nueva copia de SECOP II, salvo por el lado de SECOP II.
- El tablero debe mostrar el conteo junto a cada advertencia y decir que marzo de 2022 (5 de 20) y los demás meses bajos se leen con cautela.

## Alternativas

- **Aplicar R13 a la conciliación:** descartada. Hoy no cambiaría ninguna cifra y sumaría lógica y casos de prueba por una salida que no describe personas. La guarda cubre el caso en que cambie.
