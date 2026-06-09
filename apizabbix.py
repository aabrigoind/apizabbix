import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from dotenv import load_dotenv
import requests
import uvicorn

# Cargar las variables desde el archivo .env
load_dotenv()

GLPI_URL = os.getenv("GLPI_URL")
GLPI_USER_TOKEN = os.getenv("GLPI_USER_TOKEN")

app = FastAPI(title="Zabbix to GLPI Bridge")

class ZabbixAlert(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    event_id: Optional[str] = Field(default="0", alias="event_id")
    status: Optional[str] = Field(default="PROBLEM", alias="status")
    message: Optional[str] = Field(default="", alias="Message")
    severity: Optional[str] = Field(default="Average", alias="severity")
    subject: Optional[str] = Field(default="Alerta de Zabbix", alias="Subject")

def obtener_glpi_session():
    """Inicia sesión en GLPI usando el User-Token obtenido de Google SSO"""
    headers = {
        "Authorization": f"user_token {GLPI_USER_TOKEN}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(f"{GLPI_URL}/initSession", headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("session_token")
        else:
            print(f"[ERROR GLPI] Falla al validar User-Token. Código: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"[ERROR CRÍTICO GLPI] Conexión fallida al servidor Cloud: {e}")
        return None

def cerrar_glpi_session(session_token):
    headers = {"Session-Token": session_token, "Content-Type": "application/json"}
    requests.get(f"{GLPI_URL}/killSession", headers=headers, timeout=10)

def mapear_urgencia(severity: str) -> int:
    sev = severity.lower()
    if "disaster" in sev: return 5
    if "high" in sev: return 4
    if "average" in sev: return 3
    if "warning" in sev: return 2
    return 1

@app.post("/alertas")
async def recibir_alerta(alerta: ZabbixAlert):
    try:
        estado = alerta.status.upper() if alerta.status else "PROBLEM"
        urgencia_glpi = mapear_urgencia(alerta.severity)
        tipo_incidente = 2 if "hardware" in alerta.message.lower() or "ping" in alerta.message.lower() else 1

        if "PROBLEM" in estado or "1" in estado:
            print(f"\n[PROCESO] Generando ticket vía API Token para Evento: {alerta.event_id}")
            
            session_token = obtener_glpi_session()
            if not session_token:
                raise HTTPException(status_code=500, detail="Error de autenticación por Token con GLPI")
            
            ticket_payload = {
                "input": {
                    "name": f"[{alerta.severity.upper()}] {alerta.subject}",
                    "content": f"{alerta.message}<br><br><b>ID de Evento Zabbix:</b> {alerta.event_id}",
                    "urgency": urgencia_glpi,
                    "type": tipo_incidente,
                    "status": 1
                }
            }
            
            headers = {
                "Session-Token": session_token,
                "Content-Type": "application/json"
            }

            glpi_resp = requests.post(f"{GLPI_URL}/Ticket", json=ticket_payload, headers=headers, timeout=10)
            cerrar_glpi_session(session_token)
            
            if glpi_resp.status_code == 201:
                glpi_data = glpi_resp.json()
                print(f"[ÉXITO] ¡Ticket creado con Token de Usuario! ID: {glpi_data.get('id')}\n")
                return {"status": "success", "glpi_id": glpi_data.get("id")}
            else:
                print(f"[ERROR API GLPI] Código: {glpi_resp.status_code} - Detalle: {glpi_resp.text}")
                raise HTTPException(status_code=500, detail=f"GLPI rechazó el ticket.")
            
        elif "RESOLVED" in estado or "0" in estado:
            print(f"\n[PROCESO] Alerta resuelta: {alerta.event_id}.")
            return {"status": "success", "message": "Flujo de cierre simulado"}
            
        return {"status": "success", "message": "No se requirieron acciones"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falla: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)