# 0035. Duración de los contratos de enero en I2

- **Estado:** Aceptada
- **Fecha:** 2026-11-05
- **Fuente:** [docs/indicadores.md](../indicadores.md) sección 3 (factor de confusión, control 3), [ADR 0034](0034-calendario-electoral-y-ventanas.md)

## Contexto

El control 3 de I2 pregunta si, en los años de restricción, los contratos de enero duran más, para cubrir los meses en que no se podrá contratar. Hay que convertirlo en una cifra. La nota inicial proponía `signed_date + duration_days`, pero `duration_days` viene solo de MEData, que llega hasta junio de 2023, y no está en `linked_contracts`: no cubre 2024 a 2026.

## Decisión

- **La señal es una proporción:** contratos directos firmados en la ventana de enero cuyo plazo termina después del fin de la restricción de referencia, sobre los contratos directos de esa ventana con fecha de fin. Solo por número de contratos; variante `spans_restriction`.
- **Plazo pactado = `end_date` − `added_days`** (SECOP II). `end_date` está poblado en todos los directos de enero; restar los días adicionados evita contar prórrogas posteriores a la firma. Es un supuesto: no se pudo verificar que SECOP II actualice `end_date` con las prórrogas.
- **Fin de restricción de referencia (`reference_restriction_end`):** el real en los años de tratamiento (19 jun 2022, 21 jun 2026). En los de control, el punto medio de esos fines de restricción, calculado por día y mes: 20 de junio. Es la misma lógica que la ventana de control de enero (ADR 0034).
- **Terminar el mismo día del umbral no cuenta;** el día siguiente sí.

## Consecuencias

- `ComparisonWindow` gana el campo `reference_restriction_end`; `restriction_end` no cambia.
- Con la copia actual la señal no distingue tratamiento de control (2025 queda en 98,9 %); se declara como no concluyente en la bitácora.
- Si MEData o SECOP II permiten verificar la actualización de `end_date`, el supuesto se puede retirar.
