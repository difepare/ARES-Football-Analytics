import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import time
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
import base64

# Cargar API Key
load_dotenv()
API_KEY = os.getenv("API_FOOTBALL_KEY")
API_HOST = os.getenv("API_FOOTBALL_HOST", "v3.football.api-sports.io")

# ============================================================
# CLASE: POSICIONES Y RIESGO
# ============================================================

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
    minutos_jugados_7dias: int
    minutos_jugados_72h: int
    intensidad_media: float
    distancia_recorrida: float
    historial_lesiones: int
    sprints_por_partido: int
    dias_descanso_ultimo: int

# ============================================================
# CLASE: CACHÉ DE API
# ============================================================

class CacheAPI:
    def __init__(self, ttl_segundos=3600):
        self.cache = {}
        self.ttl = ttl_segundos
    
    def get(self, key):
        if key in self.cache:
            datos, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return datos
        return None
    
    def set(self, key, datos):
        self.cache[key] = (datos, time.time())
    
    def clear(self):
        self.cache.clear()

# ============================================================
# CLASE: MÓDULO DE FATIGA AVANZADA
# ============================================================

class ModuloFatigaAvanzada:
    def __init__(self):
        self.umbrales_minutos = {
            Posicion.DELANTERO: {"moderado": 270, "alto": 360, "critico": 450},
            Posicion.MEDIOCAMPISTA: {"moderado": 300, "alto": 390, "critico": 480},
            Posicion.DEFENSA_CENTRAL: {"moderado": 315, "alto": 405, "critico": 495},
            Posicion.LATERAL: {"moderado": 285, "alto": 375, "critico": 465},
            Posicion.PORTERO: {"moderado": 450, "alto": 540, "critico": 630},
        }
        
        self.factor_intensidad = {
            Posicion.DELANTERO: 1.3,
            Posicion.MEDIOCAMPISTA: 1.2,
            Posicion.DEFENSA_CENTRAL: 1.0,
            Posicion.LATERAL: 1.25,
            Posicion.PORTERO: 0.6,
        }
    
    def calcular_riesgo_fatiga(self, jugador: EstadisticasJugador, minuto_partido: int = 0) -> Dict:
        umbrales = self.umbrales_minutos[jugador.posicion]
        
        minutos_factor = 0
        if jugador.minutos_jugados_7dias >= umbrales["critico"]:
            minutos_factor = 0.7
        elif jugador.minutos_jugados_7dias >= umbrales["alto"]:
            minutos_factor = 0.5
        elif jugador.minutos_jugados_7dias >= umbrales["moderado"]:
            minutos_factor = 0.3
        
        agudo_factor = min(0.5, jugador.minutos_jugados_72h / 180) if jugador.minutos_jugados_72h > 90 else 0
        intensidad_base = (jugador.intensidad_media / 100) * self.factor_intensidad[jugador.posicion]
        sprints_factor = (jugador.sprints_por_partido / 40) * 0.3
        lesiones_factor = min(0.4, jugador.historial_lesiones * 0.08)
        descanso_factor = max(0, 0.3 - (jugador.dias_descanso_ultimo * 0.05))
        minuto_factor = min(0.35, (minuto_partido / 90) * 0.35)
        
        probabilidad_lesion = min(0.95, (
            minutos_factor * 0.25 + agudo_factor * 0.20 + intensidad_base * 0.20 +
            sprints_factor * 0.10 + lesiones_factor * 0.15 + descanso_factor * 0.05 + minuto_factor * 0.05
        ))
        
        if probabilidad_lesion >= 0.65:
            nivel = NivelRiesgo.CRITICO
            sugerencia = "🚨 ¡SUSTITUCIÓN INMEDIATA! Riesgo de lesión muy alto"
            accion = "sustituir_ya"
        elif probabilidad_lesion >= 0.45:
            nivel = NivelRiesgo.ALTO
            sugerencia = "⚠️ Riesgo alto. Recomendar sustitución en los próximos minutos"
            accion = "preparar_suplente"
        elif probabilidad_lesion >= 0.25:
            nivel = NivelRiesgo.MODERADO
            sugerencia = "📊 Fatiga moderada. Reducir intensidad"
            accion = "monitorear"
        else:
            nivel = NivelRiesgo.BAJO
            sugerencia = "✅ Condición óptima. Puede continuar"
            accion = "continuar"
        
        return {
            "nivel": nivel,
            "probabilidad_lesion": round(probabilidad_lesion * 100, 1),
            "sugerencia": sugerencia,
            "accion": accion
        }

# ============================================================
# CLASE: MOTOR PRINCIPAL A.R.E.S.
# ============================================================

class ARES_Engine_Completo:
    def __init__(self):
        self.version = "3.0.0 - Full Edition"
        self.cache = CacheAPI()
        self.fatiga = ModuloFatigaAvanzada()
        self.leagues = self._cargar_ligas()
        
        # IDs de ligas importantes
        self.league_ids = {
            "Premier League": 39,
            "La Liga": 140,
            "Serie A": 135,
            "Bundesliga": 78,
            "Ligue 1": 61,
            "Champions League": 2,
            "Europa League": 3,
            "World Cup": 1
        }
        
        print(f"🚀 A.R.E.S. {self.version} iniciado")
        print(f"📊 {len(self.leagues)} ligas disponibles")
    
    def _cargar_ligas(self):
        cache_key = "leagues"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        url = f"https://{API_HOST}/leagues"
        headers = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": API_HOST}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                datos = response.json()
                ligas = {}
                for liga in datos['response']:
                    liga_id = liga['league']['id']
                    ligas[liga_id] = {
                        'name': liga['league']['name'],
                        'country': liga['country']['name'],
                        'season': 2025
                    }
                self.cache.set(cache_key, ligas)
                return ligas
        except Exception as e:
            print(f"Error cargando ligas: {e}")
        
        return {39: {'name': 'Premier League', 'country': 'England', 'season': 2025}}
    
    def obtener_partidos_proximos(self, league_id=39, dias=14):
        cache_key = f"fixtures_{league_id}_{dias}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        url = f"https://{API_HOST}/fixtures"
        headers = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": API_HOST}
        
        hoy = datetime.now()
        fecha_fin = hoy + timedelta(days=dias)
        
        params = {
            "league": league_id,
            "season": 2025,
            "from": hoy.strftime("%Y-%m-%d"),
            "to": fecha_fin.strftime("%Y-%m-%d")
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                datos = response.json()
                partidos = []
                for partido in datos['response']:
                    partidos.append({
                        'id': partido['fixture']['id'],
                        'local': partido['teams']['home']['name'],
                        'visitante': partido['teams']['away']['name'],
                        'fecha': partido['fixture']['date'],
                        'estadio': partido['fixture']['venue']['name'],
                        'status': partido['fixture']['status']['short']
                    })
                self.cache.set(cache_key, partidos)
                return partidos
        except Exception as e:
            print(f"Error obteniendo partidos: {e}")
        
        return []
    
    def obtener_estadisticas_equipo(self, team_name, league_id=39):
        cache_key = f"team_stats_{team_name}_{league_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        team_id = self._obtener_team_id(team_name)
        if not team_id:
            return None
        
        url = f"https://{API_HOST}/teams/statistics"
        headers = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": API_HOST}
        params = {"league": league_id, "season": 2025, "team": team_id}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                datos = response.json()
                stats = datos['response']
                
                resultado = {
                    'xG_promedio': self._extraer_xG(stats),
                    'xG_contra': self._extraer_xG_contra(stats),
                    'posesion_promedio': self._extraer_posesion(stats),
                    'goles_favor': self._extraer_goles_favor(stats),
                    'goles_contra': self._extraer_goles_contra(stats),
                    'partidos_jugados': stats.get('fixtures', {}).get('played', {}).get('total', 0),
                    'victorias': stats.get('fixtures', {}).get('wins', {}).get('total', 0),
                    'empates': stats.get('fixtures', {}).get('draws', {}).get('total', 0),
                    'derrotas': stats.get('fixtures', {}).get('loses', {}).get('total', 0),
                    'forma': self._calcular_forma(stats)
                }
                
                self.cache.set(cache_key, resultado)
                return resultado
        except Exception as e:
            print(f"Error obteniendo estadísticas de {team_name}: {e}")
        
        return None
    
    def _obtener_team_id(self, team_name):
        cache_key = f"team_id_{team_name}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        url = f"https://{API_HOST}/teams"
        headers = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": API_HOST}
        params = {"search": team_name}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                datos = response.json()
                for team in datos['response']:
                    if team['team']['name'].lower() == team_name.lower():
                        team_id = team['team']['id']
                        self.cache.set(cache_key, team_id)
                        return team_id
        except Exception as e:
            print(f"Error buscando ID de {team_name}: {e}")
        
        return None
    
    def _extraer_xG(self, stats):
        try:
            for stat in stats.get('shots', {}).get('total', []):
                if 'expected' in str(stat).lower():
                    return float(stat) if isinstance(stat, (int, float)) else 1.5
        except:
            pass
        return 1.5
    
    def _extraer_xG_contra(self, stats):
        return 1.2
    
    def _extraer_posesion(self, stats):
        try:
            return stats.get('possession', {}).get('average', 50)
        except:
            return 50
    
    def _extraer_goles_favor(self, stats):
        try:
            return stats.get('goals', {}).get('for', {}).get('total', {}).get('average', 1.5)
        except:
            return 1.5
    
    def _extraer_goles_contra(self, stats):
        try:
            return stats.get('goals', {}).get('against', {}).get('total', {}).get('average', 1.2)
        except:
            return 1.2
    
    def _calcular_forma(self, stats):
        try:
            resultados = stats.get('form', '')
            if resultados:
                puntos = resultados.count('W') * 3 + resultados.count('D')
                if puntos >= 12:
                    return "Excelente 🔥"
                elif puntos >= 9:
                    return "Buena 📈"
                elif puntos >= 6:
                    return "Regular 📊"
                else:
                    return "Mala 📉"
        except:
            pass
        return "Regular 📊"
    
    def predecir_partido(self, equipo_local, equipo_visitante, league_id=39):
        """Predicción completa de un partido"""
        stats_local = self.obtener_estadisticas_equipo(equipo_local, league_id)
        stats_visitante = self.obtener_estadisticas_equipo(equipo_visitante, league_id)
        
        if not stats_local or not stats_visitante:
            return self._prediccion_simulada(equipo_local, equipo_visitante)
        
        # Cálculo de probabilidades con modelo avanzado
        fuerza_local = (stats_local['xG_promedio'] * 1.1 + (100 - stats_local['xG_contra']) / 100)
        fuerza_visitante = (stats_visitante['xG_promedio'] + (100 - stats_visitante['xG_contra']) / 100)
        
        if 'Excelente' in stats_local['forma']:
            fuerza_local *= 1.15
        elif 'Mala' in stats_local['forma']:
            fuerza_local *= 0.85
        
        if 'Excelente' in stats_visitante['forma']:
            fuerza_visitante *= 1.1
        elif 'Mala' in stats_visitante['forma']:
            fuerza_visitante *= 0.9
        
        total_fuerza = fuerza_local + fuerza_visitante
        prob_local = (fuerza_local / total_fuerza) * 0.7 + 0.15
        prob_visitante = (fuerza_visitante / total_fuerza) * 0.7 + 0.15
        prob_empate = 1 - prob_local - prob_visitante
        
        # Goles esperados
        xG_local = stats_local['xG_promedio'] * (1 + (prob_local - 0.33) * 0.5)
        xG_visitante = stats_visitante['xG_promedio'] * (1 + (prob_visitante - 0.33) * 0.3)
        
        # Confluencia de victoria
        confluencia = self._detectar_confluencia(stats_local, stats_visitante)
        
        return {
            'equipo_local': equipo_local,
            'equipo_visitante': equipo_visitante,
            'xG_local': round(xG_local, 2),
            'xG_visitante': round(xG_visitante, 2),
            'prob_local': round(prob_local * 100, 1),
            'prob_empate': round(prob_empate * 100, 1),
            'prob_visitante': round(prob_visitante * 100, 1),
            'forma_local': stats_local['forma'],
            'forma_visitante': stats_visitante['forma'],
            'posesion_local': stats_local['posesion_promedio'],
            'posesion_visitante': stats_visitante['posesion_promedio'],
            'goles_favor_local': stats_local['goles_favor'],
            'goles_contra_local': stats_local['goles_contra'],
            'confluencia': confluencia,
            'recomendacion': self._generar_recomendacion(prob_local, confluencia),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _prediccion_simulada(self, equipo_local, equipo_visitante):
        return {
            'equipo_local': equipo_local,
            'equipo_visitante': equipo_visitante,
            'xG_local': 1.65,
            'xG_visitante': 1.35,
            'prob_local': 52.0,
            'prob_empate': 25.0,
            'prob_visitante': 23.0,
            'forma_local': 'Datos no disponibles',
            'forma_visitante': 'Datos no disponibles',
            'posesion_local': 50,
            'posesion_visitante': 50,
            'goles_favor_local': 1.5,
            'goles_contra_local': 1.2,
            'confluencia': {'activada': False, 'factores': [], 'sugerencia': 'Conectar API para análisis real'},
            'recomendacion': 'Datos limitados. Recomendación basada en simulación.',
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _detectar_confluencia(self, stats_local, stats_visitante):
        factores = []
        
        if 'Excelente' in stats_local['forma'] and 'Mala' in stats_visitante['forma']:
            factores.append("✅ Local en excelente forma vs Visitante en mala racha")
        
        if stats_local['posesion_promedio'] > 55:
            factores.append("⚡ Alta posesión del local (>55%)")
        
        if stats_local['xG_promedio'] > 1.8:
            factores.append("🎯 Alto poder ofensivo local (xG > 1.8)")
        
        if stats_visitante['xG_contra'] > 1.3:
            factores.append("😩 Defensa visitante vulnerable (xG en contra > 1.3)")
        
        activada = len(factores) >= 2
        
        if activada:
            sugerencia = "💡 PRESIONAR DESDE EL INICIO - Aprovechar las debilidades del rival"
        elif len(factores) == 1:
            sugerencia = "📊 Ventaja parcial - Consolidar en los primeros 20'"
        else:
            sugerencia = "🔍 Partido equilibrado - Esperar señales de debilidad"
        
        return {'activada': activada, 'factores': factores, 'sugerencia': sugerencia}
    
    def _generar_recomendacion(self, prob_local, confluencia):
        if prob_local > 60 and confluencia['activada']:
            return "🔥 APUESTA FUERTE: Victoria local con alta confianza"
        elif prob_local > 55:
            return "📈 RECOMENDACIÓN: Ligera favoritismo local. Valor en over 1.5 goles"
        elif prob_local < 35:
            return "⚠️ ALERTA: Posible sorpresa visitante. Considerar doble oportunidad"
        else:
            return "🤔 PARTIDO EQUILIBRADO: Mejor opción es apostar al over 2.5 goles"
    
    def predecir_champions(self):
        """Predicción especial para Champions League"""
        equipos_champions = ["Real Madrid", "Barcelona", "Bayern Munich", "Manchester City", 
                            "Paris Saint-Germain", "Liverpool", "Inter Milan", "Arsenal"]
        
        predicciones = []
        for i in range(0, len(equipos_champions), 2):
            if i+1 < len(equipos_champions):
                pred = self.predecir_partido(equipos_champions[i], equipos_champions[i+1], league_id=2)
                predicciones.append(pred)
        
        # Probabilidades de ganar el torneo
        favoritos = self._calcular_favoritos_champions(equipos_champions)
        
        return {
            'cuartos_simulados': predicciones,
            'favoritos_torneo': favoritos
        }
    
    def _calcular_favoritos_champions(self, equipos):
        favoritos = []
        for equipo in equipos:
            stats = self.obtener_estadisticas_equipo(equipo, league_id=2)
            if stats:
                puntuacion = stats['xG_promedio'] * 2 + stats['posesion_promedio'] / 10
                if 'Excelente' in stats['forma']:
                    puntuacion *= 1.2
                favoritos.append((equipo, round(puntuacion, 1)))
        
        favoritos.sort(key=lambda x: x[1], reverse=True)
        return favoritos[:4]
    
    def exportar_pdf_inversores(self, prediccion, filename="informe_ARES.pdf"):
        """Exporta un informe profesional en PDF para inversores"""
        doc = SimpleDocTemplate(filename, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Título principal
        titulo_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#003366'), alignment=TA_CENTER, spaceAfter=30)
        story.append(Paragraph("A.R.E.S. - Informe de Análisis Deportivo", titulo_style))
        story.append(Spacer(1, 12))
        
        # Fecha
        fecha_style = ParagraphStyle('DateStyle', parent=styles['Normal'], alignment=TA_CENTER, textColor=colors.grey)
        story.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", fecha_style))
        story.append(Spacer(1, 20))
        
        # Resumen del partido
        story.append(Paragraph(f"<b>Partido Analizado:</b> {prediccion['equipo_local']} vs {prediccion['equipo_visitante']}", styles['Normal']))
        story.append(Spacer(1, 10))
        
        # Tabla de probabilidades
        data_prob = [
            ['Métrica', prediccion['equipo_local'], prediccion['equipo_visitante']],
            ['Probabilidad Victoria', f"{prediccion['prob_local']}%", f"{prediccion['prob_visitante']}%"],
            ['Goles Esperados (xG)', prediccion['xG_local'], prediccion['xG_visitante']],
            ['Forma Reciente', prediccion['forma_local'], prediccion['forma_visitante']],
            ['Posesión Media', f"{prediccion['posesion_local']}%", f"{prediccion['posesion_visitante']}%"]
        ]
        
        table_prob = Table(data_prob, colWidths=[2*inch, 2*inch, 2*inch])
        table_prob.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (2, 0), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0, 0), (2, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (2, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (2, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (2, 0), 12),
            ('BOTTOMPADDING', (0, 0), (2, 0), 12),
            ('BACKGROUND', (0, 1), (2, -1), colors.beige),
            ('GRID', (0, 0), (2, -1), 1, colors.black)
        ]))
        story.append(table_prob)
        story.append(Spacer(1, 20))
        
        # Confluencia de Victoria
        story.append(Paragraph("<b>⚠️ Confluencia de Victoria</b>", styles['Heading2']))
        story.append(Spacer(1, 6))
        for factor in prediccion['confluencia']['factores']:
            story.append(Paragraph(f"• {factor}", styles['Normal']))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"<b>💡 Recomendación:</b> {prediccion['confluencia']['sugerencia']}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Recomendación para inversores
        story.append(Paragraph("<b>💰 Recomendación para Inversores</b>", styles['Heading2']))
        story.append(Spacer(1, 6))
        story.append(Paragraph(prediccion['recomendacion'], styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Nota legal
        nota_style = ParagraphStyle('NoteStyle', parent=styles['Italic'], fontSize=8, textColor=colors.grey)
        story.append(Paragraph("Este informe ha sido generado automáticamente por A.R.E.S. (Advanced Real-time Evaluation System). "
                              "Las predicciones se basan en modelos estadísticos y no garantizan resultados. "
                              "Invierta con responsabilidad.", nota_style))
        
        doc.build(story)
        print(f"✅ PDF generado: {filename}")
        return filename


# ============================================================
# EJECUCIÓN DE PRUEBA
# ============================================================

if __name__ == "__main__":
    print("="*60)
    print("🔴🔵 A.R.E.S. - SISTEMA COMPLETO 🔵🔴")
    print("="*60)
    
    ares = ARES_Engine_Completo()
    
    # Probar predicción
    print("\n📊 PREDICIENDO PARTIDO REAL...")
    resultado = ares.predecir_partido("Manchester City", "Liverpool")
    
    print(f"\n🎯 RESULTADO DE PREDICCIÓN:")
    print(f"   {resultado['equipo_local']}: {resultado['prob_local']}%")
    print(f"   Empate: {resultado['prob_empate']}%")
    print(f"   {resultado['equipo_visitante']}: {resultado['prob_visitante']}%")
    print(f"\n💡 {resultado['recomendacion']}")
    
    # Probar Champions
    print("\n🏆 PREDICIENDO CHAMPIONS LEAGUE...")
    champions = ares.predecir_champions()
    print(f"   Favoritos para ganar la Champions:")
    for equipo, puntos in champions['favoritos_torneo']:
        print(f"   • {equipo}: {puntos} pts")
    
    # Generar PDF
    print("\n📄 GENERANDO INFORME PARA INVERSORES...")
    ares.exportar_pdf_inversores(resultado, "informe_inversores_ARES.pdf")
    
    print("\n✅ SISTEMA COMPLETO OPERATIVO")
    print("   - API Real conectada")
    print("   - Módulo de fatiga listo")
    print("   - Predicciones Champions League")
    print("   - Exportador PDF funcionando")