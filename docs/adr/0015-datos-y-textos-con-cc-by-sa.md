# 0015. Datos y textos con CC BY-SA 4.0

- **Estado:** Aceptada
- **Fecha:** 2026-10-30
- **Fuente:** [docs/producto.md](../producto.md#47-licencias)

## Contexto

`producto.md` suponía CC BY 4.0 para los datos derivados y los textos, y dejaba pendiente verificar la licencia de SECOP II. Los metadatos de datos.gov.co (consultados el 30 oct 2026) indican que `jbjy-vk9h`, `p6dx-8zbt` y `cb9c-h8sn` son CC BY-SA 4.0. MEData es CC BY 4.0.

CC BY-SA exige que lo que se redistribuye a partir de la obra lleve la misma licencia o una compatible. `data/snapshot/` es una copia de filas de SECOP II con menos columnas, es decir, una redistribución. Las salidas y los textos son agregados; si cuentan como obra adaptada depende de la jurisdicción.

## Decisión

- **`data/` (copia, salidas y esquemas) y los textos del tablero y de `docs/` van con CC BY-SA 4.0.** El archivo `LICENSE-DATA` en la raíz lo declara y enlaza el texto legal oficial.
- **El código sigue con MIT** (`LICENSE`): los datos y el código tienen licencias separadas.
- **El tablero, `instrucciones.txt` y la ficha citan la licencia de cada fuente** junto con su enlace.

## Consecuencias

- Se cumple la licencia de SECOP II sin depender de interpretar si un agregado es una adaptación.
- La combinación con MEData (CC BY) es válida: el resultado puede ir bajo CC BY-SA.
- Quien reutilice los datos debe mantener CC BY-SA 4.0. No hay forma de ofrecerlos con una licencia más permisiva.
- `LICENSE-DATA` referencia el texto legal en lugar de copiarlo.
- La interpretación es del equipo, no asesoría legal. Si los organizadores o un abogado indican otra cosa, este ADR se reemplaza.

## Alternativas

- **CC BY 4.0 para todo lo derivado:** descartada. Puede incumplir la cláusula CompartirIgual de SECOP II, y la copia de `data/snapshot/` es una redistribución directa.
- **CC BY-SA solo para la copia y CC BY para salidas y textos:** descartada. Obliga a explicar dos regímenes, y la diferencia depende de una interpretación jurídica incierta.
- **No licenciar los datos derivados:** descartada. Las bases piden un repositorio con licencia abierta.
