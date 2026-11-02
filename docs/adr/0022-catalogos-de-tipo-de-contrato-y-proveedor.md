# 0022. Catálogos de tipo de contrato y de proveedor en TOML; la justificación gana sobre el tipo

- **Estado:** Aceptada
- **Fecha:** 2026-11-02
- **Fuente:** [docs/bitacora.md](../bitacora.md#2-nov-2026--catálogos-de-tipo-de-contrato-y-de-proveedor)

## Contexto

R6 pide un catálogo de tipo de contrato y otro de tipo de proveedor. Al perfilar la copia aparece que «interadministrativo» no es un valor de `tipo_de_contrato`: 1.399 de los 1.446 contratos con justificación interadministrativa en SECOP II traen el tipo «Otro». MEData · Ejecución no tiene tipo de contrato, solo la causal.

## Decisión

- **Dos archivos en `pipeline/reference/`**, `contract_types.toml` y `supplier_types.toml`, con el mismo formato y la misma clave de comparación que el catálogo de modalidades (ADR 0020). La clave se llama ahora `catalog_key`, porque ya no es solo de modalidades.
- **La justificación (SECOP II) o la causal (MEData) interadministrativa gana sobre el tipo crudo.** Se declara en `interadministrative_justifications`, una lista única con los textos de ambas fuentes, porque el glosario trata las dos como `method_justification`.
- **Los tipos sin categoría propia se listan bajo `other`.** Así el reporte de calidad solo muestra lo realmente nuevo («No» y «No Especificado» de Procesos).
- **«Ley 489 Artículo 95/108» y «Conv. Coop. Internal» no cuentan como interadministrativos.** Desde 2022 no agregan ningún contrato a las variantes ya listadas, y la tercera es cooperación internacional.
- **Un tipo de proveedor no reconocido cae en `undefined`**, no en un tipo supuesto.
- **Ambos catálogos exigen su categoría por defecto** (`other`, `undefined`) y fallan al cargar si un texto está repetido; el de tipos de contrato exige además `interadministrative`.

## Consecuencias

- Las tareas 2 a 6 reutilizan `classify_contract_type`, `is_interadministrative` y `classify_supplier_type`.
- Las pruebas golden fijan 1.446 interadministrativos en `secop_contracts` y los únicos valores sin reconocer en Procesos; si la copia cambia, fallan y obligan a revisar.
- Un contrato de MEData con causales distintas entre filas queda pendiente para la consolidación.

## Alternativas

| Criterio | Elegida | Solo `tipo_de_contrato` | Una lista por fuente |
|---|---|---|---|
| Encuentra los 1.446 interadministrativos | Sí | No (47) | Sí |
| Un solo lugar para mantener | Sí | Sí | No |
