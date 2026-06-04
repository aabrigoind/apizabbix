from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
import uvicorn

# Inicialización de la API FastAPI
app = FastAPI(title="Zabbix to GLPI Bridge")

# Definición del modelo de validación de datos
class ZabbixAlert(BaseModel):
    # ConfigDict permite mapear tanto minúsculas como mayúsculas (Message/message)
    model_config = ConfigDict(populate_by_name=True)
    
    event_id: Optional[str] = Field(default="0", alias="event_id")
    status: Optional[str] = Field(default="PROBLEM", alias="status")
    message: Optional[str] = Field(default="", alias="Message") 

# Endpoint que recibe las alertas de Zabbix
@app.post("/alertas")
async def recibir_alerta(alerta: ZabbixAlert):
    try:
        # Normalizamos el estado a mayúsculas
        estado = alerta.status.upper() if alerta.status else "PROBLEM"
        
        # FLUJO A: Alerta de Problema activo
        if "PROBLEM" in estado or "1" in estado:
            print(f"\n[ACCION: CREAR TICKET] ──> Evento ID: {alerta.event_id}")
            print("--- Cuerpo del Requerimiento Recibido (HTML) ---")
            print(alerta.message)
            print("--------------------------------------------------------\n")
            
        # FLUJO B: Alerta de Recuperación (OK)
        elif "RESOLVED" in estado or "0" in estado:
            print(f"\n[ACCION: CERRAR TICKET] ──> Vinculado al Evento ID: {alerta.event_id}")
            print("--- Datos de Cierre e Historial de Recuperación ---")
            print(alerta.message)
            print("---------------------------------------------------\n")
            
        else:
            print(f"\n[AVISO] Estado indeterminado: '{alerta.status}' en Evento ID: {alerta.event_id}\n")
            
        return {"status": "success", "message": f"Evento {alerta.event_id} procesado exitosamente"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falla critica: {str(e)}")

if __name__ == "__main__":
    # Arrancamos Uvicorn pasando la instancia de la app directamente
    uvicorn.run(app, host="0.0.0.0", port=8000)