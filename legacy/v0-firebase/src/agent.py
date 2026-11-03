import os, json, datetime, re
from firebase_admin import credentials, initialize_app, db
import requests

# --- Telegram ---
BOT_TOKEN = os.environ["TG_BOT_TOKEN"]
CHAT_ID = os.environ["TG_CHAT_ID"]

def send(msg):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                  json={"chat_id": CHAT_ID, "text": msg})

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"timeout": 10}
    if offset:
        params["offset"] = offset
    r = requests.get(url, params=params)
    return r.json().get("result", [])

def parse_fisiologia(text):
    text = text.replace(",", ".")
    nums = re.findall(r"\d+\.?\d*", text)
    if len(nums) < 3:
        return None
    peso = float(nums[0])
    bb = int(nums[1])
    sueno = int(nums[2])
    return peso, bb, sueno

# --- Firebase ---
cred = credentials.Certificate(json.loads(os.environ["FIREBASE_SA_JSON"]))
initialize_app(cred, {
    "databaseURL": "https://alpha50-fcc77-default-rtdb.europe-west1.firebasedatabase.app/"
})

today = datetime.date.today()
dow = today.strftime("%A").lower()
mapa = {
    "monday":"lunes","tuesday":"martes","wednesday":"miercoles",
    "thursday":"jueves","friday":"viernes","saturday":"sabado","sunday":"domingo"
}
dia = mapa[dow]

# Estado
ref = db.reference("estado")
estado = ref.get() or {"fase":"intermedio","semana":9}

# Enviar saludo inicial
control_ref = db.reference("sistema/control")
control = control_ref.get() or {}
hoy = today.isoformat()

if control.get("saludo_fecha") != hoy:
    send(f"☀️ Buenos días.\nHoy es {dia.capitalize()}.\n"
         f"Semana {estado['semana']} – {estado['fase']}.\n"
         "Dame: Peso, Body Battery y Sueño (0–100).")
    control_ref.update({"saludo_fecha": hoy})


# Recuperar último update_id procesado
meta_ref = db.reference("sistema/telegram")
meta = meta_ref.get() or {}
last_id = meta.get("last_update_id")

# Obtener mensajes nuevos
updates = get_updates(last_id)

# Procesar cada mensaje
for upd in updates:
    msg = upd.get("message")
    if not msg or "text" not in msg:
        # Actualizar offset incluso si no es texto
        meta_ref.update({"last_update_id": upd["update_id"] + 1})
        continue
    
    text = msg["text"].strip()
    parsed = parse_fisiologia(text)
    
    if not parsed:
        # Si no se puede parsear, avisar pero avanzar offset
        send("⚠️ No entendí el formato. Envía: peso bb sueño (ej: 75.5 85 90)")
        meta_ref.update({"last_update_id": upd["update_id"] + 1})
        continue
    
    peso, bb, sueno = parsed
    hoy = today.isoformat()

    estado_fisio = (
        "OPTIMO" if bb >= 80 and sueno >= 80
        else "MEDIO" if bb >= 50
        else "BAJO"
    )

    payload = {
        "peso": float(peso),
        "body_battery": int(bb),
        "sueno": int(sueno),
        "estado": estado_fisio
    }

    db.reference(f"fisiologia/{hoy}").set(payload)

    dias_descanso = ["jueves", "domingo"]

    if dia in dias_descanso:
        send(
            f"✅ Datos recibidos correctamente.\n"
            f"Estado fisiológico: **{estado_fisio}**.\n"
            "🛑 Hoy toca **DESCANSO**."
        )
    else:
        send(
            f"✅ Datos recibidos correctamente.\n"
            f"Estado fisiológico: **{estado_fisio}**.\n"
            "🏋️ Hoy toca **ENTRENAR**."
        )

    meta_ref.update({"last_update_id": upd["update_id"] + 1})
