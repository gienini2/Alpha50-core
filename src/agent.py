import os, json, datetime
from firebase_admin import credentials, initialize_app, db
import requests

# --- Telegram ---
BOT = os.environ["TG_BOT_TOKEN"]
CHAT = os.environ["TG_CHAT_ID"]
def send(msg):
    requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage",
                  json={"chat_id": CHAT, "text": msg})
def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"timeout": 10}
    if offset:
        params["offset"] = offset
    r = requests.get(url, params=params).json()
    return r.get("result", [])


# --- Firebase ---
cred = credentials.Certificate(json.loads(os.environ["FIREBASE_SA_JSON"]))
initialize_app(cred, {"databaseURL": "https://alpha50-fcc77-default-rtdb.europe-west1.firebasedatabase.app/"})

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
updates = get_updates()

if updates:
    last = updates[-1]
    text = last["message"]["text"]
    update_id = last["update_id"] + 1
else:
    text = None
    update_id = None
import re

def parse_fisiologia(text):
    nums = re.findall(r"\d+\.?\d*", text)
    if len(nums) < 3:
        return None
    peso = float(nums[0])
    bb = int(nums[1])
    sueno = int(nums[2])
    return peso, bb, sueno
if text:
    parsed = parse_fisiologia(text)
    if parsed:
        peso, bb, sueno = parsed
        estado = "OPTIMO" if bb >= 80 and sueno >= 80 else "MEDIO" if bb >= 50 else "BAJO"

        hoy = today.isoformat()
        db.reference(f"fisiologia/{hoy}").set({
            "peso": peso,
            "body_battery": bb,
            "sueno": sueno,
            "estado": estado
        })

        send(
            f"Datos recibidos.\n"
            f"Estado fisiológico: **{estado}**.\n"
            f"En breve te digo qué toca hoy."
        )
meta_ref = db.reference("sistema/telegram")
meta = meta_ref.get() or {}

last_id = meta.get("last_update_id")

updates = get_updates(last_id)

if updates:
    last = updates[-1]
    meta_ref.update({"last_update_id": last["update_id"] + 1})
