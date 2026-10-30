# 0008. Fecha de corte congelada durante el concurso

- **Estado:** Aceptada
- **Fecha:** 2026-10-30
- **Fuente:** [docs/plan.md](../plan.md#3-fecha-de-corte-durante-el-concurso)

## Contexto

SECOP II se actualiza a diario y recibe registros tardíos, así que las cifras de 2026 pueden moverse aunque el periodo analizado (enero a octubre) ya haya pasado. La fecha de corte sale de los datos (R12), así que cada actualización puede producir cifras ligeramente distintas.

Al mismo tiempo, `guia_entrega.pdf` declara el hallazgo con una cifra concreta, y el jurado abre el tablero entre la entrega (10 nov) y la final (12 nov). Si el flujo semanal actualiza los datos en ese intervalo, el jurado puede leer «52 %» en la ficha y «51,8 %» en el sitio.

La rúbrica da 10 puntos por automatización, así que el pipeline debe seguir mostrando que funciona solo.

## Decisión

- **Hasta el 12 nov 2026, la copia de datos y las salidas publicadas son las del congelamiento** del 8 nov a las 6:00 p. m. La fecha de corte es la que resulta de esa copia.
- **`publish.yml` se ejecuta solo a demanda** (`workflow_dispatch`) durante el concurso. El disparador `schedule` semanal se agrega en un commit después de la final.
- **La integración continua corre `--from-snapshot` en cada push**, con las pruebas y el build. Eso demuestra la automatización y la reproducibilidad sin mover las cifras.
- **La ficha, el tablero e `instrucciones.txt` citan la misma fecha de corte.**
- **Si después del congelamiento aparece un error en los datos,** se corrige con una actualización documentada en `CORRECCIONES.md` y se ajusta la ficha antes de la entrega oficial del 10 nov. Después de la entrega no se cambian los datos publicados hasta la final.

## Consecuencias

- El jurado ve en el sitio exactamente las cifras de la ficha.
- Durante la evaluación, el tablero muestra datos al 8 nov. No afecta el análisis, que mide enero a octubre, pero el sitio debe decir con claridad que la fecha de corte es deliberada.
- La automatización se evalúa por el historial de ejecuciones de GitHub Actions y por la ejecución a demanda, no por actualizaciones en vivo.
- Después de la final hay que activar la ejecución semanal; queda como tarea en [`plan.md`](../plan.md) y en las siguientes etapas de [`producto.md`](../producto.md#51-después-de-la-final-noviembre-y-diciembre-de-2026).

## Alternativas

| Criterio | Corte congelado con automatización a demanda (elegida) | Actualización semanal desde ya | Corte congelado sin automatización |
|---|---|---|---|
| Ficha y sitio coinciden | Sí | No necesariamente | Sí |
| Evidencia de automatización | Historial de ejecuciones y ejecución a demanda | Actualizaciones en vivo | Ninguna |
| Riesgo durante la evaluación | Bajo | Cifras distintas o una ejecución fallida en pleno concurso | Pierde puntos de la rúbrica |

- **Actualización semanal desde ya:** descartada. Muestra mejor la automatización, pero arriesga que las cifras dejen de coincidir con la ficha o que una ejecución fallida coincida con la evaluación.
- **Congelar sin automatización:** descartada porque renuncia a parte de los 10 puntos de automatización.
- **Ficha sin cifras fijas («las cifras pueden variar»):** descartada porque las bases piden declarar el hallazgo principal con cifra.