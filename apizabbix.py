from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Zabbix to GLPI Bridge")

# Esquema de validación para los parámetros HTTP POST enviados por Zabbix
class ZabbixAlert(BaseModel):
    event_id: str      # Captura la macro {EVENT.ID}
    status: str        # Captura la macro {EVENT.STATUS} (PROBLEM o RESOLVED)
    message: str       # Captura la macro {ALERT.MESSAGE} (Bloque HTML)

@app.post("/alertas")
async def recibir_alerta(alerta: ZabbixAlert):
    try:
        # Evaluación del estado del evento para determinar la acción en la mesa de ayuda
        if alerta.status == "PROBLEM":
            print(f"\n[ACCION: CREAR TICKET] ──> Evento ID: {alerta.event_id}")
            print("--- Cuerpo del Requerimiento (HTML) ---")
            print(alerta.message)
            print("---------------------------------------\n")
            
            # TODO: Fase 2 - Inyectar lógica de inicialización de sesión y POST a GLPI (glpi_create_ticket)
            
        elif alerta.status == "RESOLVED":
            print(f"\n[ACCION: CERRAR TICKET] ──> Vinculado al Evento ID: {alerta.event_id}")
            print("--- Datos de Cierre y Recuperación ---")
            print(alerta.message)
            print("--------------------------------------\n")
            
            # TODO: Fase 2 - Inyectar lógica de búsqueda por ID y PUT a GLPI (glpi_close_ticket)
        
        else:
            # Manejo de contingencia si Zabbix envía un estado desconocido (ej. ACKNOWLEDGE)
            print(f"\n[AVISO] Estado no mapeado recibido: {alerta.status} para Evento ID: {alerta.event_id}\n")
            
        return {"status": "success", "message": f"Evento {alerta.event_id} procesado en el bridge"}
        
    except Exception as e:
        # En caso de falla interna, se genera una respuesta HTTP 500 (Internal Server Error)
        raise HTTPException(status_code=500, detail=f"Error interno en el bridge: {str(e)}")

if __name__ == "__main__":
    # Inicializa el servidor ASGI Uvicorn apuntando a este archivo específico (apizabbix)
    uvicorn.run("apizabbix:app", host="0.0.0.0", port=8000, reload=False)