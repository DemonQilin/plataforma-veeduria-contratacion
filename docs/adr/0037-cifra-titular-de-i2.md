# 0037. Cifra titular de I2: definición base por número de contratos

- **Estado:** Aceptada
- **Fecha:** 2026-11-05
- **Fuente:** [docs/indicadores.md](../indicadores.md) sección 3, [ADR 0036](0036-i2-variante-sin-interadministrativos.md)

## Contexto

El punto de decisión 1 (T8) pedía elegir qué lectura de I2 lleva la cifra titular. Con la copia de corte del 30 de octubre de 2026, el criterio 1 (menor año de tratamiento frente al máximo de control) da:

| Lectura | Medida | Brecha (puntos) |
|---|---|---:|
| Base | Número | 27,6 |
| Base | Valor | 0,9 |
| Sin interadministrativos | Número | 30,5 |
| Sin interadministrativos | Valor | 26,3 |

El criterio 1 se cumple en las cuatro combinaciones. La separación es mayor sin interadministrativos, pero esa variante se agregó el 4 de noviembre, después de ver que I2 era sensible a ellos (ADR 0036).

## Decisión

- La cifra titular es la **definición base, por número de contratos**. La definición se fijó el 3 de noviembre y no se cambia después de ver los resultados.
- **El valor es un complemento.** Se presenta con la nota de que, con la definición base, 2022 supera al mejor año de control (2023) por 1,8 puntos.
- **`excluding_interadministrative` se publica como sensibilidad**, a la vista, sin sustituir a la definición base.

## Consecuencias

- No cambia el código, el contrato ni `data/outputs/`: las dos lecturas ya se publican.
- La frase del hallazgo usa las cifras de la definición base por número: 58 % y 65 % en 2022 y 2026, frente a 19–31 % en los años de control.
- Se declara como limitación que, por valor, el criterio 1 se cumple por menos de dos puntos (1,8) con la definición base.
- El titular se apoya además en la serie de planeación (criterio 2), que se cumple en las dos medidas.
