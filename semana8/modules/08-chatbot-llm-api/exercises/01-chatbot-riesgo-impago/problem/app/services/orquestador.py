import json

from pydantic import ValidationError

from app.schemas.chat import ChatSalida, HerramientaUsada
from app.schemas.prestamo import PrestamoEntrada
from app.services.modelo import predecir

NOMBRE_TOOL = "calcular_riesgo_impago"
MAX_VUELTAS = 4

SISTEMA = (
    "Eres un asistente de riesgo de un banco. Cuando tengas todos los datos de una solicitud de "
    "prestamo, llama a la herramienta calcular_riesgo_impago. Si falta algun dato, pidelo. "
    "Nunca inventes valores. Responde en espanol y de forma breve."
)


def leer_argumentos(texto):
    """YA HECHO: convierte el texto JSON de la tool en dict ({} si no es JSON valido)."""
    try:
        datos = json.loads(texto)
    except (json.JSONDecodeError, TypeError):
        return {}
    if isinstance(datos, dict):
        return datos
    return {}


def definir_tool():
    return {
        "type": "function",
        "function": {
            "name": NOMBRE_TOOL,
            "description": (
                "Calcula la probabilidad de impago de una solicitud de prestamo "
                "y devuelve la decision: aprobar, revisar o rechazar."
            ),
            "parameters": PrestamoEntrada.model_json_schema(),
        },
    }


def ejecutar_tool(nombre, argumentos_json):
    if nombre != NOMBRE_TOOL:
        return {"ok": False, "error": "Tool desconocida: " + str(nombre)}

    datos = leer_argumentos(argumentos_json)
    try:
        entrada = PrestamoEntrada(**datos)
        resultado = predecir(entrada)
    except ValidationError as error:
        return {"ok": False, "error": str(error)}
    except Exception as error:
        return {"ok": False, "error": "Error inesperado: " + str(error)}

    return {"ok": True, **resultado.model_dump()}


def responder(mensajes, llm):
    conversacion = [{"role": "system", "content": SISTEMA}]
    for mensaje in mensajes:
        conversacion.append({"role": mensaje.role, "content": mensaje.content})

    herramientas = [definir_tool()]
    herramienta_usada = None

    for _ in range(MAX_VUELTAS):
        respuesta = llm.completar(conversacion, herramientas)
        llamadas = respuesta.get("tool_calls")

        if not llamadas:
            return ChatSalida(
                respuesta=respuesta.get("content") or "",
                herramienta=herramienta_usada,
            )

        conversacion.append(respuesta)
        for llamada in llamadas:
            nombre = llamada["function"]["name"]
            argumentos_json = llamada["function"]["arguments"]
            resultado = ejecutar_tool(nombre, argumentos_json)
            herramienta_usada = HerramientaUsada(
                nombre=nombre,
                argumentos=leer_argumentos(argumentos_json),
                resultado=resultado,
            )
            conversacion.append(
                {
                    "role": "tool",
                    "tool_call_id": llamada["id"],
                    "content": json.dumps(resultado),
                }
            )

    return ChatSalida(
        respuesta="No he podido completar la consulta. Revisa los datos e intentalo de nuevo.",
        herramienta=herramienta_usada,
    )