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
- **`--refresh`:** ejecuta desde Extraer, actualiza la copia y continúa.

---

## 2. Conceptos del dominio

| Concepto | Qué representa | Atributos clave |
|---|---|---|
| **Proceso** | Un procedimiento de selección (portafolio en SECOP II) | Modalidad, si es competitivo, fechas de publicación y cierre, precio base, oferentes únicos, unidad que lo adelanta |
| **Contrato** | Un contrato del Distrito, identificado por su referencia | Fecha de firma canónica, modalidad, tipo de contrato, valor inicial y final, duración, tipo de proveedor, secretaría, proceso de origen |
| **Proveedor** | Quien recibe el contrato | Tipo (natural, jurídica, no definido). Nombre y NIT solo si el NIT empieza por 8 o 9 (ADR 0017) |
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

En el Plan Anual de Adquisiciones de MEData, los textos se comparan sin mayúsculas, tildes ni espacios internos antes de mapearlos, porque vienen escritos de formas como «contratacion directa» o «concurso de m eritos».

### Tipo de contrato

Prestación de servicios, interadministrativo, obra, suministro y compraventa, operación de crédito público y otro.

- La prestación de servicios se separa porque explica la renovación de enero.
- El interadministrativo se identifica por la justificación de la modalidad en SECOP II o por la causal en MEData.

### Tipo de proveedor

| Tipo | Valores de `tipodocproveedor` |
|---|---|
| Persona jurídica | NIT (el nombre y el documento solo se piden si empieza por 8 o 9, ADR 0017) |
| Persona natural | Cédula de ciudadanía, cédula de extranjería, pasaporte, permiso de protección temporal |
| No definido | «No definido», «Otro» |

---

## 4. Reglas

### Ámbito

- **R1 · Entidad.** Solo entra el registro cuyo nombre de entidad es exactamente `DISTRITO ESPECIAL DE CIENCIA TECNOLOGIA E INNOVACION DE MEDELLIN`. El NIT no basta, porque lo comparten el Concejo y la Personería.
- **R2 · Periodo.** Entran los contratos con fecha de firma desde el 1 de enero de 2022 hasta la fecha de corte. La extracción puede traer años anteriores como contexto; esta regla se aplica en la normalización.

### Consolidación

- **R3 · Contrato canónico.** Las filas con la misma referencia se consolidan en un solo contrato.
  - La fecha de firma canónica es la primera fecha no vacía.
  - El valor inicial es el de la primera versión firmada; el valor final, el que indica D3.
- **R4 · Contratos sin firma.** Se excluyen los registros sin fecha de firma (por ejemplo, los que solo fueron enviados al proveedor).
- **R5 · Proceso canónico.** Las filas con el mismo portafolio se consolidan en un solo proceso. El número de oferentes es el máximo reportado entre sus filas.

### Clasificación

- **R6 · Modalidad y tipo.** Se aplican los catálogos de la sección 3.
- **R7 · Crédito público.** Las operaciones de crédito público cuentan en los conteos, pero se excluyen de todo indicador de valor.
- **R8 · Secretaría.** Se asigna en este orden: la de MEData si el contrato está allí; si no, la unidad del proceso en SECOP II; si no, «Sin asignar». El porcentaje de «Sin asignar» se reporta.

### Indicadores

- **R9 · Proceso válido para oferente único.** Debe ser competitivo y estar adjudicado. Si reporta cero oferentes, es un error de datos y se excluye.
- **R10 · Calendario electoral.** Las fechas de la Ley de Garantías son una tabla de referencia curada a mano, con la fuente de cada fecha (ver [`fuentes.md`](fuentes.md)). No se infieren de los datos.
- **R11 · Ventanas.** Las ventanas de comparación se derivan del calendario, según la metodología de [`indicadores.md`](indicadores.md).
- **R12 · Fecha de corte.** Es la fecha de firma más reciente en la copia de datos, nunca la fecha del reloj. Todo indicador lleva su fecha de corte, y los años incompletos se comparan solo en el tramo común.

### Privacidad

- **R13 · Supresión de celdas pequeñas.** Ningún indicador desagregado (por secretaría o por mes) se publica si se calcula sobre menos de 5 contratos. Se publica como «datos insuficientes». Así una cifra pequeña no permite identificar a una persona cruzándola con el portal de SECOP. La supresión se aplica en la etapa de publicación: el tablero nunca recibe una cifra sin suprimir.
- **R14 · Proveedores.** Solo se nombran proveedores que son personas jurídicas, y solo en el indicador de concentración (I4). Hasta que respondan los organizadores, se considera persona jurídica al proveedor con NIT que empieza por 8 o 9 (ADR 0017).

### Calidad

- **R15 · Conciliación SECOP–MEData.** Para el periodo común se calcula, por mes, qué proporción de contratos aparece en ambas fuentes. Si un mes queda por debajo del 80 %, el tablero lo advierte.
- **R16 · Trazabilidad.** Cada indicador guarda numerador, denominador, n, fuentes, fecha de corte y versión de las reglas, para que cualquier cifra se pueda reconstruir.
- **R17 · Planeación.** El Plan Anual de Adquisiciones se compara con la ejecución solo de forma agregada, porque no tiene llave por contrato.

---

## 5. Decisiones de dominio

Se resolvieron siguiendo la práctica habitual en análisis de compras públicas. Las decisiones técnicas (herramientas, formatos, estructura) están en [`adr/`](adr/).

| # | Pregunta | Decisión | Por qué |
|---|---|---|---|
| D1 | ¿La «Contratación Directa (con ofertas)» cuenta como directa? | Sí | En SECOP II es una variante de la contratación directa: la entidad pide cotizaciones, pero no abre competencia |
| D2 | ¿El régimen especial se suma a la contratación directa? | No en el indicador principal. I1 se reporta en dos niveles: contratación directa sola y «no competitiva» (directa más régimen especial) | La literatura de *red flags* mide los procedimientos no abiertos en conjunto, pero el público reconoce el término «contratación directa» |
| D3 | ¿Qué valor representa al contrato? | Inicial: primera versión firmada. Final: MEData si existe; si no, la versión más reciente de SECOP II | Es la distinción entre valor firmado y valor modificado que usa el estándar de datos de contratación abierta (OCDS) |
| D4 | ¿Qué umbral de supresión? | 5 contratos | Es un umbral habitual en control de divulgación estadística para datos no sensibles |
| D5 | ¿Cómo se tratan las secretarías que cambiaron de nombre? | Se conserva el nombre histórico y se agrega una tabla de equivalencias solo si afecta las comparaciones | Evita reescribir la historia de los datos y mantiene la trazabilidad |

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
| Indicadores | Una fila por indicador, nivel y periodo, con los campos de trazabilidad de R16 |
| Serie mensual | Contratos y valor por mes, modalidad y tipo, para las gráficas del hallazgo |
| Calidad de datos | Cobertura, conciliación SECOP–MEData, porcentaje sin secretaría, filas truncadas de MEData, valores no reconocidos en catálogos |
| Metadatos | Fecha de corte, fuentes con enlace y licencia, versión de las reglas |

---

## 8. Qué se prueba

- **Catálogos:** cada texto crudo conocido cae en la categoría correcta, y uno desconocido cae en «Otra».
- **Consolidación:** casos con varias versiones de un contrato producen la fecha y los valores esperados.
- **Ventanas:** las fechas de cada año coinciden con el calendario de referencia.
- **Privacidad:** ninguna salida contiene columnas fuera de la lista blanca, y ninguna celda publicada tiene menos de 5 contratos.
- **Datos:** la conciliación SECOP–MEData de enero de 2022 se mantiene cerca de lo observado (723 frente a 727).
- **Determinismo:** dos ejecuciones con la misma copia producen salidas idénticas, byte a byte.