import joblib

from app.config import MODEL_PATH
from app.schemas.prestamo import PrediccionSalida, PrestamoEntrada

# Orden en el que el modelo espera las variables
VARIABLES = [
    "edad",
    "ingresos_mensuales",
    "importe_prestamo",
    "plazo_meses",
    "antiguedad_laboral_anios",
    "impagos_previos",
]

# Se carga una sola vez, al importar el modulo
modelo = joblib.load(MODEL_PATH)


def decidir(probabilidad: float) -> str:
    """Menor de 0,2 -> aprobar; menor de 0,5 -> revisar; resto -> rechazar."""
    if probabilidad < 0.2:
        return "aprobar"
    if probabilidad < 0.5:
        return "revisar"
    return "rechazar"


def predecir(entrada: PrestamoEntrada) -> PrediccionSalida:
    # Los 6 valores, en el orden exacto de VARIABLES
    valores = [getattr(entrada, nombre) for nombre in VARIABLES]
    # Fila 0, columna 1: probabilidad de la clase de impago
    probabilidad = float(modelo.predict_proba([valores])[0][1])
    return PrediccionSalida(
        probabilidad_impago=probabilidad,
        decision=decidir(probabilidad),
    )
