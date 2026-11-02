# 0020. Catálogo de modalidades en TOML con una sola clave de comparación

- **Estado:** Aceptada
- **Fecha:** 2026-11-02
- **Fuente:** [docs/bitacora.md](../bitacora.md#2-nov-2026--catálogo-de-modalidades-contra-la-copia)

## Contexto

R6 traduce cada texto crudo de modalidad a un valor cerrado con dos propiedades: si es contratación directa y si es competitiva. Los textos llegan escritos de formas distintas según la fuente: variantes de mayúsculas en SECOP II, mojibake en MEData · Ejecución (se repara antes, ADR 0010) y letras perdidas en el Plan Anual («mnima cuanta»).

## Decisión

- **El catálogo vive en `pipeline/reference/procurement_methods.toml`**, una entrada por modalidad con `code`, `label`, `direct_award`, `competitive` y la lista `raw` de textos conocidos. Las dos propiedades se declaran una vez por modalidad, no por cada texto. TOML se lee con `tomllib`, sin dependencias nuevas, y es el mismo formato de `sources.toml`.
- **Una sola clave de comparación para todas las fuentes** (`catalog_key`): sin mayúsculas, tildes ni espacios. Así «Contratacion Directa», «contratacion directa» y «Contratación directa» comparten entrada, y solo se listan las formas que difieren más allá de eso.
- **Un valor no reconocido, vacío o nulo cae en `other`**, que el catálogo debe declarar. «Solicitud de información a los Proveedores» y «Subasta de prueba» no son modalidades de selección y quedan ahí.
- **Una clave repetida entre entradas detiene la carga** con un error que nombra el texto, para que un texto nunca pertenezca a dos modalidades.
- `classify_procurement_method` no repara la codificación: recibe texto ya reparado, para que esa reparación siga siendo un paso visible (ADR 0010).

## Consecuencias

- Agregar una variante es una línea en el TOML y no toca el código.
- Las pruebas recorren la copia y fijan que los únicos valores no reconocidos son esas dos modalidades de Procesos; si una fuente trae un texto nuevo, la prueba falla y obliga a revisar el catálogo.
- La normalización del Plan Anual (tarea 10) reutiliza este catálogo.

## Alternativas

| Criterio | TOML con clave única (elegida) | CSV de texto a modalidad | Diccionario en Python |
|---|---|---|---|
| Propiedades por modalidad | Una vez | Repetidas por fila | Una vez |
| Curación a mano sin tocar código | Sí | Sí | No |
| Reglas de `reference/` (R10) | Cumple | Cumple | Incumple |
