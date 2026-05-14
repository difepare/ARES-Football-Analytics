# api_rest_ares.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from ares_completo import ARES_Engine_Completo

app = Flask(__name__)
CORS(app)
ares = ARES_Engine_Completo()

@app.route('/api/predict', methods=['GET'])
def predict():
    """Endpoint para predicciones de partidos"""
    local = request.args.get('local')
    visitante = request.args.get('visitante')
    league = request.args.get('league', 'Premier League')
    
    if not local or not visitante:
        return jsonify({"error": "Faltan parámetros: local y visitante"}), 400
    
    league_id = ares.league_ids.get(league, 39)
    prediccion = ares.predecir_partido(local, visitante, league_id)
    
    return jsonify(prediccion)

@app.route('/api/champions', methods=['GET'])
def champions():
    """Endpoint para predicciones de Champions"""
    return jsonify(ares.predecir_champions())

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "online", "version": ares.version})

if __name__ == '__main__':
    app.run(debug=True, port=5000)