# app.py - Version avec APIs réelles uniquement (pas de simulation)
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
import time
import sqlite3
import requests
import os
from pathlib import Path
from streamlit.components.v1 import html
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import ta
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import warnings
warnings.filterwarnings('ignore')

# ==================== CONFIGURATION DE LA PAGE ====================
st.set_page_config(
    page_title="Dashboard Financier Pro MC.PA",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== INITIALISATION SESSION STATE ====================
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()
if 'data_history' not in st.session_state:
    st.session_state.data_history = []
if 'update_counter' not in st.session_state:
    st.session_state.update_counter = 0
if 'current_symbols' not in st.session_state:
    st.session_state.current_symbols = ["MC.PA"]
if 'paused' not in st.session_state:
    st.session_state.paused = False
if 'alerts' not in st.session_state:
    st.session_state.alerts = []
if 'api_source' not in st.session_state:
    st.session_state.api_source = "Yahoo Finance"  # Changé en Yahoo Finance par défaut
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = False
if 'comparison_mode' not in st.session_state:
    st.session_state.comparison_mode = False
if 'favorites' not in st.session_state:
    st.session_state.favorites = []
if 'ml_model_trained' not in st.session_state:
    st.session_state.ml_model_trained = False
if 'ml_predictions' not in st.session_state:
    st.session_state.ml_predictions = {}

# ==================== CONFIGURATION DES CHEMINS ====================
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "stock_data.db"
EXPORT_DIR = BASE_DIR / "exports"
MODELS_DIR = BASE_DIR / "models"
EXPORT_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

# ==================== API RÉELLES UNIQUEMENT ====================
class RealAPIManager:
    """Gestionnaire d'APIs financières réelles uniquement"""
    
    @staticmethod
    def get_yahoo_finance_data(symbol):
        """Récupère les données via Yahoo Finance"""
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                    result = data['chart']['result'][0]
                    meta = result.get('meta', {})
                    
                    price = meta.get('regularMarketPrice', 0)
                    previous_close = meta.get('previousClose', price)
                    change = ((price - previous_close) / previous_close) * 100 if previous_close > 0 else 0
                    
                    return {
                        'success': True,
                        'price': round(price, 2),
                        'change': round(change, 2),
                        'volume': meta.get('regularMarketVolume', 0),
                        'source': 'Yahoo Finance',
                        'currency': meta.get('currency', 'EUR'),
                        'timestamp': datetime.now().isoformat()
                    }
            return {'success': False, 'error': 'No data available'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_alpha_vantage_data(symbol, api_key):
        """Récupère les données via Alpha Vantage"""
        if not api_key:
            return {'success': False, 'error': 'API key required'}
        
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                quote = data.get('Global Quote', {})
                
                if quote:
                    change_percent = quote.get('10. change percent', '0%').replace('%', '')
                    return {
                        'success': True,
                        'price': float(quote.get('05. price', 0)),
                        'change': float(change_percent),
                        'volume': int(quote.get('06. volume', 0)),
                        'source': 'Alpha Vantage',
                        'timestamp': datetime.now().isoformat()
                    }
            return {'success': False, 'error': 'No data available'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_historical_data(symbol, api_source="yahoo", api_key=None):
        """Récupère les données historiques"""
        try:
            if api_source == "yahoo":
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
                params = {'range': '1mo', 'interval': '1d'}
            else:  # Alpha Vantage
                if not api_key:
                    return None
                url = "https://www.alphavantage.co/query"
                params = {
                    'function': 'TIME_SERIES_DAILY',
                    'symbol': symbol,
                    'apikey': api_key,
                    'outputsize': 'compact'
                }
            
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if api_source == "yahoo":
                    if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                        result = data['chart']['result'][0]
                        timestamps = result.get('timestamp', [])
                        quotes = result.get('indicators', {}).get('quote', [{}])[0]
                        
                        if timestamps and quotes:
                            df = pd.DataFrame({
                                'date': pd.to_datetime(timestamps, unit='s'),
                                'open': quotes.get('open', []),
                                'high': quotes.get('high', []),
                                'low': quotes.get('low', []),
                                'close': quotes.get('close', []),
                                'volume': quotes.get('volume', [])
                            })
                            return df.dropna()
                else:
                    # Alpha Vantage format
                    time_series = data.get('Time Series (Daily)', {})
                    if time_series:
                        records = []
                        for date, values in time_series.items():
                            records.append({
                                'date': pd.to_datetime(date),
                                'open': float(values['1. open']),
                                'high': float(values['2. high']),
                                'low': float(values['3. low']),
                                'close': float(values['4. close']),
                                'volume': int(values['5. volume'])
                            })
                        df = pd.DataFrame(records)
                        return df.sort_values('date')
            
            return None
        except Exception as e:
            st.error(f"Erreur historique: {e}")
            return None

# ==================== GÉNÉRATION DE DONNÉES UNIQUEMENT API ====================
def get_live_data(symbol, api_source="Yahoo Finance", api_key=""):
    """Récupère les données en direct UNIQUEMENT depuis les APIs réelles"""
    
    if api_source == "Yahoo Finance":
        result = RealAPIManager.get_yahoo_finance_data(symbol)
        if result['success']:
            # Ajouter les métriques par défaut
            result['pe_ratio'] = 0
            result['dividend'] = 0
            result['dividend_yield'] = 0
            return result
    
    elif api_source == "Alpha Vantage" and api_key:
        result = RealAPIManager.get_alpha_vantage_data(symbol, api_key)
        if result['success']:
            result['pe_ratio'] = 0
            result['dividend'] = 0
            result['dividend_yield'] = 0
            return result
    
    # Si aucune API ne fonctionne, afficher une erreur
    st.error(f"❌ Impossible de récupérer les données pour {symbol}. Vérifiez votre connexion ou votre clé API.")
    return None

# ==================== INDICATEURS TECHNIQUES ====================
class TechnicalIndicators:
    """Calcul des indicateurs techniques avancés"""
    
    @staticmethod
    def calculate_all(df):
        """Calcule tous les indicateurs techniques"""
        if df is None or df.empty:
            return None
            
        df = df.copy()
        
        # RSI
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        
        # MACD
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_diff'] = macd.macd_diff()
        
        # Bollinger Bands
        bollinger = ta.volatility.BollingerBands(df['close'])
        df['bb_upper'] = bollinger.bollinger_hband()
        df['bb_middle'] = bollinger.bollinger_mavg()
        df['bb_lower'] = bollinger.bollinger_lband()
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # Moyennes mobiles
        df['sma_20'] = ta.trend.sma_indicator(df['close'], window=20)
        df['sma_50'] = ta.trend.sma_indicator(df['close'], window=50)
        
        return df

# ==================== GRAPHIQUES ====================
def create_advanced_chart(df, symbol):
    """Crée un graphique avancé avec indicateurs"""
    
    if df is None or df.empty:
        return None
    
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.5, 0.25, 0.25],
        subplot_titles=(f"{symbol} - Prix", "Volume", "RSI")
    )
    
    # Prix avec chandeliers
    fig.add_trace(go.Candlestick(
        x=df['date'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Prix',
        showlegend=False
    ), row=1, col=1)
    
    # Volume
    colors = ['red' if df['close'].iloc[i] < df['open'].iloc[i] else 'green' 
              for i in range(len(df))]
    
    fig.add_trace(go.Bar(
        x=df['date'],
        y=df['volume'],
        name='Volume',
        marker_color=colors,
        showlegend=False
    ), row=2, col=1)
    
    # RSI
    if 'rsi' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['rsi'],
            line=dict(color='purple'),
            name='RSI',
            showlegend=False
        ), row=3, col=1)
        
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
    
    fig.update_layout(
        height=800,
        template='plotly_white',
        showlegend=False,
        hovermode='x unified'
    )
    
    return fig

# ==================== BASE DE DONNÉES ====================
class DatabaseManager:
    """Gestionnaire de base de données SQLite"""
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    price REAL NOT NULL,
                    change REAL,
                    volume INTEGER,
                    source TEXT,
                    UNIQUE(symbol, timestamp)
                )
            ''')
            
            conn.commit()
            conn.close()
            st.session_state.db_initialized = True
            
        except Exception as e:
            st.error(f"Erreur BDD: {e}")
    
    def save_price(self, symbol, data):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO stock_prices 
                (symbol, timestamp, price, change, volume, source)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                symbol,
                datetime.now().isoformat(),
                data.get('price', 0),
                data.get('change', 0),
                data.get('volume', 0),
                data.get('source', 'API')
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            return False

# ==================== INTERFACE PRINCIPALE ====================
def main():
    st.title("📊 Dashboard Financier Pro - Données Réelles Uniquement")
    st.caption("APIs: Yahoo Finance | Alpha Vantage")
    
    db = DatabaseManager()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        st.subheader("📈 Symboles")
        symbol = st.selectbox(
            "Symbole",
            options=["MC.PA", "RMS.PA", "KER.PA", "CDI.PA", "AI.PA", "OR.PA", "BNP.PA", "SAN.PA", "TOT.PA"],
            index=0
        )
        
        st.subheader("🔌 Source API")
        api_source = st.radio(
            "API",
            ["Yahoo Finance", "Alpha Vantage"],
            index=0
        )
        
        api_key = ""
        if api_source == "Alpha Vantage":
            api_key = st.text_input("Clé API Alpha Vantage", type="password")
            if not api_key:
                st.warning("Clé API requise pour Alpha Vantage")
        
        refresh_rate = st.slider("Fréquence (s)", 5, 60, 10)
        
        if st.button("🔄 Rafraîchir maintenant"):
            st.rerun()
    
    # Récupérer les données réelles
    with st.spinner(f"Chargement des données pour {symbol}..."):
        data = get_live_data(symbol, api_source, api_key)
    
    if data:
        st.session_state.update_counter += 1
        st.session_state.last_update = datetime.now()
        
        # Sauvegarder dans BDD
        db.save_price(symbol, data)
        
        # Métriques principales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Cours", f"{data['price']:.2f} €", f"{data['change']:+.2f}%")
        with col2:
            st.metric("Volume", f"{data['volume']:,}")
        with col3:
            st.metric("Source", data['source'])
        with col4:
            st.metric("Dernière MAJ", datetime.now().strftime('%H:%M:%S'))
        
        # Récupérer données historiques pour les graphiques
        hist_source = "yahoo" if api_source == "Yahoo Finance" else "alpha"
        hist_data = RealAPIManager.get_historical_data(symbol, hist_source, api_key)
        
        if hist_data is not None and not hist_data.empty:
            # Calculer indicateurs
            hist_data_with_indicators = TechnicalIndicators.calculate_all(hist_data)
            
            # Graphique avancé
            st.subheader("📈 Analyse technique")
            fig = create_advanced_chart(hist_data_with_indicators, symbol)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            
            # Dernières valeurs
            st.subheader("📊 Dernières valeurs")
            st.dataframe(
                hist_data[['date', 'open', 'high', 'low', 'close', 'volume']].tail(10),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("Données historiques non disponibles")
    
    else:
        st.error("❌ Impossible de charger les données. Vérifiez :")
        st.info("""
        - Votre connexion internet
        - Le symbole est correct (ex: MC.PA, RMS.PA)
        - Votre clé API Alpha Vantage (si utilisée)
        - Les serveurs de l'API sont disponibles
        """)
    
    # Auto-refresh
    if not st.session_state.get('paused', False):
        time.sleep(refresh_rate)
        st.rerun()

if __name__ == "__main__":
    main()
