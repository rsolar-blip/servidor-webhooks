from fastapi import FastAPI, Request, HTTPException
import json
import os

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
