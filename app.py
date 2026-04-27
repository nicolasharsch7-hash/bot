import os
import requests
import sqlite3
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather

app = Flask(__name__)

# =========================
# CONFIG (USA VARIABLES ENV EN PRODUCCIÓN)
# =========================
TELEGRAM_TOKEN = os.environ.get("8671100191:AAGnjEeOD4LUgQJiVzNj79-nWhdnh2neh90")
ADMIN_CHAT_ID = os.environ.get("8225742299")

TWILIO_SID = os.environ.get("ACd39155611dc69a0f0b049a178e61a5ec")
TWILIO_AUTH = os.environ.get("aabbc52cd1ed16e8efbbc3d55fcff8dd")
TWILIO_NUMBER = os.environ.get("+19783545896")

BOT_URL = f"https://api.telegram.org/bot8671100191:AAGnjEeOD4LUgQJiVzNj79-nWhdnh2neh90"

client = Client("ACd39155611dc69a0f0b049a178e61a5ec"," aabbc52cd1ed16e8efbbc3d55fcff8dd")

# =========================
# DB INIT
# =========================
def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT,
            customer_id TEXT,
            rating TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# =========================
# MEMORY SIMPLE (estado usuario)
# =========================
user_state = {}

# =========================
# TELEGRAM SEND
# =========================
def send_telegram(chat_id, text):
    requests.post(f"{https://simplebot-2cgu.onrender.com/telegram}/sendMessage", data={
        "chat_id": chat_id,
        "text": text
    })

# =========================
# TWILIO CALL
# =========================
def make_call(number):
    try:
        call = client.calls.create(
            to=number,
            from_=+19783545896,
            url="https://simplebot-2cgu.onrender.com/call"
        )
        print("CALL SID:", call.sid)
        return True
    except Exception as e:
        print("CALL ERROR:", e)
        return False

# =========================
# TELEGRAM WEBHOOK
# =========================
@app.route("/telegram", methods=["POST"])
def telegram():
    data = request.get_json()

    if not data or "message" not in data:
        return "ok", 200

    msg = data["message"]
    text = msg.get("text", "").strip()
    chat_id = str(msg["chat"]["id"])

    # START FLOW
    if text == "/start":
        user_state[chat_id] = {"step": "phone"}

        send_telegram(chat_id,
            "👋 Bienvenido\n\nEnvía el número a llamar (formato +549...):"
        )
        return "ok", 200

    # STEP 1: phone number
    if chat_id in user_state and user_state[chat_id]["step"] == "phone":
        user_state[chat_id]["phone"] = text
        user_state[chat_id]["step"] = "customer"

        ok = make_call(text)

        if ok:
            send_telegram(chat_id, f"📞 Llamando a {text}")
        else:
            send_telegram(chat_id, "❌ Error al iniciar llamada")

        return "ok", 200

    send_telegram(chat_id, "Escribe /start para comenzar.")
    return "ok", 200

# =========================
# TWILIO CALL FLOW
# =========================
@app.route("/call", methods=["POST"])
def call():
    response = VoiceResponse()

    gather = Gather(
        input="dtmf",
        num_digits=6,
        action="/rating",
        timeout=10
    )

    gather.say("Ingrese su número de cliente.", language="es-ES")
    response.append(gather)

    response.redirect("/call")
    return str(response)

# =========================
# RATING STEP
# =========================
@app.route("/rating", methods=["POST"])
def rating():
    customer_id = request.form.get("Digits", "")

    response = VoiceResponse()

    gather = Gather(
        input="dtmf",
        num_digits=1,
        action=f"/save?customer_id={customer_id}",
        timeout=10
    )

    gather.say("Califique del 1 al 5.", language="es-ES")

    response.append(gather)
    response.redirect(f"/rating?customer_id={customer_id}")

    return str(response)

# =========================
# SAVE RESULT
# =========================
@app.route("/save", methods=["POST"])
def save():
    customer_id = request.args.get("customer_id")
    rating = request.form.get("Digits")
    phone = request.form.get("From")

    # SAVE DB
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO reviews (phone, customer_id, rating) VALUES (?, ?, ?)",
        (phone, customer_id, rating)
    )
    conn.commit()
    conn.close()

    # SEND TO ADMIN TELEGRAM
    send_telegram(ADMIN_CHAT_ID,
        f"📞 NUEVA LLAMADA\n\n"
        f"📱 {phone}\n"
        f"🧾 Cliente: {customer_id}\n"
        f"⭐ Rating: {rating}"
    )

    response = VoiceResponse()
    response.say("Gracias. Su respuesta fue registrada.", language="es-ES")

    return str(response)

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