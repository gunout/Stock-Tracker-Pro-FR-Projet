# api/client.py - Version améliorée
import requests
import streamlit as st
from config.settings import APIConfig

class FinancialAPIClient:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = APIConfig.BASE_URL
    
    @st.cache_data(ttl=300)  # Cache 5 minutes
    def get_stock_data(_self, symbol):
        """Récupère les données d'une action"""
        try:
            # Exemple avec Yahoo Finance (gratuit)
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            response = _self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Extraire les données pertinentes
                result = data['chart']['result'][0]
                meta = result['meta']
                
                return {
                    'price': meta['regularMarketPrice'],
                    'change': meta['regularMarketChangePercent'],
                    'volume': meta['regularMarketVolume'],
                    'currency': meta['currency'],
                    'symbol': symbol
                }
            else:
                st.warning(f"API indisponible, utilisation des données simulées")
                return _self._get_mock_data(symbol)
                
        except Exception as e:
            st.warning(f"Erreur API: {e}, utilisation des données simulées")
            return _self._get_mock_data(symbol)
    
    def _get_mock_data(self, symbol):
        """Données simulées de secours"""
        mock_data = {
            'MC.PA': {'price': 519.60, 'change': -0.93, 'volume': 26164},
            'RMS.PA': {'price': 2450.00, 'change': 0.85, 'volume': 15000},
            'KER.PA': {'price': 320.00, 'change': -1.20, 'volume': 50000}
        }
        return mock_data.get(symbol, {'price': 100.00, 'change': 0, 'volume': 10000})
