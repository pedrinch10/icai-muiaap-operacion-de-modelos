# wine-quality

Proyecto reproducible con `uv` para entrenar un clasificador de calidad de vinos.

## Instalación

1. Clonar el fork y situarse en `semana2/wine-quality-project`.
2. Ejecutar:
uv sync --locked

   Esto instala Python 3.12 (gestionado automáticamente vía `.python-version`) y todas las dependencias con las versiones exactas fijadas en `uv.lock`, sin resolver versiones nuevas.

## Estructura

- `data/raw/WineQT.csv` — dataset original de calidad de vinos.
- `src/wine_quality/train.py` — carga el dataset, entrena un `ExtraTreesClassifier` y calcula el F1 macro de validación.
- `tests/test_train.py` — test que valida el pipeline completo de carga y entrenamiento.
- `pyproject.toml` / `uv.lock` — definición del paquete y bloqueo de dependencias.

## Comprobaciones

Con el entorno instalado (`uv sync --locked`), ejecutar desde `semana2/wine-quality-project`:

- Entrenamiento:
uv run --frozen python -m wine_quality.train

  Imprime número de filas, variables, clases y F1 macro de validación.

- Tests:
uv run --frozen pytest

- Estilo de código:
uv run --frozen ruff check .