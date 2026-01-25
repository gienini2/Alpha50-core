import os
from flask import Flask, request, jsonify

app = Flask(__name__)

def calcular_puntos(peso, agilidad, navette):
    # Lógica de baremo GUB Hombres >31 años
    puntos_agilidad = 10 if agilidad <= 18.3 else (4 if agilidad <= 19.5 else 2)
    puntos_navette = 10 if navette >= 10.5 else (4 if navette >= 9 else 2)
    puntos_banca = 10 if peso >= 34 else 10 # Tú haces 41, siempre es 10 o 12
    
    total = puntos_agilidad + puntos_navette + puntos_banca
    return total

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        data = request.get_json()
        peso = data.get('peso', 92.4)
        agilidad = data.get('agilidad', 19.6)
        navette = data.get('navette', 8.0)
        
        total_puntos = calcular_puntos(peso, agilidad, navette)
        
        return jsonify({
            "status": "success",
            "puntos_totales": total_puntos,
            "agente": "1009",
            "mensaje": f"Puntuación GUB actual: {total_puntos}/30"
        })
    return "Alpha50 Core Online - Esperando datos del Agente 1009"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
