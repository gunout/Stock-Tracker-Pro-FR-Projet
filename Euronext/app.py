# app.py - Version avec comparaison et données réelles uniquement
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
    st.session_state.api_source = "Yahoo Finance"
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = False
if 'comparison_mode' not in st.session_state:
    st.session_state.comparison_mode = False  # Mode comparaison
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

# ==================== API RÉELLES ====================
class RealAPIManager:
    """Gestionnaire d'APIs financières réelles"""
    
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
                        'symbol': symbol,
                        'price': round(price, 2),
                        'change': round(change, 2),
                        'volume': meta.get('regularMarketVolume', 0),
                        'source': 'Yahoo Finance',
                        'currency': meta.get('currency', 'EUR'),
                        'timestamp': datetime.now().isoformat()
                    }
            return {'success': False, 'error': 'No data available', 'symbol': symbol}
        except Exception as e:
            return {'success': False, 'error': str(e), 'symbol': symbol}
    
    @staticmethod
    def get_alpha_vantage_data(symbol, api_key):
        """Récupère les données via Alpha Vantage"""
        if not api_key:
            return {'success': False, 'error': 'API key required', 'symbol': symbol}
        
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
                        'symbol': symbol,
                        'price': float(quote.get('05. price', 0)),
                        'change': float(change_percent),
                        'volume': int(quote.get('06. volume', 0)),
                        'source': 'Alpha Vantage',
                        'timestamp': datetime.now().isoformat()
                    }
            return {'success': False, 'error': 'No data available', 'symbol': symbol}
        except Exception as e:
            return {'success': False, 'error': str(e), 'symbol': symbol}
    
    @staticmethod
    def get_historical_data(symbol, api_source="yahoo", api_key=None):
        """Récupère les données historiques"""
        try:
            if api_source == "yahoo" or api_source == "Yahoo Finance":
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
                params = {'range': '1mo', 'interval': '1d'}
                headers = {'User-Agent': 'Mozilla/5.0'}
                
                response = requests.get(url, params=params, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
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
            
            elif api_source == "alpha" or api_source == "Alpha Vantage":
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
            st.error(f"Erreur historique {symbol}: {e}")
            return None

# ==================== RÉCUPÉRATION DONNÉES ====================
def get_live_data(symbol, api_source="Yahoo Finance", api_key=""):
    """Récupère les données en direct depuis les APIs réelles"""
    
    if api_source == "Yahoo Finance":
        result = RealAPIManager.get_yahoo_finance_data(symbol)
        return result
    
    elif api_source == "Alpha Vantage" and api_key:
        result = RealAPIManager.get_alpha_vantage_data(symbol, api_key)
        return result
    
    return {'success': False, 'error': 'No API selected', 'symbol': symbol}

def get_multiple_symbols_data(symbols, api_source, api_key):
    """Récupère les données pour plusieurs symboles"""
    results = {}
    failed = []
    
    for symbol in symbols:
        data = get_live_data(symbol, api_source, api_key)
        if data['success']:
            results[symbol] = data
        else:
            failed.append(symbol)
    
    return results, failed

# ==================== INDICATEURS TECHNIQUES ====================
class TechnicalIndicators:
    @staticmethod
    def calculate_all(df):
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
        
        # Moyennes mobiles
        df['sma_20'] = ta.trend.sma_indicator(df['close'], window=20)
        df['sma_50'] = ta.trend.sma_indicator(df['close'], window=50)
        
        return df

# ==================== GRAPHIQUES ====================
def create_single_chart(df, symbol):
    """Graphique pour un seul symbole"""
    if df is None or df.empty:
        return None
    
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.5, 0.25, 0.25],
        subplot_titles=(f"{symbol} - Prix", "Volume", "RSI")
    )
    
    # Prix
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

def create_comparison_chart(symbols_data):
    """Graphique de comparaison pour plusieurs symboles"""
    fig = go.Figure()
    
    for symbol, data in symbols_data.items():
        # Récupérer données historiques pour normalisation
        hist_data = RealAPIManager.get_historical_data(symbol)
        
        if hist_data is not None and not hist_data.empty:
            # Normaliser à 100 pour comparaison
            base_price = hist_data['close'].iloc[0]
            normalized_prices = (hist_data['close'] / base_price) * 100
            
            fig.add_trace(go.Scatter(
                x=hist_data['date'],
                y=normalized_prices,
                mode='lines',
                name=symbol,
                line=dict(width=2)
            ))
    
    fig.update_layout(
        title="Comparaison des performances (Base 100)",
        xaxis_title="Date",
        yaxis_title="Performance (%)",
        hovermode='x unified',
        template='plotly_white',
        height=500
    )
    
    return fig

# ==================== BASE DE DONNÉES ====================
class DatabaseManager:
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
    st.title("📊 Dashboard Financier Pro - Données Réelles")
    st.caption("Mode Comparaison inclus • Yahoo Finance • Alpha Vantage")
    
    db = DatabaseManager()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Mode comparaison
        comparison_mode = st.checkbox("📊 Mode comparaison", value=st.session_state.comparison_mode)
        st.session_state.comparison_mode = comparison_mode
        
        # Symboles
        all_symbols = ["MC.PA", "RMS.PA", "KER.PA", "CDI.PA", "AI.PA", "OR.PA", "BNP.PA", "SAN.PA", "TOT.PA"]
        
        if comparison_mode:
            st.subheader("📈 Symboles à comparer")
            symbols = st.multiselect(
                "Sélectionnez 2 à 4 symboles",
                all_symbols,
                default=st.session_state.current_symbols[:2] if len(st.session_state.current_symbols) >= 2 else ["MC.PA", "RMS.PA"],
                max_selections=4
            )
            if len(symbols) < 2:
                st.warning("Sélectionnez au moins 2 symboles")
                symbols = ["MC.PA", "RMS.PA"]
            st.session_state.current_symbols = symbols
        else:
            st.subheader("📈 Symbole unique")
            symbol = st.selectbox(
                "Sélectionnez un symbole",
                all_symbols,
                index=all_symbols.index(st.session_state.current_symbols[0]) if st.session_state.current_symbols else 0
            )
            st.session_state.current_symbols = [symbol]
        
        # Source API
        st.subheader("🔌 Source API")
        api_source = st.radio(
            "API",
            ["Yahoo Finance", "Alpha Vantage"],
            index=0
        )
        st.session_state.api_source = api_source
        
        api_key = ""
        if api_source == "Alpha Vantage":
            api_key = st.text_input("Clé API Alpha Vantage", type="password", value=st.session_state.api_key)
            st.session_state.api_key = api_key
            if not api_key:
                st.warning("Clé API requise pour Alpha Vantage")
        
        # Rafraîchissement
        refresh_rate = st.slider("Fréquence (s)", 5, 60, 10)
        
        if st.button("🔄 Rafraîchir maintenant"):
            st.rerun()
        
        st.markdown("---")
        st.metric("Mises à jour", st.session_state.update_counter)
    
    # ==================== CORPS PRINCIPAL ====================
    
    if st.session_state.comparison_mode:
        # MODE COMPARAISON
        st.subheader("📊 Mode Comparaison Multi-symboles")
        
        with st.spinner(f"Chargement des données pour {len(st.session_state.current_symbols)} symboles..."):
            results, failed = get_multiple_symbols_data(
                st.session_state.current_symbols,
                st.session_state.api_source,
                st.session_state.api_key
            )
        
        if failed:
            st.error(f"❌ Impossible de charger: {', '.join(failed)}")
        
        if results:
            st.session_state.update_counter += 1
            
            # Graphique de comparaison
            fig_comp = create_comparison_chart(results)
            st.plotly_chart(fig_comp, use_container_width=True)
            
            # Tableau comparatif
            st.subheader("📋 Comparaison en direct")
            
            comparison_data = []
            for symbol, data in results.items():
                comparison_data.append({
                    "Symbole": symbol,
                    "Prix": f"{data['price']:.2f} €",
                    "Variation": f"{data['change']:+.2f}%",
                    "Volume": f"{data['volume']:,}",
                    "Source": data['source']
                })
            
            df = pd.DataFrame(comparison_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Sauvegarde BDD
            for symbol, data in results.items():
                db.save_price(symbol, data)
    
    else:
        # MODE SIMPLE
        symbol = st.session_state.current_symbols[0]
        
        with st.spinner(f"Chargement des données pour {symbol}..."):
            data = get_live_data(symbol, st.session_state.api_source, st.session_state.api_key)
        
        if data['success']:
            st.session_state.update_counter += 1
            st.session_state.last_update = datetime.now()
            
            # Sauvegarde BDD
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
            
            # Données historiques
            hist_source = "yahoo" if st.session_state.api_source == "Yahoo Finance" else "alpha"
            hist_data = RealAPIManager.get_historical_data(
                symbol, 
                hist_source, 
                st.session_state.api_key if st.session_state.api_source == "Alpha Vantage" else None
            )
            
            if hist_data is not None and not hist_data.empty:
                # Indicateurs techniques
                hist_data_with_indicators = TechnicalIndicators.calculate_all(hist_data)
                
                # Graphique
                st.subheader("📈 Analyse technique")
                fig = create_single_chart(hist_data_with_indicators, symbol)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                
                # Dernières valeurs
                with st.expander("📊 Voir les données historiques"):
                    st.dataframe(
                        hist_data[['date', 'open', 'high', 'low', 'close', 'volume']].tail(10),
                        use_container_width=True,
                        hide_index=True
                    )
            else:
                st.warning("Données historiques non disponibles")
        
        else:
            st.error(f"❌ Erreur: {data.get('error', 'Inconnue')}")
            st.info("""
            Vérifiez:
            - Votre connexion internet
            - Le symbole est correct
            - Votre clé API Alpha Vantage (si utilisée)
            """)
    
    # Auto-refresh
    if not st.session_state.get('paused', False):
        time.sleep(refresh_rate)
        st.rerun()

if __name__ == "__main__":
    main()
