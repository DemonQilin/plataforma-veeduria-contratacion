# 0017. Proveedores: solo NIT que empiezan por 8 o 9

- **Estado:** Aceptada
- **Fecha:** 2026-11-01
- **Fuente:** [docs/bitacora.md](../bitacora.md#1-nov-2026--orden-de-secop-ii-procesos-y-nit-de-proveedores)

## Contexto

El ADR [0007](0007-lista-blanca-unica.md) asumió que un NIT identifica a una persona jurídica. En Colombia una persona natural también puede tener NIT. De los 4.508 contratos con `tipodocproveedor = 'NIT'` al 1 nov, 42 (10 documentos distintos) no empiezan por 8 ni por 9, el prefijo habitual de las empresas.

El prefijo es un indicio, no una prueba: no demuestra que esos 10 sean personas naturales ni que el resto sean empresas. El repositorio es público y la consulta de proveedores escribe nombre y documento. Los organizadores aún no responden la pregunta sobre el tratamiento de datos de proveedores; se espera antes del 4 nov.

## Decisión

- **La consulta `secop_contracts_suppliers` pide solo NIT que empiezan por 8 o 9:** `tipodocproveedor = 'NIT' AND (documento_proveedor LIKE '8%' OR documento_proveedor LIKE '9%')`.
- **La prueba de privacidad exige los dos filtros** en toda consulta que pida columnas del proveedor, y rechaza filas de la copia cuyo documento tenga otro prefijo. El mensaje cita la línea, nunca el valor.
- **Los contratos con NIT de otro prefijo siguen en `secop_contracts`**, con su `tipodocproveedor`, pero sin nombre ni documento del proveedor.
- La decisión rige hasta que respondan los organizadores. Si piden más restricción, se cambia en `sources.toml`, en la prueba y en este ADR.

## Consecuencias

- Queda un riesgo residual: un NIT de persona natural que empiece por 8 o 9 pasa el filtro.
- Los indicadores que usen el nombre o el documento del proveedor no verán esos contratos.
- El filtro viaja en el `$where`, así que los datos excluidos nunca salen de la API.

## Alternativas

- **Esperar la respuesta de los organizadores:** descartada. Bloquea la tarea de proveedores sin necesidad, porque el filtro se puede ajustar después.
- **Mantener solo el filtro `NIT`:** descartada. Escribiría en un repositorio público el nombre de posibles personas naturales.
- **No pedir proveedores:** descartada. Los indicadores de concentración los necesitan.
