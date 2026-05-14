import pandas as pd
import numpy as np
from datetime import datetime
import random  # Solo para simular datos. Tú lo reemplazarás con API real

class ARES_Engine:
    def __init__(self):
        self.version = "1.0.0"
        self.target_league = "Premier League"
        print(f"🚀 A.R.E.S. {self.version} - Vigilando {self.target_league}")
        
    def obtener_datos_equipo(self, equipo_nombre):
        """
        SIMULACIÓN: Aquí irá tu llamada real a API-Football, Sportmonks, etc.
        Por ahora generamos datos coherentes de ejemplo.
        """
        # Datos base de ejemplo (tú los reemplazarás con API real)
        datos_ejemplo = {
            "Manchester City": {
                "xG_promedio_local": 2.1,
                "xG_contra_promedio": 0.8,
                "posesion_promedio": 62,
                "velocidad_extremos": 34,  # km/h promedio últimos partidos
                "goles_ultimos_15_local": 0.65,  # probabilidad de gol en 76-90'
                "fatiga_acumulada": 0.25,  # 0 a 1, donde 1 es máximo riesgo
                "ultimos_5_partidos": [3, 1, 2, 4, 2],  # goles a favor
            },
            "Liverpool": {
                "xG_promedio_visitante": 1.7,
                "xG_contra_visitante": 1.2,
                "posesion_visitante": 58,
                "velocidad_extremos": 36,
                "goles_ultimos_15_visitante": 0.58,
                "fatiga_acumulada": 0.45,
                "ultimos_5_partidos": [2, 3, 1, 2, 4],
            },
            "Arsenal": {
                "xG_promedio_local": 1.9,
                "xG_contra_promedio": 1.0,
                "posesion_promedio": 56,
                "velocidad_extremos": 32,
                "goles_ultimos_15_local": 0.52,
                "fatiga_acumulada": 0.30,
                "ultimos_5_partidos": [2, 1, 3, 2, 5],
            }
        }
        return datos_ejemplo.get(equipo_nombre, {
            "xG_promedio_local": 1.5,
            "xG_contra_promedio": 1.3,
            "posesion_promedio": 50,
            "velocidad_extremos": 30,
            "goles_ultimos_15_local": 0.40,
            "fatiga_acumulada": 0.35,
            "ultimos_5_partidos": [1, 1, 2, 1, 1],
        })
    
    def calcular_xG(self, equipo_data, es_local):
        """
        Calcula Goles Esperados ajustando por localía y forma reciente.
        """
        if es_local:
            xG_base = equipo_data["xG_promedio_local"]
            # Factor forma: si últimos partidos tienen altos goles, aumenta xG
            promedio_goles_reciente = np.mean(equipo_data["ultimos_5_partidos"])
            factor_forma = 1 + (promedio_goles_reciente - 2) * 0.1
            factor_forma = max(0.7, min(1.3, factor_forma))
        else:
            xG_base = equipo_data.get("xG_promedio_visitante", 1.2)
            promedio_goles_reciente = np.mean(equipo_data["ultimos_5_partidos"])
            factor_forma = 1 + (promedio_goles_reciente - 2) * 0.05
            factor_forma = max(0.7, min(1.3, factor_forma))
        
        # Ajuste por fatiga
        factor_fatiga = 1 - (equipo_data["fatiga_acumulada"] * 0.2)
        
        xG_final = xG_base * factor_forma * factor_fatiga
        return round(xG_final, 2)
    
    def calcular_probabilidad_victoria(self, xG_local, xG_visitante):
        """
        Modelo simplificado: diferencia de xG mapeada a probabilidad.
        Basado en distribuciones de Poisson.
        """
        diferencia = xG_local - xG_visitante
        
        # Fórmula empírica (mejorable con modelo Poisson real)
        if diferencia > 0.8:
            prob_local = 0.70
        elif diferencia > 0.4:
            prob_local = 0.60
        elif diferencia > 0.1:
            prob_local = 0.52
        elif diferencia > -0.1:
            prob_local = 0.45
        elif diferencia > -0.4:
            prob_local = 0.38
        else:
            prob_local = 0.30
            
        prob_empate = 0.26 - abs(diferencia) * 0.08
        prob_empate = max(0.18, min(0.30, prob_empate))
        prob_visitante = 1 - prob_local - prob_empate
        
        return {
            "local": round(prob_local * 100, 1),
            "empate": round(prob_empate * 100, 1),
            "visitante": round(prob_visitante * 100, 1)
        }
    
    def confluencia_victoria(self, equipo_local, equipo_visitante, datos_local, datos_visitante):
        """
        Detector de señales de acción: igual que RSI + Soporte pero en fútbol.
        Retorna: (activada, factores_cumplidos, sugerencia)
        """
        factores = []
        
        # Factor 1: El rival pierde posesión fuera de casa
        posesion_rival_fuera = datos_visitante.get("posesion_visitante", 50)
        if posesion_rival_fuera < datos_local["posesion_promedio"] - 5:
            factores.append("⚠️ Rival baja posesión fuera (-5% vs su media)")
        
        # Factor 2: Alta velocidad de nuestros extremos
        if datos_local["velocidad_extremos"] > 33:
            factores.append("⚡ Extremos locales +10% velocidad última hora")
        
        # Factor 3: Historial de goles tardíos (últimos 15')
        if datos_local["goles_ultimos_15_local"] > 0.55:
            factores.append("⏰ Historial fuerte de goles en minutos finales")
        
        # Factor 4: Fatiga acumulada del rival
        if datos_visitante["fatiga_acumulada"] > 0.4:
            factores.append("😩 Rival con alta fatiga acumulada (>40%)")
        
        activada = len(factores) >= 3
        
        sugerencia = ""
        if activada:
            sugerencia = "💡 PRESIONAR SALIDA POR BANDA IZQUIERDA - Confluencia detectada"
        elif len(factores) == 2:
            sugerencia = "📊 Confluencia parcial. Monitorear primeros 20 minutos."
        else:
            sugerencia = "🔍 Sin confluencia clara. Seguir plan base."
        
        return activada, factores, sugerencia
    
    def analizar_partido(self, equipo_local_nombre, equipo_visitante_nombre):
        """
        Función principal que ejecuta TODO el análisis.
        """
        print(f"\n{'='*50}")
        print(f"📊 A.R.E.S. - Análisis en tiempo real")
        print(f"{equipo_local_nombre} vs {equipo_visitante_nombre}")
        print(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}\n")
        
        # Obtener datos
        datos_local = self.obtener_datos_equipo(equipo_local_nombre)
        datos_visitante = self.obtener_datos_equipo(equipo_visitante_nombre)
        
        # Calcular xG
        xG_local = self.calcular_xG(datos_local, es_local=True)
        xG_visitante = self.calcular_xG(datos_visitante, es_local=False)
        
        # Calcular probabilidades
        probs = self.calcular_probabilidad_victoria(xG_local, xG_visitante)
        
        # Confluencia de Victoria
        confluencia_activada, factores, sugerencia = self.confluencia_victoria(
            equipo_local_nombre, equipo_visitante_nombre, datos_local, datos_visitante
        )
        
        # Mostrar resultados
        print(f"🎯 PROBABILIDADES:")
        print(f"   {equipo_local_nombre}: {probs['local']}%")
        print(f"   Empate: {probs['empate']}%")
        print(f"   {equipo_visitante_nombre}: {probs['visitante']}%")
        
        print(f"\n⚽ GOLES ESPERADOS (xG):")
        print(f"   {equipo_local_nombre}: {xG_local}")
        print(f"   {equipo_visitante_nombre}: {xG_visitante}")
        
        print(f"\n⚠️ CONFLUENCIA DE VICTORIA:")
        if confluencia_activada:
            print(f"   ✅ ACTIVADA ({len(factores)}/4 factores)")
        else:
            print(f"   ❌ NO ACTIVADA ({len(factores)}/4 factores)")
        for f in factores:
            print(f"   {f}")
        
        print(f"\n{sugerencia}")
        
        # Alerta de riesgo de lesión (bonus)
        if datos_local["fatiga_acumulada"] > 0.5:
            print(f"\n🚨 ALERTA: Fatiga crítica en {equipo_local_nombre} - Riesgo lesión elevado")
        if datos_visitante["fatiga_acumulada"] > 0.5:
            print(f"\n🚨 ALERTA: Fatiga crítica en {equipo_visitante_nombre} - Riesgo lesión elevado")
        
        print(f"\n{'='*50}")
        print("🔮 A.R.E.S. recomienda seguir monitoreando datos en vivo")
        
        return {
            "xG_local": xG_local,
            "xG_visitante": xG_visitante,
            "probabilidad_local": probs["local"],
            "confluencia_activada": confluencia_activada,
            "sugerencia": sugerencia
        }


# --- EJECUCIÓN PRINCIPAL ---
if __name__ == "__main__":
    # Inicializar el cerebro
    ares = ARES_Engine()
    
    # Analizar un partido
    resultado = ares.analizar_partido("Manchester City", "Liverpool")
    
    # Bonus: puedes analizar otro partido cambiando los nombres
    print("\n\n" + "🔥"*25)
    print("PROBAR CON OTRO PARTIDO:")
    resultado2 = ares.analizar_partido("Arsenal", "Manchester City")