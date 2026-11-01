# Fuentes

Conjuntos de datos, campos, llaves de cruce, lista blanca de columnas, problemas de calidad y calendario de la Ley de Garantías.

Lo que aquí se describe está validado con consultas reales al 29 oct 2026. Las cifras de exploración y su fecha están en [`bitacora.md`](bitacora.md).

---

## 1. Conjuntos de datos

| Fuente | Identificador | Papel | Cobertura validada | Actualización |
|---|---|---|---|---|
| SECOP II · Contratos Electrónicos | `jbjy-vk9h` | Base del análisis | Distrito: 1.300–1.700 contratos por año desde 2018 | Diaria |
| SECOP II · Procesos de Contratación | `p6dx-8zbt` | Competencia, plazos y precio base | Distrito: 3.000–4.100 procesos por año desde 2020 | Diaria |
| SECOP II · Adiciones | `cb9c-h8sn` | Ocurrencia y fecha de adiciones | Sin montos | Diaria |
| MEData · Ejecución contractual histórico | `1-028-12-000088` | Validación cruzada, secretaría y valor de adiciones | 2.939 contratos firmados entre el 4 ene 2022 y el 30 jun 2023 | Irregular; última en dic 2023 |
| MEData · Plan anual de adquisiciones histórico | `1-028-11-000089` | Planeación: mes estimado de inicio, modalidad, valor estimado y unidad | 18.764 líneas planeadas, vigencias 2014 a 2023; 27 unidades en 2022 | Irregular; última en sep 2023 |

Otros conjuntos identificados, sin uso en el MVP: Ejecución de contratos (`mfmm-jqmq`) y Proveedores registrados (`qmzu-gj57`).

---

## 2. SECOP II · Contratos Electrónicos (`jbjy-vk9h`)

Validado con el diccionario oficial de Colombia Compra Eficiente (ago. 2025) y consultas reales a la API.

| Necesidad | Campo |
|---|---|
| Llave única | `id_contrato` |
| Cruce con Procesos | `proceso_de_compra` |
| Cruce con MEData | `referencia_del_contrato` (número de contrato del Distrito, serie 4600…) |
| Filtrar la entidad | `nombre_entidad` exacto |
| Modalidad y causal | `modalidad_de_contratacion`, `justificacion_modalidad_de` |
| Fecha para la serie | `fecha_de_firma` |
| Valor | `valor_del_contrato`, `dias_adicionados` |
| Persona natural o jurídica | `tipodocproveedor` (NIT frente a cédula) |

**Lo que hay que saber:**

- **Filtro de entidad.** El NIT `890905211` lo comparten el Distrito, el Concejo y la Personería. Se filtra por `nombre_entidad = 'DISTRITO ESPECIAL DE CIENCIA TECNOLOGIA E INNOVACION DE MEDELLIN'` (R1).
- **Duplicados.** Una referencia puede tener varios `id_contrato` (modificaciones o envíos al proveedor). Se consolida antes de contar (R3).
- **Modalidad inconsistente.** Conviven «Contratación directa» y «Contratación Directa (con ofertas)», entre otras variantes. Se normaliza con el catálogo de [`reglas.md`](reglas.md).
- **Valores atípicos.** Las operaciones de crédito público inflan los totales: un solo contrato de 2025 vale 503 mil millones. Se excluyen de los indicadores de valor (R7).
- **Adiciones.** Sigue sin confirmarse si `valor_del_contrato` ya incluye las adiciones.

## 3. SECOP II · Procesos de Contratación (`p6dx-8zbt`)

El indicador de oferente único es viable: el campo está poblado y aparecen procesos competitivos adjudicados con un solo oferente.

| Necesidad | Campo |
|---|---|
| Cruce con Contratos | `id_del_portafolio` = `proceso_de_compra` (no `id_del_proceso`) |
| Oferente único | `proveedores_unicos_con`, `respuestas_al_procedimiento` |
| Plazo de publicación | `fecha_de_publicacion_del`, `fecha_de_recepcion_de` |
| Desviación de valor | `precio_base` frente a `valor_total_adjudicacion` |
| Dependencia | `nombre_de_la_unidad_de` |

**Lo que hay que saber:**

- Las filas se repiten por lote o adjudicación. Se consolida por `id_del_portafolio` (R5).
- **Sin filtro de fecha:** el conjunto trae procesos desde 2015, y un contrato firmado en 2022 puede venir de un proceso publicado antes. Se extraen todos los del Distrito; 633 no tienen fecha de publicación.
- **Orden:** se pagina por `:id` y la copia se ordena en local (ADR 0016). No hay llave natural: el par portafolio-proceso se repite hasta 84 veces.
- **Verificado el 30 oct:** el nombre de la entidad en Procesos se escribe igual que en Contratos (23.400 filas).

## 4. SECOP II · Adiciones (`cb9c-h8sn`)

- Solo trae tipo, descripción y fecha de cada adición, sin montos.
- No tiene campo de entidad: se consulta por `id_contrato` de los contratos del Distrito, en lotes.

## 5. MEData · Ejecución contractual histórico (`1-028-12-000088`)

- Cada fila es una línea presupuestal de un contrato, no un contrato. CSV de 26,7 MB y 25.783 filas.
- Cubre contratos firmados del 4 ene 2022 al 30 jun 2023: 2.939 contratos únicos (1.730 de 2022 y 1.209 de 2023), de 28 secretarías.
- **Aporta lo que SECOP no tiene:** secretaría, proyecto, ruta presupuestal y el valor de cada adición como pedido aparte.
- **Cruce con SECOP II:** 2.628 de los 2.939 contratos (89 %) aparecen en SECOP II por `referencia_del_contrato`. El 11 % restante está por revisar: pueden ser contratos fuera de SECOP II (por ejemplo, en la Tienda Virtual del Estado) o referencias con formato distinto.
- **Solo se descarga completo.** La fuente no permite elegir columnas, así que el archivo se guarda en `data/raw/` (fuera de git) y la lista blanca se aplica al leerlo.

**Papel en el proyecto:** integración real para 2022 y el primer semestre de 2023, que incluyen un año electoral presidencial y la víspera de las locales. Valida SECOP contra la fuente del Distrito y aporta la secretaría, la causal detallada y el valor de las adiciones.

## 6. MEData · Plan anual de adquisiciones histórico (`1-028-11-000089`)

- 18.764 líneas planeadas, vigencias 2014 a 2023.
- Se consulta por la API SQL del portal (`/api/1/datastore/sql`), que permite elegir columnas.
- **No tiene llave por contrato:** un plan describe necesidades, no contratos firmados. Se compara con la ejecución solo de forma agregada, por año, mes, modalidad y unidad (R17).
- La API responde de forma intermitente (errores 504). Como el conjunto ya no se actualiza, la copia en `data/snapshot/` es en la práctica la fuente canónica.

---

## 7. Llaves de cruce

```
SECOP II Procesos.id_del_portafolio          ──  SECOP II Contratos.proceso_de_compra
SECOP II Contratos.id_contrato               ──  SECOP II Adiciones.id_contrato
SECOP II Contratos.referencia_del_contrato   ──  MEData Ejecución.contrato
```

El cruce con MEData se probó a escala: 2.628 de 2.939 contratos (89 %). En enero de 2022, la conciliación da 723 contratos en SECOP II frente a 727 en MEData.

---

## 8. Lista blanca de columnas

El pipeline solo pide o conserva estas columnas. Los datos personales nunca llegan a `data/snapshot/`, `data/outputs/` ni al repositorio.

**Este documento y `pipeline/sources.toml` deben coincidir.** Aquí se explica qué se usa y por qué; `sources.toml` lo implementa. Se cambian juntos, en el mismo commit, y la prueba de privacidad verifica que ninguna salida tenga columnas fuera de `sources.toml`.

### SECOP II · Contratos

Se hacen dos consultas, para que el nombre y el documento de personas naturales nunca se pidan:

- **Todos los contratos:** `id_contrato`, `referencia_del_contrato`, `proceso_de_compra`, `nombre_entidad`, `modalidad_de_contratacion`, `justificacion_modalidad_de`, `tipo_de_contrato`, `fecha_de_firma`, `fecha_de_inicio_del_contrato`, `fecha_de_fin_del_contrato`, `valor_del_contrato`, `dias_adicionados`, `estado_contrato`, `tipodocproveedor`, `codigo_de_categoria_principal`, `urlproceso`.
- **Solo con `tipodocproveedor = 'NIT'` y documento que empieza por 8 o 9:** `id_contrato`, `documento_proveedor` y `proveedor_adjudicado`. Una persona natural también puede tener NIT, y el prefijo es un indicio, no una prueba (ADR 0017).

### SECOP II · Procesos

`id_del_portafolio`, `id_del_proceso`, `nit_entidad`, `entidad`, `modalidad_de_contratacion`, `tipo_de_contrato`, `fecha_de_publicacion_del`, `fecha_de_recepcion_de`, `precio_base`, `valor_total_adjudicacion`, `respuestas_al_procedimiento`, `proveedores_unicos_con`, `adjudicado`, `nombre_de_la_unidad_de`.

### SECOP II · Adiciones

`id_contrato`, `tipo`, `fecharegistro`.

### MEData · Ejecución contractual

`contrato`, `fecha_contrato`, `modalidad`, `causal`, `nombre_secretaria`, `nombre_programa`, `valor_inicial_contrato`, `valor_total_adic_contrato`, `valor_fin_contrato`, `duracion_en_dias`, `estado`, `ano`, y `truncated`, una marca que agrega el parser en las filas incompletas; no viene de la fuente y no contiene datos personales.

### MEData · Plan anual de adquisiciones

`ano`, `fecha_estimada_inicio`, `modalidad_seleccion`, `valor_total_estimado`, `unidad_de_contratacion`, `codigos_unspsc`.

### Columnas excluidas de forma explícita

| Fuente | Columnas excluidas | Motivo |
|---|---|---|
| SECOP II · Contratos | Nombres y documentos del supervisor, del ordenador del gasto y del ordenador de pago; nombre, documento, domicilio y género del representante legal; banco, tipo y número de cuenta; nombre y documento del proveedor cuando es persona natural | Datos personales |
| SECOP II · Procesos | `nombre_del_adjudicador` | Nombre de un funcionario |
| SECOP II · Adiciones | `descripcion` | Texto libre que puede contener nombres |
| MEData · Ejecución | `contratista`, `cc_nit`, `supervisor_interventor`, `nit_ced_sup_interv` | Nombres y cédulas |
| MEData · Plan | `nombre_del_responsable`, `telefono_del_responsable`, `correo_del_responsable` | Datos de funcionarios |
| MEData · Plan | `descripcion` | Texto libre |

---

## 9. Problemas de calidad conocidos y tratamiento

| Problema | Fuente | Tratamiento | Regla |
|---|---|---|---|
| NIT compartido con Concejo y Personería | Contratos | Filtrar por nombre exacto de la entidad | R1 |
| Varios `id_contrato` por referencia (modificaciones, envíos al proveedor) | Contratos | Consolidar por referencia | R3 |
| Modalidades escritas de distintas formas | Contratos, Procesos | Normalizar a un catálogo cerrado | R6 |
| Operaciones de crédito público con valores enormes | Contratos | Excluirlas de los indicadores de valor | R7 |
| Filas repetidas por lote o adjudicación | Procesos | Consolidar por `id_del_portafolio` | R5 |
| Cada línea envuelta en comillas, con comillas escapadas de forma irregular dentro | MEData · Ejecución | Parser propio en la extracción, con pruebas sobre líneas reales | — |
| Tildes rotas por doble codificación UTF-8 | MEData · Ejecución | Reparar con `ftfy` en la normalización | — |
| 2.083 filas (8 %) truncadas en origen después de la columna 28: conservan contrato, fecha, modalidad, causal y secretaría, pero pierden valores, estado y enlace | MEData · Ejecución | Usarlas solo para los campos que conservan; marcarlas y reportar el porcentaje | — |
| La vista previa del portal carga el CSV en una sola columna | MEData · Ejecución | Trabajar siempre con la descarga | — |
| Adiciones sin montos | SECOP II | Montos solo desde MEData (2022–2023) | — |
| Modalidad y mes escritos de formas distintas («Contratacion Directa», «contratacion directa», «concurso de m eritos», «mnima cuanta») | MEData · Plan | Normalizar sin mayúsculas, tildes ni espacios internos, y mapear al catálogo | R6 |
| La API del portal responde de forma intermitente (errores 504) | MEData | Reintentos y copia con huella; el conjunto ya no se actualiza | — |

---

## 10. Calendario de la Ley de Garantías

Tabla de referencia curada a mano (R10). Vive en `pipeline/reference/` con la fuente de cada fecha; no se infiere de los datos.

| Ciclo | Restricción | Desde | Hasta | Estado |
|---|---|---|---|---|
| Presidencial 2022 | Contratación directa (todas las entidades) | 29 ene 2022 | 19 jun 2022 (2.ª vuelta) | Verificado |
| Locales 2023 | Convenios interadministrativos y nómina (territorial) | ≈29 jun 2023 | 29 oct 2023 | Por verificar |
| Congreso 2026 | Convenios interadministrativos (territorial) | 8 nov 2025 | 8 mar 2026 | Verificado |
| Presidencial 2026 | Contratación directa (todas las entidades) | 31 ene 2026 | 21 jun 2026 (2.ª vuelta) | Verificado |
| Locales 2027 | Convenios interadministrativos y nómina (territorial) | ≈jun 2027 | oct 2027 | Estimado |

---

## 11. Notas para la extracción

Los detalles de implementación están en `pipeline/CLAUDE.md` y en [`adr/`](adr/). Lo esencial:

- La API de datos.gov.co se consulta en formato CSV, con paginación ordenada y filtros en el `$where`.
- Solo la extracción usa la red. La copia en `data/snapshot/` guarda los valores tal como vienen de la fuente, ya filtrados por la lista blanca, con un `manifest.json` que registra consulta, filas, huella y fecha de corte.

---

## Referencias

- [Colombia Compra Eficiente · Diccionario de datos y ficha técnica de registros administrativos](https://www.colombiacompra.gov.co/wp-content/uploads/2026/01/Diccionario_de_Datos_RegistrosAdministrativos-1.pdf)
- [datos.gov.co · API de SECOP II Contratos](https://www.datos.gov.co/resource/jbjy-vk9h.json)
- [datos.gov.co · API de SECOP II Procesos](https://www.datos.gov.co/resource/p6dx-8zbt.json)
- [MEData · Ejecución contractual histórico](https://medata.app.medellin.gov.co/dataset/1-028-12-000088)
- [SECOP-MCP · identificadores de los conjuntos SECOP II](https://github.com/amgallego8/SECOP-MCP)
- [Bloomberg Línea · Ley de Garantías 2026](https://www.bloomberglinea.com/latinoamerica/colombia/ley-de-garantias-2026-que-es-a-quienes-impacta-este-ano-y-hasta-cuando-va/)
- [Valora Analitik · Ley de Garantías 2022](https://www.valoraanalitik.com/?p=158425)