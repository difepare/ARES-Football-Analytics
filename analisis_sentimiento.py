# analisis_sentimiento.py
import tweepy
from textblob import TextBlob
import time

class AnalisisSentimiento:
    def __init__(self, bearer_token=None):
        self.bearer_token = bearer_token
        self.client = None
        if bearer_token:
            self.client = tweepy.Client(bearer_token=bearer_token)
    
    def analizar_sentimiento_jugador(self, jugador_nombre, num_tweets=50):
        """
        Analiza el sentimiento de Twitter hacia un jugador
        Retorna: positivo, negativo, neutral (porcentajes)
        """
        if not self.client:
            return {"positivo": 50, "negativo": 25, "neutral": 25, "presion": "MEDIA"}
        
        try:
            query = f"{jugador_nombre} lang:es -is:retweet"
            tweets = self.client.search_recent_tweets(query=query, max_results=num_tweets)
            
            if not tweets.data:
                return {"positivo": 50, "negativo": 25, "neutral": 25, "presion": "MEDIA"}
            
            positivos = 0
            negativos = 0
            neutrales = 0
            
            for tweet in tweets.data:
                analysis = TextBlob(tweet.text)
                if analysis.sentiment.polarity > 0.1:
                    positivos += 1
                elif analysis.sentiment.polarity < -0.1:
                    negativos += 1
                else:
                    neutrales += 1
            
            total = positivos + negativos + neutrales
            if total > 0:
                pct_pos = (positivos / total) * 100
                pct_neg = (negativos / total) * 100
                pct_neu = (neutrales / total) * 100
                
                # Determinar nivel de presión
                if pct_neg > 40:
                    presion = "ALTA 🔴"
                elif pct_neg > 25:
                    presion = "MEDIA 🟡"
                else:
                    presion = "BAJA 🟢"
                
                return {"positivo": round(pct_pos), "negativo": round(pct_neg), 
                       "neutral": round(pct_neu), "presion": presion}
        except Exception as e:
            print(f"Error en análisis de sentimiento: {e}")
        
        return {"positivo": 50, "negativo": 25, "neutral": 25, "presion": "MEDIA"}