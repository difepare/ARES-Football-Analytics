# ============================================================
# SISTEMA DE PREDICCIÓN DE TARJETAS
# ============================================================

class SistemaTarjetas:
    """
    Predice la probabilidad de que un jugador reciba tarjeta amarilla/roja
    basado en: historial, posición, intensidad, minutos jugados
    """
    
    def __init__(self):
        # Factor base por posición (defensas y mediocampistas tienen más riesgo)
        self.factor_posicion = {
            Posicion.DELANTERO: 0.6,
            Posicion.MEDIOCAMPISTA: 1.0,
            Posicion.DEFENSA_CENTRAL: 1.2,
            Posicion.LATERAL: 1.1,
            Posicion.PORTERO: 0.2,
        }
        
        # Propensión base por estilo de juego
        self.propension_base = {
            "Baja": 0.15,
            "Media": 0.35,
            "Alta": 0.55,
        }
    
    def predecir_tarjeta_amarilla(self, jugador, minutos_jugados=90, intensidad_partido=75):
        """
        Calcula probabilidad de recibir tarjeta amarilla en el próximo partido
        """
        datos = JUGADORES_DISPONIBLES.get(jugador.nombre, {})
        propension = datos.get("propension_tarjetas", "Media")
        
        prob_base = self.propension_base.get(propension, 0.35)
        
        # Ajustes
        prob_posicion = self.factor_posicion.get(jugador.posicion, 0.8)
        prob_intensidad = intensidad_partido / 100  # Mayor intensidad = más faltas
        prob_minutos = min(1.0, minutos_jugados / 90)  # Más minutos = más exposición
        
        # Factor fatiga (jugador cansado comete más faltas)
        riesgo_fatiga = jugador.minutos_jugados_7dias / 500 if jugador.minutos_jugados_7dias > 0 else 0
        prob_fatiga = min(0.4, riesgo_fatiga * 0.3)
        
        # Cálculo final
        probabilidad = prob_base * prob_posicion * (0.7 + prob_intensidad * 0.3) * prob_minutos + prob_fatiga
        probabilidad = min(0.85, probabilidad)  # Máximo 85%
        
        # Determinar nivel de riesgo
        if probabilidad >= 0.5:
            nivel = "Alto 🔴"
            sugerencia = "Riesgo alto de tarjeta. Recomendar cuidado en entradas."
        elif probabilidad >= 0.3:
            nivel = "Medio 🟡"
            sugerencia = "Riesgo moderado. Evitar faltas tontas."
        else:
            nivel = "Bajo 🟢"
            sugerencia = "Riesgo bajo. Jugar con normalidad."
        
        return {
            "probabilidad": round(probabilidad * 100, 1),
            "nivel": nivel,
            "sugerencia": sugerencia,
            "factores": {
                "propension": propension,
                "posicion": jugador.posicion.value,
                "intensidad": intensidad_partido,
                "fatiga": round(prob_fatiga * 100, 1)
            }
        }
    
    def predecir_tarjeta_roja(self, jugador, amarillas_recibidas=0):
        """
        Calcula probabilidad de tarjeta roja (directa o doble amarilla)
        """
        amarilla_pred = self.predecir_tarjeta_amarilla(jugador)
        
        # Probabilidad base de roja (mucho más baja)
        prob_base = 0.08
        
        # Si ya tiene amarillas, aumenta riesgo de doble amarilla
        if amarillas_recibidas >= 1:
            prob_base += 0.15
        if amarillas_recibidas >= 2:
            prob_base += 0.25
        
        # Ajuste por propensión
        datos = JUGADORES_DISPONIBLES.get(jugador.nombre, {})
        propension = datos.get("propension_tarjetas", "Media")
        if propension == "Alta":
            prob_base *= 1.5
        elif propension == "Baja":
            prob_base *= 0.7
        
        # Ajuste por posición (defensas más propensos a rojas)
        prob_base *= self.factor_posicion.get(jugador.posicion, 0.8)
        
        probabilidad = min(0.35, prob_base)
        
        if probabilidad >= 0.2:
            nivel = "Alto 🔴"
            sugerencia = "Riesgo significativo de expulsión. Extremar precaución."
        elif probabilidad >= 0.1:
            nivel = "Medio 🟡"
            sugerencia = "Riesgo moderado de tarjeta roja."
        else:
            nivel = "Bajo 🟢"
            sugerencia = "Riesgo bajo de expulsión."
        
        return {
            "probabilidad": round(probabilidad * 100, 1),
            "nivel": nivel,
            "sugerencia": sugerencia
        }
    
    def riesgo_disciplinario_total(self, jugador, minutos_jugados=90):
        """
        Calcula el riesgo disciplinario total (amarillas + rojas)
        """
        amarilla = self.predecir_tarjeta_amarilla(jugador, minutos_jugados)
        roja = self.predecir_tarjeta_roja(jugador)
        
        # Puntaje de riesgo (0-100)
        puntaje = (amarilla["probabilidad"] * 0.6) + (roja["probabilidad"] * 2)
        puntaje = min(100, puntaje)
        
        if puntaje >= 60:
                    nivel_total = "Alto 🔴"
            recomendacion = "⚠️ ALERTA: Riesgo disciplinario elevado. Considerar sustitución preventiva."
        elif puntaje >= 35:
            nivel_total = "Medio 🟡"
            recomendacion = "📊 Riesgo disciplinario moderado. Monitorear faltas."
        else:
            nivel_total = "Bajo 🟢"
            recomendacion = "✅ Riesgo disciplinario bajo."
        
        return {
            "puntaje": round(puntaje, 1),
            "nivel": nivel_total,
            "recomendacion": recomendacion,
            "amarilla": amarilla,
            "roja": roja
        }

# Instanciar el sistema
sistema_tarjetas = SistemaTarjetas()