import json
import subprocess
from datetime import date

# --- CONFIG ---
FASE = "intermedio"
SEMANA = 9
DIA = "miercoles"
ENTRENO = "anaerobico"

# --- INPUT ---
print("Registro de sensaciones\n")

sensacion = int(input("Sensación global (1-10): "))
fatiga = int(input("Fatiga (1-10): "))
motivacion = int(input("Motivación (1-10): "))

dolor = {
    "rodilla": 0,
    "espalda": 0,
    "hombro": 0,
    "cadera": 0,
    "tobillo": 0,
    "otro": 0
}

hay_dolor = input("¿Dolor relevante? (si/no): ").lower()
if hay_dolor == "si":
    for zona in dolor:
        dolor[zona] = int(input(f"Dolor en {zona} (0-10): "))

comentario = input("Comentario (opcional): ")

# --- JSON ---
hoy = date.today().isoformat()

data = {
    "fecha": hoy,
    "fase": FASE,
    "semana": SEMANA,
    "dia": DIA,
    "entreno": ENTRENO,
    "sensacion_global": sensacion,
    "fatiga": fatiga,
    "motivacion": motivacion,
    "dolor": dolor,
    "comentario": comentario
}

ruta = f"data/metricas/sensaciones/{hoy}.json"

with open(ruta, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# --- GIT ---
subprocess.run(["git", "add", ruta])
subprocess.run(["git", "commit", "-m", f"registro sensaciones {hoy}"])
subprocess.run(["git", "push"])

print(f"\n✔ Sensaciones registradas y subidas: {ruta}")
