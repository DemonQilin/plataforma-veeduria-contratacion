# 0039. I1 se publica por año y secretaría, con el año de corte parcial

- **Estado:** Aceptada
- **Fecha:** 2026-11-05
- **Fuente:** [docs/indicadores.md](../indicadores.md#1-catálogo) (I1), [docs/reglas.md](../reglas.md#4-reglas) (R7, R8, R12, R13, D1, D2, D6), [ADR 0033](0033-celda-de-indicador-en-el-contrato.md)

## Contexto

I1 mide qué parte de la contratación es directa. La fórmula pide el resultado por año y secretaría, y dos niveles: contratación directa sola y «no competitiva» (directa más régimen especial, D2). Hacía falta decidir cómo se publican los años, qué pasa con el año de la fecha de corte y cómo entran las secretarías a la supresión de R13.

## Decisión

- **Todos los años de la copia.** I1 publica cada año con contratos firmados (2022 a 2026), sin una lista fija de años.
- **El año de corte queda parcial.** 2026 llega hasta el 30 de octubre y se publica así, del 1 de enero al corte. A diferencia de I2, I1 es una proporción dentro del año, así que no necesita recortar los años completos al tramo común de R12. El tablero muestra la fecha de corte junto a la cifra.
- **Variantes.** `None` es la contratación directa sola (D1: incluye la «con ofertas»); `non_competitive` suma el régimen especial (D2).
- **Medidas.** Por número, el denominador es todo contrato firmado en el año. Por valor se usa el valor inicial (D3) y se excluyen el crédito público y los contratos sin valor (R7); el `sample_size` de la medida por valor cuenta solo los contratos con valor.
- **Niveles.** Distrito y una celda por secretaría de R8. La secretaría `unassigned` tiene celda propia, para que las secretarías sumen al Distrito: si se omitiera, la supresión complementaria (D6) trabajaría sobre un desglose incompleto.
- **La supresión no vive aquí.** `build_direct_award_share` publica las celdas sin suprimir y `publish_indicators` aplica R13 y D6, como con I2 e I8.

## Consecuencias

- `indicators.json` crece de 93 a 661 celdas, 568 de I1. De las 548 celdas por secretaría, 16 quedan suprimidas (8 por número y 8 por valor), por R13 o por la supresión complementaria.
- Los años 2022 a 2025 son completos y 2026 es parcial. Comparar 2026 con otro año por cifras absolutas no es válido; las razones sí se pueden leer, con la cautela de que octubre aún no cierra el año.
- La secretaría `unassigned` aparece como una secretaría más. El tablero debe nombrarla «Sin asignar» y no mezclarla con las demás.

## Alternativas

- **Variante de tramo común para 2026:** descartada. Duplica las celdas y complica la lectura, para corregir un sesgo que en una proporción dentro del año es pequeño.
- **Excluir 2026:** descartada. El tablero perdería el año en curso, que es el que más interesa a quien lo consulte.
- **Omitir «sin asignar»:** descartada. Rompe que las secretarías sumen al Distrito, que D6 necesita.
