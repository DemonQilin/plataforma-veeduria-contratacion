# Bitácora

Registro de lo que se observó al explorar los datos, con su fecha y sus cifras. Las entradas más recientes van arriba.

Las decisiones que salen de estas observaciones no se registran aquí: pasan a [`reglas.md`](reglas.md), [`indicadores.md`](indicadores.md), [`fuentes.md`](fuentes.md) o [`adr/`](adr/). Una entrada antigua no se corrige: si una cifra cambia, se agrega una entrada nueva que lo explica.

---

## Preguntas abiertas

| Pregunta | Desde | Cómo se resuelve |
|---|---|---|
| ¿`valor_del_contrato` de SECOP II ya incluye las adiciones? | 29 oct | Comparar contra `valor_fin_contrato` de MEData en contratos con adición |
| ¿Qué es el 11 % de contratos de MEData que no cruza con SECOP II? | 29 oct | Revisar formatos de referencia y buscar en la Tienda Virtual del Estado |
| ¿El repunte de junio de 2023 y la caída de julio tienen relación con la restricción de convenios por las locales? | 29 oct | Separar interadministrativos del resto y comparar contra el calendario |
| ¿Las fechas de la restricción de las locales de 2023 son las estimadas? | 29 oct | Fuente oficial |
| ¿Qué valores de `tipo` de Adiciones cuentan como adición en I5? | 1 nov | Cruzar `Adicion en el valor` con `valor_total_adic_contrato` de MEData |

---

## 1 nov 2026 · Ejecución contractual de MEData

- La URL de la ficha del conjunto no es el archivo. El CSV está en `/sites/default/files/distribution/1-028-12-000088/Ejecucion_contractual.csv`: responde 200 directo, 26.714.918 bytes, UTF-8 sin BOM y líneas CRLF. La ficha de metadatos dio 504 dos veces antes de responder.
- 25.783 filas de 59 columnas, 2.939 contratos únicos y 28 secretarías.
- **Filas cortadas: 2.072, no 2.083.** 2.020 tienen 28 columnas y 52 tienen 21. La diferencia de 11 coincide con las filas completas cuyo objeto del contrato trae una comilla suelta, que un conteo por número de columnas ingenuo, como el de la exploración del 29 oct, clasifica como irregulares.
- «Comillas escapadas de forma irregular» resultó ser un formato de dos capas de escape, casi regular (ver [ADR 0010](adr/0010-parser-medata-y-ftfy.md)). Con la decodificación de dos capas, ninguna línea queda con un número de columnas inesperado.
- Modalidad, todas las filas: contratación directa 21.262, selección abreviada 3.063, licitación pública 676, mínima cuantía 279, régimen especial 276 y concurso de méritos 227. Las cortadas son sobre todo selección abreviada (1.582) y licitación pública (258); de contratación directa solo 196 de 21.262 (0,9 %).
- Las tildes llegan rotas («ContrataciÃ³n Directa»), como se esperaba. La copia las conserva y `ftfy` las repara en la normalización.
- Extracción: 25.783 filas con las 13 columnas de la lista blanca, SHA-256 `2759a1f3…`, igual en dos corridas. Ninguno de los ~4.000 nombres, cédulas y NIT distintos del archivo crudo aparece en la copia.

---

## 1 nov 2026 · Plan Anual de Adquisiciones de MEData

- La ficha del conjunto (`/api/1/metastore/schemas/dataset/items/1-028-11-000089`) dio 504 cuatro veces seguidas y luego respondió en 0,5 s. La API SQL respondió bien en todas las consultas de la prueba.
- La distribución CSV es `f338ad23-c393-51bc-8455-b0405e7d8655`. `SELECT COUNT(*)` da 18.764, igual a `docs/fuentes.md`. La API SQL no tiene tope de filas por respuesta: la consulta completa devolvió las 18.764 en 4,5 s.
- `record_number` es un orden único. Pagina de a 1.000 y da las mismas filas que la consulta completa (12,9 s). Decisión en [ADR 0018](adr/0018-api-sql-de-medata-con-record-number-y-tiempo-limite.md).
- Ninguna de las seis columnas de la lista blanca tiene valores vacíos. `ano` llega como `2014.0`; hay 24 grafías de mes, 15 de modalidad y 84 unidades. Se guardan crudas y se normalizan después.
- La unidad más larga mide 61 caracteres y las tres columnas de texto no traen correos ni números largos.
- Contratación directa planeada con inicio en enero de 2022: 726, la cifra de la exploración del 29 oct.
- Extracción: 18.764 filas, igual al `COUNT(*)`, SHA-256 `650f3e5e…`, igual en dos corridas.

---

## 1 nov 2026 · Adiciones de SECOP II

- Adiciones (`cb9c-h8sn`) tiene 8.451.617 filas en el país y no trae entidad. Se consultó con los 7.468 `id_contrato` de la copia de Contratos, en 38 lotes de 200 con GET: la URL más larga fue de 5.657 caracteres y la API respondió bien.
- Resultado: 15.884 filas de 5.990 contratos. Ningún lote vino vacío. `:id` e `identificador` son únicos, no hay duplicados exactos y `fecharegistro` nunca está vacía (del 12 ene 2022 al 30 oct 2026). Todos los `id_contrato` devueltos están en la copia de Contratos. SHA-256 `9e37494a…`, igual en dos extracciones.
- Solo 642 filas son `Adicion en el valor`. Las otras son `Modificacion General` (7.958), `No definido` (4.354), `Conclusion` (2.379), `Reactivación` (262), `Suspensión` (244) y `Cesion` (45). La copia conserva todo, sin filtrar; I5 no puede contar filas como adiciones sin separar el `tipo`.
- `descripcion`, que puede traer nombres, sigue fuera de la lista blanca.

---

## 1 nov 2026 · Orden de SECOP II Procesos y NIT de proveedores

- Resuelta la pregunta sobre el nombre de la entidad en Procesos: se escribe igual que en Contratos. Hoy son 23.428 filas con ese nombre; el 30 oct eran 23.400, porque la fuente recibe registros tardíos.
- El orden `id_del_portafolio,id_del_proceso` no es único: la pareja se repite hasta 84 veces. Tampoco hay llave natural: con `id_adjudicacion`, `codigoproveedor` y `fecha_adjudicacion` quedan 944 grupos repetidos, el peor con 40 filas.
- Se descargó Procesos completo (23.428 filas, páginas de 1.000) dos veces con cada orden. El orden por la pareja y el orden por `:id` dieron las mismas filas, sin faltantes ni sobrantes, y cada uno fue estable entre sus dos corridas. La pérdida de filas no se reprodujo. `:id` es único y `:created_at` es igual en todas las filas. Solo 19.367 filas son distintas en las columnas de la lista blanca: 4.061 son duplicados exactos. Decisión en [ADR 0016](adr/0016-orden-determinista-de-la-copia.md).
- Procesos del Distrito: 14.577 publicados desde el 1 ene 2022, otros anteriores desde 2015 y 633 sin fecha de publicación. No se filtra por fecha, para no romper el cruce con contratos de 2022 cuyo proceso es anterior.
- De 4.508 contratos con `tipodocproveedor = 'NIT'`, 42 (10 documentos distintos) no empiezan por 8 ni por 9. El prefijo es un indicio, no una prueba de persona jurídica. Decisión en [ADR 0017](adr/0017-proveedores-solo-nit-con-prefijo-8-o-9.md).
- Extracción del 1 nov con las dos decisiones aplicadas: `secop_contracts_suppliers` dio 4.466 filas (4.508 contratos con NIT menos 42), todas con prefijo 8 o 9 y todas de contratos que están en `secop_contracts`; `secop_procurement_processes` dio 23.428 filas, igual al `count(*)`, con 4.061 duplicados exactos que se conservan. `secop_contracts` conservó su SHA-256 (`c825d206…`): su orden por `id_contrato`, que es único, coincide con el orden local. Las tres copias quedan ordenadas por todas sus columnas.

---

## 31 oct 2026 · Primera extracción de SECOP II Contratos

- Con el filtro de `sources.toml` (entidad exacta y firma desde el 1 ene 2022): 7.453 filas y 7.453 `id_contrato` distintos, con firmas del 6 ene 2022 al 30 oct 2026. El orden por `id_contrato` es estable.
- 75 contratos del Distrito no tienen fecha de firma y quedan fuera del filtro, coherente con R2 y R4. En 2021 hay 1.739 contratos, que no se extraen.
- Dos extracciones seguidas dieron el mismo SHA-256 (`d4bcf19b…`).
- Un `X-App-Token` inválido hace que la API responda HTTP 403 aunque el conjunto sea público; sin el encabezado responde 200. Lo que se había creado era una Clave API; el encabezado exige el Token de la aplicación, que es otra credencial.
- Con el Token de la aplicación correcto, la extracción del 1 nov dio 7.468 filas y 7.468 `id_contrato` distintos (SHA-256 `c825d206…`), con firmas del 6 ene 2022 al 30 oct 2026 a las 22:26. Son 15 contratos más que el día anterior: la fuente recibe registros tardíos. La copia versionada es esta.

---

## 30 oct 2026 · Decisiones técnicas y consulta a los organizadores

- Se definieron la estructura del repositorio, las herramientas y la convención de idioma. Quedan registradas en [`adr/`](adr/).
- Correo a los organizadores (envío programado para las 9:00 a. m.) con cinco preguntas: tratamiento de datos de proveedores personas jurídicas y naturales, si el uso de «Ejecución contractual histórico» cumple el requisito de integrar MEData, si SECOP II filtrado por el Distrito cuenta como fuente admitida, si hay lineamientos para publicar indicadores de riesgo sobre entidades públicas, y la descripción de los niveles de la rúbrica. Respuesta pendiente.

---

## 29 oct 2026 · Validación de las fuentes

### SECOP II · Contratos

- El NIT `890905211` aparece en registros del Distrito, del Concejo y de la Personería. Filtrar por nombre exacto de la entidad resuelve la ambigüedad.
- El Distrito tiene entre 1.300 y 1.700 contratos por año desde 2018.
- `referencia_del_contrato` coincide con el número de contrato de MEData. Verificado primero con tres contratos de enero de 2022 y luego a escala.
- Una misma referencia puede tener varios `id_contrato`, por modificaciones o envíos al proveedor.
- Conviven «Contratación directa» y «Contratación Directa (con ofertas)».
- Un solo contrato de operación de crédito público de 2025 vale 503 mil millones de pesos.
- El conjunto de Adiciones (`cb9c-h8sn`) solo trae tipo, descripción y fecha, sin montos.

### SECOP II · Procesos

- `proveedores_unicos_con` está poblado. Aparecen procesos competitivos adjudicados con un solo oferente.
- El cruce con Contratos funciona por `id_del_portafolio` = `proceso_de_compra`, no por `id_del_proceso`.
- Las filas se repiten por lote o adjudicación.
- El Distrito tiene entre 3.000 y 4.100 procesos por año desde 2020.

### MEData · Ejecución contractual histórico

- Última modificación el 06-12-2023. CSV de 26,7 MB y 25.783 filas.
- Cada fila es una línea presupuestal, no un contrato. Hay 2.939 contratos únicos firmados del 4 ene 2022 al 30 jun 2023 (1.730 de 2022 y 1.209 de 2023), de 28 secretarías.
- 2.628 de los 2.939 contratos (89 %) aparecen en SECOP II por `referencia_del_contrato`.
- 2.083 filas (8 %) vienen cortadas en origen después de la columna 28.
- Cada línea viene envuelta en comillas, con comillas escapadas de forma irregular dentro.
- Las tildes están rotas por doble codificación UTF-8, y la vista previa del portal carga el CSV en una sola columna.
- Contiene nombre y cédula del contratista y del supervisor.

### MEData · Plan anual de adquisiciones histórico

- 18.764 líneas planeadas, vigencias 2014 a 2023; 27 unidades en 2022. Última modificación en sep 2023.
- La API SQL del portal respondió con errores 504 de forma intermitente.
- Modalidad y mes vienen escritos de muchas formas («Contratacion Directa», «contratacion directa», «concurso de m eritos», «mnima cuanta»).
- Contratación directa planeada con inicio estimado en enero: 46 % (2014), 57 % (2018) y 52 % (2022), frente a 24–34 % en 2016, 2017, 2020 y 2021. Con inicio de febrero a junio: 15 %, 16 % y 8 %, frente a 35–46 %.
- En 2019, último año de una administración, el 66 % de la contratación directa planeada tenía inicio en enero.
- Para enero de 2022 había 726 contratos directos planeados.

---

## 29 oct 2026 · Primer vistazo a la contratación directa del Distrito

*Preliminar, sin consolidar.* Contratos de contratación directa firmados por el Distrito en SECOP II, por mes. Datos al 29 oct 2026; 2026 llega hasta octubre. ⚑ = año con restricción presidencial a la contratación directa.

| Año | Ene | Feb | Mar | Abr | May | Jun | Jul | Ago | Sep | Oct | Nov | Dic | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 184 | 285 | 157 | 78 | 69 | 106 | 123 | 96 | 84 | 106 | 88 | 71 | 1.447 |
| 2022 ⚑ | **723** | 2 | 2 | 0 | 1 | 19 | 117 | 172 | 150 | 62 | 118 | 24 | 1.390 |
| 2023 | 375 | 192 | 127 | 102 | 106 | **173** | 35 | 74 | 74 | 32 | 29 | 56 | 1.375 |
| 2024 | 196 | 169 | 77 | 112 | 66 | 45 | 68 | 111 | 48 | 46 | 31 | 17 | 986 |
| 2025 | 410 | 171 | 118 | 79 | 69 | 67 | 56 | 59 | 56 | 66 | 36 | 5 | 1.192 |
| 2026 ⚑ | **709** | 0 | 0 | 0 | 4 | 16 | 142 | 90 | 79 | 39 | – | – | 1.079 |

- En 2022 y 2026, enero concentra 723 y 709 contratos, y de febrero a junio la cifra cae casi a cero mientras rige la restricción.
- En los años de control, enero tuvo 196 (2024) y 410 (2025).
- En 2023 hay un repunte en junio (173) y una caída en julio (35), justo antes de la restricción por las elecciones locales.
- Proporción del año firmada en enero: 52 % (2022), 27 % (2023), 20 % (2024), 34 % (2025) y 66 % (2026, sobre enero a octubre).

**Contraste con MEData (todas las modalidades, contratos únicos, 2022):** enero 727 · febrero 4 · marzo 20 · abril 24 · mayo 39 · junio 91 · julio 145. La fuente del Distrito reproduce el mismo patrón que SECOP II.

Es una señal fuerte, todavía no un hallazgo. Falta consolidar, separar prestación de servicios de otros tipos y comparar contra los años de control con la metodología de [`indicadores.md`](indicadores.md).

---

## 29 oct 2026 · Volumen de las instituciones universitarias

Fuera del alcance del MVP. Se registra como contexto para una siguiente etapa.

- El Distrito firma entre 1.300 y 1.700 contratos al año en SECOP II. El ITM pasó de 5.582 contratos en 2022 a 19.225 en 2025, y en 2025 casi todos (18.803) fueron con personas naturales. Pascual Bravo y Colegio Mayor también tienen volúmenes altos.
- Una hipótesis es que parte de la contratación del Distrito se ejecute a través de contratos interadministrativos con sus instituciones universitarias. **No está verificada.**
- En MEData (ene 2022 – jun 2023), el Distrito firmó 407 contratos interadministrativos en 18 meses. Entre las contrapartes con más contratos están la Universidad de Antioquia (62), Metroparques (45), Plaza Mayor (36), el ITM (34), Metrosalud (33), Pascual Bravo (29) y Colegio Mayor (19). Esto confirma que el canal existe, pero no dice cuánto de la contratación de esas instituciones viene del Distrito.
- Calendario de los interadministrativos: ninguno entre enero y mayo de 2022, 61 en julio de 2022 (justo después de la segunda vuelta) y 47 en junio de 2023, el mes previo a la restricción de convenios por las elecciones locales. Este patrón también encaja con el repunte de junio de 2023 en SECOP II.

---

## 29 oct 2026 · Precedente nacional de la Ley de Garantías

- En la víspera de la restricción de 2022, Colombia Compra Eficiente reportó cerca de 32.000 contratos en SECOP II en un solo día, frente a un máximo previo de unos 6.400, y la mitad de los procesos del periodo se concentró en los últimos siete días.
- Un profesor del Externado matizó que parte del efecto venía de que la restricción se corrió de noviembre a enero.
- Enero es también el mes de renovación anual de los contratos de prestación de servicios, así que un pico en enero no prueba nada por sí solo. Esto definió la metodología de comparación contra años de control.

Fuente: [Portafolio · En víspera de Ley de Garantías se quintuplicó la contratación](https://www.portafolio.co/economia/en-vispera-a-ley-de-garantias-se-quintuplico-la-contratacion-561050).