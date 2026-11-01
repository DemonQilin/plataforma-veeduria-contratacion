# 0007. Lista blanca de columnas en un solo archivo

- **Estado:** Aceptada
- **Fecha:** 2026-10-30
- **Fuente:** [docs/fuentes.md](../fuentes.md#8-lista-blanca-de-columnas)

## Contexto

Las fuentes publican datos personales: SECOP II trae nombres y documentos de supervisores, ordenadores del gasto, representantes legales y proveedores personas naturales, además de cuentas bancarias; MEData trae nombres y cédulas de contratistas y supervisores. Las bases del concurso prohíben que un entregable exponga datos personales, y el repositorio es público.

La lista de columnas permitidas se usa en al menos dos lugares: la extracción, que la convierte en el `$select` de cada consulta, y la prueba de privacidad, que verifica que nada se haya colado. Si cada uno tiene su propia copia, tarde o temprano dejan de coincidir, y la prueba pasa mientras la extracción pide una columna nueva.

Además, las fuentes se comportan distinto: SECOP II permite elegir columnas en la consulta, mientras que MEData · Ejecución solo se descarga completo.

## Decisión

- **`pipeline/sources.toml` es la única implementación de la lista blanca.** Por cada consulta declara el conjunto, el endpoint, el filtro, la llave de orden y las columnas permitidas.
- **También declara las columnas excluidas de forma explícita**, las de la tabla de [`fuentes.md`](../fuentes.md#8-lista-blanca-de-columnas). No se usan para filtrar; sirven como segunda red en las pruebas.
- **SECOP II Contratos usa dos consultas:** una con las columnas generales para todos los contratos, y otra con `documento_proveedor` y `proveedor_adjudicado` solo para `tipodocproveedor = 'NIT'` con documento que empiece por 8 o 9 (ver [0017](0017-proveedores-solo-nit-con-prefijo-8-o-9.md)). El nombre y el documento de personas naturales nunca se piden.
- **La extracción construye el `$select` desde `sources.toml`.** Nunca usa `$select=*`.
- **Para MEData, el parser conserva solo las columnas permitidas** antes de escribir la copia. El archivo completo queda en `data/raw/`, fuera de git.
- **La prueba de privacidad lee el mismo archivo** y verifica que:
  - las columnas de cada CSV de `data/snapshot/` estén contenidas en la lista permitida;
  - ninguna columna excluida aparezca en `data/snapshot/` ni en `data/outputs/`;
  - las listas permitida y excluida no se crucen;
  - `data/raw/` esté ignorado por git.
- **Cambiar la lista blanca exige actualizar `docs/fuentes.md` en el mismo commit**, con la razón de la columna nueva.

## Consecuencias

- La privacidad la garantizan el código y una prueba, no una convención.
- Una columna nueva en una fuente no se filtra sola: SECOP II solo devuelve lo que pide el `$select`, y el parser de MEData solo conserva lo permitido.
- Agregar una columna tiene fricción deliberada: tres archivos y una justificación.
- La lista de excluidas hay que mantenerla a mano si las fuentes agregan campos personales. No es la protección principal, así que una omisión ahí no expone datos.
- Las salidas de `data/outputs/` tienen su propio control: sus campos los definen los modelos de Pydantic (ver [0004](0004-contrato-pydantic-json-schema-ts.md)), y la supresión de celdas pequeñas se prueba aparte (R13).

## Alternativas

| Criterio | Archivo único con permitidas y excluidas (elegida) | Constantes en cada extractor | Solo lista de excluidas | Filtrar al publicar |
|---|---|---|---|---|
| Fuentes de verdad | Una | Una por extractor, más la de la prueba | Una | Una |
| Columna nueva en la fuente | No entra | No entra | Entra | Llega a la copia |
| Datos personales en el repositorio | Nunca | Nunca, si las copias coinciden | Posible | Sí, en `data/snapshot/` |

- **Constantes en cada extractor:** descartada. La lista queda repartida y la prueba necesita su propia copia.
- **Solo lista de excluidas:** descartada. Cualquier columna personal que la fuente agregue en el futuro pasaría sin aviso.
- **Filtrar solo al publicar:** descartada. Los datos personales llegarían a `data/snapshot/`, que se versiona en un repositorio público.