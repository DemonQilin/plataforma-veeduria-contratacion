# Bitácora

Registro de lo que se observó al explorar los datos, con su fecha y sus cifras. Las entradas más recientes van arriba.

Las decisiones que salen de estas observaciones no se registran aquí: pasan a [`reglas.md`](reglas.md), [`indicadores.md`](indicadores.md), [`fuentes.md`](fuentes.md) o [`adr/`](adr/). Una entrada antigua no se corrige: si una cifra cambia, se agrega una entrada nueva que lo explica.

---

## Preguntas abiertas

| Pregunta | Desde | Cómo se resuelve |
|---|---|---|
| ¿`valor_del_contrato` de SECOP II ya incluye las adiciones? | 29 oct | Comparar contra `valor_fin_contrato` de MEData en contratos con adición |
| ¿Qué es el 10 % de contratos de MEData (307 de 2.939, medido el 5 nov) que no cruza con SECOP II? | 29 oct | Revisar formatos de referencia y buscar en la Tienda Virtual del Estado |
| ¿El repunte de junio de 2023 y la caída de julio tienen relación con la restricción de convenios por las locales? | 29 oct | Separar interadministrativos del resto y comparar contra el calendario |
| ¿Las fechas de la restricción de las locales de 2023 son las estimadas? | 29 oct | Fuente oficial |
| ¿Qué valores de `tipo` de Adiciones cuentan como adición en I5? | 1 nov | Decidido el 3 nov: solo `Adicion en el valor` (ADR 0025). Falta confirmarlo cruzando con `valor_total_adic_contrato` de MEData (R15) |

---

## 5 nov 2026 · Locales de 2027 verificadas

La Registraduría fijó la jornada de elecciones territoriales para el domingo 31 de octubre de 2027 (Resolución 12338 del 28 de octubre de 2026). Con el parágrafo del artículo 38 de la Ley 996 (cuatro meses antes), la restricción de convenios interadministrativos va del 30 de junio al 31 de octubre de 2027 y entra al calendario como `local_2027` ([ADR 0041](adr/0041-calendario-electoral-publicado.md)). No genera ventanas de I2, así que ninguna cifra publicada cambia. La fuente es prensa porque `registraduria.gov.co` rechazó la consulta automática; falta confirmarla en el sitio oficial.

---

## 5 nov 2026 · Serie mensual publicada

`data/outputs/monthly_series.json` trae contratos y valor por mes, modalidad y tipo del Distrito, de enero de 2022 a octubre de 2026 (58 meses, 2.088 filas). La decisión sobre R13 está en el [ADR 0040](adr/0040-serie-mensual-con-valor-suprimido.md): el conteo siempre se publica y el valor se suprime.

- **La caída de la restricción se ve en el conteo.** Contratación directa de 2022: enero 723, febrero 2, marzo 2, abril 0, mayo 1. El valor de febrero, marzo y mayo queda suprimido; el de abril es cero, porque no hay contratos.
- **La suma mensual coincide con I1.** Para cada año, los meses de contratación directa suman el numerador de I1 en número y en valor (prueba `test_golden_series_direct_award_matches_i1_numerators_by_year`).
- **757 de 2.088 filas** tienen el valor suprimido (primaria, complementaria D6 y espejos). Una primera versión dejaba 710 y un verificador independiente despejó 35 valores de menos de 5 contratos en cascada; la regla de espejos del [ADR 0040](adr/0040-serie-mensual-con-valor-suprimido.md) lo corrige y una prueba propaga los desgloses sobre la salida publicada. El valor de la contratación directa de enero de 2022 también queda oculto, porque en ese mes solo hay 3 contratos de régimen especial y la directa es la única parte publicada que los despejaría. Es el costo de D6; el conteo sí se publica y la cifra anual de I1 no cambia.

---

## 5 nov 2026 · I1 publicado

I1 entra a `data/outputs/indicators.json` por año y secretaría (decisión en el [ADR 0039](adr/0039-i1-anual-por-secretaria.md)). Cifras del Distrito, copia de corte 30 oct 2026; 2026 llega hasta el corte.

| Año | Directa · número | No competitiva · número | Directa · valor | No competitiva · valor |
|---|---:|---:|---:|---:|
| 2022 | 80,8 % (1.387 de 1.716) | 85,3 % (1.463) | 68,7 % | 72,0 % |
| 2023 | 82,0 % (1.366 de 1.666) | 87,0 % (1.449) | 49,6 % | 88,0 % |
| 2024 | 76,0 % (978 de 1.287) | 82,4 % (1.061) | 67,9 % | 77,8 % |
| 2025 | 81,8 % (1.186 de 1.449) | 85,9 % (1.244) | 77,0 % | 82,7 % |
| 2026 | 82,7 % (1.084 de 1.310) | 85,5 % (1.120) | 66,4 % | 67,9 % |

- Los 1.387 de 2022 coinciden con el denominador de I8 firmado.
- En 2023 la proporción por valor pasa de 49,6 % (directa) a 88,0 % (no competitiva): ese año el régimen especial concentra mucho valor, aunque pocos contratos (83 de 1.666). Es una lectura para revisar, no una conclusión.
- De 548 celdas por secretaría, 16 quedan suprimidas (8 por número y 8 por valor). «Sin asignar» tiene 2 contratos en 2023, y por eso se suprime ese año.

## 5 nov 2026 · Cierre de los pendientes de C1

- **R15 publicada.** `data/outputs/quality.json` trae la conciliación por mes (18 meses), con los conteos de cada fuente, las razones y el umbral de 0,8. Marca los seis meses de 2022 bajo el 80 %: marzo, abril, mayo, junio, julio y diciembre. No se aplica la supresión R13 a esta salida; la decisión y su guarda están en el [ADR 0038](adr/0038-r15-publicada-sin-supresion.md). El mínimo de contratos es 5, en los contratos de ambas fuentes de febrero y marzo de 2022 y en SECOP II de febrero de 2022.
- **El 727 de MEData tiene prueba.** `test_r15_snapshot_medata_january_2022_by_its_own_date_is_727` fija los 727 contratos de MEData en enero de 2022 por su propia fecha. Son 2 más que los 725 que da la fecha de SECOP II, porque SECOP II firma esos 2 en febrero.
- **La diferencia de 4 contratos sí tiene causa.** La entrada de C1 dice que 2.632 frente a 2.628 «no tiene causa verificada». Se verificó con una consulta de solo lectura sobre la copia: los 2.632 contratos de MEData están en SECOP II, y 4 los firma SECOP II en julio de 2023 mientras MEData los fecha en junio. Quedan fuera de los 18 meses de la conciliación, que cuentan por la fecha de SECOP II, y por eso la suma mensual da 2.628. La cobertura de 2.632 de 2.939 no cambia.

---

## 5 nov 2026 · Punto de decisión 1 (T8)

Evaluación de los dos criterios de [`indicadores.md`](indicadores.md) §3 con la copia de corte 30 oct 2026. Las cifras salen de `data/outputs/indicators.json`.

**Criterio 1 · serie ejecutada (I2).** Menor año de tratamiento frente al máximo de control, en nivel Distrito.

| Lectura | Medida | 2022 | 2026 | Control (2023 / 2024 / 2025) | Brecha | Resultado |
|---|---|---:|---:|---|---:|---|
| Base | Número | 58,3 % (723 de 1.240) | 65,3 % (708 de 1.084) | 25,1 / 18,6 / 30,7 % | 27,6 | Se cumple |
| Base | Valor | 30,7 % | 52,3 % | 29,8 / 19,5 / 22,3 % | 0,9 | Se cumple, por menos de un punto |
| Sin interadministrativos | Número | 70,1 % (723 de 1.031) | 77,9 % (675 de 867) | 27,9 / 25,3 / 39,6 % | 30,5 | Se cumple |
| Sin interadministrativos | Valor | 74,5 % | 78,2 % | 48,2 / 27,7 / 44,1 % | 26,3 | Se cumple |

**Criterio 2 · serie de planeación (I8).** Se cumple en las dos medidas: por número, 8,3–16,0 % frente a un mínimo de control de 34,8 %; por valor, 6,3–23,5 % frente a 37,4 %. Por valor el margen baja a 3,2 puntos al quitar las cinco líneas más grandes de cada año (entrada del 4 nov).

**Resultado:** el titular se mantiene. Se cumplen los dos criterios, y bastaba con uno.

- **Cifra titular de I2:** la definición base, por número de contratos. La definición se fijó el 3 nov y no se cambia después de ver los resultados. El valor se presenta como complemento, con la nota de que el margen es de 0,9 puntos, y la variante sin interadministrativos se publica como sensibilidad (ADR 0037).
- **Apoyos que no deciden:** en 2022 lo firmado en enero coincide con lo planeado (52,1 % frente a 52,5 %). La duración de los contratos de enero no es concluyente, por lo que no entra en la decisión.
- **Frase del hallazgo:** completada en [`indicadores.md`](indicadores.md) §3. El denominador llega hasta el 30 de octubre, no hasta el fin del año.

---

## 5 nov 2026 · Revisión de cifras del hallazgo (C1)

Revisión de las cifras publicadas (corte 30 oct 2026) contra la metodología de [`indicadores.md`](indicadores.md) §3. Las consultas se corrieron en memoria sobre la copia, sin escribir nada.

**Verificado**

- **Salidas al día:** `run --from-snapshot` en una carpeta aparte produce `indicators.json` y `metadata.json` idénticos (mismo SHA-256) a los de `data/outputs/`.
- **Cifras de referencia:** I2 2022 = 723 de 1.240; I8 planeado 2022 = 726 y 115 de 1.383; I8 firmado 2022 = 723 de 1.387. Las fija `test_indicators.py`.
- **Conciliación R15, 2022:** marzo a julio y diciembre quedan por debajo del 80 % (25,0; 68,4; 70,8; 74,3; 67,6 y 61,5 %). En 2023 ningún mes baja del 80 %. Las fija `test_reconciliation_snapshot.py`.
- **Serie de planeación:** el criterio 2 se cumple por número (tratamiento 8,3–16,0 % frente a control 34,8–45,8 %) y por valor (6,3–23,5 % frente a 37,4–55,9 %).
- **Lenguaje:** ninguno de los términos que evita la guía ([`producto.md`](producto.md) 4.4) aparece en `web/src/`, `pipeline/src/` ni `data/outputs/`. En `docs/` solo salen en la propia guía y en usos técnicos (el índice de Fazekas, comillas «irregulares», «no una irregularidad»).

**Corregido en los documentos**

- El catálogo de I2 decía «de enero a octubre»; ahora dice el tramo común hasta la fecha de corte (R12).
- El rango «8–16 % frente a 35–46 %» de `indicadores.md` valía solo por número; ahora se dan las dos medidas.
- La cobertura de MEData en SECOP II es **2.632 de 2.939 (90 %)**, no 2.628 (89 %). Quedan 307 sin cruce (10 %). Las entradas anteriores se conservan; la diferencia de 4 contratos no tiene causa verificada. En la copia actual no hay contratos de MEData sin proceso, así que la explicación del 3 nov («menos 4 sin proceso») ya no aplica.
- ADR 0036: «1.436 de 1.708» es correcto contando todas las fechas de 2022 a 2026; en el tramo común son 1.336 de 1.595. Las brechas de 37 y 43 puntos son diferencias de medias, no la métrica del criterio 1.
- El ejemplo de base de [`producto.md`](producto.md) usaba «52 % de 1.390» (cifra preliminar); ahora usa 58,3 % de 1.240.
- Se declaran en las limitaciones los seis meses de 2022 bajo el 80 %, el resultado no concluyente de la duración de los contratos y la robustez de I8 por valor.

**Abierto**

- **R15 no se publica:** se calcula en `build`, pero no hay salida en `data/outputs/` y el tablero no puede advertir los meses bajos. Queda en [`plan.md`](plan.md) §10.
- **Ninguna prueba fija el 727** de MEData para enero de 2022; la prueba de conciliación fija las cifras por fecha de SECOP II.
- **Para T8, cifra titular de I2.** Brecha entre el menor año de tratamiento y el máximo de control:

| Medida | I2 base | `excluding_interadministrative` |
|---|---|---|
| Por número | 58,3 − 30,7 = 27,6 puntos | 70,1 − 39,6 = 30,5 puntos |
| Por valor | 30,7 − 29,8 = 0,9 puntos | 74,5 − 48,2 = 26,3 puntos |

  Con la definición base, el criterio 1 por valor se cumple por menos de un punto; con la variante, la separación es amplia. Elegir la cifra después de ver esto es una decisión de T8 (ADR 0036).

---

## 5 nov 2026 · I8: planeado frente a firmado, 2022–2023 (R17)

Misma proporción sobre lo planeado (`procurement_plan`) y sobre lo firmado (`linked_contracts`, contratación directa del año calendario completo). Corte 30 oct 2026. Solo comparación agregada: el plan no tiene llave por contrato.

| Año | Medida | Enero planeado | Enero firmado | Feb–jun planeado | Feb–jun firmado |
|---|---|---:|---:|---:|---:|
| 2022 (tratamiento) | Número | 726 de 1.383 (52,5 %) | 723 de 1.387 (52,1 %) | 115 de 1.383 (8,3 %) | 24 de 1.387 (1,7 %) |
| 2022 (tratamiento) | Valor | 19,8 % | 18,3 % | 17,1 % | 7,1 % |
| 2023 (local) | Número | 576 de 1.296 (44,4 %) | 375 de 1.366 (27,5 %) | 572 de 1.296 (44,1 %) | 693 de 1.366 (50,7 %) |
| 2023 (local) | Valor | 46,6 % | 35,1 % | 51,4 % | 59,3 % |

- **2022:** lo firmado en enero coincide con lo planeado (52,1 % frente a 52,5 %): la concentración de enero ya estaba en el plan. En febrero–junio se firmó menos de lo planeado (1,7 % frente a 8,3 % por número), coherente con la restricción.
- **2023:** sin restricción presidencial, lo firmado en enero (27,5 %) queda 17 puntos por debajo de lo planeado (44,4 %), y lo firmado de febrero a junio supera lo planeado. El plan de 2023 no es confiable como referencia mensual: su última modificación es de septiembre de 2023.
- **Límite de la medida por valor:** la firmada excluye el crédito público (R7) y la planeada no puede excluirlo, así que no son estrictamente comparables.
- Para T8/C1: la coincidencia de 2022 apoya que la concentración de enero es planeada, no improvisada; 2023 es el contraste.

---

## 5 nov 2026 · Duración de los contratos de enero (factor de confusión 3 de I2)

Proporción de contratos directos firmados en la ventana de enero cuyo plazo pactado (`end_date` menos `added_days`) termina después del fin de la restricción de referencia (ADR 0035): el real en 2022 y 2026, y el 20 de junio en los años de control. Solo por número de contratos.

| Año | Termina después de la restricción |
|---|---:|
| 2022 (tratamiento) | 720 de 723 (99,6 %) |
| 2023 (control) | 176 de 320 (55,0 %) |
| 2024 (control) | 121 de 173 (69,9 %) |
| 2025 (control) | 345 de 349 (98,9 %) |
| 2026 (tratamiento) | 701 de 708 (99,0 %) |

- `duration_days` solo existe en MEData (hasta junio de 2023), así que no cubre 2024–2026. Se usó la fecha de fin de SECOP II, presente en todos los directos de enero.
- **La señal no separa tratamiento de control:** 2025, año de control, queda igual que 2022 y 2026. Los contratos de enero duran hasta después de junio casi siempre, con o sin restricción. Para T8: este control no apoya ni refuta el titular, y se declara como no concluyente.
- No se pudo verificar si SECOP II actualiza `end_date` cuando se agregan días (solo hay 31 directos con más de una versión), así que restar `added_days` es un supuesto.

---

## 4 nov 2026 · Primera corrida de I8 (serie de planeación) sobre la copia

Proporción de las líneas directas del Plan Anual con inicio estimado en enero y de febrero a junio, 2014–2023. Todas las líneas directas traen mes; solo 2 de 2017 no traen valor y quedan fuera de la medida por valor.

| Año | Papel | Enero (número) | Feb–jun (número) | Enero (valor) | Feb–jun (valor) |
|---|---|---:|---:|---:|---:|
| 2014 | tratamiento | 45,7 % | 15,0 % | 10,2 % | 6,3 % |
| 2015 | local | 50,4 % | 41,7 % | 36,9 % | 57,0 % |
| 2016 | control (1.er año) | 26,8 % | 45,8 % | 38,5 % | 38,9 % |
| 2017 | control | 33,5 % | 37,6 % | 30,0 % | 38,4 % |
| 2018 | tratamiento | 57,0 % | 16,0 % | 23,9 % | 23,5 % |
| 2019 | local | 66,3 % | 30,3 % | 52,3 % | 46,3 % |
| 2020 | control (1.er año) | 34,5 % | 34,8 % | 36,0 % | 37,4 % |
| 2021 | control | 24,5 % | 41,0 % | 18,1 % | 55,9 % |
| 2022 | tratamiento | 52,5 % | 8,3 % | 19,8 % | 17,1 % |
| 2023 | local | 44,4 % | 44,1 % | 46,6 % | 51,4 % |

- Criterio 2 del punto de decisión 1: en los tres años de elección presidencial, febrero a junio queda por debajo del mínimo de los años de control (34,8 % por número y 37,4 % por valor): 15,0 / 16,0 / 8,3 % y 6,3 / 23,5 / 17,1 %. Se cumple en las dos medidas; la decisión formal es de T8.
- Los primeros años de administración (2016, 2020) se señalan, como pide [`indicadores.md`](indicadores.md). Su enero por número (26,8 % y 34,5 %) no es sistemáticamente menor que el de los otros controles (33,5 % y 24,5 %), y el mínimo de febrero a junio de los controles por número es 2020 (34,8 %).
- El plan no distingue el crédito público, así que la medida por valor no puede excluirlo (R7). No se encontró en el plan ninguna señal de esas operaciones; los códigos UNSPSC que contienen «84» (servicios financieros) son un indicador débil y no se usan.
- Por valor pesan pocas líneas: en 2014 dos líneas con inicio en julio suman el 46,7 % del valor directo (por eso su feb–jun da 6,3 %) y en 2022 una línea de noviembre pesa el 19,8 %. Ninguna parece crédito (códigos de mantenimiento e infraestructura).

### Sensibilidad del criterio 2 por valor

Feb–jun por valor, quitando de cada año las *k* líneas directas de mayor valor. Se compara el máximo de los años de tratamiento con el mínimo de los de control.

| *k* | Máx. tratamiento | Mín. control | Brecha | Criterio 2 |
|---:|---:|---:|---:|---|
| 0 | 23,5 % | 37,4 % | 13,9 | Se cumple |
| 1 | 25,2 % | 39,2 % | 14,0 | Se cumple |
| 3 | 29,0 % | 34,9 % | 5,9 | Se cumple |
| 5 | 30,4 % | 33,6 % | 3,2 | Se cumple |
| 10 | 31,4 % | 36,2 % | 4,8 | Se cumple |

- El criterio por valor se mantiene en todos los casos, pero con poco margen: la brecha baja de unos 14 puntos a unos 3 con *k* = 5.
- Es un ejercicio de robustez, no una prueba de que no haya crédito público en el plan.
- Para T8: apoyar el titular en la medida por número, que no tiene este problema, y presentar la de valor como complemento, con la nota de que el resultado se mantiene al quitar las líneas más grandes, con menor margen.

---

## 4 nov 2026 · Primera corrida de I2 sobre la copia

Concentración pre-restricción del Distrito, con el denominador en el tramo común hasta el 30 de octubre y el valor inicial. Los años de tratamiento son 2022 y 2026; los de control, 2023 a 2025.

| Año | Por número | Por valor |
|---|---:|---:|
| 2022 (tratamiento) | 723 de 1.240 (58,3 %) | 30,7 % |
| 2023 (control) | 320 de 1.277 (25,1 %) | 29,8 % |
| 2024 (control) | 173 de 929 (18,6 %) | 19,5 % |
| 2025 (control) | 349 de 1.138 (30,7 %) | 22,3 % |
| 2026 (tratamiento) | 708 de 1.084 (65,3 %) | 52,3 % |

- Los 723 contratos de 2022 coinciden con la cifra de control de enero de 2022 en `linked_contracts`.
- Por tipo, la prestación de servicios pesa casi todo el pico por número (2022: 70,1 %; 2026: 78,6 %), y el resto de contratos se queda entre 11,7 % y 27,1 %. Es el factor de confusión de enero que describe [`indicadores.md`](indicadores.md), y lo evalúa T3 y el punto de decisión 1.
- Por valor, 2022 (30,7 %) supera al control más alto (29,8 %) por menos de un punto.

---

## 4 nov 2026 · Fin del denominador de I2

- La documentación decía que el denominador de I2 va «de enero a octubre», pero la fecha de corte de la copia es el 30 de octubre de 2026 (`metadata.json`): a 2026 le falta el 31 de octubre.
- Se resolvió con R12 (tramo común): todos los años se miden del 1 de enero al día y mes de la fecha de corte (ADR 0034). Hoy da el 30 de octubre.

---

## 3 nov 2026 · Cruce con MEData y asignación de secretaría

- MEData tiene 25.783 líneas de 2.939 contratos (de 1 a 682 líneas por contrato). Secretaría, fecha de firma, valores, duración y estado no cambian entre las líneas de un contrato; solo varían el programa (249 contratos) y la causal (420). 54 contratos tienen todas sus líneas truncadas: conservan la secretaría y no tienen valores.
- 2.632 de esos 2.939 contratos están en los contratos canónicos de SECOP II. De los 7.428 contratos canónicos, 23 no tienen proceso.
- Las dos fuentes escriben la secretaría con vocabularios distintos: 28 textos en MEData y 41 en SECOP II. Con el catálogo de 28 secretarías, 2.632 contratos toman la secretaría de MEData, 4.777 la de SECOP II y 19 (0,26 %) quedan sin asignar. Un único texto de SECOP II no se mapea, «SUMINISTRO DE VESTIDO Y CALZADO DE LABOR», un nombre de proceso escrito en el campo de la unidad.
- Los 2.628 contratos presentes en las dos fuentes (2.632 en MEData menos 4 sin proceso) tienen la misma secretaría en ambas, una vez que «Alcaldía» de MEData se unifica con «Secretaria Privada» de SECOP II (5 contratos).
- 11 contratos son de crédito público y quedan fuera de los indicadores de valor (R7).

---

## 3 nov 2026 · Consolidación de contratos y procesos

- De 7.468 filas de Contratos salen 7.428 referencias. 40 referencias se repiten, cada una con exactamente 2 filas, y 13 de esas 40 tienen valores distintos entre sus versiones.
- 6 de las 40 referencias apuntan a procesos distintos entre sus filas. Ninguna tiene dos firmas con la misma marca de tiempo, así que hoy el desempate por identificador no se usa. Ninguna fila trae la firma vacía: R4 no excluye nada con esta copia.
- De 23.450 filas de Procesos salen 17.260 portafolios, y 4.147 quedan adjudicados. 1.169 portafolios mezclan filas adjudicadas y no adjudicadas; con la regla de R5 («alguna fila adjudicada») cuentan como adjudicados.

---

## 3 nov 2026 · Normalización de la ejecución contractual de MEData

- La copia tiene 25.783 líneas, 2.939 contratos y 2.072 líneas truncadas. Ninguna fecha de firma es anterior al 1 de enero de 2022: van del 4 de enero de 2022 al 30 de junio de 2023, y todas se leen con `d/mm/yyyy`.
- Las 23.711 líneas completas cumplen el formato de montos y de duración. `ano` solo falta en las truncadas.
- Un contrato tiene dos modalidades entre sus líneas. La fecha y la secretaría sí coinciden en todos.
- Tras `ftfy.fix_encoding`, ninguna columna de texto conserva `Ã` y ninguna modalidad cae en `other`.

## 2 nov 2026 · Normalización de Procesos

- La copia de Procesos tiene 23.450 filas, 17.260 portafolios y 18.852 procesos. Todas las fechas y cifras se leen sin error. Faltan 633 fechas de publicación y 12.023 de cierre de ofertas.
- Cada portafolio trae una sola modalidad y un solo tipo de contrato, así que el catálogo no cambia de una fila a otra del mismo portafolio. En «Otra» caen 1.129 filas, las 786 de «Solicitud de información a los Proveedores» y las 343 de «Subasta de prueba»; ninguna está adjudicada.
- **1.169 portafolios mezclan filas adjudicadas y no adjudicadas.** R5 solo define cómo se consolida el número de oferentes. Hay que decidir cómo se consolida `adjudicado` antes de la tarea 7, porque I3 y R9 dependen de eso.
- Hay 251 filas adjudicadas con cero proveedores únicos y 10 adjudicadas con valor adjudicado en cero. R9 excluye las primeras del indicador; aquí se conservan.
- 7.085 de los 7.108 `proceso_de_compra` de Contratos aparecen como portafolio en Procesos. Los otros 23 quedan sin proceso al cruzar.

---

## 3 nov 2026 · NIT de proveedores con menos de 9 dígitos

- La copia de proveedores tenía 4.466 filas y 980 NIT. 5 documentos (7 filas) tenían 7 u 8 dígitos y al menos 3 traían el nombre de una persona natural. La nueva copia tiene 4.459 filas. Decisión en [ADR 0026](adr/0026-proveedores-nit-de-9-o-10-digitos.md).
- 24 NIT tienen 10 dígitos. En 23 el último dígito coincide con el dígito de verificación de la DIAN calculado sobre los 9 primeros, y 4 de ellos también aparecen con 9 dígitos: el mismo proveedor con dos documentos distintos.
- 11 NIT tienen más de un nombre, por ejemplo la sigla y la razón social de la misma empresa («ESU», 105 filas). La llave del proveedor debe ser el NIT, no el nombre.

---

## 2 nov 2026 · Catálogos de tipo de contrato y de proveedor

- `interadministrativo` no es un valor de `tipo_de_contrato`. En `secop_contracts` hay 1.446 contratos con justificación interadministrativa («con valor» 1.353, «valor cero» 93): 1.399 traen el tipo «Otro», 43 «Suministros» y 4 «Obra». La justificación debe ganarle al tipo.
- Las 4.079 filas con justificación «Servicios profesionales y apoyo a la gestión» ya tienen el tipo «Prestación de servicios»; no hace falta la justificación para ese tipo.
- MEData · Ejecución no trae tipo de contrato, solo `causal` (49 valores distintos tras reparar la codificación). Las interadministrativas son «Contrato Interadmin» (406 contratos), «Adic. Contr. Interad», «Cto Interadm Segurid», «Convenio Interadmin» y «Ad. Cto InterSegurid»: 432 contratos con firma desde 2022.
- «Ley 489 Artículo 95» y «Ley 489 Artículo 108» no se incluyen: desde 2022 no suman ningún contrato respecto de las variantes anteriores (431 con y sin ellas). «Conv. Coop. Internal» es cooperación internacional.
- SECOP II · Procesos trae «No» (492 filas) y «No Especificado» (638) como tipo de contrato; caen en `other`. Contratos no tiene valores sin reconocer.
- `tipodocproveedor` trae NIT, Cédula de Ciudadanía, Cédula de Extranjería, «No Definido» (65) y «Otro» (20): todos están en la tabla de `reglas.md`. Decisiones en [ADR 0022](adr/0022-catalogos-de-tipo-de-contrato-y-proveedor.md).

---

## 2 nov 2026 · Normalización del Plan Anual

- La copia tiene 18.764 líneas y 15.139 distintas: 3.625 son idénticas en las seis columnas de la lista blanca. Se conservan; con todas se reproducen las 726 líneas directas de enero de 2022.
- `valor_total_estimado`: 18.752 enteros, 10 en notación científica con coma («1,10E+11») y 2 sin lectura segura («1,2611», «5,1995», ambas de contratación directa en 2017). Hay 11 valores en 0: 9 en 2014, 1 en 2017 y 1 en 2023.
- Serie de I8 sobre la tabla normalizada: enero 46 % (2014), 57 % (2018) y 52 % (2022); de febrero a junio, 15, 16 y 8 %. Coincide con la exploración. Decisiones en [ADR 0021](adr/0021-normalizacion-del-plan-anual-sin-deduplicar.md).
- Sigue 2023 en 44 y 44 %: es año de elección local, que se analiza aparte.

---

## 2 nov 2026 · Catálogo de modalidades contra la copia

- Contratos usa 11 textos de modalidad y todos están en el catálogo de `docs/reglas.md`. Ejecución contractual usa 6, que `ftfy.fix_encoding` repara sin dejar restos. El Plan Anual usa 15 escrituras de 6 modalidades; «mnima cuanta» perdió las letras con tilde en origen, así que quitar tildes no basta y se cataloga como variante.
- Procesos trae 13 textos: los 11 de Contratos más «Solicitud de información a los Proveedores» (786 filas, 388 con respuestas) y «Subasta de prueba» (343 filas, ninguna con respuestas). Ninguna de las 1.129 filas está adjudicada. Caen en «Otra».
- Con el catálogo, esos dos son los únicos valores no reconocidos de las cuatro fuentes (decisión en [ADR 0020](adr/0020-catalogo-de-modalidades-en-toml.md)).

## 2 nov 2026 · Primera corrida completa de `--refresh`

- Las seis consultas salieron en una sola corrida de 3 min 46 s. Se escribió `data/snapshot/manifest.json`.
- Reproducibilidad: Contratos (7.468 filas), Adiciones (15.884), Ejecución contractual (25.783) y Plan Anual (18.764) dieron el mismo SHA-256 que la extracción individual del 1 nov. Proveedores quedó en 4.466 filas.
- Procesos pasó de 23.428 a 23.450 filas: 22 registros tardíos de la fuente, como ya había ocurrido con Contratos.
- Fecha de corte global: 30 oct 2026 (firma más reciente de los contratos). Por fuente: Procesos y Adiciones, 30 oct 2026; Ejecución contractual, 30 jun 2023, que coincide con la cobertura documentada. Proveedores y Plan Anual quedan en `null`: no tienen una columna de fecha utilizable (el Plan solo trae nombres de mes).
- Las fechas de MEData vienen día/mes/año («24/06/2022»). Como texto, «9/12/2022» ordena después de «10/11/2022»; la fecha de corte se calcula sobre fechas, no sobre texto.

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

## 4 nov 2026 · Conciliación mensual SECOP–MEData (R15)

- Con la copia, seis de los 18 meses de MEData (2022-01 a 2023-06) quedan bajo el 80 % de contratos en ambas fuentes: marzo a julio y diciembre de 2022. Detalle por mes en el [ADR 0031](adr/0031-conciliacion-secop-medata.md).
- En 2.503 de los 2.632 contratos compartidos, MEData fecha la firma después que SECOP II (mediana de 5 días). Por eso el mes de la conciliación sale de la fecha de SECOP II.
- Enero de 2022: 727 contratos por la fecha propia de MEData y 725 por la de SECOP II. Los 723 de la primera validación son solo contratación directa en SECOP II; los 727, todas las modalidades en MEData. La comparación no es estricta, pero la conciliación de R15 sí usa todas las modalidades en las dos fuentes.
- Pendiente: confirmar `Adicion en el valor` contra `valor_total_adic_contrato` (ADR 0025).
