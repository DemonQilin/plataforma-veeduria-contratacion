# Producto

Qué se construye, para quién, con qué alcance y con qué principios éticos.

---

## 1. Propósito

### Pregunta

¿Cómo cambia la contratación de la Alcaldía de Medellín alrededor de las restricciones de la Ley de Garantías, y qué muestran los indicadores estándar de riesgo en compras públicas sobre su contratación entre 2022 y 2026?

### Para quién

| Público | Qué necesita |
|---|---|
| Ciudadanía y veedurías | Entender en lenguaje claro cómo contrata la Alcaldía y qué patrones vale la pena vigilar |
| Periodistas | Indicadores con método documentado que puedan citar y contrastar |
| Jurado del hackathon | Un artefacto que funcione, con datos reales y un hallazgo con cifra |

### Hallazgo titular (hipótesis por confirmar)

> En los años con restricción presidencial a la contratación directa (2022 y 2026), la Alcaldía firmó antes de que empezara la restricción una proporción de su contratación directa anual muy superior a la de los años sin restricción.

Señal preliminar, sin limpieza (SECOP II, contratación directa, proporción firmada en enero):

| Año | 2022 ⚑ | 2023 | 2024 | 2025 | 2026 ⚑ |
|---|---:|---:|---:|---:|---:|
| % del año firmado en enero | 52 % | 27 % | 20 % | 34 % | 66 %* |

⚑ Año con restricción presidencial. *2026 sobre enero a octubre. Estas cifras se recalculan con la metodología de [`indicadores.md`](indicadores.md) antes de usarse.

### Segundo nivel del hallazgo: la anticipación se planea

Los Planes Anuales de Adquisiciones publicados en MEData (2014–2023) muestran que el patrón no es improvisado: en los tres años de elección presidencial del periodo, la Alcaldía programó desde el plan su contratación directa para enero y casi nada para los meses de restricción.

| Contratación directa planeada | 2014 ⚑ | 2018 ⚑ | 2022 ⚑ | Años sin elecciones (2016, 2017, 2020, 2021) |
|---|---:|---:|---:|---:|
| % con inicio estimado en enero | 46 % | 57 % | 52 % | 24–34 % |
| % con inicio estimado de febrero a junio | 15 % | 16 % | 8 % | 35–46 % |

Para enero de 2022, las tres fuentes coinciden: 726 contratos directos planeados, 723 firmados según SECOP II y 727 según la ejecución contractual de MEData.

Este nivel tiene dos ventajas: cubre tres ciclos presidenciales con tres administraciones distintas, lo que lo hace más robusto y políticamente neutral, y muestra que se trata de un comportamiento institucional planeado.

### Por qué importa ahora

Las elecciones locales de octubre de 2027 traen nuevas restricciones desde mediados de ese año. Este proyecto deja una **línea base**: cómo se ve la contratación normal y cómo se movió en los ciclos anteriores, para que la ciudadanía y la prensa tengan con qué comparar.

---

## 2. Alcance

### Qué entra

| Dimensión | Decisión |
|---|---|
| Entidad | Distrito de Medellín, sector central (R1 en [`reglas.md`](reglas.md)) |
| Periodo | 1 ene 2022 a la fecha de corte de los datos (R2) |
| Unidad de análisis | El contrato (referencia única del Distrito) y el proceso de contratación |
| Nivel de agregación | Distrito, secretaría y mes. Nunca persona natural |
| Indicadores | Los marcados como MVP en [`indicadores.md`](indicadores.md) |

### Qué queda fuera, de forma explícita

| Fuera | Motivo |
|---|---|
| Concejo y Personería | Son otras entidades, aunque compartan NIT |
| Conglomerado (EPM, Metro, empresas industriales) | Volumen y calidad de datos distintos; siguiente etapa |
| Instituciones universitarias, incluido el ITM | Conflicto con la institución anfitriona y cruce de convenios no verificado; siguiente etapa |
| Tienda Virtual del Estado (acuerdos marco) | Fuente distinta; el 11 % de contratos de MEData que no cruza con SECOP II podría estar allí |
| Información de personas naturales | Bases del concurso y Ley 1581 de 2012 |
| Juicios sobre casos individuales | El proyecto muestra patrones, no acusa |

### Periodos de comparación

| Año | Papel en el análisis | Por qué |
|---|---|---|
| 2022 | Tratamiento | Restricción presidencial a la contratación directa desde el 29 ene |
| 2023 | Control para contratación directa | Las locales restringen convenios interadministrativos y nómina, no la contratación directa en general |
| 2024 | Control | Sin elecciones |
| 2025 | Control | La restricción de convenios por el Congreso empezó el 8 nov; no afecta enero |
| 2026 | Tratamiento | Restricción presidencial desde el 31 ene |

**Análisis de planeación (2014–2023).** Con el Plan Anual de Adquisiciones de MEData se agrega una serie de diez años: 2014, 2018 y 2022 como años de elección presidencial; 2015, 2019 y 2023 como años de elecciones locales, analizados aparte; y 2016, 2017, 2020 y 2021 como control.

---

## 3. Tablero

### 3.1 Principios

- **Para un ciudadano, no para un analista.** Cada gráfico lleva una frase que dice qué muestra. Los términos técnicos se explican donde aparecen.
- **Primero la historia, después la exploración.** El tablero abre con el hallazgo titular y luego permite explorar los indicadores.
- **Pensado primero para el celular,** que es donde la mayoría de la gente lo va a abrir.
- **Sin tono acusatorio.** Los patrones se presentan como «para revisar», con las limitaciones visibles.
- **Accesible.** Cada gráfico tiene una descripción en texto y su tabla de datos, siguiendo los patrones WAI-ARIA.
- **Solo presenta.** El tablero no calcula ni filtra: toda cifra sale tal cual de `data/outputs/`.

### 3.2 Recorrido de la historia guiada

| # | Pantalla | Qué responde | Contenido |
|---|---|---|---|
| 1 | Portada | ¿Qué encontraron? | La frase del hallazgo con su cifra, la fecha de corte y un botón para empezar |
| 2 | La regla | ¿Qué es la Ley de Garantías? | Explicación en dos frases y una línea de tiempo con los periodos de restricción de 2022 a 2027 |
| 3 | El patrón | ¿Qué pasa con la contratación alrededor de esas fechas? | Gráfico mensual de contratación directa, de 2022 a la fecha de corte, con los periodos de restricción sombreados |
| 4 | La comparación | ¿Es distinto en los años con restricción? | Barras de concentración pre-restricción por año, distinguiendo tratamiento y control |
| 5 | La objeción | ¿No es solo la renovación de enero? | Prestación de servicios frente al resto y duración de los contratos de enero |
| 6 | Más allá de las elecciones | ¿Qué otros patrones hay? | Explorador de I1, I3, I4 e I5 por año y secretaría |
| 7 | Cómo leer esto | ¿Qué significa y qué no? | Metodología en lenguaje claro, limitaciones y calidad de los datos |
| 8 | Hacia 2027 | ¿Para qué sirve ahora? | La línea base y qué vigilar en las elecciones locales |
| 9 | Fuentes | ¿De dónde salen los datos? | Fuentes con enlace y licencia, fecha de corte, código abierto y declaración de uso de IA |

### 3.3 Explorador de indicadores (pantalla 6)

- **Filtros:** indicador, año y secretaría.
- **Vista principal:** ranking de secretarías para el indicador y año elegidos, con el promedio del Distrito como referencia.
- **Detalle:** evolución anual de la secretaría seleccionada.
- **Reglas visibles:** las celdas con menos de 5 contratos aparecen como «datos insuficientes» (R13). Cada cifra muestra su n.
- **Sin listas de contratos individuales.** El explorador llega hasta la secretaría. Quien quiera ver contratos puede ir a SECOP II, enlazado desde las fuentes.

### 3.4 Stack y despliegue

Las razones de cada elección están en [`adr/`](adr/).

| Pieza | Decisión |
|---|---|
| Tipo de sitio | Sitio estático: no hay servidor que mantener ni que se caiga durante la evaluación |
| Frontend | Astro con TypeScript estricto, y componentes de React solo donde hay interacción (el explorador) |
| Gestor de paquetes | pnpm, con la versión declarada en `package.json` |
| Gráficos | Observable Plot, renderizado como SVG en el build para la historia y en el navegador solo en el explorador |
| Páginas por secretaría | Una página estática por secretaría, con sus indicadores y su propia tarjeta al compartir |
| Datos | El sitio lee `data/outputs/` en el build, con tipos generados desde el contrato del pipeline. No consulta APIs externas |
| Hosting | GitHub Pages: gratuito, público y en el mismo repositorio que exigen las bases |
| Actualización | GitHub Actions corre el pipeline, reconstruye el sitio y lo publica. Durante el concurso, la fecha de corte queda fija (ver [`plan.md`](plan.md)) |
| Indexación | Durante el concurso el sitio es público pero no indexable (`noindex` y `robots.txt`). Después de la final y de validar las cifras, se habilita la indexación |
| Compartir | Etiquetas Open Graph desde el inicio, con título, descripción e imagen del hallazgo |

La indexación se bloquea durante el concurso para que un hallazgo aún sin validar no circule en buscadores en medio de la discusión pública, como en la práctica de embargo de los medios. La tarjeta al compartir importa desde el primer día, porque la difusión ciudadana pasa más por WhatsApp y redes que por buscadores.

### 3.5 Fuera del MVP del tablero

- Búsqueda de contratos o proveedores individuales.
- Comparación con otras ciudades o entidades.
- Alertas o suscripciones.
- Versión en inglés.

---

## 4. Ética y privacidad

### 4.1 Principios

1. **Patrones, no personas.** El proyecto describe cómo contrata una entidad. No señala contratistas, funcionarios ni alcaldes.
2. **Datos mínimos.** Solo se descargan las columnas necesarias. Los datos personales no entran al pipeline ni al repositorio (ver la lista blanca en [`fuentes.md`](fuentes.md)).
3. **Método a la vista.** Cada cifra se puede reconstruir desde las fuentes con el código publicado (R16).
4. **Señales, no veredictos.** Un indicador alto invita a revisar; no prueba una irregularidad.
5. **Neutralidad política.** El análisis se organiza por calendario electoral, no por administración, y aplica las mismas reglas a todos los años.

### 4.2 Cumplimiento de las bases del concurso

| Compromiso de las bases | Cómo se cumple |
|---|---|
| Uso íntegro y privacidad | Ningún cruce busca identificar personas. Las cifras desagregadas con menos de 5 contratos se suprimen (R13) |
| Transparencia y apertura | Código, análisis y tablero en un repositorio público, con licencia abierta |
| Información restringida | No aplica: no se usan datos entregados bajo confidencialidad (no se compite en Finanzas) |
| Atribución de fuentes | Cada conjunto se cita con fuente, enlace y licencia en el tablero, en `instrucciones.txt` y en la ficha |
| Datos reales | Solo SECOP II y MEData, sin datos sintéticos |
| Originalidad | Trabajo propio del equipo; las metodologías externas (OCP, Fazekas) se citan |
| Inteligencia artificial | Se declara en `instrucciones.txt` (sección 4.6) |
| Sin datos personales | Lista blanca de columnas, supresión de celdas pequeñas y proveedores nombrados solo si son personas jurídicas |
| Divulgación | El equipo autoriza al ITM a divulgar el proyecto con crédito |

### 4.3 Marco legal

- **Ley 1712 de 2014 (transparencia).** La información de contratación pública es pública y su uso para control ciudadano es legítimo.
- **Ley 1581 de 2012 (datos personales).** Aunque SECOP II publique nombres y documentos de personas naturales, el proyecto no los reutiliza. Que un dato sea público no obliga a redistribuirlo, y las bases del concurso piden un estándar más estricto.
- **Personas jurídicas.** No son titulares de datos personales bajo la Ley 1581, por eso pueden nombrarse en el indicador de concentración. Queda sujeto a la respuesta de los organizadores (ver [`plan.md`](plan.md), pendientes).

### 4.4 Guía de lenguaje

Aplica a todo texto del proyecto: tablero, ficha, pitch, documentación y mensajes del código.

| Usar | Evitar |
|---|---|
| Patrón, señal, concentración, proporción | Corrupción, clientelismo, irregular, sospechoso |
| «Vale la pena revisar» | «Hay evidencia de» |
| «La Alcaldía firmó» | «El alcalde favoreció» |
| «Antes de la restricción» | «Para burlar la ley» |
| Cifras con su base («52 % de 1.390 contratos») | Porcentajes sueltos |

La motivación del proyecto (la veeduría frente al clientelismo) se explica en el pitch y en la ficha, pero el tablero no usa esa palabra. Los indicadores dan los elementos y el lector saca sus conclusiones.

### 4.5 Corrección y réplica

- El tablero muestra un correo de contacto para reportar errores, como texto que se pueda copiar.
- Las correcciones se registran en `CORRECCIONES.md`, en la raíz del repositorio, con fecha y motivo.
- Si la Alcaldía o una secretaría ofrece una explicación de un patrón, se publica junto al indicador.

### 4.6 Declaración de uso de IA

Texto base para `instrucciones.txt`, a completar con el detalle final:

> Se usó Claude (Anthropic) para investigar fuentes y metodología, validar la estructura de los conjuntos de datos, redactar la documentación de diseño y asistir en la escritura de código con Claude Code. Las decisiones de diseño, el análisis y los resultados fueron revisados por el equipo, que puede explicar cada parte de la solución.

### 4.7 Licencias

- **Código:** MIT.
- **Datos derivados y textos:** CC BY 4.0, compatible con la licencia de MEData (CC BY 4.0).
- **Pendiente:** verificar en los metadatos de datos.gov.co la licencia de cada conjunto de SECOP II antes de fijar la licencia de los datos derivados.

---

## 5. Siguientes etapas

### 5.1 Después de la final (noviembre y diciembre de 2026)

- Validar las cifras con calma, corregir lo necesario y habilitar la indexación del sitio.
- Activar la actualización semanal programada.
- Compartir el proyecto con veedurías ciudadanas, organizaciones de control social y medios locales que trabajan con datos.
- Extender la serie de planeación a 2024–2026 con los conjuntos de Plan Anual de Adquisiciones de SECOP II, ya que MEData se detuvo en 2023.

### 5.2 Antes de las elecciones locales (primer semestre de 2027)

- Pasar de reporte a monitoreo: una sección de seguimiento del ciclo 2027.
- Publicar la línea base antes de que empiece la restricción local, para comparar en tiempo real.

### 5.3 Ampliación del alcance

- **Instituciones universitarias y conglomerado:** analizar los 407 contratos interadministrativos de 2022–2023 y su relación con el volumen de contratación de esas instituciones.
- **Otros municipios:** el pipeline sirve para cualquier entidad que publique en SECOP II cambiando el filtro; un primer paso natural son los municipios del Valle de Aburrá.
- **Efecto de fin de gobierno:** explorar por qué 2019 planeó el 66 % de su contratación directa en enero.

### 5.4 Evolución técnica

- Publicar los indicadores en el estándar de datos de contratación abierta (OCDS) y como una API pública.
- Incorporar los indicadores extra (I6 e I7) con plazos legales calibrados por modalidad.