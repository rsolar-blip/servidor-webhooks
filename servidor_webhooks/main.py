from fastapi import FastAPI, Request, HTTPException
import json
import os
import base64
import requests


app = FastAPI()

# ----------------------------------------
# Seguridad: Token desde variables de entorno
# ----------------------------------------
SECRET_TOKEN = os.environ.get("WEBHOOK_TOKEN", "12345")

def validate_token(token: str):
    """Valida el token recibido como query param."""
    if token is None:
        raise HTTPException(status_code=400, detail="Token requerido")
    if token != SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Token inválido")


# ----------------------------------------
# Ruta raíz
# ----------------------------------------
@app.get("/")
def home():
    return {"status": "online", "message": "Servidor funcionando correctamente"}


# ----------------------------------------
# Webhook Telegram
# ----------------------------------------
@app.post("/telegram/webhook")
async def telegram_webhook(request: Request, token: str = None):
    validate_token(token)

    data = await request.json()
    print("📩 Telegram webhook recibido:")
    print(json.dumps(data, indent=4))

    return {"ok": True}


# ----------------------------------------
# Webhook Telnyx
# ----------------------------------------
@app.post("/telnyx/webhook")
async def telnyx_webhook(request: Request, token: str = None):
    validate_token(token)

    data = await request.json()
    print("📞 Telnyx webhook recibido:")
    print(json.dumps(data, indent=4))

    event_type = data["data"]["event_type"]

    if event_type == "call.answered":
        call_id = data["data"]["payload"]["call_control_id"]

        client_state_b64 = data["data"]["payload"].get("client_state", "")
        mensaje = base64.b64decode(client_state_b64).decode()

        print(f"🗣️ Mensaje a reproducir: {mensaje}")

        headers = {
            "Authorization": f"Bearer {os.environ.get('TELNYX_API_KEY')}",
            "Content-Type": "application/json"
        }

        # 🔥 1. ANSWER (aunque ya venga answered, lo reforzamos)
        r1 = requests.post(
            f"https://api.telnyx.com/v2/calls/{call_id}/actions/answer",
            headers=headers
        )
        print("ANSWER STATUS:", r1.status_code, r1.text)

        # 🔥 2. ESPERA MÁS TIEMPO (CLAVE)
        import time
        time.sleep(2)

        # 🔥 3. SPEAK
        r2 = requests.post(
            f"https://api.telnyx.com/v2/calls/{call_id}/actions/speak",
            json={
                "payload": mensaje,
                "voice": "Polly.Conchita",
                "language": "es-MX"
            },
            headers=headers
        )

        print("SPEAK STATUS:", r2.status_code)
        print("SPEAK RESPONSE:", r2.text)


# ----------------------------------------
# Webhook Commvault
# ----------------------------------------
@app.post("/commvault/webhook")
async def commvault_webhook(request: Request, token: str = None):
    validate_token(token)

    data = await request.json()
    print("💾 Commvault webhook recibido:")
    print(json.dumps(data, indent=4))

    return {"status": "success"}
