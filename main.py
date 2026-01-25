import os
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Base de datos temporal (En el futuro conectaremos con Firebase Realtime DB)
historico_salud = []

def analizar_estado_entreno(body_battery, sueno_score):
    if sueno_score > 80 and body_battery > 70:
        return "ÓPTIMO: Puedes dar el 100% en la carrera de hoy."
    elif sueno_score < 50:
        return "RECUPERACIÓN: Baja la intensidad, prioriza caminar rápido sobre correr."
    return "ESTÁNDAR: Sigue el plan eis9.pdf sin cambios."

@app.route('/', methods=['GET', 'POST'])
def alpha50_webhook():
    if request.method == 'POST':
        data = request.get_json()
        
        # Extraer datos recibidos
        peso = data.get('peso', 92.4)
        sueno = data.get('sueno_score', 0)
        battery = data.get('body_battery_max', 0)
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Lógica de salud y mejora
        recomendacion = analizar_estado_entreno(battery, sueno)
        
        # Guardar en el log (Memoria del sistema)
        registro = {
            "fecha": fecha,
            "peso": peso,
            "sueno": sueno,
            "body_battery": battery,
            "recomendacion": recomendacion
        }
        historico_salud.append(registro)

        return jsonify({
            "status": "registrado",
            "mensaje": "Datos de salud sincronizados con Alpha50-Core",
            "analisis": recomendacion,
            "progreso_peso": f"Actual: {peso}kg | Meta: 80kg"
        })
    
    return "Alpha50 Health Monitor Online - Esperando datos biométricos."

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
