# 0043. I3 publica el oferente único por año y secretaría, y la exclusión de R9 en la calidad

- **Estado:** Aceptada
- **Fecha:** 2026-11-05
- **Fuente:** [docs/indicadores.md](../indicadores.md#1-catálogo) (I3), [docs/reglas.md](../reglas.md#4-reglas) (R5, R8, R9, R12, R13), [ADR 0029](0029-consolidacion-de-contratos-y-procesos.md), [ADR 0039](0039-i1-anual-por-secretaria.md), [ADR 0042](0042-calidad-de-datos-completa.md)

## Contexto

I3 es un indicador del MVP: de los procesos competitivos adjudicados, cuántos tuvieron un solo oferente. Faltaba decidir el periodo, la secretaría, la unidad de conteo y dónde se reporta la exclusión de R9. El ADR 0042 dejó esa exclusión para este indicador.

## Decisión

- **Procesos válidos (R9).** Un proceso canónico (R5) entra si es competitivo, está adjudicado (ADR 0029) y su fecha de publicación va del 1 de enero de 2022 a la fecha de corte (R12). Si reporta cero oferentes o ninguno, es un error de datos y queda fuera del indicador.
- **Periodo.** El año de publicación del proceso. Ningún proceso competitivo adjudicado publicado antes de 2022 se cruza con un contrato de la copia, así que el corte de 2022 no descarta procesos que importen. El año de la fecha de corte queda parcial, como en I1 (ADR 0039).
- **Fórmula.** Procesos válidos con un oferente único ÷ procesos válidos. Solo por número: la unidad es el proceso y no tiene un valor propio comparable. `sample_size` es el denominador.
- **Secretaría.** La unidad que adelanta el proceso en SECOP II, traducida con el catálogo de R8; un texto que el catálogo no reconoce cae en «sin asignar», para que las secretarías sumen al Distrito (D6). Es la unidad que conduce la compra, no necesariamente la que pidió el bien: la mayor parte de los procesos la conduce la unidad de compras centralizada. El tablero lo aclara.
- **Supresión.** R13 y D6 se aplican en `publish_indicators` sin cambios: la celda por secretaría con menos de 5 procesos se suprime.
- **Calidad.** `quality.json` agrega `single_bidder_exclusions`: procesos excluidos por R9 sobre los competitivos adjudicados del periodo, sin supresión (como el resto de la calidad, ADR 0042). Cada exclusión queda también en `quality_issues` con la regla `R9`, identificada por el portafolio.
- **Una sola regla.** El indicador y la calidad leen la misma tabla, `single_bidder_processes`, que arma el pipeline.

## Consecuencias

- `indicators.json` agrega las celdas de I3 (Distrito y secretarías, por año). `quality.json` agrega `single_bidder_exclusions`.
- Cambia el contrato: se regeneran `data/schema/` y `web/src/types/contract.ts`.
- Con la copia actual, hay 21 procesos con cero oferentes de 894 competitivos adjudicados (20 en 2022).

## Alternativas

- **Periodo por la fecha de firma del contrato:** descartada. No todo proceso tiene contrato en la copia y los procesos sin contrato desaparecerían del denominador.
- **Solo nivel Distrito:** descartada. Se pierde el desglose de Seguridad y Gestión del Riesgo; el riesgo de lectura se cubre con la aclaración sobre la unidad.
- **Publicar el valor adjudicado:** descartada. El proceso no tiene un valor comparable entre modalidades y la medida por número responde la pregunta del indicador.
