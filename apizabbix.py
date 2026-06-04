# ==============================================================================
#                  BRIDGE DE ALERTAS: ZABBIX TO GLPI
# ==============================================================================
# Este script actúa como un middleware (intermediario) HTTP asíncrono.
# Su función es recibir peticiones POST con payloads en formato JSON enviados
# por el motor de Webhooks de Zabbix, validar su estructura mediante Pydantic,
# y segmentar el flujo según el estado del evento (Apertura o Cierre de tickets).
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. IMPORTACIÓN DE MÓDULOS Y LIBRERÍAS
# ------------------------------------------------------------------------------
# FastAPI: Framework web de alto rendimiento para construir APIs REST bajo el estándar ASGI.
# HTTPException: Clase de excepción para retornar códigos de estado HTTP de error (ej: 400, 500).
from fastapi import FastAPI, HTTPException

# BaseModel: Clase base de Pydantic para el análisis, tipado y validación de esquemas JSON.
# Field: Permite añadir metadatos, valores por defecto y alias a los atributos del modelo.
from pydantic import BaseModel, Field

# Optional: Módulo de tipado estático para definir que un campo puede aceptar un tipo de dato o ser None.
from typing import Optional

# uvicorn: Servidor web de producción ASGI que procesa la comunicación a nivel de red (sockets TCP/IP).
import uvicorn


# ------------------------------------------------------------------------------
# 2. INICIALIZACIÓN DE LA APLICACIÓN
# ------------------------------------------------------------------------------
# Instanciamos el objeto principal de la API. "app" será el encargado de orquestar
# las rutas web, los middlewares de seguridad y el ciclo de vida del servidor.
app = FastAPI(title="Zabbix to GLPI Bridge")


# ------------------------------------------------------------------------------
# 3. DEFINICIÓN DEL MODELO DE DATOS (CONTRATO DE ENTRADA)
# ------------------------------------------------------------------------------
# Definimos la clase 'ZabbixAlert' que hereda de 'BaseModel'. Esto obliga a que 
# cualquier petición entrante cumpla estrictamente con esta estructura de datos.
class ZabbixAlert(BaseModel):
    
    # event_id: Almacena el identificador único del evento ({EVENT.ID} de Zabbix).
    # Se define como opcional con valor por defecto "0" para evitar que falle si se hace un test vacío.
    event_id: Optional[str] = Field(default="0", alias="event_id")
    
    # status: Almacena el estado de la alerta ({EVENT.STATUS} de Zabbix), el cual de forma nativa
    # devuelve los strings rígidos "PROBLEM" o "RESOLVED".
    status: Optional[str] = Field(default="PROBLEM", alias="status")
    
    # message: Almacena el cuerpo completo del mensaje generado por Zabbix ({ALERT.MESSAGE}).
    # Nota técnica: Usamos el parámetro 'alias="Message"' para que Pydantic sea tolerante
    # y acepte el campo tanto si viene en minúscula desde producción o con M mayúscula desde el botón Test.
    message: Optional[str] = Field(default="", alias="Message") 

    # Configuración interna del modelo de validación
    class Config:
        # populate_by_name = True: Habilita a Pydantic a mapear el JSON utilizando 
        # indistintamente el nombre de la variable (message) o su alias (Message).
        populate_by_name = True


# ------------------------------------------------------------------------------
# 4. CONTROLADOR DE LA RUTA (ENDPOINT HTTP POST)
# ------------------------------------------------------------------------------
# El decorador '@app.post' configura al servidor para escuchar peticiones de escritura.
# Dirección URL final de escucha: http://<IP_DEL_SERVIDOR>:8000/alertas
@app.post("/alertas")
async def recibir_alerta(alerta: ZabbixAlert):
    """
    Función controladora asíncrona (corrutina). Recibe el objeto 'alerta' ya 
    validado y parseado por Pydantic bajo el molde de la clase ZabbixAlert.
    """
    try:
        # .upper() normaliza el string a mayúsculas para evitar fallas por sensibilidad de caracteres.
        # Si por algún motivo viene nulo, por defecto se asume "PROBLEM" para no perder la alerta.
        estado = alerta.status.upper() if alerta.status else "PROBLEM"
        
        # ----------------------------------------------------------------------
        # FLUJO A: DETECCIÓN DE INCIDENTE NUEVO (CREAR TICKET)
        # ----------------------------------------------------------------------
        # Si el estado mapeado contiene la palabra "PROBLEM" o el código numérico "1",
        # significa que Zabbix detectó un fallo activo en la infraestructura.
        if "PROBLEM" in estado or "1" in estado:
            print(f"\n[ACCION: CREAR TICKET] ──> Evento ID asignado por Zabbix: {alerta.event_id}")
            print("--- Cuerpo del Requerimiento Recibido (Formato HTML) ---")
            print(alerta.message)
            print("--------------------------------------------------------\n")
            
            # TODO (Fase GLPI): 
            # 1. Ejecutar autenticación contra la REST API de GLPI para obtener el session_token.
            # 2. Mapear criticidad (severity) y parsear la categoría (Hardware/Software).
            # 3. Ejecutar petición HTTP POST hacia el endpoint /Ticket de GLPI inyectando 'alerta.message'.
            # 4. Destruir/Cerrar la sesión de GLPI para liberar memoria.
            
        # ----------------------------------------------------------------------
        # FLUJO B: DETECCIÓN DE RECUPERACIÓN (CERRAR TICKET)
        # ----------------------------------------------------------------------
        # Si el estado contiene "RESOLVED" o el código numérico "0", significa que
        # el trigger en Zabbix volvió a su estado normal y el servicio se recuperó.
        elif "RESOLVED" in estado or "0" in estado:
            print(f"\n[ACCION: CERRAR TICKET] ──> Buscando Ticket vinculado al Evento ID: {alerta.event_id}")
            print("--- Datos de Cierre e Historial de Recuperación ---")
            print(alerta.message)
            print("---------------------------------------------------\n")
            
            # TODO (Fase GLPI):
            # 1. Iniciar sesión en la API de GLPI.
            # 2.