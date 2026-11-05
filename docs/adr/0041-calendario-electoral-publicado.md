# 0041. El calendario electoral se publica como salida del tablero

- **Estado:** Aceptada
- **Fecha:** 2026-11-05
- **Fuente:** [docs/reglas.md](../reglas.md#4-reglas) (R10, R11, R12) y sección 7, [docs/producto.md](../producto.md) (pantallas 2, 3 y 4), [ADR 0034](0034-calendario-electoral-y-ventanas.md)

## Contexto

Las pantallas 2 y 3 dibujan los periodos de restricción de la Ley de Garantías (línea de tiempo de 2022 a 2027 y sombreado del gráfico mensual), y la 4 distingue los años de tratamiento de los de control. Esas fechas solo viven en `pipeline/reference/electoral_calendar.toml`; `data/outputs/` no las publica. El tablero no puede calcularlas ni escribirlas a mano (el dominio vive en Python).

## Decisión

- **Salida `electoral_calendar.json`** (`publish/electoral_calendar.py`, modelo `ElectoralCalendar`) con dos listas:
  - `restrictions`, ordenadas por inicio: `cycle`, `scope`, `start`, `end`, `status` y `sources`.
  - `comparison_windows`, ordenadas por año: `year`, `role` (`treatment` o `control`), `window_start`, `window_end`, `denominator_end` y `reference_restriction_end`. Son las ventanas de I2 (R11, R12), para que la pantalla 4 y la metodología digan qué compara cada año sin recalcularlo.
- **`status` se calcula contra la fecha de corte (R12), nunca contra el reloj:** `ended` si el fin es anterior al corte, `upcoming` si el inicio es posterior, y `ongoing` en cualquier otro caso. Los extremos son inclusivos: el día de la elección sigue restringido. El tablero no compara fechas.
- **Sin supresión.** Son fechas públicas con su fuente, no cifras de contratos; R13 no aplica.
- **Las locales de 2027 entran al calendario como verificadas.** La Registraduría fijó la jornada para el domingo 31 de octubre de 2027 (Resolución 12338 del 28 de octubre de 2026). El parágrafo del artículo 38 de la Ley 996 prohíbe los convenios interadministrativos en los cuatro meses anteriores, igual que en 2023, así que la restricción va del 30 de junio al 31 de octubre de 2027 con alcance `interadministrative`. No genera ventanas de I2 (ADR 0034), por lo que las cifras publicadas no cambian.

## Consecuencias

- Las pantallas 2, 3 y 4 leen todo del contrato: fechas, papel de cada año y si el periodo ya pasó, está en curso o viene.
- Cambiar una fecha es editar el TOML y su fuente; la salida se regenera sola.
- Con corte al 30 de octubre de 2026, 2027 sale como `upcoming`; cuando la copia avance, el estado cambia sin tocar código.
- La resolución de la Registraduría se verificó por prensa porque `registraduria.gov.co` rechazó la consulta automática; conviene confirmarla en el sitio oficial antes de la entrega.

## Alternativas

- **Que el tablero lea el TOML o escriba las fechas:** descartada. Rompe la regla 2 y duplica la fuente de verdad.
- **Publicar solo las restricciones, sin ventanas:** descartada. La pantalla 4 tendría que inferir qué años son tratamiento y control, y esa lógica es del dominio.
- **Publicar 2027 como estimada:** descartada. La fecha de la elección ya es oficial y la regla del artículo 38 es fija; una marca de estimada no aporta nada.
