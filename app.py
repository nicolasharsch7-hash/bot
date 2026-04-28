import os
import requests
from flask import Flask, request, Response
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather

app = Flask(__name__)

# =========================
# 🔐 CONFIG (EDITAR SOLO AQUÍ)
# =========================

TELEGRAM_TOKEN = "8671100191:AAGnjEeOD4LUgQJiVzNj79-nWhdnh2neh90"
# ↑ Pegá EXACTAMENTE tu token entre comillas

ADMIN_CHAT_ID = "8225742299"
# ↑ Este ya está bien, no lo cambies si es tuyo

TWILIO_SID = "ACd39155611dc69a0f0b049a178e61a5ec"
# ↑ Empieza con AC...

TWILIO_AUTH = "f8189d7b2b187d72be3f19351de3e0aa"
# ↑ Token secreto de Twilio

TWILIO_NUMBER = "+19783545896"
# ↑ Tu número de Twilio (déjalo así si es el tuyo)

BASE_URL = "https://simplebot-2cgu.onrender.com"
# ↑ Tu URL de Render (NO cambiar si es esa)

# =========================
# ⚙️ NO TOCAR DESDE AQUÍ
# =========================

BOT_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
client = Client(TWILIO_SID, TWILIO_AUTH)

# =========================
# TELEGRAM
# =========================
def send_telegram(chat_id, text):
    requests.post(f"{BOT_URL}/sendMessage", data={
        "chat_id": chat_id,
        "text": text
    })

# =========================
# LLAMADA
# =========================
def make_call(number):
    try:
        call = client.calls.create(
            to=number,
            from_=TWILIO_NUMBER,
            url=f"{BASE_URL}/call",
            method="POST"
        )
        return f"📞 Llamando...\nSID: {call.sid}"
    except Exception as e:
        return f"❌ Error:\n{str(e)}"

# =========================
# TELEGRAM WEBHOOK
# =========================
user_state = {}

@app.route("/telegram", methods=["POST"])
def telegram():
    data = request.get_json()

    if not data or "message" not in data:
        return "ok", 200

    msg = data["message"]
    text = msg.get("text", "").strip()
    chat_id = str(msg["chat"]["id"])

    if text == "/start":
        user_state[chat_id] = {"step": "phone"}
        send_telegram(chat_id, "Envía el número (+549...)")
        return "ok", 200

    if chat_id in user_state and user_state[chat_id]["step"] == "phone":
        result = make_call(text)
        send_telegram(chat_id, result)
        return "ok", 200

    return "ok", 200

# =========================
# FLUJO TWILIO
# =========================
@app.route("/call", methods=["GET", "POST"])
def call():
    vr = VoiceResponse()

    gather = Gather(
        input="dtmf",
        num_digits=6,
        action=f"{BASE_URL}/rating",
        method="POST",
        timeout=10
    )

    gather.say("Ingrese su número de cliente.", language="es-ES")
    vr.append(gather)

    vr.redirect(f"{BASE_URL}/call", method="POST")

    return Response(str(vr), mimetype="text/xml")

@app.route("/rating", methods=["GET", "POST"])
def rating():
    customer_id = request.form.get("Digits", "")

    vr = VoiceResponse()

    gather = Gather(
        input="dtmf",
        num_digits=1,
        action=f"{BASE_URL}/save?customer_id={customer_id}",
        method="POST",
        timeout=10
    )

    gather.say("Califique del uno al cinco.", language="es-ES")
    vr.append(gather)

    vr.redirect(f"{BASE_URL}/rating?customer_id={customer_id}", method="POST")

    return Response(str(vr), mimetype="text/xml")

@app.route("/save", methods=["GET", "POST"])
def save():
    customer_id = request.args.get("customer_id")
    rating = request.form.get("Digits")
    phone = request.form.get("From")

    send_telegram(
        ADMIN_CHAT_ID,
        f"📞 {phone}\n🧾 Cliente: {customer_id}\n⭐ Rating: {rating}"
    )

    vr = VoiceResponse()
    vr.say("Gracias. Su respuesta fue registrada.", language="es-ES")

    return Response(str(vr), mimetype="text/xml")

# =========================
# HOME
# =========================
@app.route("/", methods=["GET"])
def home():
    return "Bot activo 🚀", 200

# =========================
# RUN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)