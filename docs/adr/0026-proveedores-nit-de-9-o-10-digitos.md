# 0026. Proveedores: solo NIT de 9 o 10 dígitos

- **Estado:** Aceptada
- **Fecha:** 2026-11-03
- **Fuente:** [docs/bitacora.md](../bitacora.md#3-nov-2026--nit-de-proveedores-con-menos-de-9-dígitos) (R14), ajusta el [ADR 0017](0017-proveedores-solo-nit-con-prefijo-8-o-9.md)

## Contexto

Al perfilar la copia de proveedores para normalizarla, 5 documentos (7 filas) tenían 7 u 8 dígitos. Un NIT de empresa tiene 9 dígitos, más uno de verificación; los de 7 u 8 son números de cédula. Al menos 3 de esos 5 traían el nombre de una persona natural en una copia versionada de un repositorio público (regla 1). Pasaban el filtro del ADR 0017 porque las cédulas también pueden empezar por 8 o 9.

## Decisión

- **La consulta `secop_contracts_suppliers` exige además `length(documento_proveedor) >= 9 AND length(documento_proveedor) <= 10`.** Quedan 4.459 filas (antes 4.466); las 7 que salen son exactamente las de 7 u 8 dígitos.
- **La prueba de privacidad exige los tres filtros** (NIT, prefijo y longitud) y rechaza filas de la copia cuyo documento no tenga 9 o 10 dígitos. El mensaje cita la fila, nunca el valor.
- La entrada de `secop_contracts_suppliers` en `manifest.json` se actualizó con la consulta nueva, el número de filas y la huella. El resto de la copia no cambió.

## Consecuencias

- Se pierde, a propósito, alguna empresa con NIT de 8 dígitos (2 filas); es preferible a publicar un nombre personal.
- Queda el riesgo residual del ADR 0017: una persona natural cuyo NIT tenga 9 dígitos y empiece por 8 o 9 pasa el filtro.
- Los commits anteriores de la rama principal conservan las 7 filas. Reescribir el historial queda como decisión aparte.

## Alternativas

- **Descartar los documentos en la normalización:** descartada. La copia versionada seguiría publicando los nombres.
- **Seguir con el filtro del ADR 0017:** descartada. Contradice la regla 1.
