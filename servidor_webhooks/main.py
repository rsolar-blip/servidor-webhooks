from fastapi import FastAPI, Request, HTTPException
import json
import os
import base64

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

    try:
        event_type = data["data"]["event_type"]
        print("👉 EVENT TYPE:", event_type)

        if event_type == "call.answered":
            call_id = data["data"]["payload"]["call_control_id"]

            encoded = data["data"]["payload"].get("client_state")

            mensaje = "Mensaje por defecto"
            if encoded:
                try:
                    mensaje = base64.b64decode(encoded).decode("utf-8")
                except Exception as e:
                    print("Error decodificando client_state:", e)



            import requests

            url = f"https://api.telnyx.com/v2/calls/{call_id}/actions/speak"

            payload = {
                "payload": mensaje,
                "voice": "female",
                "language": "es-MX"
            }

            headers = {
                "Authorization": f"Bearer {os.environ.get('TELNYX_API_KEY')}",
                "Content-Type": "application/json"
            }

            r = requests.post(url, json=payload, headers=headers)

            print("🗣️ Respuesta speak:", r.status_code, r.text)

    except Exception as e:
        print("❌ Error:", e)

    return {"received": True}


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
