# app.py - Version avec ML, PWA et indicateurs avancés
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
import ta  # Technical Analysis library
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
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.streamlit.io',
        'Report a bug': 'https://github.com',
        'About': '# Dashboard Financier Pro\nVersion 2.0 avec ML et indicateurs avancés'
    }
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
    st.session_state.api_source = "Simulation"
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
if 'pwa_installed' not in st.session_state:
    st.session_state.pwa_installed = False

# ==================== CONFIGURATION DES CHEMINS ====================
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "stock_data.db"
EXPORT_DIR = BASE_DIR / "exports"
MODELS_DIR = BASE_DIR / "models"
STATIC_DIR = BASE_DIR / "static"
EXPORT_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# ==================== CONFIGURATION PWA ====================
def create_pwa_manifest():
    """Crée le manifeste PWA"""
    manifest = {
        "name": "Dashboard Financier Pro",
        "short_name": "FinDash",
        "description": "Dashboard financier en temps réel avec ML",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#667eea",
        "theme_color": "#667eea",
        "icons": [
            {
                "src": "https://cdn.jsdelivr.net/npm/@streamlit/theme/favicon.png",
                "sizes": "192x192",
                "type": "image/png"
            }
        ]
    }
    
    manifest_path = STATIC_DIR / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f)
    
    return manifest_path

def create_pwa_service_worker():
    """Crée le service worker PWA"""
    sw_code = """
    const CACHE_NAME = 'fin-dash-v1';
    const urlsToCache = [
        '/',
        '/static/manifest.json'
    ];
    
    self.addEventListener('install', event => {
        event.waitUntil(
            caches.open(CACHE_NAME)
                .then(cache => cache.addAll(urlsToCache))
        );
    });
    
    self.addEventListener('fetch', event => {
        event.respondWith(
            caches.match(event.request)
                .then(response => response || fetch(event.request))
        );
    });
    """
    
    sw_path = STATIC_DIR / "sw.js"
    with open(sw_path, 'w') as f:
        f.write(sw_code)
    
    return sw_path

# ==================== INDICATEURS TECHNIQUES AVANCÉS ====================
class TechnicalIndicators:
    """Calcul des indicateurs techniques avancés"""
    
    @staticmethod
    def calculate_all(df):
        """Calcule tous les indicateurs techniques"""
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
        df['ema_12'] = ta.trend.ema_indicator(df['close'], window=12)
        df['ema_26'] = ta.trend.ema_indicator(df['close'], window=26)
        
        # Volume indicators
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # Momentum
        df['momentum'] = ta.momentum.ROCIndicator(df['close'], window=10).roc()
        df['stoch_k'] = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close']).stoch()
        df['stoch_d'] = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close']).stoch_signal()
        
        # Volatilité
        df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()
        df['volatility'] = df['close'].pct_change().rolling(window=20).std() * np.sqrt(252)
        
        # Support and Resistance
        df['resistance'] = df['high'].rolling(window=20).max()
        df['support'] = df['low'].rolling(window=20).min()
        
        return df
    
    @staticmethod
    def get_signals(df):
        """Génère des signaux d'achat/vente basés sur les indicateurs"""
        signals = []
        last = df.iloc[-1]
        
        # RSI signals
        if last['rsi'] < 30:
            signals.append(("RSI", "Surachaté 📈", "Achat possible"))
        elif last['rsi'] > 70:
            signals.append(("RSI", "Survendu 📉", "Vente possible"))
        
        # MACD signals
        if last['macd'] > last['macd_signal']:
            signals.append(("MACD", "Hausse", "Signal haussier"))
        else:
            signals.append(("MACD", "Baisse", "Signal baissier"))
        
        # Bollinger signals
        if last['close'] < last['bb_lower']:
            signals.append(("Bollinger", "Sous la bande basse", "Rebond possible"))
        elif last['close'] > last['bb_upper']:
            signals.append(("Bollinger", "Sur la bande haute", "Correction possible"))
        
        # Moving average signals
        if last['sma_20'] > last['sma_50']:
            signals.append(("Golden Cross", "20 > 50", "Tendance haussière"))
        elif last['sma_20'] < last['sma_50']:
            signals.append(("Death Cross", "20 < 50", "Tendance baissière"))
        
        return signals

# ==================== MODÈLE DE PRÉDICTION ML ====================
class MLPredictor:
    """Prédiction des prix avec Machine Learning"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.features = ['open', 'high', 'low', 'close', 'volume', 
                        'rsi', 'macd', 'bb_width', 'volatility', 'momentum']
        
    def prepare_features(self, df):
        """Prépare les features pour le modèle"""
        df = df.copy()
        
        # Calculer tous les indicateurs
        df = TechnicalIndicators.calculate_all(df)
        
        # Créer les features
        feature_df = pd.DataFrame()
        
        for feature in self.features:
            if feature in df.columns:
                feature_df[feature] = df[feature]
            else:
                feature_df[feature] = 0
        
        # Ajouter les lag features
        for i in range(1, 6):
            feature_df[f'close_lag_{i}'] = df['close'].shift(i)
        
        # Ajouter les rolling statistics
        feature_df['close_ma_5'] = df['close'].rolling(5).mean()
        feature_df['close_ma_10'] = df['close'].rolling(10).mean()
        feature_df['volume_ma_5'] = df['volume'].rolling(5).mean()
        
        return feature_df.fillna(method='bfill').fillna(0)
    
    def train(self, df):
        """Entraîne le modèle sur les données historiques"""
        try:
            # Préparer les features
            feature_df = self.prepare_features(df)
            
            # Créer la target (prix futur)
            df['target'] = df['close'].shift(-1)
            df = df.dropna()
            
            # Aligner les données
            feature_df = feature_df.iloc[:len(df)]
            target = df['target'].values
            
            # Split train/test
            X_train, X_test, y_train, y_test = train_test_split(
                feature_df, target, test_size=0.2, random_state=42
            )
            
            # Normaliser
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Entraîner le modèle
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            self.model.fit(X_train_scaled, y_train)
            
            # Évaluer
            train_score = self.model.score(X_train_scaled, y_train)
            test_score = self.model.score(X_test_scaled, y_test)
            
            # Feature importance
            feature_importance = pd.DataFrame({
                'feature': feature_df.columns,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            return {
                'train_score': train_score,
                'test_score': test_score,
                'feature_importance': feature_importance,
                'model': self.model,
                'scaler': self.scaler
            }
            
        except Exception as e:
            st.error(f"Erreur entraînement ML: {e}")
            return None
    
    def predict(self, df, days=5):
        """Prédit les prix futurs"""
        if self.model is None:
            return None
        
        try:
            predictions = []
            confidence_intervals = []
            
            current_df = df.copy()
            
            for i in range(days):
                # Préparer les features
                feature_df = self.prepare_features(current_df)
                last_features = feature_df.iloc[-1:].values
                
                # Normaliser
                last_features_scaled = self.scaler.transform(last_features)
                
                # Prédire
                pred = self.model.predict(last_features_scaled)[0]
                
                # Intervalle de confiance (std des arbres)
                tree_preds = np.array([tree.predict(last_features_scaled)[0] 
                                      for tree in self.model.estimators_])
                ci = np.std(tree_preds) * 1.96  # 95% confidence interval
                
                predictions.append(pred)
                confidence_intervals.append(ci)
                
                # Ajouter la prédiction aux données
                new_row = current_df.iloc[-1:].copy()
                new_row['close'] = pred
                new_row.index = [new_row.index[0] + timedelta(days=1)]
                current_df = pd.concat([current_df, new_row])
            
            return {
                'predictions': predictions,
                'confidence_intervals': confidence_intervals,
                'dates': [datetime.now() + timedelta(days=i+1) for i in range(days)]
            }
            
        except Exception as e:
            st.error(f"Erreur prédiction ML: {e}")
            return None
    
    def save_model(self, symbol):
        """Sauvegarde le modèle"""
        model_path = MODELS_DIR / f"model_{symbol}.joblib"
        scaler_path = MODELS_DIR / f"scaler_{symbol}.joblib"
        
        joblib.dump(self.model, model_path)
        joblib.dump(self.scaler, scaler_path)
        
        return model_path, scaler_path
    
    def load_model(self, symbol):
        """Charge un modèle existant"""
        model_path = MODELS_DIR / f"model_{symbol}.joblib"
        scaler_path = MODELS_DIR / f"scaler_{symbol}.joblib"
        
        if model_path.exists() and scaler_path.exists():
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            return True
        
        return False

# ==================== GÉNÉRATION DE DONNÉES AVANCÉE ====================
def generate_advanced_historical_data(symbol, days=100):
    """Génère des données historiques réalistes pour le ML"""
    base_prices = {
        'MC.PA': 519.60, 'RMS.PA': 2450.00, 'KER.PA': 320.00,
        'CDI.PA': 65.50, 'AI.PA': 180.30, 'OR.PA': 95.20,
        'BNP.PA': 62.40, 'SAN.PA': 89.70, 'TOT.PA': 58.30
    }
    
    base_price = base_prices.get(symbol, 100.00)
    
    # Générer des dates
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # Générer les prix avec une tendance et volatilité réaliste
    np.random.seed(42)  # Pour reproductibilité
    returns = np.random.randn(days) * 0.02
    trend = np.linspace(0, 0.1, days)  # Tendance haussière légère
    price_series = base_price * (1 + np.cumsum(returns) + trend)
    
    # Créer OHLCV
    df = pd.DataFrame({
        'date': dates,
        'open': price_series * (1 + np.random.randn(days) * 0.005),
        'high': price_series * (1 + abs(np.random.randn(days)) * 0.01),
        'low': price_series * (1 - abs(np.random.randn(days)) * 0.01),
        'close': price_series,
        'volume': np.random.randint(100000, 1000000, days)
    })
    
    return df

# ==================== GRAPHIQUES AVANCÉS ====================
def create_advanced_chart(df, symbol, show_indicators=True):
    """Crée un graphique avancé avec indicateurs"""
    
    # Calculer les indicateurs
    df = TechnicalIndicators.calculate_all(df)
    
    # Créer subplots
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.4, 0.2, 0.2, 0.2],
        subplot_titles=(f"{symbol} - Prix", "Volume", "RSI", "MACD")
    )
    
    # Prix avec Bollinger Bands
    fig.add_trace(go.Candlestick(
        x=df['date'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Prix',
        showlegend=False
    ), row=1, col=1)
    
    # Bollinger Bands
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['bb_upper'],
        line=dict(color='rgba(173, 216, 230, 0.5)', dash='dash'),
        name='BB Upper',
        showlegend=False
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['bb_lower'],
        line=dict(color='rgba(173, 216, 230, 0.5)', dash='dash'),
        fill='tonexty',
        fillcolor='rgba(173, 216, 230, 0.2)',
        name='BB Lower',
        showlegend=False
    ), row=1, col=1)
    
    # Moyennes mobiles
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['sma_20'],
        line=dict(color='orange', width=1),
        name='SMA 20',
        showlegend=False
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['sma_50'],
        line=dict(color='blue', width=1),
        name='SMA 50',
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
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['rsi'],
        line=dict(color='purple'),
        name='RSI',
        showlegend=False
    ), row=3, col=1)
    
    # Lignes RSI
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
    
    # MACD
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['macd'],
        line=dict(color='blue'),
        name='MACD',
        showlegend=False
    ), row=4, col=1)
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['macd_signal'],
        line=dict(color='orange'),
        name='Signal',
        showlegend=False
    ), row=4, col=1)
    
    # Barres MACD
    colors_macd = ['green' if val >= 0 else 'red' for val in df['macd_diff']]
    fig.add_trace(go.Bar(
        x=df['date'],
        y=df['macd_diff'],
        marker_color=colors_macd,
        name='MACD Hist',
        showlegend=False
    ), row=4, col=1)
    
    # Mise en page
    fig.update_layout(
        height=800,
        template='plotly_white',
        showlegend=False,
        hovermode='x unified'
    )
    
    fig.update_xaxes(rangeslider_visible=False)
    
    return fig

def create_prediction_chart(historical_df, predictions, symbol):
    """Crée un graphique avec prédictions ML"""
    
    fig = go.Figure()
    
    # Historique
    fig.add_trace(go.Scatter(
        x=historical_df['date'],
        y=historical_df['close'],
        mode='lines',
        name='Historique',
        line=dict(color='blue', width=2)
    ))
    
    # Prédictions
    pred_dates = predictions['dates']
    pred_values = predictions['predictions']
    ci = predictions['confidence_intervals']
    
    # Intervalle de confiance
    fig.add_trace(go.Scatter(
        x=pred_dates + pred_dates[::-1],
        y=[p + ci[i] for i, p in enumerate(pred_values)] + 
          [p - ci[i] for i, p in enumerate(pred_values)][::-1],
        fill='toself',
        fillcolor='rgba(0,100,80,0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Intervalle de confiance 95%'
    ))
    
    # Ligne de prédiction
    fig.add_trace(go.Scatter(
        x=pred_dates,
        y=pred_values,
        mode='lines+markers',
        name='Prédiction ML',
        line=dict(color='red', width=2, dash='dash'),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title=f"Prédictions ML - {symbol}",
        xaxis_title="Date",
        yaxis_title="Prix (€)",
        hovermode='x unified',
        template='plotly_white',
        height=500
    )
    
    return fig

# ==================== DASHBOARD HTML AVEC PWA ====================
def create_pwa_dashboard_html(data, update_counter, comparison_mode=False):
    """Crée le HTML du dashboard avec support PWA"""
    
    html_code = f"""
    <!DOCTYPE html>
    <html lang="fr" manifest="manifest.appcache">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Dashboard Financier Pro</title>
        <link rel="manifest" href="/static/manifest.json">
        <meta name="theme-color" content="#667eea">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black">
        <style>
            /* Styles existants + styles mobiles */
            @media (max-width: 768px) {{
                .metrics-grid {{
                    grid-template-columns: repeat(2, 1fr);
                    gap: 10px;
                }}
                .metric-value {{
                    font-size: 20px;
                }}
                .symbol-title {{
                    font-size: 20px;
                }}
                .tabs {{
                    flex-wrap: wrap;
                }}
                .tab {{
                    flex: 1 1 auto;
                    font-size: 12px;
                    padding: 8px;
                }}
            }}
            
            /* Styles pour installation PWA */
            .install-prompt {{
                position: fixed;
                bottom: 20px;
                left: 20px;
                right: 20px;
                background: white;
                padding: 15px;
                border-radius: 10px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.2);
                display: none;
                z-index: 2000;
            }}
            .install-prompt.show {{
                display: block;
            }}
            .install-btn {{
                background: #667eea;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                width: 100%;
                font-size: 16px;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="install-prompt" id="installPrompt">
            <div style="font-weight: bold; margin-bottom: 10px;">📱 Installer l'application</div>
            <div style="font-size: 14px; color: #666; margin-bottom: 15px;">
                Installez cette application sur votre écran d'accueil pour un accès rapide
            </div>
            <button class="install-btn" onclick="installPWA()">Installer</button>
            <button style="background: none; border: none; color: #666; width: 100%; margin-top: 10px;" onclick="closeInstallPrompt()">
                Plus tard
            </button>
        </div>

        <!-- Reste du dashboard identique -->
        <div class="dashboard">
            <!-- ... (même contenu que précédemment) ... -->
        </div>

        <script>
            let deferredPrompt;
            
            window.addEventListener('beforeinstallprompt', (e) => {{
                e.preventDefault();
                deferredPrompt = e;
                document.getElementById('installPrompt').classList.add('show');
            }});
            
            function installPWA() {{
                if (!deferredPrompt) return;
                
                deferredPrompt.prompt();
                deferredPrompt.userChoice.then((choiceResult) => {{
                    if (choiceResult.outcome === 'accepted') {{
                        console.log('User accepted install');
                        document.getElementById('installPrompt').classList.remove('show');
                    }}
                    deferredPrompt = null;
                }});
            }}
            
            function closeInstallPrompt() {{
                document.getElementById('installPrompt').classList.remove('show');
            }}
            
            // Détection du mode standalone (installé)
            if (window.matchMedia('(display-mode: standalone)').matches) {{
                console.log('Running in standalone mode');
            }}
        </script>
    </body>
    </html>
    """
    return html_code

# ==================== INTERFACE PRINCIPALE ====================
def main():
    st.title("📊 Dashboard Financier Pro")
    st.caption("Version 2.0 - ML, PWA et Indicateurs Avancés")
    
    # Initialisation PWA
    create_pwa_manifest()
    create_pwa_service_worker()
    
    db = DatabaseManager()
    period = "1H"
    ml_predictor = MLPredictor()
    
    # Sidebar avec nouveaux onglets
    with st.sidebar:
        st.header("⚙️ Configuration")
        config_tab = st.tabs(["📈 Symboles", "🔌 API", "🤖 ML", "📊 Indicateurs", "📱 PWA", "🔔 Alertes", "💾 BDD", "📤 Export"])
        
        with config_tab[0]:  # Symboles
            st.subheader("Sélection des symboles")
            comparison_mode = st.checkbox("Mode comparaison", value=st.session_state.comparison_mode)
            st.session_state.comparison_mode = comparison_mode
            
            all_symbols = ["MC.PA", "RMS.PA", "KER.PA", "CDI.PA", "AI.PA", "OR.PA", "BNP.PA", "SAN.PA", "TOT.PA"]
            
            if comparison_mode:
                symbols = st.multiselect("Symboles", all_symbols, default=st.session_state.current_symbols)
                st.session_state.current_symbols = symbols if symbols else ["MC.PA"]
            else:
                symbol = st.selectbox("Symbole", all_symbols, index=0)
                st.session_state.current_symbols = [symbol]
            
            period = st.selectbox("Période", ["1H", "4H", "1J", "1S", "1M", "3M", "1Y"], index=2)
        
        with config_tab[1]:  # API
            st.subheader("Source des données")
            api_source = st.radio("API", ["Simulation", "Yahoo Finance", "Alpha Vantage"], index=0)
            st.session_state.api_source = api_source
            if api_source == "Alpha Vantage":
                api_key = st.text_input("Clé API", type="password")
                st.session_state.api_key = api_key
        
        with config_tab[2]:  # ML
            st.subheader("Machine Learning")
            
            ml_symbol = st.selectbox("Symbole ML", st.session_state.current_symbols)
            
            if st.button("🔄 Entraîner modèle", use_container_width=True):
                with st.spinner("Entraînement en cours..."):
                    # Générer données historiques
                    hist_data = generate_advanced_historical_data(ml_symbol, days=500)
                    
                    # Entraîner modèle
                    result = ml_predictor.train(hist_data)
                    
                    if result:
                        st.session_state.ml_model_trained = True
                        st.success(f"Score train: {result['train_score']:.3f}")
                        st.success(f"Score test: {result['test_score']:.3f}")
                        
                        # Afficher feature importance
                        st.subheader("Features importantes")
                        st.dataframe(result['feature_importance'].head(5))
                        
                        # Sauvegarder
                        ml_predictor.save_model(ml_symbol)
            
            if st.button("📈 Prédire", use_container_width=True):
                if ml_predictor.load_model(ml_symbol):
                    with st.spinner("Calcul des prédictions..."):
                        hist_data = generate_advanced_historical_data(ml_symbol, days=100)
                        predictions = ml_predictor.predict(hist_data, days=5)
                        
                        if predictions:
                            st.session_state.ml_predictions[ml_symbol] = predictions
                            st.success("Prédictions calculées")
                else:
                    st.warning("Entraînez d'abord le modèle")
        
        with config_tab[3]:  # Indicateurs
            st.subheader("Indicateurs techniques")
            
            show_rsi = st.checkbox("RSI", value=True)
            show_macd = st.checkbox("MACD", value=True)
            show_bollinger = st.checkbox("Bollinger Bands", value=True)
            show_sma = st.checkbox("Moyennes mobiles", value=True)
            show_volume = st.checkbox("Volume", value=True)
            show_signals = st.checkbox("Signaux", value=True)
        
        with config_tab[4]:  # PWA
            st.subheader("Application mobile")
            
            st.info("📱 Installez cette application sur votre téléphone")
            
            if st.button("📲 Installer PWA", use_container_width=True):
                st.session_state.pwa_installed = True
                st.balloons()
                st.success("Application prête à être installée")
            
            st.markdown("""
            **Instructions:**
            1. Sur Android: Menu Chrome → Installer l'app
            2. Sur iPhone: Partager → Sur l'écran d'accueil
            """)
        
        with config_tab[5]:  # Alertes
            st.subheader("Alertes")
            # ... (code alertes existant)
        
        with config_tab[6]:  # BDD
            st.subheader("Base de données")
            # ... (code BDD existant)
        
        with config_tab[7]:  # Export
            st.subheader("Export")
            # ... (code export existant)
        
        st.markdown("---")
        st.metric("Mises à jour", st.session_state.update_counter, "+1/3s")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⏸️ Pause", use_container_width=True):
                st.session_state.paused = True
        with col2:
            if st.button("▶️ Reprendre", use_container_width=True):
                st.session_state.paused = False
    
    # ==================== CORPS PRINCIPAL AVEC NOUVELLES FONCTIONNALITÉS ====================
    
    if st.session_state.comparison_mode:
        # Mode comparaison (inchangé)
        pass
    else:
        # Mode simple avec indicateurs et ML
        symbol = st.session_state.current_symbols[0]
        data = generate_live_data(symbol, st.session_state.api_source, st.session_state.api_key)
        st.session_state.update_counter += 1
        st.session_state.last_update = datetime.now()
        
        # Générer données historiques pour indicateurs
        hist_data = generate_advanced_historical_data(symbol, days=100)
        
        # Calculer indicateurs
        hist_data_with_indicators = TechnicalIndicators.calculate_all(hist_data)
        
        # Métriques principales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Cours", f"{data['price']:.2f} €", f"{data['change']:+.2f}%")
        with col2:
            st.metric("Volume", f"{data['volume']:,}")
        with col3:
            last_rsi = hist_data_with_indicators['rsi'].iloc[-1]
            st.metric("RSI", f"{last_rsi:.1f}")
        with col4:
            last_bb_width = hist_data_with_indicators['bb_width'].iloc[-1]
            st.metric("Volatilité", f"{last_bb_width:.3f}")
        
        # Graphique avancé
        st.subheader("📈 Analyse technique avancée")
        fig = create_advanced_chart(
            hist_data_with_indicators, 
            symbol,
            show_indicators=True
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Signaux
        if show_signals:
            signals = TechnicalIndicators.get_signals(hist_data_with_indicators)
            if signals:
                st.subheader("🚦 Signaux")
                cols = st.columns(len(signals))
                for i, (indicator, status, action) in enumerate(signals):
                    with cols[i]:
                        st.info(f"**{indicator}**\n\n{status}\n\n*{action}*")
        
        # Prédictions ML
        if symbol in st.session_state.ml_predictions:
            st.subheader("🤖 Prédictions Machine Learning")
            predictions = st.session_state.ml_predictions[symbol]
            
            fig_pred = create_prediction_chart(hist_data, predictions, symbol)
            st.plotly_chart(fig_pred, use_container_width=True)
            
            # Afficher les prédictions
            cols = st.columns(len(predictions['predictions']))
            for i, (col, pred, ci, date) in enumerate(zip(
                cols, 
                predictions['predictions'], 
                predictions['confidence_intervals'],
                predictions['dates']
            )):
                with col:
                    st.metric(
                        f"J+{i+1}",
                        f"{pred:.2f} €",
                        f"±{ci:.2f}",
                        help=f"Prédiction pour le {date.strftime('%d/%m')}"
                    )
        
        # Support PWA
        st.components.v1.html("""
        <script>
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.register('/static/sw.js');
            }
        </script>
        """, height=0)
    
    # Auto-refresh
    if not st.session_state.get('paused', False):
        time.sleep(3)
        st.rerun()

if __name__ == "__main__":
    main()
