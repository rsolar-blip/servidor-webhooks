import os
import json
import base64
import asyncio
import requests
import gspread
from fastapi import FastAPI, Request, HTTPException, Header
from oauth2client.service_account import ServiceAccountCredentials
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

# --- CONFIGURACIÓN DE GOOGLE SHEETS DESDE ENTORNO ---
# TIP: Para no subir el archivo JSON físico a Render por seguridad, 
# puedes guardar la ruta en una variable de entorno de Render, o leer el JSON directo de una variable.
CREDENTIALS_FILE = os.environ.get("GOOGLE_SHEETS_JSON_PATH", r"D:\Python\JS\twilio-guardias-3cb6ae8b259c.json")
NOMBRE_HOJA_CALCULO = "guardias"
PESTANA_CONTROL = "control_alertas"

def validate_token(token: str):
    """Valida el token recibido como query param."""
    if token is None:
        raise HTTPException(status_code=400, detail="Token requerido")
    if token != SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Token inválido")

def actualizar_estado_en_sheets(hash_id: str, nuevo_estado: str):
    """Lee el JSON desde las variables de entorno y actualiza la hoja de cálculo."""
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # 1. Recuperamos el texto completo del JSON desde la variable de entorno de Render
        json_texto = os.environ.get("GOOGLE_SHEETS_JSON_DATA")
        
        if not json_texto:
            print("❌ [Sheets Error] La variable GOOGLE_SHEETS_JSON_DATA está vacía.")
            return False
            
        # 2. Convertimos el texto string a un diccionario de Python
        info_credenciales = json.loads(json_texto)
        
        # 3. Nos autenticamos usando el diccionario cargado en memoria (from_json_keyfile_dict)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info_credenciales, scope)
        client = gspread.authorize(creds)
        hoja = client.open(NOMBRE_HOJA_CALCULO).worksheet(PESTANA_CONTROL)
        
        # 4. Buscamos el hash_id en la columna A y actualizamos la columna B
        celda = hoja.find(hash_id)
        if celda:
            hoja.update_cell(celda.row, 2, nuevo_estado)
            print(f"🟩 [Sheets] Alerta {hash_id} actualizada a {nuevo_estado} con éxito.")
            return True
        else:
            print(f"🟨 [Sheets] No se encontró el hash_id {hash_id} en la hoja.")
    except Exception as e:
        print(f"❌ [Sheets Error] No se pudo actualizar el estado: {e}")
    return False
# ----------------------------------------
# Ruta raíz
# ----------------------------------------
@app.get("/")
def home():
    return {"status": "online", "message": "Servidor funcionando correctamente"}

# ----------------------------------------
# WEBHOOK NUEVO: Twilio Confirmación de Llamadas
# ----------------------------------------
@app.post("/twilio/webhook")
async def twilio_webhook(request: Request, token: str = None):
    validate_token(token)
    
    form_data = await request.form()
    params = request.query_params
    hash_id = params.get("hash_id")
    digit_pressed = form_data.get("Digits")
    
    print(f"☎️ Webhook Twilio: Hash={hash_id} | Dígito Presionado={digit_pressed}")
    
    if digit_pressed == "1":
        if hash_id:
            # Ejecutamos la actualización de Google Sheets de manera asíncrona en segundo plano
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, actualizar_estado_en_sheets, hash_id, "CONFIRMADO")
            
        twiml_response = """<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="Polly.Mia" language="es-MX">Alerta confirmada correctamente. Muchas gracias. Adiós.</Say>
            <Hangup/>
        </Response>"""
    else:
        twiml_response = """<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="Polly.Mia" language="es-MX">Opción no válida o tiempo agotado. Escalando alerta.</Say>
            <Hangup/>
        </Response>"""
        
    from fastapi.responses import Response
    return Response(content=twiml_response, media_type="application/xml")

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
    # print(json.dumps(data, indent=4)) # Puedes comentar esto para limpiar logs

    event_type = data["data"]["event_type"]

    if event_type == "call.answered":
        # Extraemos datos necesarios
        payload = data["data"]["payload"]
        call_id = payload["call_control_id"]
        client_state_b64 = payload.get("client_state", "")
        
        # 1. Decodificación limpia (UTF-8)
        try:
            mensaje_raw = base64.b64decode(client_state_b64).decode('utf-8')
            # Limpiamos caracteres que rompen el ritmo del audio
            mensaje = mensaje_raw.replace("|", ". ").replace("[", "").replace("]", ". ")
        except:
            mensaje = "Alerta de monitoreo."

        print(f"🗣️ Mensaje a reproducir: {mensaje}")

        headers = {
            "Authorization": f"Bearer {os.environ.get('TELNYX_API_KEY')}",
            "Content-Type": "application/json"
        }

        # 2. PAUSA ASÍNCRONA (Clave para evitar el silencio inicial)
        import asyncio
        await asyncio.sleep(1.0) 

        # 3. COMANDO SPEAK (Sin pasar por 'answer')
        # Agregamos comas iniciales para dar tiempo al usuario de escuchar
        r2 = requests.post(
            f"https://api.telnyx.com/v2/calls/{call_id}/actions/speak",
            json={
                "payload": f", , , Atención. . . {mensaje}",
                "voice": "female",
                "language": "es-MX",
                "voice_engine": "google" # Más rápido que Polly para alertas
            },
            headers=headers
        )

        print("SPEAK STATUS:", r2.status_code)
        print("SPEAK RESPONSE:", r2.text)

    return {"status": "success"}


# ----------------------------------------
# Webhook Commvault
# ----------------------------------------
# ----------------------------------------
# Webhook Commvault
# ----------------------------------------
@app.post("/commvault/webhook")
async def commvault_webhook(request: Request, token: str = Header(None)):
    # El resto de tu función validate_token(token) se queda igualita.
    validate_token(token)

    try:
        # 2. Recibimos los datos de la consola
        data = await request.json()
        print("💾 Commvault webhook recibido:")
        # print(json.dumps(data, indent=4)) # Úsalo para debug si necesitas ver más campos

        # 3. Extracción de datos clave (usando .get para evitar errores si falta un campo)
        # Commvault envía estos tokens si los activas en la configuración de la Alerta
        client_name = data.get("clientName", "Servidor no identificado")
        status      = data.get("status", "Estado desconocido")
        job_id      = data.get("jobId", "N/A")
        error_info  = data.get("error", "Sin detalle técnico")
        commcell    = data.get("commCellName", "Consola Desconocida")
        
        # 4. Lógica de alertas visuales (Emojis)
        # Esto ayuda a los administradores a identificar la gravedad de un vistazo
        if "Fail" in status or "Error" in status:
            emoji = "🔴"
            prioridad = "ALTA"
        elif "Warning" in status:
            emoji = "🟡"
            prioridad = "MEDIA"
        else:
            emoji = "✅"
            prioridad = "BAJA"

        # 5. Construcción del mensaje para Telegram
        # Usamos Markdown para que el nombre del servidor resalte
        mensaje_telegram = (
            f"{emoji} *ALERTA DE RESPALDO*\n\n"
            f"🏢 *Consola:* {commcell}\n"
            f"🖥️ *Servidor:* `{client_name}`\n"
            f"📊 *Estado:* {status}\n"
            f"🆔 *Job ID:* {job_id}\n"
            f"⚠️ *Prioridad:* {prioridad}\n"
            f"📝 *Detalle:* {error_info}\n\n"
            f"🤖 _Enviado desde Middleware Render_"
        )

        # 6. Envío a Telegram (Usando tus variables de entorno)
        TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
        TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

        url_tg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensaje_telegram,
            "parse_mode": "Markdown"
        }

        response = requests.post(url_tg, json=payload)
        
        if response.status_code != 200:
            print(f"❌ Error en Telegram API: {response.text}")

    except Exception as e:
        print(f"❌ Error procesando el webhook de Commvault: {str(e)}")
        return {"status": "error", "message": str(e)}

    return {"status": "success", "client": client_name}