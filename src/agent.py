import os, json, datetime
from firebase_admin import credentials, initialize_app, db
import requests

# --- Telegram ---
BOT = os.environ["TG_BOT_TOKEN"]
CHAT = os.environ["TG_CHAT_ID"]
def send(msg):
    requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage",
                  json={"chat_id": CHAT, "text": msg})

# --- Firebase ---
cred = credentials.Certificate(json.loads(os.environ["FIREBASE_SA_JSON"]))
initialize_app(cred, {"databaseURL": "https://TU-PROYECTO.firebaseio.com"})

today = datetime.date.today()
dow = today.strftime("%A").lower()  # monday...
mapa = {
    "monday":"lunes","tuesday":"martes","wednesday":"miercoles",
    "thursday":"jueves","friday":"viernes","saturday":"sabado","sunday":"domingo"
}
dia = mapa[dow]

# Estado mínimo (ejemplo)
ref = db.reference("estado")
estado = ref.get() or {"fase":"intermedio","semana":9}

# Lógica simple del día (sin parseo fino)
send(f"☀️ Buenos días.\nHoy es {dia.capitalize()}.\n"
     f"Semana {estado['semana']} – {estado['fase']}.\n"
     "Dame: Peso, Body Battery y Sueño (0–100).")
