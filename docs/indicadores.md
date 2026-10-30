# Indicadores

Indicadores I1–I8 y metodología del hallazgo titular.

Los indicadores siguen la literatura de *red flags* en compras públicas: la guía de la Open Contracting Partnership (2024) y el índice de riesgo de corrupción de Fazekas. Al escribir la metodología final se citarán con el nombre y la definición exactos de la guía. Son indicadores elementales, sin pesos ni índices compuestos.

**Regla de lectura para todos:** un valor alto marca un patrón que vale la pena revisar, no prueba una irregularidad. El tablero lo dice así en cada indicador.

---

## 1. Catálogo

| ID | Indicador | Pregunta para el ciudadano | Fórmula | Fuente | Prioridad |
|---|---|---|---|---|---|
| I1 | Proporción de contratación directa | ¿Cuánto se contrata sin competencia? | Contratos (y valor) por contratación directa ÷ total, por año y secretaría. Se reporta también la proporción «no competitiva» (directa más régimen especial) | Contratos | **MVP** |
| I2 | Concentración antes de la restricción | ¿Se adelanta la contratación cuando se acerca la Ley de Garantías? | % de la contratación directa de enero a octubre firmada antes del inicio de la restricción, frente a la misma ventana en años de control | Contratos + MEData | **MVP · titular** |
| I3 | Oferente único | En los procesos con competencia, ¿cuántas veces se presentó una sola empresa? | Procesos competitivos adjudicados con `proveedores_unicos_con = 1` ÷ procesos competitivos adjudicados | Procesos | **MVP** |
| I4 | Concentración de proveedores | ¿Unas pocas empresas reciben buena parte del dinero? | Valor adjudicado a las 5 personas jurídicas con más valor ÷ valor total a personas jurídicas, por secretaría y año | Contratos + Procesos | **MVP** |
| I5 | Adiciones | ¿Cuánto crecen los contratos después de firmados? | Contratos con adición ÷ total; valor adicionado ÷ valor inicial, por secretaría | MEData (2022–2023) + Adiciones | **MVP** |
| I6 | Plazo de publicación corto | ¿Hubo tiempo suficiente para que otros se presentaran? | Días entre publicación y cierre de ofertas, por modalidad | Procesos | Extra |
| I7 | Desviación de valor | ¿Se adjudicó por encima de lo presupuestado? | `valor_total_adjudicacion` ÷ `precio_base` | Procesos | Extra |
| I8 | Planeación frente a ejecución | ¿La contratación de los años electorales se planea así desde el inicio? | % de la contratación directa planeada con inicio en enero y de febrero a junio, por año; y comparación con lo firmado donde hay datos de ambos (2022–2023) | MEData · Plan + Contratos | **MVP** |

Todo indicador se publica con numerador, denominador, n, fuentes, fecha de corte y versión de las reglas (R16), y con supresión de celdas pequeñas cuando está desagregado (R13).

## 2. Detalles de cálculo

- **Modalidades competitivas para I3:** licitación pública, selección abreviada (menor cuantía y subasta inversa), concurso de méritos y mínima cuantía. Se excluyen contratación directa y régimen especial. La clasificación sale del catálogo de modalidad de [`reglas.md`](reglas.md).
- **I1 en dos niveles:** contratación directa sola, y «no competitiva» (directa más régimen especial). Ver D2 en [`reglas.md`](reglas.md).
- **I4 por secretaría:** Contratos no trae la dependencia, así que se toma de `nombre_de_la_unidad_de` en Procesos a través de la llave de cruce. Si el campo resulta poco confiable, I4 se reporta solo a nivel Distrito.
- **I4 y los nombres:** es el único indicador que nombra proveedores, y solo si son personas jurídicas (R14).
- **I5 y la regla del 50 %:** la ley limita las adiciones al 50 % del valor inicial. El indicador muestra cuántos contratos se acercan a ese tope, sin calificarlos.
- **I6 queda como extra** porque los plazos mínimos legales cambian según la modalidad y la cuantía, y calibrarlos bien toma más tiempo del disponible.
- **I7 y el crédito público:** como todo indicador de valor, excluye las operaciones de crédito público (R7).

---

## 3. Metodología del hallazgo titular (I2)

### Medida

Para cada año *a* se calcula:

> **Concentración pre-restricción (a)** = contratos de contratación directa firmados entre el 1 de enero y el día anterior al inicio de la restricción ÷ contratos de contratación directa firmados de enero a octubre del mismo año.

- **Ventanas:** en 2022, del 1 al 28 de enero; en 2026, del 1 al 30 de enero. En los años de control (2023, 2024, 2025) se usa la misma ventana, del 1 al 29 de enero, para comparar periodos de igual duración. Las ventanas se derivan del calendario de referencia (R10, R11).
- **Denominador de enero a octubre:** 2026 solo tiene datos hasta octubre, así que todos los años se miden con ese mismo tramo (R12).
- **Dos versiones:** por número de contratos y por valor (sin operaciones de crédito público).

### El principal factor de confusión

Enero es también el mes en que se renuevan los contratos de prestación de servicios. Un pico en enero no prueba por sí solo un efecto electoral. Se controla de tres formas:

1. **Comparación con años de control:** la renovación ocurre todos los años, así que solo cuenta el exceso de los años de restricción sobre los de control.
2. **Separación por tipo:** se calcula aparte para prestación de servicios y para el resto de contratos.
3. **Duración de los contratos:** si en los años de restricción los contratos de enero duran más (para cubrir los meses en que no se podrá contratar), es una señal de anticipación independiente del volumen.

### Serie de planeación (I8, 2014–2023)

Con el Plan Anual de Adquisiciones se calcula, para cada año, la proporción de la contratación directa planeada con inicio estimado en enero y la proporción planeada de febrero a junio (los meses de la restricción presidencial).

- **Tratamiento:** 2014, 2018 y 2022, años de elección presidencial.
- **Elecciones locales (2015, 2019, 2023):** se analizan aparte, porque su restricción afecta convenios y nómina desde mediados de año, no la contratación directa en enero.
- **Control:** 2016, 2017, 2020 y 2021.
- **Factor de confusión adicional:** el primer año de cada administración (2016, 2020) tiende a planear menos para enero, porque el plan lo arma un gobierno que apenas llega. Se señala en los resultados.
- **Limitaciones propias:** un plan no es un contrato; el mes es una estimación, y puede referirse al inicio del proceso y no a la firma.

### Limpieza previa

- **Consolidación:** una fila por `referencia_del_contrato`, con la primera fecha de firma no vacía; se descartan los registros sin fecha de firma (R3, R4).
- **Normalización de modalidad:** todo lo que empiece por «Contratación directa», sin distinguir mayúsculas, cuenta como directa (R6, D1).
- **Validación cruzada:** para 2022 y el primer semestre de 2023, los conteos mensuales de SECOP II se comparan con MEData (R15). La primera prueba dio 723 en SECOP II frente a 727 en MEData para enero de 2022.

### Criterio de decisión (3 nov 2026)

El hallazgo se mantiene como titular si se cumple al menos una de estas condiciones:

1. **Serie ejecutada:** en ambos años de restricción, la concentración supera el valor más alto de los años de control, tanto por número como por valor.
2. **Serie de planeación:** en los tres años de elección presidencial, la proporción planeada de febrero a junio queda por debajo del mínimo de los años de control.

Con los datos preliminares, la serie de planeación ya cumple su criterio (8–16 % frente a 35–46 %). Si ninguna se cumple, el titular pasa al indicador con el resultado más claro entre I3, I4 e I5, y la Ley de Garantías queda como contexto.

### Cómo se comunica

Plantilla de la frase del hallazgo, a completar con las cifras finales:

> En 2022 y 2026, antes de que la Ley de Garantías restringiera la contratación directa, la Alcaldía de Medellín firmó en enero el **X %** de la contratación directa del año. En los años sin restricción, esa proporción estuvo entre **Y %** y **Z %**.

### Limitaciones que se declaran

- **Adelantar contratos es legal.** La ley restringe contratar durante el periodo, no antes. El hallazgo describe cómo se planea la contratación, no una irregularidad.
- **Correlación, no causalidad.** Otros factores, como los cambios de gobierno o de presupuesto, pueden influir.
- **Cobertura.** El 11 % de los contratos de MEData no aparece en SECOP II, y MEData solo cubre hasta junio de 2023.
- **Dos años de tratamiento.** Con tan pocos casos, el resultado se presenta como un patrón descriptivo, sin pruebas de significancia estadística.

---

## Referencias

- [Open Contracting Partnership · Red Flags in Public Procurement (2024)](https://open-contracting.org/redflags)
- [Portafolio · En víspera de Ley de Garantías se quintuplicó la contratación](https://www.portafolio.co/economia/en-vispera-a-ley-de-garantias-se-quintuplico-la-contratacion-561050)