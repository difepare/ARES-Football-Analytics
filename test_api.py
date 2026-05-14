import requests
import os
from dotenv import load_dotenv

# Cargar la API Key desde el archivo .env
load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
API_HOST = os.getenv("API_FOOTBALL_HOST", "v3.football.api-sports.io")

def test_conexion():
    """Prueba básica: obtener las ligas disponibles"""
    
    url = f"https://{API_HOST}/leagues"
    
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": API_HOST
    }
    
    print("🚀 Conectando a API-Football...")
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            datos = response.json()
            print(f"✅ Conexión exitosa! Status: {response.status_code}")
            print(f"📊 Total de ligas disponibles: {len(datos['response'])}")
            
            # Mostrar las primeras 5 ligas como ejemplo
            print("\n🏆 Ejemplo de ligas disponibles:")
            for liga in datos['response'][:5]:
                print(f"   - {liga['league']['name']} ({liga['country']['name']})")
                
            return True
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def obtener_partidos_hoy():
    """Obtener los partidos que se juegan hoy"""
    
    url = f"https://{API_HOST}/fixtures"
    
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": API_HOST
    }
    
    # Parámetros: fecha actual y liga (por defecto Premier League - 39)
    params = {
        "date": "2026-05-13",  # Cambia esta fecha si quieres
        "league": 39,  # 39 = Premier League
        "season": 2025
    }
    
    print("\n⚽ Buscando partidos de hoy...")
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            datos = response.json()
            partidos = datos['response']
            
            if partidos:
                print(f"✅ Encontrados {len(partidos)} partidos:")
                for partido in partidos:
                    local = partido['teams']['home']['name']
                    visitante = partido['teams']['away']['name']
                    print(f"   🏠 {local} vs {visitante} ✈️")
            else:
                print("📭 No hay partidos programados para hoy en la Premier League")
            return partidos
        else:
            print(f"❌ Error {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

if __name__ == "__main__":
    print("="*50)
    print("🔑 PRUEBA DE API-FOOTBALL PARA A.R.E.S.")
    print("="*50)
    
    # Probar conexión básica
    if test_conexion():
        print("\n" + "="*50)
        # Probar obtener partidos
        obtener_partidos_hoy()
    
    print("\n" + "="*50)
    print("💡 Si todo funcionó, ¡tu API está lista para A.R.E.S.!")