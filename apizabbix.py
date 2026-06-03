from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Zabbix to GLPI Bridge")

# Definimos la estructura de los datos que Zabbix nos va a enviar
class ZabbixAlert(BaseModel):
    host: str
    severity: str
    trigger_name: str
    ip: str
    status: str  # Por ejemplo: PROBLEM o RESOLVED

@app.post("/alertas")
async def recibir_alerta(alerta: ZabbixAlert):
    """
    Este endpoint se queda escuchando en http://IP:8000/alertas
    Zabbix enviará un POST aquí cuando ocurra un evento.
    """
    try:
        print("\n=== Nueva Alerta Recibida de Zabbix ===")
        print(f"Host afectado: {alerta.host} ({alerta.ip})")
        print(f"Gravedad: {alerta.severity}")
        print(f"Problema: {alerta.trigger_name}")
        print(f"Estado: {alerta.status}")
        print("=======================================\n")
        
        # TODO: Aquí irá la lógica para conectar con GLPI en el paso 2
        
        return {"status": "success", "message": "Alerta recibida correctamente"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Arranca el servidor en el puerto 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)