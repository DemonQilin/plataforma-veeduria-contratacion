# Plan

Cronograma, prioridades, riesgos, mapa contra la rúbrica y entregables.

| Hito | Fecha |
|---|---|
| Cierre de inscripción | 4 nov 2026, 11:59 p. m. |
| Congelamiento interno | 8 nov 2026, 6:00 p. m. |
| Entrega interna | 9 nov 2026 |
| Entrega oficial | 10 nov 2026 |
| Publicación de finalistas | 11 nov 2026 |
| Pitch, final y premiación | 12 nov 2026 |

---

## 1. Equipo y supuestos

| Integrante | Papel |
|---|---|
| Juan (líder) | Desarrollo del pipeline y del tablero |
| Compañero | Ficha de hallazgos, pitch, prueba final de `instrucciones.txt` en su computador y apoyo de código en tareas acotadas |

- **Capacidad:** Juan, unas 6 horas al día (≈60 h hasta el 9 nov).
- **Entrega interna el lunes 9 de noviembre.** El plazo oficial es el martes 10; el día extra queda como margen.
- **Congelamiento el domingo 8 de noviembre a las 6:00 p. m.** Desde ese momento no se agregan funciones; solo se corrigen errores.

---

## 2. Cronograma

| Fecha | Juan | Compañero | Hito |
|---|---|---|---|
| Vie 30 oct | Enviar el correo a los organizadores (9:00 a. m.). Crear el repositorio, el proyecto con `uv` y la documentación | Reunir carnés vigentes. Leer `producto.md`, `indicadores.md` y la guía de lenguaje | **Inscripción del equipo** (ver sección 4) |
| Sáb 31 oct – Dom 1 nov | Extracción de SECOP II (Contratos, Procesos, Adiciones) y de la ejecución contractual de MEData, con lista blanca y copia con huella | Normalización del Plan Anual de Adquisiciones y catálogo de modalidades, con pruebas | Copia de datos sin información personal |
| Lun 2 nov | Consolidación y cruce (R3 a R8). Conciliación SECOP–MEData (R15) | Pruebas de privacidad: ninguna salida fuera de la lista blanca, ninguna celda menor a 5 | Contratos y procesos canónicos |
| Mar 3 nov | Indicadores I2 e I8 y cálculo del hallazgo | Revisar las cifras del hallazgo contra la metodología | **Punto de decisión 1:** ¿se mantiene el titular? |
| Mié 4 nov | Indicadores I1, I3, I4 e I5. Salidas para el tablero y contrato de tipos | Empezar el borrador de la ficha de hallazgos | Cierre de inscripciones a las 11:59 p. m. (ya debe estar hecha). Charla de términos, si es este día |
| Jue 5 – Vie 6 nov | Astro: estructura del sitio y pantallas 1 a 5 de la historia, con gráficos estáticos | Textos de la historia en lenguaje ciudadano (guía de lenguaje) | **Punto de decisión 2 (vie 6):** recortes del tablero |
| Sáb 7 nov | Explorador (pantalla 6), páginas por secretaría y pantallas 7 a 9 | Ficha de hallazgos con las cifras finales | Tablero completo |
| Dom 8 nov | GitHub Actions (pipeline, build y despliegue), `noindex`, etiquetas para compartir, `instrucciones.txt` | Revisión de la ficha y primera prueba de `instrucciones.txt` | **Congelamiento, 6:00 p. m.** |
| Lun 9 nov | Correcciones de la prueba | Prueba completa en su computador y en ventana privada | **Entrega interna** |
| Mar 10 nov | Margen. Ensayos del pitch | Guion del pitch y ensayos | Plazo oficial de entrega |
| Mié 11 nov | Resumen del pitch de una página, si son finalistas | Ensayo final | Publicación de finalistas |
| Jue 12 nov | Pitch | Pitch | Final y premiación |

### Estimación de horas de Juan

| Bloque | Horas |
|---|---:|
| Repositorio, `uv` e integración continua básica | 3 |
| Extracción de las cinco fuentes y copia con huella | 8 |
| Normalización y parser de la ejecución contractual de MEData | 6 |
| Consolidación, cruce y conciliación | 6 |
| Indicadores y hallazgo | 8 |
| Aprendizaje de Astro y estructura del sitio | 4 |
| Historia guiada (pantallas 1 a 5, 7 a 9) | 10 |
| Explorador y páginas por secretaría | 6 |
| Automatización, despliegue y etiquetas | 4 |
| `instrucciones.txt`, pruebas finales y correcciones | 5 |
| **Total** | **60** |

El plan no tiene holgura en horas: el margen está en el día de entrega y en los recortes de la sección 5.

---

## 3. Fecha de corte durante el concurso

Desde la entrega hasta la final, la publicación queda con una **fecha de corte fija**, la del congelamiento del 8 de noviembre. Si el flujo semanal actualizara los datos durante la evaluación, el tablero podría mostrar una cifra distinta a la de `guia_entrega.pdf`.

- El pipeline se puede ejecutar a demanda y la integración continua lo corre en cada push, lo que demuestra la automatización ante la rúbrica.
- La ejecución semanal programada se activa después del 12 de noviembre.

---

## 4. Inscripción: el 30 de octubre, no el 4 de noviembre

Según las bases, la fecha de la charla de términos llega al correo del líder después de inscribirse, y la charla es antes del 4 de noviembre. Inscribirse temprano asegura recibir esa fecha y poder llevar a la charla las preguntas que el correo no alcance a resolver. El formulario pide los datos de los integrantes, no el proyecto, así que no depende de la respuesta de los organizadores.

| Campo | Decisión | Por qué |
|---|---|---|
| Categoría | Interna | Ambos integrantes son estudiantes de Ingeniería del ITM |
| Modalidad | Visualización | El producto es para un público no técnico |
| Temática | Libre | Ninguna de las diez temáticas de ciudad cubre contratación o gobierno; la rúbrica es la misma para todas |

---

## 5. Prioridades y recortes

Si el tiempo no alcanza, se recorta de abajo hacia arriba.

| Prioridad | Qué incluye |
|---|---|
| **Imprescindible** | Pipeline con I1, I2 e I8. Pantallas 1 a 5, 7 y 9. `instrucciones.txt`. Ficha de hallazgos con propuesta de mejora |
| **Importante** | I3 e I5. Explorador. Automatización con GitHub Actions (10 puntos de la rúbrica) |
| **Deseable** | I4. Páginas por secretaría. Pantalla 8. Etiquetas para compartir |
| **Fuera** | I6 e I7 |

## 6. Puntos de decisión

| Fecha | Decisión | Si sale bien | Si sale mal |
|---|---|---|---|
| Mar 3 nov | ¿El hallazgo cumple el criterio de [`indicadores.md`](indicadores.md)? | Se mantiene como titular | El titular pasa al indicador más claro entre I3, I4 e I5, y la Ley de Garantías queda como contexto |
| Antes del 4 nov | ¿Qué respondieron los organizadores? | Se sigue el plan | Si no permiten nombrar personas jurídicas, I4 se reporta solo agregado. Si SECOP II no cuenta como fuente admitida, MEData pasa a ser la fuente principal del hallazgo |
| Vie 6 nov | ¿El tablero va al ritmo previsto? | Se completa todo lo importante | Se recorta lo deseable (sección 5) |

---

## 7. Riesgos y planes B

| Riesgo | Probabilidad | Impacto | Mitigación | Plan B |
|---|---|---|---|---|
| El hallazgo ejecutado no sobrevive a la limpieza | Media | Alto | Criterio explícito el 3 nov; la serie de planeación ya cumple su criterio con datos preliminares | El titular se apoya en la serie de planeación; si tampoco se sostiene, pasa a I3, I4 o I5 |
| Los organizadores no aceptan SECOP II como fuente o no permiten nombrar personas jurídicas | Baja | Alto | Correo del 30 oct y charla de términos | MEData como fuente principal (plan y ejecución); I4 solo agregado |
| La API de datos.gov.co o de MEData falla durante el desarrollo o la evaluación (MEData ya dio errores 504) | Alta | Alto | El repositorio incluye la copia de datos sin información personal y las salidas; el tablero no consulta APIs | El jurado prueba todo con `--from-snapshot`; la actualización desde las APIs queda como paso opcional |
| Las cifras del tablero cambian durante la evaluación y no coinciden con la ficha | Media | Alto | Fecha de corte fija hasta la final (sección 3) | Corregir la ficha antes de la entrega oficial |
| La curva de Astro consume tiempo del pipeline | Media | Medio | El tablero empieza el 5 nov, con los datos listos; aprendizaje acotado a 4 horas | Si al mediodía del 5 nov no hay avance, se hace una sola página estática sin islas y el explorador se simplifica |
| Falta de tiempo de Juan por otros compromisos | Media | Alto | Recortes por prioridad (sección 5) y congelamiento el 8 nov | Se entrega lo imprescindible |
| El compañero no está disponible en momentos clave | Baja | Alto | Plantillas de ficha y pitch listas desde el 4 nov; ambos ensayan el pitch | Juan asume la ficha; el pitch lo presentan los dos para no depender de uno |
| `instrucciones.txt` no funciona en otro computador (por ejemplo, Windows) | Media | Alto (requisito habilitante) | La integración continua ejecuta los comandos de `instrucciones.txt` en Linux y Windows; prueba en el computador del compañero el 8 y 9 nov | Dos caminos documentados (uv y pnpm, o mise) |
| Errores en las cifras por duplicados o valores atípicos | Media | Alto | Reglas de consolidación, conciliación entre tres fuentes y pruebas | Corregir antes del congelamiento y documentar el ajuste en `CORRECCIONES.md` |
| Lectura política del proyecto en un tema sensible | Media | Medio | Guía de lenguaje, neutralidad por calendario, tres administraciones en la serie y sitio no indexado durante el concurso | Canal de réplica y corrección |
| La licencia de los datos de SECOP II no permite la redistribución elegida | Baja | Bajo | Verificarla en los metadatos de datos.gov.co | Ajustar la licencia de los datos derivados |

---

## 8. Mapa contra la rúbrica

### 8.1 Requisitos habilitantes

Si uno falla, el proyecto no se califica.

| Requisito | Cómo se cumple | Responsable |
|---|---|---|
| Usa e integra al menos un conjunto de MEData | «Ejecución contractual histórico», cruzado con SECOP II (89 % de coincidencia) y usado para validar, asignar secretaría y medir adiciones; «Plan anual de adquisiciones histórico» para la serie de planeación | Juan |
| Solo fuentes admitidas y datos reales | MEData y datos.gov.co filtrado por Medellín. Pendiente confirmar SECOP II (pregunta 3 del correo) | Juan |
| Ficha de hallazgos con al menos una propuesta de mejora | Ver sección 8.4 | Compañero |
| Repositorio público que abre sin iniciar sesión | GitHub público; se prueba en ventana privada antes de entregar | Juan |
| Entrega en plazo y todos matriculados | Entrega el 9 nov (un día de margen); copia de ambos carnés | Ambos |
| Funciona siguiendo solo `instrucciones.txt` | Integración continua con los mismos comandos y prueba en el computador del compañero, sin ayuda | Compañero |

### 8.2 Rúbrica de 100 puntos

Cada criterio se califica por niveles (el peso equivale a 5 niveles por un multiplicador). Las bases no publican la descripción de cada nivel, así que se pidió en el correo (pregunta 5).

| Criterio | Puntos | Qué lo cubre | Evidencia para el jurado | Brecha y acción |
|---|---:|---|---|---|
| Uso de datos de MEData | 30 | Dos conjuntos integrados. El Plan Anual de Adquisiciones (2014–2023) sostiene el segundo nivel del hallazgo con tres ciclos presidenciales; la ejecución contractual valida SECOP II y aporta secretaría y adiciones | Pantalla del tablero sobre la planeación; conciliación entre plan, SECOP II y ejecución de MEData para enero de 2022; sección de fuentes en la ficha | Brecha mitigada: MEData pasó de apoyo a centro del análisis. Queda el límite de que ambos conjuntos se detienen en 2023 |
| Análisis de información | 20 | Años de control, tratamiento de la renovación de enero, criterio de decisión y limitaciones | Pantallas 4, 5 y 7; sección de método en la ficha | Que el hallazgo sobreviva al criterio del 3 de noviembre |
| Diseño y creatividad | 15 | Historia guiada, enfoque en celular, gráficos estáticos, páginas por secretaría | Recorrido del tablero en el pitch | Ninguna, si el tablero se termina a tiempo |
| Impacto potencial | 15 | Línea base para 2027 y método replicable | Pantalla 8 y cierre del pitch | Mostrar que, como SECOP II es nacional, el mismo pipeline sirve para cualquier entidad del país cambiando un filtro |
| Uso de otras fuentes | 10 | Tres conjuntos de SECOP II y el calendario de la Ley de Garantías con sus fuentes | Sección de fuentes | Ninguna |
| Automatización, IA o tecnologías | 10 | Pipeline automático con pruebas, integración continua en Linux y Windows, despliegue con GitHub Actions y uso declarado de IA | Repositorio, ejecuciones de GitHub Actions e `instrucciones.txt` | Ninguna |

### 8.3 Desempate

En caso de empate gana el mayor puntaje en uso de datos de MEData y, si persiste, en análisis de información. Los dos criterios que desempatan son los de mayor peso, así que la brecha de MEData es la prioridad número uno.

### 8.4 Propuestas de mejora para la ficha de hallazgos

Requisito habilitante. Propuestas basadas en lo que encontramos al trabajar con los datos:

1. **Para la Alcaldía de Medellín:** reanudar la publicación en MEData de «Ejecución contractual histórico» (detenida desde diciembre de 2023) y del «Plan anual de adquisiciones histórico» (detenido desde septiembre de 2023), y corregir la codificación y las filas truncadas. Sin esos conjuntos, la ciudadanía no puede comparar lo planeado con lo contratado de 2024 en adelante.
2. **Para la Alcaldía de Medellín:** publicar con anticipación su calendario de contratación en años con Ley de Garantías, para que la concentración de enero se pueda leer contra lo planeado.
3. **Para Colombia Compra Eficiente:** incluir el valor de cada adición en el conjunto «SECOP II – Adiciones», que hoy solo registra tipo y fecha.

La ficha incluirá las que sigan siendo válidas después del análisis final, con su cifra de respaldo.

---

## 9. Entregables

### 9.1 Lista de entrega

| Entregable | Contenido | Responsable | Fecha |
|---|---|---|---|
| Repositorio público | Código del pipeline y del tablero, copia de datos y salidas sin información personal, `instrucciones.txt` en la carpeta principal, `guia_entrega.pdf`, licencias, `CORRECCIONES.md`, README y `docs/` | Juan | 9 nov |
| Artefacto funcionando | Tablero publicado en GitHub Pages y pipeline reproducible desde el repositorio | Juan | 9 nov |
| `instrucciones.txt` | Plantilla oficial diligenciada (9.2) | Juan; prueba del compañero | 8–9 nov |
| `guia_entrega.pdf` | Guía de entrega de los organizadores diligenciada, con la ficha de hallazgos: pregunta, hallazgo principal con cifra, datos usados y al menos una propuesta de mejora | Compañero | Borrador 4 nov; final 8 nov |
| Datos o script | Script que descarga desde las fuentes (`--refresh`), más la copia de datos sin información personal | Juan | 9 nov |
| Carnés estudiantiles | Copia del carné vigente de ambos integrantes | Ambos | 30 oct |
| Resumen del pitch (solo finalistas) | Una página con el problema, los datos, el hallazgo y el aporte | Compañero, revisa Juan | 11 nov |

### 9.2 Borrador de `instrucciones.txt`

Sigue la plantilla oficial de las bases. La integración continua ejecuta los comandos de la opción A, así que cualquier cambio aquí debe reflejarse en los flujos de GitHub Actions.

```
INSTRUCCIONES - Veeduría de contratación de la Alcaldía de Medellín
Equipo: [nombre] · Hackathon de Datos 2026

1. QUÉ ES
Tablero ciudadano que muestra cómo la Alcaldía de Medellín concentra su
contratación directa alrededor de la Ley de Garantías, con indicadores
estándar de riesgo en compras públicas, a partir de SECOP II y MEData.

2. PROBARLO EN LÍNEA
[enlace de GitHub Pages]

3. ENTORNO
- Python [versión] (fijada en pipeline/.python-version), instalado por uv [versión]
- Node.js [versión] (fijada en web/.node-version) y pnpm [versión],
  solo para reconstruir el tablero
- Dependencias con versión:
  pipeline/pyproject.toml y pipeline/uv.lock
  (alternativa para pip: pipeline/requirements.txt)
  web/package.json y web/pnpm-lock.yaml

4. EJECUTARLO
Opción A (recomendada): requiere uv y Node.js
  cd pipeline
  uv sync
  uv run veeduria run --from-snapshot
  cd ../web
  npx --yes pnpm@[versión] install --frozen-lockfile
  npx --yes pnpm@[versión] build
  npx --yes pnpm@[versión] preview

Opción B (un solo instalador, versiones exactas): requiere mise
  mise trust
  mise install
  mise run pipeline
  mise run build
  mise run preview

Opcional, actualizar los datos desde las fuentes oficiales:
  cd pipeline
  uv run veeduria run --refresh

5. QUÉ DEBE VER
En la portada del tablero, la frase del hallazgo con su cifra:
"[frase final del hallazgo]".
En la pantalla 4, las barras de concentración por año, con 2022 y 2026
por encima de los años sin restricción.

6. DATOS Y FUENTES
- SECOP II Contratos Electrónicos · jbjy-vk9h · [enlace] · [licencia]
- SECOP II Procesos de Contratación · p6dx-8zbt · [enlace] · [licencia]
- SECOP II Adiciones · cb9c-h8sn · [enlace] · [licencia]
- MEData Ejecución contractual histórico · 1-028-12-000088 · [enlace] · CC BY 4.0
- MEData Plan anual de adquisiciones histórico · 1-028-11-000089 · [enlace] · CC BY 4.0
- Calendario de la Ley de Garantías: tabla propia con fuentes citadas
- Copia de los datos usados: data/snapshot/ (sin datos personales)
  Los archivos son CSV en UTF-8. Para abrirlos en Excel en Windows, use
  Datos > Desde texto/CSV; si se abren con doble clic, las tildes pueden
  verse mal.

7. USO DE IA
[texto de docs/producto.md, sección 4.6]

8. CONTACTO
[nombre y correo del líder]
```

### 9.3 Estructura del pitch (5 minutos)

Sigue la distribución de tiempos de las bases.

| Tramo | Tiempo | Contenido |
|---|---|---|
| Problema | 45 s | La contratación pública es pública, pero ilegible para un ciudadano. En un año electoral, ¿cómo saber si lo que hace la Alcaldía es normal? |
| Datos | 75 s | Tres fuentes cruzadas: SECOP II, la ejecución contractual y el Plan Anual de Adquisiciones de MEData. Coinciden en enero de 2022 (726, 723 y 727). Datos personales excluidos desde el origen |
| Demostración | 120 s | Recorrido por la historia: el patrón, la comparación con años sin elecciones, la respuesta a la objeción de la renovación de enero y el explorador por secretaría |
| Aporte | 60 s | Línea base para las elecciones locales de 2027, método replicable a cualquier entidad del país y propuestas de mejora para la Alcaldía |

Después del pitch el jurado ajusta el puntaje con la rúbrica y no suma puntos por oratoria, así que la demostración debe mostrar el artefacto funcionando, no diapositivas.

---

## 10. Pendientes

| Pendiente | Cómo se resuelve | Fecha |
|---|---|---|
| Respuesta de los organizadores a las cinco preguntas | Correo del 30 oct y charla de términos | Antes del 4 nov |
| Descripción de los niveles de la rúbrica | Pregunta 5 del correo | Antes del 4 nov |
| Plantilla oficial de `guia_entrega.pdf` | Solicitarla en la charla o por correo | Antes del 4 nov |
| Licencia de los conjuntos de SECOP II | Metadatos de datos.gov.co | 31 oct |
| Nombre exacto de la entidad en SECOP II Procesos | Consulta a la API antes de fijar el filtro | 31 oct |
| Token de aplicación de datos.gov.co | Crearlo y guardarlo como *secret* `SOCRATA_APP_TOKEN` en GitHub | 31 oct |
| Activar la ejecución semanal programada | Agregar el disparador `schedule` a `publish.yml` (ADR 0008) | Después del 12 nov |
| Fechas de la restricción de las locales de 2023 | Verificar con fuente oficial | Antes del 3 nov |
| Nombre del equipo | Decisión del equipo | 30 oct |