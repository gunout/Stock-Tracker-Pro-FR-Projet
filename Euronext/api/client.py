# src/api/client.py
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import streamlit as st
from src.config.settings import APIConfig

class FinancialAPIClient:
    """Client API avec gestion intelligente des rate limits"""
    
    def __init__(self):
        self.session = self._create_session()
        self.base_url = APIConfig.BASE_URL
        
    def _create_session(self):
        """Crée une session avec retry strategy"""
        session = requests.Session()
        
        # Configuration des retries
        retry_strategy = Retry(
            total=APIConfig.MAX_RETRIES,
            backoff_factor=APIConfig.BACKOFF_FACTOR,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Headers par défaut
        session.headers.update({
            "User-Agent": "Streamlit-Finance-App/1.0",
            "Accept": "application/json"
        })
        
        if APIConfig.API_KEY:
            session.headers.update({"Authorization": f"Bearer {APIConfig.API_KEY}"})
            
        return session
    
    @st.cache_data(ttl=APIConfig.CACHE_TTL, show_spinner=False)
    def get_stock_data(_self, symbol: str):
        """Récupère les données d'une action avec cache"""
        try:
            response = _self.session.get(
                f"{_self.base_url}/stock/{symbol}",
                timeout=APIConfig.TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                st.warning(f"⚠️ Rate limit atteint pour {symbol}")
                return None
            else:
                st.error(f"Erreur {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            st.error(f"Timeout pour {symbol}")
            return None
        except requests.exceptions.ConnectionError:
            st.error(f"Erreur de connexion pour {symbol}")
            return None
        except Exception as e:
            st.error(f"Erreur inattendue: {str(e)}")
            return None
    
    def get_multiple_stocks(self, symbols: list):
        """Récupère plusieurs actions avec gestion intelligente"""
        results = {}
        
        with st.spinner("Chargement des données..."):
            progress_bar = st.progress(0)
            
            for i, symbol in enumerate(symbols):
                # Récupération des données
                data = self.get_stock_data(symbol)
                if data:
                    results[symbol] = data
                
                # Mise à jour progression
                progress_bar.progress((i + 1) / len(symbols))
                
                # Pause entre les requêtes
                if i < len(symbols) - 1:
                    time.sleep(1)  # Évite de bombarder l'API
                    
        return results