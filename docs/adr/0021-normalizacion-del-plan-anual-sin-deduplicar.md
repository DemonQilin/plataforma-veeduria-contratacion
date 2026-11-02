# 0021. Normalización del Plan Anual: todas las líneas, valores sin inventar

- **Estado:** Aceptada
- **Fecha:** 2026-11-02
- **Fuente:** [docs/bitacora.md](../bitacora.md#2-nov-2026--normalización-del-plan-anual)

## Contexto

La copia del Plan Anual de Adquisiciones tiene 18.764 líneas y seis columnas de la lista blanca. Al perfilarla aparecen tres decisiones que no están en la documentación: líneas idénticas, valores que no son enteros y 84 grafías de unidad.

## Decisión

- **Se conservan todas las líneas.** Hay 3.625 líneas idénticas en las seis columnas, pero la lista blanca dejó fuera `descripcion`, así que son necesidades distintas del plan. Con todas las líneas se reproducen las cifras documentadas (726 contratos directos planeados para enero de 2022; 46, 57 y 52 % en enero para 2014, 2018 y 2022). Quitarlas las rompería.
- **El valor estimado solo se convierte si la lectura es segura.** 18.752 valores son enteros; 10 vienen en notación científica con coma («1,10E+11») y se convierten; 2 («1,2611» y «5,1995») no tienen lectura segura y quedan en `NULL`. El 0 se conserva (11 líneas). I8 cuenta líneas y no suma valores, así que ninguna de estas decisiones cambia el hallazgo.
- **Las unidades no se unifican.** I8 es por año, y D5 manda agregar equivalencias solo si afectan las comparaciones. Si R17 llega a compararse por unidad, hará falta un catálogo de equivalencias.
- **El mes desconocido es `NULL`**, no un mes supuesto; la copia actual no tiene ninguno.
- **El catálogo de modalidades (ADR 0020) se aplica en Python sobre los textos distintos** y llega al SQL como listas paralelas. `create_function` de DuckDB exige numpy, que no es dependencia, y un `CASE` con 15 grafías duplicaría el catálogo.
- **El CSV se lee en un `WITH ... AS MATERIALIZED`.** Sin eso, DuckDB empuja el `TRY_CAST` al lector del CSV y falla con «1,10E+11» pese a `all_varchar`.

## Consecuencias

- `procurement_plan` queda con ocho columnas en inglés (`year`, `estimated_start_month`, `procurement_method`, `direct_award`, `competitive`, `estimated_value`, `department`, `unspsc_codes`).
- Las pruebas golden fijan 18.764 líneas, ninguna en `other`, ningún mes nulo y exactamente 2 valores nulos; si la copia cambia, fallan y obligan a revisar.
- `unidad_de_contratacion` y `codigos_unspsc` pasan sin tocar; los sufijos como « c06» de los códigos siguen ahí.

## Alternativas

| Criterio | Elegida | Quitar líneas idénticas | Sumar el valor en notación científica a ciegas |
|---|---|---|---|
| Reproduce 726 y 46/57/52 % | Sí | No | Sí |
| Inventa datos | No | No | Sí, en 2 valores |
