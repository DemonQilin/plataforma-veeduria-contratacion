# Indicadores

Indicadores I1–I8 y metodología del hallazgo titular.

Los indicadores siguen la literatura de *red flags* en compras públicas: la guía de la Open Contracting Partnership (2024) y el índice de riesgo de corrupción de Fazekas. Al escribir la metodología final se citarán con el nombre y la definición exactos de la guía. Son indicadores elementales, sin pesos ni índices compuestos.

**Regla de lectura para todos:** un valor alto marca un patrón que vale la pena revisar, no prueba una irregularidad. El tablero lo dice así en cada indicador.

---

## 1. Catálogo

| ID | Indicador | Pregunta para el ciudadano | Fórmula | Fuente | Prioridad |
|---|---|---|---|---|---|
| I1 | Proporción de contratación directa | ¿Cuánto se contrata sin competencia? | Contratos (y valor) por contratación directa ÷ total, por año y secretaría. Se reporta también la proporción «no competitiva» (directa más régimen especial) | Contratos | **MVP** |
| I2 | Concentración antes de la restricción | ¿Se adelanta la contratación cuando se acerca la Ley de Garantías? | % de la contratación directa del 1 de enero a la fecha de corte (día y mes) firmada antes del inicio de la restricción, frente a la misma ventana en años de control | Contratos + MEData | **MVP · titular** |
| I3 | Oferente único | En los procesos con competencia, ¿cuántas veces se presentó una sola empresa? | Procesos competitivos adjudicados con `proveedores_unicos_con = 1` ÷ procesos competitivos adjudicados | Procesos | **MVP** |
| I4 | Concentración de proveedores | ¿Unas pocas empresas reciben buena parte del dinero? | Valor adjudicado a las 5 personas jurídicas con más valor ÷ valor total a personas jurídicas, por secretaría y año | Contratos + Procesos | **MVP** |
| I5 | Adiciones | ¿Cuánto crecen los contratos después de firmados? | Contratos con adición ÷ total; valor adicionado ÷ valor inicial, por secretaría | MEData (2022–2023) | **MVP** |
| I6 | Plazo de publicación corto | ¿Hubo tiempo suficiente para que otros se presentaran? | Días entre publicación y cierre de ofertas, por modalidad | Procesos | Extra |
| I7 | Desviación de valor | ¿Se adjudicó por encima de lo presupuestado? | `valor_total_adjudicacion` ÷ `precio_base` | Procesos | Extra |
| I8 | Planeación frente a ejecución | ¿La contratación de los años electorales se planea así desde el inicio? | % de la contratación directa planeada con inicio en enero y de febrero a junio, por año; y comparación con lo firmado donde hay datos de ambos (2022–2023) | MEData · Plan + Contratos | **MVP** |

Todo indicador se publica con numerador, denominador, n, fuentes, fecha de corte y versión de las reglas (R16), y con supresión de celdas pequeñas cuando está desagregado (R13).

## 2. Detalles de cálculo

- **Modalidades competitivas para I3:** licitación pública, selección abreviada (menor cuantía y subasta inversa), concurso de méritos y mínima cuantía. Se excluyen contratación directa y régimen especial. La clasificación sale del catálogo de modalidad de [`reglas.md`](reglas.md).
- **I1 en dos niveles:** contratación directa sola, y «no competitiva» (directa más régimen especial). Ver D2 en [`reglas.md`](reglas.md).
- **I1 por año y secretaría:** se publica cada año de la copia, en el Distrito y en cada secretaría de R8. La secretaría «sin asignar» tiene su propia celda, para que las secretarías sumen al Distrito y la supresión complementaria (D6) funcione. El año de la fecha de corte queda parcial (1 de enero al corte); es una proporción dentro del año y el tablero muestra la fecha de corte. Por valor se usa el valor inicial (D3, que en SECOP II incluye las adiciones) y se excluye el crédito público (R7). Decisión en el [ADR 0039](adr/0039-i1-anual-por-secretaria.md).
- **I3 por año y secretaría:** se cuenta por proceso canónico (R5), por año de publicación, del 1 de enero de 2022 a la fecha de corte; el último año queda parcial. Los procesos que reportan cero oferentes se excluyen (R9) y se reportan en la calidad de datos. La secretaría es la unidad que adelanta el proceso, que no siempre es la que pidió el bien. Solo por número de procesos. Decisión en el [ADR 0043](adr/0043-i3-oferente-unico.md).
- **I4 por año y secretaría:** se calcula solo por valor inicial (D3), por año de la fecha de firma, en el Distrito y en cada secretaría de R8 (incluida «sin asignar»). Parte de los contratos con proveedor persona jurídica (R14), sin crédito público ni contratos sin valor (R7). El proveedor se cruza con el contrato por referencia, porque `suppliers` puede apuntar a una versión no canónica. Decisión en el [ADR 0045](adr/0045-i4-concentracion-agregada-de-proveedores.md).
- **I4 sin nombres:** como los organizadores no han respondido si se pueden nombrar personas jurídicas, I4 se publica solo agregado (plan B del [plan](plan.md)). Ningún proveedor sale de `data/outputs/`.
- **I4 en secretarías pequeñas:** una secretaría con 5 proveedores o menos se publica suprimida, porque su razón sería 100 % por construcción; las demás celdas siguen R13 y D6.
- **I5 y la regla del 50 %:** la ley limita las adiciones al 50 % del valor inicial. El indicador muestra cuántos contratos se acercan a ese tope, sin calificarlos: la variante `near_addition_cap` es la proporción de contratos con adición cuya adición llega al 45 % del valor inicial.
- **I5 solo con MEData:** el valor de SECOP II ya incluye las adiciones y su tipo «Adicion en el valor» subcuenta, así que el conteo, el valor adicionado (sin crédito público, R7) y la variante salen de MEData: contratos firmados del 4 de enero de 2022 al 30 de junio de 2023, por año y secretaría (Distrito y R8). Un contrato sin monto de adiciones informado sale del denominador. No hay cifra para 2024–2026. Decisión en el [ADR 0044](adr/0044-i5-adiciones-desde-medata.md).
- **I6 queda como extra** porque los plazos mínimos legales cambian según la modalidad y la cuantía, y calibrarlos bien toma más tiempo del disponible.
- **I7 y el crédito público:** como todo indicador de valor, excluye las operaciones de crédito público (R7).

---

## 3. Metodología del hallazgo titular (I2)

### Medida

Para cada año *a* se calcula:

> **Concentración pre-restricción (a)** = contratos de contratación directa firmados entre el 1 de enero y el día anterior al inicio de la restricción ÷ contratos de contratación directa firmados del 1 de enero a la fecha de corte (día y mes) del mismo año.

- **Ventanas:** en 2022, del 1 al 28 de enero; en 2026, del 1 al 30 de enero. En los años de control (2023, 2024, 2025) se usa la ventana a mitad de camino entre las dos, del 1 al 29 de enero, para comparar periodos de igual duración. Las ventanas se derivan del calendario de referencia (R10, R11, ADR 0034).
- **Denominador en el tramo común:** del 1 de enero al día y mes de la fecha de corte, en todos los años (R12). Con la copia actual, el corte es el 30 de octubre, así que todos los años se miden del 1 de enero al 30 de octubre.
- **Dos versiones:** por número de contratos y por valor (sin operaciones de crédito público, R7). El valor es el inicial (D3), el de la primera versión firmada en SECOP II: no depende de si el contrato aparece en MEData, pero incluye las adiciones, porque SECOP II sobrescribe el valor. En 2022 y 2023 esto mueve la proporción por valor menos de un punto (ADR 0044); las adiciones propiamente las mide I5.
- **Cuatro variantes:** el total, la prestación de servicios (`service_contract`), el resto de tipos de contrato (`non_service_contract`) y el total sin contratos interadministrativos (`excluding_interadministrative`).
  - La última es una sensibilidad: quita los interadministrativos del numerador y del denominador, porque su peso cambia entre años (en 2023 no hay interadministrativos de julio a octubre por la restricción local). La definición base no cambia y es la cifra titular, por número de contratos; la variante se publica como sensibilidad (ADR 0036, ADR 0037).

### El principal factor de confusión

Enero es también el mes en que se renuevan los contratos de prestación de servicios. Un pico en enero no prueba por sí solo un efecto electoral. Se controla de tres formas:

1. **Comparación con años de control:** la renovación ocurre todos los años, así que solo cuenta el exceso de los años de restricción sobre los de control.
2. **Separación por tipo:** se calcula aparte para prestación de servicios y para el resto de contratos.
3. **Duración de los contratos:** si en los años de restricción los contratos de enero duran más (para cubrir los meses en que no se podrá contratar), es una señal de anticipación independiente del volumen. Se mide como la proporción de contratos directos firmados en la ventana de enero cuyo plazo pactado termina después del fin de la restricción de referencia (variante `spans_restriction`, solo por número, ADR 0035).
   - **Plazo pactado:** la fecha de fin de SECOP II menos los días adicionados. Se usa SECOP II y no `duracion_en_dias` de MEData porque este llega hasta junio de 2023.
   - **Fin de restricción de referencia:** el real en 2022 (19 de junio) y 2026 (21 de junio); en los años de control, el punto medio de ambos, el 20 de junio.
   - **Limitación:** no se pudo verificar que SECOP II actualice la fecha de fin cuando se agregan días, así que restar los días adicionados es un supuesto.
   - **Resultado: no concluyente.** La señal no separa tratamiento de control. En 2022 es 99,6 % (720 de 723) y en 2026, 99,2 % (701 de 707), pero en 2025, año de control, es 98,9 % (345 de 349). Casi todos los contratos de enero duran hasta después de junio, con o sin restricción. Por eso no apoya ni refuta el titular y no entra en los criterios de decisión.

### Serie de planeación (I8, 2014–2023)

Con el Plan Anual de Adquisiciones se calcula, para cada año, la proporción de la contratación directa planeada con inicio estimado en enero y la proporción planeada de febrero a junio (los meses de la restricción presidencial).

- **Tratamiento:** 2014, 2018 y 2022, años de elección presidencial.
- **Elecciones locales (2015, 2019, 2023):** se analizan aparte, porque su restricción afecta convenios y nómina desde mediados de año, no la contratación directa en enero.
- **Control:** 2016, 2017, 2020 y 2021.
- **Factor de confusión adicional:** el primer año de cada administración (2016, 2020) tiende a planear menos para enero, porque el plan lo arma un gobierno que apenas llega. Se señala en los resultados.
- **Cálculo:** el denominador son las líneas directas del año con mes estimado de inicio; el numerador, las que empiezan en enero (`planned_january`) o de febrero a junio (`planned_february_june`). Se publica por número y por valor (`estimated_value`), a nivel Distrito. Las líneas sin valor quedan fuera de la medida por valor.
- **Limitaciones propias:** un plan no es un contrato; el mes es una estimación, y puede referirse al inicio del proceso y no a la firma. El plan no distingue el crédito público, así que la medida por valor no puede excluirlo (R7).
- **Comparación con lo firmado (2022–2023):** donde hay plan y ejecución a la vez, se calcula la misma proporción sobre los contratos directos firmados del año calendario completo, en `linked_contracts`: `signed_january` y `signed_february_june`, por número y por valor. Las dos series se leen lado a lado. Como el plan no tiene llave por contrato, la comparación es solo agregada (R17). La medida por valor firmada usa el valor inicial (D3, que en SECOP II incluye las adiciones) y excluye el crédito público (R7); la planeada no puede, así que las dos no son estrictamente comparables en valor.

### Limpieza previa

- **Consolidación:** una fila por `referencia_del_contrato`, con la primera fecha de firma no vacía; se descartan los registros sin fecha de firma (R3, R4).
- **Normalización de modalidad:** todo lo que empiece por «Contratación directa», sin distinguir mayúsculas, cuenta como directa (R6, D1).
- **Validación cruzada:** para 2022 y el primer semestre de 2023, se calcula por mes qué proporción de contratos aparece en ambas fuentes (R15, ADR 0031).
  - **2022:** cuatro meses quedan por debajo del 80 %: marzo (66,7 %), abril (77,8 %), mayo (74,5 %) y diciembre (70,3 %). Antes de reconocer las referencias «de AAAA» (ADR 0047) eran seis, con junio (74,3 %) y julio (67,6 %), que ahora llegan a 88,7 % y 86,1 %. Las cifras de I2 de 2022 se leen con esa advertencia.
  - **2023:** ningún mes baja del 80 %; el más bajo es marzo (88,1 %).
  - **Enero de 2022:** 723 contratos en SECOP II frente a 727 en MEData. La comparación no es estricta, porque cada fuente usa su propia fecha de firma.

### Criterio de decisión (3 nov 2026)

El hallazgo se mantiene como titular si se cumple al menos una de estas condiciones:

1. **Serie ejecutada:** en ambos años de restricción, la concentración supera el valor más alto de los años de control, tanto por número como por valor.
2. **Serie de planeación:** en los tres años de elección presidencial, la proporción planeada de febrero a junio queda por debajo del mínimo de los años de control.

Con la copia actual, la serie de planeación cumple su criterio en las dos medidas. Por número de contratos, los años de tratamiento van de 8,3 a 16,0 % y el mínimo de control es 34,8 %; por valor, de 6,3 a 23,5 % frente a 37,4 %.

La serie ejecutada también lo cumple. Con la definición base, el menor año de tratamiento (2022) supera al máximo de control (2025) por 27,6 puntos por número (58,3 % frente a 30,7 %) y por 1,8 puntos por valor (30,7 % frente a 28,9 %). Sin interadministrativos, las brechas son 30,5 y 26,3 puntos.

**Resultado del punto de decisión 1 (5 nov 2026):** el titular se mantiene. La cifra titular de I2 es la definición base por número de contratos (ADR 0037); el registro está en la [bitácora](bitacora.md). Si ninguna se cumpliera, el titular pasa al indicador con el resultado más claro entre I3, I4 e I5, y la Ley de Garantías queda como contexto.

### Cómo se comunica

Frase del hallazgo, con las cifras finales de la definición base por número de contratos (ADR 0037):

> En 2022 y 2026, antes de que la Ley de Garantías restringiera la contratación directa, la Alcaldía de Medellín firmó en enero el **58 %** y el **65 %** de su contratación directa del 1 de enero al 30 de octubre. En los años sin restricción (2023 a 2025), esa proporción estuvo entre **19 %** y **31 %**.

### Limitaciones que se declaran

- **Adelantar contratos es legal.** La ley restringe contratar durante el periodo, no antes. El hallazgo describe cómo se planea la contratación, no una irregularidad.
- **Correlación, no causalidad.** Otros factores, como los cambios de gobierno o de presupuesto, pueden influir.
- **Cobertura.** El 4 % de los contratos de MEData (106 de 2.939) no aparece en SECOP II, y MEData solo cubre hasta junio de 2023.
- **Conciliación de 2022.** Cuatro meses de 2022 (marzo, abril, mayo y diciembre) tienen menos del 80 % de los contratos en ambas fuentes (R15).
- **I8 por valor es menos robusto que por número.** Si se quitan las cinco líneas directas más grandes de cada año, la brecha por valor baja de 13,9 a 3,2 puntos. La medida principal es el número de contratos; el valor se presenta como complemento. El plan tampoco permite excluir el crédito público (R7), y el de 2023 no sirve como referencia mensual.
- **I2 por valor es menos concluyente que por número.** Con la definición base, 2022 supera al mejor año de control (2023) por 1,8 puntos (30,7 % frente a 28,9 %). Sin interadministrativos la brecha es de 26,3 puntos. Por eso la cifra titular es la del número de contratos y el valor es un complemento (ADR 0037).
- **Dos años de tratamiento.** Con tan pocos casos, el resultado se presenta como un patrón descriptivo, sin pruebas de significancia estadística.

---

## Referencias

- [Open Contracting Partnership · Red Flags in Public Procurement (2024)](https://open-contracting.org/redflags)
- [Portafolio · En víspera de Ley de Garantías se quintuplicó la contratación](https://www.portafolio.co/economia/en-vispera-a-ley-de-garantias-se-quintuplico-la-contratacion-561050)