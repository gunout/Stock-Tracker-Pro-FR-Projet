# api/client.py - Version avec Yahoo Finance
import requests
import streamlit as st
from config.settings import APIConfig

class FinancialAPIClient:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://query1.finance.yahoo.com"
    
    @st.cache_data(ttl=300)  # Cache 5 minutes
    def get_stock_data(_self, symbol):
        """Récupère les données d'une action via Yahoo Finance"""
        try:
            # URL pour les données en temps réel
            url = f"{_self.base_url}/v8/finance/chart/{symbol}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = _self.session.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier que les données sont valides
                if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                    result = data['chart']['result'][0]
                    meta = result.get('meta', {})
                    
                    # Extraire les données
                    price = meta.get('regularMarketPrice', 0)
                    previous_close = meta.get('previousClose', price)
                    
                    if previous_close > 0:
                        change = ((price - previous_close) / previous_close) * 100
                    else:
                        change = 0
                    
                    return {
                        'price': price,
                        'change': change,
                        'volume': meta.get('regularMarketVolume', 0),
                        'currency': meta.get('currency', 'EUR'),
                        'symbol': symbol,
                        'source': 'Yahoo Finance'
                    }
            
            # Si erreur, retourner None (utilisera les données simulées)
            return None
            
        except Exception as e:
            st.warning(f"Erreur Yahoo Finance: {e}")
            return None
    
    def get_historical_data(_self, symbol, period="3mo"):
        """Récupère les données historiques"""
        try:
            url = f"{_self.base_url}/v8/finance/chart/{symbol}"
            params = {
                'range': period,
                'interval': '1d'
            }
            
            response = _self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                    result = data['chart']['result'][0]
                    
                    # Extraire les timestamps et prix
                    timestamps = result.get('timestamp', [])
                    quotes = result.get('indicators', {}).get('quote', [{}])[0]
                    
                    if timestamps and quotes:
                        import pandas as pd
                        import numpy as np
                        
                        df = pd.DataFrame({
                            'Date': pd.to_datetime(timestamps, unit='s'),
                            'Open': quotes.get('open', []),
                            'High': quotes.get('high', []),
                            'Low': quotes.get('low', []),
                            'Close': quotes.get('close', []),
                            'Volume': quotes.get('volume', [])
                        })
                        
                        # Nettoyer les données
                        df = df.dropna()
                        return df
            
            return None
            
        except Exception as e:
            st.warning(f"Erreur données historiques: {e}")
            return None
