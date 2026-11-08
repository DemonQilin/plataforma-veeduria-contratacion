# Reglas de negocio

Qué hace el pipeline y con qué reglas. Cada regla tiene un identificador estable (R1–R17) que se cita en el código, en las pruebas, en los archivos SQL y en la ficha de hallazgos, para que cada regla sea explícita, se pueda probar y se pueda explicar al jurado.

Los detalles de implementación (herramientas, estructura de carpetas, convenciones de código) están en `pipeline/CLAUDE.md` y en [`adr/`](adr/). Los nombres en código de cada concepto están en el glosario del `CLAUDE.md` de la raíz.

---

## 1. Flujo

```
Extraer → Normalizar → Consolidar → Cruzar → Calcular → Publicar
```

| Etapa | Qué hace | Resultado |
|---|---|---|
| Extraer | Pide a las fuentes solo la lista blanca de columnas. Es la única etapa que usa la red | `data/snapshot/`: valores crudos sin información personal, más `manifest.json` |
| Normalizar | Repara codificación, unifica formatos, traduce valores crudos a catálogos cerrados y renombra según el glosario | Registros limpios por fuente |
| Consolidar | Convierte varias filas del mismo contrato o proceso en un único registro canónico | Un contrato por referencia, un proceso por portafolio |
| Cruzar | Une procesos, contratos, adiciones y MEData por las llaves validadas | Contratos enriquecidos con competencia, secretaría y adiciones |
| Calcular | Aplica las fórmulas de [`indicadores.md`](indicadores.md) por año, mes y secretaría | Indicadores con numerador, denominador y tamaño de muestra |
| Publicar | Aplica la supresión de celdas pequeñas y exporta las salidas | `data/outputs/` con fecha de corte |

El pipeline tiene dos modos:

- **`--from-snapshot`:** ejecuta desde Normalizar usando la copia versionada. No usa la red. Es el camino del jurado.
- **`--refresh`:** ejecuta desde Extraer, actualiza la copia y continúa. La extracción es todo o nada: si una consulta falla, la copia y el `manifest.json` quedan como estaban. El Plan Anual de Adquisiciones solo se vuelve a pedir con `--force-procurement-plan` o si aún no tiene entrada en el manifiesto.

---

## 2. Conceptos del dominio

| Concepto | Qué representa | Atributos clave |
|---|---|---|
| **Proceso** | Un procedimiento de selección (portafolio en SECOP II) | Modalidad, si es competitivo, fechas de publicación y cierre, precio base, oferentes únicos, unidad que lo adelanta |
| **Contrato** | Un contrato del Distrito, identificado por su referencia | Fecha de firma canónica, modalidad, tipo de contrato, valor inicial y final, duración, tipo de proveedor, secretaría, proceso de origen |
| **Proveedor** | Quien recibe el contrato | Tipo (natural, jurídica, no definido). Nombre y NIT solo si el NIT empieza por 8 o 9 y tiene 9 o 10 dígitos (ADR 0017, ADR 0026) |
| **Adición** | Un cambio posterior a la firma | Contrato, fecha, tipo y valor (este último solo desde MEData) |
| **Restricción electoral** | Un periodo de la Ley de Garantías | Ciclo, qué restringe (contratación directa, convenios), inicio, fin, ámbito, fuente |
| **Ventana de comparación** | El tramo que se compara entre años | Año, inicio, fin, papel (tratamiento o control) |
| **Indicador** | Un valor calculado | Identificador, nivel (Distrito, secretaría), periodo, valor, numerador, denominador, n, fecha de corte, versión de las reglas |

---

## 3. Catálogos

Los catálogos viven en `pipeline/reference/`. Un valor no reconocido no rompe el pipeline: se clasifica como «Otra» (o «Otro») y aparece en el reporte de calidad para revisar el catálogo.

### Modalidad

Cada texto crudo se traduce a un valor cerrado con dos propiedades: si es contratación directa y si es competitiva.

| Modalidad normalizada | Textos crudos que agrupa | Directa | Competitiva |
|---|---|:---:|:---:|
| Contratación directa | «Contratación directa», «Contratación Directa (con ofertas)», variantes de mayúsculas | Sí | No |
| Régimen especial | «Contratación régimen especial», «… (con ofertas)» | No | No |
| Licitación pública | «Licitación pública», «Licitación pública Obra Publica» | No | Sí |
| Selección abreviada | Menor cuantía, sin manifestación de interés, subasta inversa | No | Sí |
| Concurso de méritos | «Concurso de méritos abierto» | No | Sí |
| Mínima cuantía | «Mínima cuantía» | No | Sí |
| Otra | Cualquier valor no reconocido | No | No |

El catálogo es `pipeline/reference/procurement_methods.toml` (ADR 0020). En todas las fuentes, los textos se comparan sin mayúsculas, tildes ni espacios internos antes de mapearlos, porque el Plan Anual de MEData los trae escritos de formas como «contratacion directa» o «concurso de m eritos». Los textos de MEData · Ejecución se comparan después de reparar la codificación (ADR 0010).

Dos modalidades de SECOP II · Procesos no están en la tabla y caen en «Otra»: «Solicitud de información a los Proveedores» (786 filas) y «Subasta de prueba» (343). Ninguna está adjudicada, así que no entran en R9.

### Tipo de contrato

Prestación de servicios, interadministrativo, obra, suministro y compraventa, operación de crédito público y otro. El catálogo es `pipeline/reference/contract_types.toml` (ADR 0022).

- La prestación de servicios se separa porque explica la renovación de enero.
- El interadministrativo se identifica por la justificación de la modalidad en SECOP II o por la causal en MEData, y gana sobre el tipo crudo: 1.399 de los 1.446 contratos interadministrativos de SECOP II traen el tipo «Otro». Las variantes de causal de MEData que cuentan son «Contrato Interadmin», «Adic. Contr. Interad», «Cto Interadm Segurid», «Convenio Interadmin» y «Ad. Cto InterSegurid».
- Los tipos sin categoría propia (arrendamiento, interventoría, consultoría, seguros, comodato, etc.) se listan bajo «Otro» para que el reporte de calidad solo muestre valores nuevos. «No» y «No Especificado» de Procesos caen ahí y se reportan.

### Tipo de proveedor

El catálogo es `pipeline/reference/supplier_types.toml` (ADR 0022). Un valor no reconocido cae en «No definido».

| Tipo | Valores de `tipodocproveedor` |
|---|---|
| Persona jurídica | NIT (el nombre y el documento solo se piden si empieza por 8 o 9 y tiene 9 o 10 dígitos, ADR 0017 y ADR 0026) |
| Persona natural | Cédula de ciudadanía, cédula de extranjería, pasaporte, permiso de protección temporal |
| No definido | «No definido», «Otro» |

---

## 4. Reglas

### Ámbito

- **R1 · Entidad.** Solo entra el registro cuyo nombre de entidad es exactamente `DISTRITO ESPECIAL DE CIENCIA TECNOLOGIA E INNOVACION DE MEDELLIN`. El NIT no basta, porque lo comparten el Concejo y la Personería.
- **R2 · Periodo.** Entran los contratos con fecha de firma desde el 1 de enero de 2022 hasta la fecha de corte. La extracción puede traer años anteriores como contexto; esta regla se aplica en la normalización.

### Consolidación

- **R3 · Contrato canónico.** Las filas con la misma referencia se consolidan en un solo contrato. La referencia, llave de cruce con MEData, se guarda sin espacios en los extremos, incluido el espacio no separable (ADR 0046). Si SECOP II la escribe «NNNNNNNNNN de AAAA» (sin distinguir mayúsculas, con «del» o un guion) o con un punto, guion o asterisco final, se reduce al número, que es lo que guarda MEData; las filas que quedan con la misma referencia se consolidan (ADR 0047).
  - La fecha de firma canónica es la primera fecha no vacía.
  - El valor inicial es el de la primera versión firmada, que en SECOP II ya incluye las adiciones (D3); el valor final, el que indica D3.
  - «Primera» se decide por la marca de tiempo completa de la firma; si coinciden, por el identificador del contrato.
  - Los atributos del contrato (proceso, modalidad, tipo, proveedor) salen de la primera versión firmada. Si las versiones apuntan a procesos distintos, gana el proceso de la primera firma y la referencia se reporta en la calidad de datos. El estado, los días adicionados y la fecha de fin salen de la versión más reciente.
- **R4 · Contratos sin firma.** Se excluyen los registros sin fecha de firma (por ejemplo, los que solo fueron enviados al proveedor). Cada exclusión se reporta en la calidad de datos.
- **R5 · Proceso canónico.** Las filas con el mismo portafolio se consolidan en un solo proceso. El número de oferentes es el máximo reportado entre sus filas.
  - El proceso está adjudicado si alguna de sus filas lo está.
  - El precio base y el valor adjudicado son el máximo entre las filas, porque las filas repetidas no se suman.
  - Los demás campos salen de la fila con la primera fecha de publicación.

### Clasificación

- **R6 · Modalidad y tipo.** Se aplican los catálogos de la sección 3.
- **R7 · Crédito público.** Las operaciones de crédito público cuentan en los conteos, pero se excluyen de todo indicador de valor.
- **R8 · Secretaría.** Se asigna en este orden: la de MEData si el contrato está allí; si no, la unidad del proceso en SECOP II; si no, «Sin asignar». Los textos de las dos fuentes se traducen con el catálogo `pipeline/reference/departments.toml` (ADR 0030); un texto que no está en el catálogo no asigna secretaría y se reporta. El porcentaje de «Sin asignar» se reporta.

### Indicadores

- **R9 · Proceso válido para oferente único.** Debe ser competitivo y estar adjudicado. Si reporta cero oferentes, es un error de datos y se excluye.
- **R10 · Calendario electoral.** Las fechas de la Ley de Garantías son una tabla de referencia curada a mano, con la fuente de cada fecha (ver [`fuentes.md`](fuentes.md)). No se infieren de los datos.
- **R11 · Ventanas.** Las ventanas de comparación se derivan del calendario, según la metodología de [`indicadores.md`](indicadores.md).
- **R12 · Fecha de corte.** Es la fecha de firma más reciente en la copia de datos, nunca la fecha del reloj. Todo indicador lleva su fecha de corte, y los años incompletos se comparan solo en el tramo común.

### Privacidad

- **R13 · Supresión de celdas pequeñas.** Ningún indicador desagregado (por secretaría o por mes) se publica si se calcula sobre menos de 5 contratos. Se publica como «datos insuficientes»: la celda conserva su n (`sample_size`) y oculta numerador, denominador y razón. La cifra anual del Distrito siempre se publica. Así una cifra pequeña no permite identificar a una persona cruzándola con el portal de SECOP. Si un desglose (las secretarías de un periodo o los meses de un año) queda con una sola celda suprimida, se suprime también la siguiente más chica, para que no se despeje restando del total (D6). En la serie mensual, el conteo es la `n` y siempre se publica; la supresión recae en el valor (ADR 0040). La supresión se aplica en la etapa de publicación (`publish/suppression.py`), y `run` la ejecuta siempre antes de escribir `indicators.json`: el tablero nunca recibe una cifra sin suprimir.
- **R14 · Proveedores.** Ningún proveedor se nombra, sea persona natural o jurídica, como pidieron los organizadores el 6 nov (ADR 0049). El nombre del proveedor no entra a la copia de datos. Solo se usa el documento de los proveedores que son personas jurídicas, para el indicador de concentración (I4), que se publica solo agregado (ADR 0045). Se considera persona jurídica al proveedor con NIT que empieza por 8 o 9 y tiene 9 o 10 dígitos (ADR 0017, ADR 0026). El identificador es el NIT sin dígito de verificación (ADR 0027).

### Calidad

- **R15 · Conciliación SECOP–MEData.** Para el periodo común (los meses que cubre MEData) se calcula, por mes, qué proporción de contratos aparece en ambas fuentes: los de ambas ÷ la unión de las dos. Si un mes queda por debajo del 80 %, el tablero lo advierte. El mes sale de la fecha de firma de SECOP II y, si el contrato no está allí, de la de MEData. Además se guarda la cobertura de cada fuente en la otra (ADR 0031).
- **R16 · Trazabilidad.** Cada indicador guarda numerador, denominador, n, fuentes, fecha de corte y versión de las reglas, para que cualquier cifra se pueda reconstruir.
- **R17 · Planeación.** El Plan Anual de Adquisiciones se compara con la ejecución solo de forma agregada, porque no tiene llave por contrato.

---

## 5. Decisiones de dominio

Se resolvieron siguiendo la práctica habitual en análisis de compras públicas. Las decisiones técnicas (herramientas, formatos, estructura) están en [`adr/`](adr/).

| # | Pregunta | Decisión | Por qué |
|---|---|---|---|
| D1 | ¿La «Contratación Directa (con ofertas)» cuenta como directa? | Sí | En SECOP II es una variante de la contratación directa: la entidad pide cotizaciones, pero no abre competencia |
| D2 | ¿El régimen especial se suma a la contratación directa? | No en el indicador principal. I1 se reporta en dos niveles: contratación directa sola y «no competitiva» (directa más régimen especial) | La literatura de *red flags* mide los procedimientos no abiertos en conjunto, pero el público reconoce el término «contratación directa» |
| D3 | ¿Qué valor representa al contrato? | Inicial: el valor de la primera versión firmada en SECOP II, que ya incluye las adiciones registradas hasta la fecha de corte, porque SECOP II sobrescribe el valor en la misma fila (ADR 0044). Final: MEData si existe; si no, la versión más reciente de SECOP II. El valor inicial sin adiciones solo existe en MEData (2022–2023) | Es la distinción entre valor firmado y valor modificado que usa el estándar de datos de contratación abierta (OCDS). SECOP II no deja separarlos: en 2022 y 2023 la diferencia mueve menos de un punto las proporciones por valor de I1 e I2 |
| D4 | ¿Qué umbral de supresión? | 5 contratos | Es un umbral habitual en control de divulgación estadística para datos no sensibles |
| D5 | ¿Cómo se tratan las secretarías que cambiaron de nombre? | Se conserva el nombre histórico y se agrega una tabla de equivalencias solo si afecta las comparaciones | Evita reescribir la historia de los datos y mantiene la trazabilidad |
| D6 | ¿Cómo se evita despejar una celda suprimida restando del total? | Supresión complementaria: si un desglose tiene una sola celda suprimida, se suprime también la de menor n; se repite hasta que ningún desglose cambie | Es la supresión secundaria habitual en control de divulgación estadística; una sola celda oculta se despeja con el total y las demás |

---

## 6. Automatización

- **Ejecución.** El pipeline corre a demanda y en la integración continua. La ejecución semanal programada se activa después de la final (12 nov 2026); hasta entonces, la fecha de corte publicada queda fija para que el tablero coincida con la ficha de hallazgos.
- **Idempotencia.** Con la misma copia de datos, el pipeline produce exactamente la misma salida.
- **Falla segura.** Si una fuente no responde, se conserva la última publicación válida y el tablero muestra que los datos no están al día. Nunca se publica una salida a medias.
- **MEData.** Como ya no se actualiza, se guarda la huella del archivo en el `manifest.json`. Si cambia, el pipeline lo detecta y lo reporta.

---

## 7. Salidas que consume el tablero

Se publican en `data/outputs/` como JSON. Su estructura la definen los modelos de Pydantic del pipeline, que se exportan como JSON Schema a `data/schema/` y como tipos de TypeScript al tablero.

| Salida | Contenido |
|---|---|
| Calendario electoral | Restricciones de la Ley de Garantías (ciclo, alcance, inicio, fin, estado frente a la fecha de corte y fuentes) y ventanas de comparación de I2 por año, con su papel de tratamiento o control. Sin supresión: son fechas públicas ([ADR 0041](adr/0041-calendario-electoral-publicado.md)) |
| Indicadores | Una fila por indicador, nivel y periodo, con los campos de trazabilidad de R16 (forma de la celda en el [ADR 0033](adr/0033-celda-de-indicador-en-el-contrato.md)) |
| Serie mensual | Contratos y valor por mes, modalidad y tipo, para las gráficas del hallazgo. El conteo siempre se publica; el valor se suprime con R13 y D6 ([ADR 0040](adr/0040-serie-mensual-con-valor-suprimido.md)) |
| Calidad de datos | Cobertura, conciliación SECOP–MEData, porcentaje sin secretaría, filas truncadas de MEData, valores no reconocidos en catálogos. `quality.json` publica la conciliación R15 por mes ([ADR 0038](adr/0038-r15-publicada-sin-supresion.md)), el porcentaje sin secretaría (R8), las filas truncadas de MEData, los registros sin firma excluidos (R4) y los valores no reconocidos de los catálogos (R6), sin supresión ([ADR 0042](adr/0042-calidad-de-datos-completa.md)). Los procesos que R9 excluye del oferente único se cuentan sobre los competitivos adjudicados ([ADR 0043](adr/0043-i3-oferente-unico.md)) |
| Metadatos | Fecha de corte, fuentes con enlace y licencia, versión de las reglas |

---

## 8. Qué se prueba

- **Catálogos:** cada texto crudo conocido cae en la categoría correcta, y uno desconocido cae en «Otra».
- **Consolidación:** casos con varias versiones de un contrato producen la fecha y los valores esperados.
- **Ventanas:** las fechas de cada año coinciden con el calendario de referencia.
- **Privacidad:** ninguna salida contiene columnas fuera de la lista blanca, y ninguna celda publicada tiene menos de 5 contratos.
- **Datos:** la conciliación SECOP–MEData de enero de 2022 se mantiene cerca de lo observado (723 frente a 727).
- **Determinismo:** dos ejecuciones con la misma copia producen salidas idénticas, byte a byte.