import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional

class Posicion(Enum):
    DELANTERO = "Delantero"
    MEDIOCAMPISTA = "Mediocampista"
    DEFENSA_CENTRAL = "Defensa Central"
    LATERAL = "Lateral"
    PORTERO = "Portero"

class NivelRiesgo(Enum):
    BAJO = "🟢 Bajo"
    MODERADO = "🟡 Moderado"
    ALTO = "🔴 Alto"
    CRITICO = "⚫ Crítico"

@dataclass
class EstadisticasJugador:
    nombre: str
    posicion: Posicion
    edad: int
    minutos_jugados_7dias: int  # Última semana
    minutos_jugados_72h: int     # Últimas 72 horas
    intensidad_media: float      # 0-100, km/h o métrica de esfuerzo
    distancia_recorrida: float   # km por partido
    historial_lesiones: int      # Número de lesiones últimas 2 temporadas
    sprints_por_partido: int
    dias_descanso_ultimo: int    # Días desde último partido

class ModuloFatigaAvanzada:
    """
    Sistema de análisis de fatiga con umbrales personalizados por posición
    Basado en estudios de ciencia del deporte y métricas reales
    """
    
    def __init__(self):
        # Umbrales de fatiga por posición (minutos antes de riesgo)
        self.umbrales_minutos = {
            Posicion.DELANTERO: {"moderado": 270, "alto": 360, "critico": 450},
            Posicion.MEDIOCAMPISTA: {"moderado": 300, "alto": 390, "critico": 480},
            Posicion.DEFENSA_CENTRAL: {"moderado": 315, "alto": 405, "critico": 495},
            Posicion.LATERAL: {"moderado": 285, "alto": 375, "critico": 465},
            Posicion.PORTERO: {"moderado": 450, "alto": 540, "critico": 630},
        }
        
        # Factor intensidad por posición (los delanteros y laterales sufren más)
        self.factor_intensidad = {
            Posicion.DELANTERO: 1.3,
            Posicion.MEDIOCAMPISTA: 1.2,
            Posicion.DEFENSA_CENTRAL: 1.0,
            Posicion.LATERAL: 1.25,
            Posicion.PORTERO: 0.6,
        }
        
        print("✅ Módulo de Fatiga Avanzada inicializado")
    
    def calcular_riesgo_fatiga(self, jugador: EstadisticasJugador, minuto_partido: int = 0) -> Dict:
        """
        Calcula el riesgo de lesión/fatiga en tiempo real
        Retorna: nivel_riesgo, probabilidad_lesion, sugerencia
        """
        umbrales = self.umbrales_minutos[jugador.posicion]
        
        # Factor 1: Minutos acumulados en 7 días
        minutos_factor = 0
        if jugador.minutos_jugados_7dias >= umbrales["critico"]:
            minutos_factor = 0.7
        elif jugador.minutos_jugados_7dias >= umbrales["alto"]:
            minutos_factor = 0.5
        elif jugador.minutos_jugados_7dias >= umbrales["moderado"]:
            minutos_factor = 0.3
        
        # Factor 2: Minutos en últimas 72h (fatiga aguda)
        agudo_factor = min(0.5, jugador.minutos_jugados_72h / 180) if jugador.minutos_jugados_72h > 90 else 0
        
        # Factor 3: Intensidad (sprints + distancia)
        intensidad_base = (jugador.intensidad_media / 100) * self.factor_intensidad[jugador.posicion]
        sprints_factor = (jugador.sprints_por_partido / 40) * 0.3  # 40 sprints es muy alto
        
        # Factor 4: Historial de lesiones
        lesiones_factor = min(0.4, jugador.historial_lesiones * 0.08)
        
        # Factor 5: Días de descanso (inverso)
        descanso_factor = max(0, 0.3 - (jugador.dias_descanso_ultimo * 0.05))
        
        # Factor 6: Minuto actual del partido (fatiga durante el juego)
        minuto_factor = min(0.35, (minuto_partido / 90) * 0.35)
        
        # Cálculo final de probabilidad de lesión (0 a 1)
        probabilidad_lesion = min(0.95, (
            minutos_factor * 0.25 +
            agudo_factor * 0.20 +
            intensidad_base * 0.20 +
            sprints_factor * 0.10 +
            lesiones_factor * 0.15 +
            descanso_factor * 0.05 +
            minuto_factor * 0.05
        ))
        
        # Determinar nivel de riesgo
        if probabilidad_lesion >= 0.65:
            nivel = NivelRiesgo.CRITICO
            sugerencia = "🚨 ¡SUSTITUCIÓN INMEDIATA! Riesgo de lesión muy alto"
            accion = "sustituir_ya"
        elif probabilidad_lesion >= 0.45:
            nivel = NivelRiesgo.ALTO
            sugerencia = f"⚠️ Riesgo alto. Recomendar sustitución en los próximos {max(5, 25 - minuto_partido)} minutos"
            accion = "preparar_suplente"
        elif probabilidad_lesion >= 0.25:
            nivel = NivelRiesgo.MODERADO
            sugerencia = "📊 Fatiga moderada. Reducir intensidad o preparar cambio para 2T"
            accion = "monitorear"
        else:
            nivel = NivelRiesgo.BAJO
            sugerencia = "✅ Condición óptica. Puede continuar con normalidad"
            accion = "continuar"
        
        return {
            "nivel": nivel,
            "probabilidad_lesion": round(probabilidad_lesion * 100, 1),
            "sugerencia": sugerencia,
            "accion": accion,
            "detalles": {
                "minutos_7dias": jugador.minutos_jugados_7dias,
                "minutos_72h": jugador.minutos_jugados_72h,
                "intensidad": jugador.intensidad_media,
                "sprints": jugador.sprints_por_partido,
                "lesiones_historial": jugador.historial_lesiones
            }
        }
    
    def generar_onces_ideal_fatiga(self, plantilla: List[EstadisticasJugador], minuto: int = 0) -> List[Dict]:
        """
        Recomienda la alineación óptima basada en fatiga
        """
        analisis = []
        for jugador in plantilla:
            riesgo = self.calcular_riesgo_fatiga(jugador, minuto)
            analisis.append({
                "nombre": jugador.nombre,
                "posicion": jugador.posicion.value,
                "riesgo": riesgo["nivel"].value,
                "prob_lesion": riesgo["probabilidad_lesion"],
                "sugerencia": riesgo["sugerencia"],
                "debe_jugar": riesgo["probabilidad_lesion"] < 40
            })
        
        # Ordenar por riesgo (más bajo primero)
        analisis.sort(key=lambda x: x["prob_lesion"])
        
        return analisis
    
    def alerta_tiempo_real(self, jugador: EstadisticasJugador, minuto_actual: int):
        """
        Simula monitoreo en vivo durante el partido
        """
        riesgo = self.calcular_riesgo_fatiga(jugador, minuto_actual)
        
        if riesgo["nivel"] in [NivelRiesgo.ALTO, NivelRiesgo.CRITICO]:
            print(f"\n🚨 ALERTA EN VIVO - Minuto {minuto_actual}")
            print(f"   Jugador: {jugador.nombre} ({jugador.posicion.value})")
            print(f"   Riesgo: {riesgo['nivel'].value} - {riesgo['probabilidad_lesion']}%")
            print(f"   {riesgo['sugerencia']}")
            return True
        return False


# --- DEMOSTRACIÓN DEL MÓDULO DE FATIGA ---
if __name__ == "__main__":
    fatiga = ModuloFatigaAvanzada()
    
    # Crear jugadores de ejemplo
    jugadores = [
        EstadisticasJugador(
            nombre="Erling Haaland",
            posicion=Posicion.DELANTERO,
            edad=23,
            minutos_jugados_7dias=340,
            minutos_jugados_72h=180,
            intensidad_media=78.5,
            distancia_recorrida=9.8,
            historial_lesiones=2,
            sprints_por_partido=28,
            dias_descanso_ultimo=3
        ),
        EstadisticasJugador(
            nombre="Rodri",
            posicion=Posicion.MEDIOCAMPISTA,
            edad=27,
            minutos_jugados_7dias=410,
            minutos_jugados_72h=270,
            intensidad_media=72.0,
            distancia_recorrida=11.2,
            historial_lesiones=0,
            sprints_por_partido=18,
            dias_descanso_ultimo=3
        ),
        EstadisticasJugador(
            nombre="Kyle Walker",
            posicion=Posicion.LATERAL,
            edad=33,
            minutos_jugados_7dias=450,
            minutos_jugados_72h=270,
            intensidad_media=82.0,
            distancia_recorrida=10.5,
            historial_lesiones=3,
            sprints_por_partido=32,
            dias_descanso_ultimo=2
        )
    ]
    
    print("\n" + "="*60)
    print("🔬 ANÁLISIS DE FATIGA PRE-PARTIDO")
    print("="*60)
    
    for jugador in jugadores:
        riesgo = fatiga.calcular_riesgo_fatiga(jugador)
        print(f"\n👤 {jugador.nombre} ({jugador.posicion.value})")
        print(f"   🎯 Riesgo: {riesgo['nivel'].value} - {riesgo['probabilidad_lesion']}%")
        print(f"   💡 {riesgo['sugerencia']}")
        print(f"   📊 Detalles: {riesgo['detalles']}")
    
    # Simular alerta durante el partido
    print("\n" + "="*60)
    print("📡 MONITOREO EN VIVO - SIMULACIÓN DE PARTIDO")
    print("="*60)
    
    for minuto in [15, 30, 45, 60, 70, 80]:
        fatiga.alerta_tiempo_real(jugadores[2], minuto)  # Walker (el más fatigado)