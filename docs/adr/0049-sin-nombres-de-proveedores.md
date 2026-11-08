# 0049. Sin nombres de proveedores, ni en la copia ni en las salidas

- **Estado:** Aceptada. Reemplaza la parte del nombre del [ADR 0027](0027-normalizacion-de-proveedores.md) y vuelve definitiva la decisión del [ADR 0045](0045-i4-concentracion-agregada-de-proveedores.md).
- **Fecha:** 2026-11-08
- **Fuente:** reunión con los organizadores del 6 nov 2026 ([bitácora](../bitacora.md)), [docs/reglas.md](../reglas.md#4-reglas) (R14), [ADR 0017](0017-proveedores-solo-nit-con-prefijo-8-o-9.md), [ADR 0026](0026-proveedores-nit-de-9-o-10-digitos.md)

## Contexto

En la reunión del 6 de noviembre, los organizadores respondieron las preguntas del correo del 5 de noviembre:

- Todos los datos de MEData y de SECOP son válidos y están permitidos.
- No se deben mostrar nombres de personas naturales ni de personas jurídicas.
- Compartieron el formato del informe (`guia_entrega.pdf`).

El tablero ya cumplía la segunda respuesta: I4 se publica solo agregado desde el ADR 0045 y ningún proveedor sale de `data/outputs/`. Pero la copia de datos sí publicaba nombres: `data/snapshot/secop_contracts_suppliers.csv` traía `proveedor_adjudicado` en sus 4.459 filas, y la normalización calculaba `supplier_name` con el nombre más frecuente de cada NIT (ADR 0027), aunque ningún cálculo lo usaba. El repositorio es público y el jurado lo descarga, así que la copia también muestra lo que contiene.

## Decisión

- **`proveedor_adjudicado` pasa de la lista permitida a la lista excluida** de `secop_contracts_suppliers` en `pipeline/sources.toml`. Las pruebas de privacidad ya verifican que una columna excluida no aparezca en `data/snapshot/` ni en `data/outputs/`. Además, una prueba fija que esa columna esté excluida y no esté permitida en ninguna consulta.
- **La copia se rehízo sin volver a extraer.** Se quitó la columna de las mismas 4.459 filas con el escritor de la copia (`write_snapshot`). En `manifest.json` cambian la consulta (`select`) y la huella SHA-256; `row_count` y `extracted_at` se conservan, porque los datos no se volvieron a pedir a la API. Una extracción nueva habría traído contratos posteriores a la fecha de corte.
- **`suppliers` queda con `contract_id` y `supplier_id`.** Se mantiene la normalización del NIT del ADR 0027 y se elimina `supplier_name`.
- **I4 se publica solo agregado de forma definitiva.** El tablero no nombra proveedores.
- **SECOP II y MEData siguen siendo las fuentes.** Se descarta el plan B de usar MEData como fuente principal.

## Consecuencias

- `data/outputs/` no cambia: `run --from-snapshot` produce los mismos archivos.
- `documento_proveedor` (el NIT) sigue en la copia, porque I4 agrupa por proveedor. Es un identificador, no un nombre, y nunca sale de `data/outputs/`.
- Los nombres siguen en el historial de git, en las versiones anteriores de la copia. Para borrarlos habría que reescribir el historial, una decisión aparte del equipo.
- El próximo `--refresh` pide la consulta sin la columna del nombre.

## Alternativas

- **Dejar el nombre en la copia porque el tablero no lo muestra:** descartada. La copia se publica en el repositorio y el jurado la descarga.
- **Quitar también la consulta de proveedores:** descartada. I4 necesita el NIT para medir la concentración.
- **Volver a extraer la consulta de proveedores sin el nombre:** descartada. Traería filas nuevas que no coinciden con la fecha de corte del resto de la copia.
