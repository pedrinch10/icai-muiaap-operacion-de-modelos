# Semana 9 — Observaciones de 9.1 y nota de compatibilidad de 9.2

**BORRADOR ASISTIDO (redactado y ejecutado por Claude), pendiente de revisión
de Pedro.** Las observaciones M1–M4 son resultados de ejecuciones hechas por el
asistente sobre las demos de 9.1; no son observaciones personales de Pedro
hasta que él las repita y las valide. Pedro debe leerlas, entenderlas y poder
explicarlas.

Uso de IA: no se encontró ninguna norma, ni a favor ni en contra, en el README,
`AGENTS.md`, los PDF 9.1/9.2 ni los README de semana 9. Esa ausencia no es una
autorización docente; conviene confirmarlo con el docente. Las prácticas son
individuales.

## Pruebas: qué está comprobado y por quién

| Entorno | Resultado | Estado |
| --- | --- | --- |
| Nube auxiliar (Claude; no es el lock exacto: pydantic 2.13.5, Ruff 0.16.9) | módulo 9.1: 10 passed; starter 9.2: 33 passed; Ruff verde | ejecutado por el asistente; M1–M4 salen de aquí |
| Linux externo, lock exacto (Python 3.13.18, pydantic 2.14.1, Ruff 0.17.1) | módulo 9.1: 10 passed; starter: 33 passed; `ruff check` y `ruff format --check` verdes; `fastapi dev` y `/docs` abiertos; repetido tras los ejemplos de error del commit `c4d9b37` | verificado por una revisión externa; resultado comunicado, sin salida adjunta aquí |
| Windows (Python 3.12.14, pydantic 2.14.1, Ruff 0.17.1) | `uv sync --locked` correcto; starter: 33 passed; `ruff check` OK; `ruff format --check`: 18 archivos ya formateados | salida pegada por Pedro en el chat; no está guardada en ningún archivo |
| Windows, módulo 9.1 | 10 passed | solo reportado por Pedro, sin salida pegada |

## 9.1 — Observaciones M1–M4

Se ejecutaron las demos de `examples/` con `uvicorn` y `curl`. Pedro puede
repetirlas con `uv run fastapi dev examples/<demo>.py`.

**M1 — Campos internos.** Solo `/leaky` devuelve `raw_score` y
`threshold_config`. `/filtered` no los devuelve porque `response_model` filtra lo
que el modelo de respuesta no declara. El modelo `PublicScore` en `/docs` sí
incluye `is_reliable`.

**M2 — Respuestas reales de la demo de errores.**

| Petición | Status | `error.code` | `fields` |
| --- | --- | --- | --- |
| `{"age":30,"income":1000}` | 200 | (no es error) | — |
| `{"age":"treinta",...}` | 422 | `validation_error` | `age` |
| `{"age":30}` | 422 | `validation_error` | `income` |
| `GET /v1/nada` | 404 | `not_found` | — |
| `GET /v1/boom` | 500 | `internal_error` | — |

Son 5 peticiones: **4 errores y 1 respuesta válida** (el primer cuerpo es
correcto). El PDF habla de «cinco respuestas de error»; la discrepancia no está
resuelta y conviene preguntarla al docente. Sin el manejador de validación,
FastAPI responde con un objeto cuyo campo `detail` contiene errores con las
claves `type`, `loc`, `msg` e `input` (estructura orientativa, no una respuesta
literal), y ese `input` devuelve el dato del usuario. Ninguna respuesta contiene `TU_SECRETO`.

**M3 — Documentación en OpenAPI.** `summary` va al campo `summary` de la operación;
el docstring va a `description`; `response_description` va a
`responses.200.description`;
`responses` declara 422 y 503 con `ErrorResponse`. Observación importante: la
documentación dice `ErrorResponse`, pero el 422 real de esa demo devuelve
`{"detail": ...}` porque no tiene manejador, así que el OpenAPI «miente». Un
tercer ejemplo (`no_income`) se probó en una copia temporal y se deshizo, porque
el test que cuenta ejemplos exige exactamente `valid` y `minor`.

**M4 — `raise_server_exceptions=False`.** Con `TestClient`, una excepción no
controlada se relanza dentro del test salvo que se pase
`raise_server_exceptions=False`. Al quitarlo en una copia temporal, el
`RuntimeError` de `/v1/boom` se propaga y `test_unexpected_error_hides_secrets`
falla, porque el test ya no llega a ver el 500 con su cuerpo. Con el parámetro,
el 500 llega como respuesta y se puede comprobar que no filtra el secreto. Se
añadió además `test_zero_income_is_rejected_with_the_field_name`: `income: 0` da
422 con `fields[0].field == "income"`. Los cambios temporales de M2–M4 no quedan
en los archivos.

## 9.2 — Nota de compatibilidad (borrador)

Compatible: añadir `served_at` a la respuesta (un cliente de S7 ignora campos
que no conoce), redondear `confidence` a dos decimales y no exponer `raw_score`
(no forma parte del contrato de S7). Documentar con OpenAPI no cambia el
comportamiento. Podría romper a clientes que ya parseaban `{"detail": ...}`,
porque ahora los errores usan el sobre `error` con `request_id`, y a quien
esperase 422 para un JSON mal formado, porque ahora devuelve 400. Para S7 es lo
prometido; para un cliente de S8 es un cambio visible y debe anunciarse.
Versionado: `1.1.0` (menor, por el campo nuevo). Quitar o renombrar campos,
cambiar un `error.code` o un status sería mayor (`2.0.0` o `/v2`).

## Captura de `/docs`

`docs_api_1_1_linux.png`: captura de `/docs` con la API 1.1.0, tomada en
**Linux** en la revisión externa (no en Windows), con `uv sync --locked`,
Python 3.13.18, pydantic 2.14.1 y Ruff 0.17.1, y `fastapi dev` arrancado sobre
el mismo código del commit `c4d9b37`. Es la captura final, posterior a los
ejemplos de error explícitos; no se reutiliza la captura anterior. Muestra 400 `invalid_json` sin
`fields`, 422 `validation_error` con `features.alcohol` y 503
`model_unavailable` sin `fields`. No hay captura de Windows guardada.
