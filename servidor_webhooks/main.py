from fastapi import FastAPI, Request
import json

app = FastAPI()

# -----------------------------
# Ruta de prueba
# -----------------------------
@app.get("/")
def home():
    return {"status": "online", "message": "Servidor funcionando correctamente"}

# -----------------------------
# Webhook para Telegram
# -----------------------------
@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    print("📩 Telegram webhook recibido:")
    print(json.dumps(data, indent=4))
    return {"ok": True}

# -----------------------------
# Webhook para Telnyx
# -----------------------------
@app.post("/telnyx/webhook")
async def telnyx_webhook(request: Request):
    data = await request.json()
    print("📞 Telnyx webhook recibido:")
    print(json.dumps(data, indent=4))
    return {"received": True}

# -----------------------------
# Webhook para Commvault
# -----------------------------
@app.post("/commvault/webhook")
async def commvault_webhook(request: Request):
    data = await request.json()
    print("💾 Commvault webhook recibido:")
    print(json.dumps(data, indent=4))
    return {"status": "success"}
