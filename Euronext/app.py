# Euronext/app.py
import streamlit as st
from datetime import datetime
import time
import sys
import os
import pandas as pd
import plotly.graph_objects as go

# Configuration de la page (PREMIÈRE commande Streamlit)
st.set_page_config(
    page_title="Analyse Financière MC.PA",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ajouter le répertoire courant au PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# IMPORTS CORRIGÉS
from api.client import FinancialAPIClient
from api.rate_limiter import RateLimiter
from api.cache import CacheManager
from components.metrics import display_stock_metrics, display_rate_limit_status
from components.charts import ChartBuilder, display_advanced_charts
from components.status import StatusDisplay, NotificationManager
from utils.validators import validate_all_inputs, DataValidator
from utils.formatters import DataFormatter, StockFormatter
from config.settings import AppConfig, DEFAULT_SYMBOLS

# Initialisation des composants avec cache
@st.cache_resource
def init_api_client():
    """Initialise le client API (une seule fois)"""
    return FinancialAPIClient()

@st.cache_resource
def init_rate_limiter():
    """Initialise le rate limiter (une seule fois)"""
    return RateLimiter(max_requests=30, time_window=60)

@st.cache_resource
def init_cache_manager():
    """Initialise le gestionnaire de cache"""
    return CacheManager(default_ttl=3600)

@st.cache_resource
def init_notification_manager():
    """Initialise le gestionnaire de notifications"""
    return NotificationManager()

def generate_sample_data(symbol: str):
    """Génère des données d'exemple pour le développement"""
    import numpy as np
    
    dates = pd.date_range(start='2025-01-01', periods=100, freq='D')
    
    if symbol == "MC.PA":
        base_price = 519.60
    elif symbol == "RMS.PA":
        base_price = 2450.00
    elif symbol == "KER.PA":
        base_price = 320.00
    else:
        base_price = 100.00
    
    # Générer des prix avec une tendance
    returns = np.random.randn(100) * 0.02
    price_series = base_price * (1 + np.cumsum(returns) / 10)
    
    df = pd.DataFrame({
        'Date': dates,
        'Open': price_series * (1 + np.random.randn(100) * 0.005),
        'High': price_series * (1 + abs(np.random.randn(100)) * 0.01),
        'Low': price_series * (1 - abs(np.random.randn(100)) * 0.01),
        'Close': price_series,
        'Volume': np.random.randint(100000, 1000000, 100)
    })
    
    # Ajouter les moyennes mobiles
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA50'] = df['Close'].rolling(50).mean()
    
    return df

def main():
    """Fonction principale de l'application"""
    
    # Initialisation
    api_client = init_api_client()
    rate_limiter = init_rate_limiter()
    cache_manager = init_cache_manager()
    notifications = init_notification_manager()
    
    # Titre principal avec date
    st.title(f"{AppConfig.APP_ICON} {AppConfig.APP_NAME}")
    current_time = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    st.caption(f"Dernière mise à jour: {current_time}")
    
    # Sidebar - Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Sélection des symboles
        symbols = st.multiselect(
            "Symboles à analyser",
            options=DEFAULT_SYMBOLS + ["CDI.PA", "AI.PA", "OR.PA", "BNP.PA"],
            default=["MC.PA"]
        )
        
        # Options d'affichage
        st.subheader("📊 Options d'affichage")
        show_charts = st.checkbox("Afficher les graphiques", value=True)
        show_indicators = st.checkbox("Afficher les indicateurs techniques", value=True)
        show_historical = st.checkbox("Afficher les données historiques", value=False)
        
        # Période d'analyse
        st.subheader("📅 Période")
        period = st.selectbox(
            "Période",
            options=["1M", "3M", "6M", "1Y", "2Y", "5Y"],
            index=2
        )
        
        # Bouton de rafraîchissement
        col1, col2 = st.columns(2)
        with col1:
            refresh = st.button("🔄 Rafraîchir", use_container_width=True)
        with col2:
            auto_refresh = st.checkbox("Auto", value=False)
        
        # Intervalle de rafraîchissement auto
        if auto_refresh:
            refresh_interval = st.slider(
                "Intervalle (minutes)",
                min_value=1,
                max_value=30,
                value=5
            )
        
        # Affichage du statut rate limiting
        st.sidebar.markdown("---")
        display_rate_limit_status(rate_limiter)
        
        # Statistiques du cache
        with st.expander("📦 Statistiques cache"):
            cache_stats = cache_manager.get_stats()
            st.write(f"**Entrées totales:** {cache_stats['total_entries']}")
            st.write(f"**Entrées actives:** {cache_stats['active_entries']}")
            st.write(f"**Taille estimée:** {cache_stats['memory_estimate'] / 1024:.2f} KB")
            
            if st.button("🗑️ Vider le cache"):
                cache_manager.clear()
                st.success("Cache vidé !")
                time.sleep(1)
                st.rerun()
    
    # Corps principal
    if symbols:
        # Vérification rate limiting
        if rate_limiter.can_proceed() or refresh:
            
            if refresh:
                rate_limiter.add_request()
                notifications.add_notification("Données actualisées", "success")
            
            # Afficher les notifications
            notifications.display_notifications()
            
            # Créer des onglets pour chaque symbole
            tabs = st.tabs([f"📈 {symbol}" for symbol in symbols])
            
            for i, symbol in enumerate(symbols):
                with tabs[i]:
                    st.subheader(f"Analyse {symbol}")
                    
                    # Deux colonnes pour les métriques principales
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # Récupération des données (simulées pour l'exemple)
                        # En production: data = api_client.get_stock_data(symbol)
                        
                        # Données simulées pour MC.PA
                        if symbol == "MC.PA":
                            stock_data = {
                                'price': 519.60,
                                'change': -0.93,
                                'volume': 26164,
                                'volume_change': -93.3,
                                'pe_ratio': 23.76,
                                'dividend': 13.00,
                                'dividend_yield': 2.48,
                                'market_cap': 257.87e9,
                                'day_high': 524.10,
                                'day_low': 519.20,
                                'year_high': 723.00,
                                'year_low': 436.55
                            }
                        elif symbol == "RMS.PA":
                            stock_data = {
                                'price': 2450.00,
                                'change': 0.85,
                                'volume': 15000,
                                'volume_change': -45.2,
                                'pe_ratio': 48.50,
                                'dividend': 15.00,
                                'dividend_yield': 0.61,
                                'market_cap': 255.84e9
                            }
                        else:
                            stock_data = {
                                'price': 320.00,
                                'change': -1.20,
                                'volume': 50000,
                                'volume_change': -20.5,
                                'pe_ratio': 18.30,
                                'dividend': 4.50,
                                'dividend_yield': 1.40,
                                'market_cap': 40.00e9
                            }
                        
                        # Afficher les métriques
                        display_stock_metrics(symbol, stock_data)
                        
                        # Informations supplémentaires
                        with st.expander("📊 Détails supplémentaires"):
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.metric("Plus haut (jour)", 
                                        DataFormatter.format_currency(stock_data.get('day_high', 0)))
                                st.metric("Plus bas (jour)", 
                                        DataFormatter.format_currency(stock_data.get('day_low', 0)))
                            with col_b:
                                st.metric("Plus haut (an)", 
                                        DataFormatter.format_currency(stock_data.get('year_high', 0)))
                                st.metric("Plus bas (an)", 
                                        DataFormatter.format_currency(stock_data.get('year_low', 0)))
                    
                    with col2:
                        st.info("""
                        **🔍 Analyse rapide**
                        
                        Le ratio P/E de {:.2f} indique une valorisation {}.
                        
                        Le rendement du dividende est de {:.2f}%.
                        
                        Capitalisation: {}
                        """.format(
                            stock_data.get('pe_ratio', 0),
                            "élevée" if stock_data.get('pe_ratio', 0) > 20 else "modérée",
                            stock_data.get('dividend_yield', 0),
                            DataFormatter.format_currency(stock_data.get('market_cap', 0))
                        ))
                    
                    # Graphiques
                    if show_charts:
                        st.markdown("---")
                        st.subheader("📉 Évolution du cours")
                        
                        # Générer des données historiques simulées
                        historical_data = generate_sample_data(symbol)
                        
                        # Afficher les graphiques avancés
                        display_advanced_charts(symbol, historical_data)
                        
                        # Indicateurs techniques
                        if show_indicators:
                            st.markdown("---")
                            st.subheader("📊 Indicateurs techniques")
                            
                            ind_col1, ind_col2, ind_col3 = st.columns(3)
                            
                            # Calculer quelques indicateurs
                            current_price = historical_data['Close'].iloc[-1]
                            ma20 = historical_data['MA20'].iloc[-1]
                            ma50 = historical_data['MA50'].iloc[-1]
                            
                            with ind_col1:
                                st.metric(
                                    "Moyenne mobile 20j",
                                    DataFormatter.format_currency(ma20),
                                    DataFormatter.format_percentage((current_price - ma20) / ma20 * 100)
                                )
                            
                            with ind_col2:
                                st.metric(
                                    "Moyenne mobile 50j",
                                    DataFormatter.format_currency(ma50),
                                    DataFormatter.format_percentage((current_price - ma50) / ma50 * 100)
                                )
                            
                            with ind_col3:
                                # RSI simulé
                                rsi = 55.3
                                st.metric(
                                    "RSI (14j)",
                                    f"{rsi:.1f}",
                                    "Neutre" if 40 < rsi < 60 else "Surachaté" if rsi > 70 else "Survendu"
                                )
                    
                    # Données historiques
                    if show_historical:
                        st.markdown("---")
                        st.subheader("📋 Données historiques")
                        
                        # Générer des données historiques
                        hist_data = generate_sample_data(symbol)
                        
                        # Formater pour l'affichage
                        display_df = hist_data.tail(10).copy()
                        display_df['Date'] = display_df['Date'].dt.strftime('%d/%m/%Y')
                        
                        for col in ['Open', 'High', 'Low', 'Close', 'MA20', 'MA50']:
                            if col in display_df.columns:
                                display_df[col] = display_df[col].apply(
                                    lambda x: DataFormatter.format_currency(x, "€", 2)
                                )
                        
                        display_df['Volume'] = display_df['Volume'].apply(
                            lambda x: DataFormatter.format_number(x)
                        )
                        
                        st.dataframe(
                            display_df,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Date": "Date",
                                "Open": "Ouverture",
                                "High": "Plus haut",
                                "Low": "Plus bas",
                                "Close": "Clôture",
                                "Volume": "Volume",
                                "MA20": "MM20",
                                "MA50": "MM50"
                            }
                        )
                        
                        # Bouton de téléchargement
                        csv = hist_data.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Télécharger les données CSV",
                            data=csv,
                            file_name=f"{symbol}_historique.csv",
                            mime="text/csv"
                        )
        
        else:
            # Rate limit atteint
            wait_time = rate_limiter.get_wait_time()
            
            st.error(f"🔴 Limite de requêtes atteinte. Veuillez patienter {wait_time:.0f} secondes.")
            
            # Barre de progression
            progress = 1 - (wait_time / 60)
            st.progress(progress)
            
            # Compteur
            remaining = rate_limiter.get_remaining_requests()
            st.info(f"Requêtes restantes: {remaining}/{rate_limiter.max_requests}")
            
            # Bouton pour forcer
            if st.button("⏰ Forcer la mise à jour"):
                rate_limiter.clear_history()
                st.rerun()
    
    else:
        # Message si aucun symbole sélectionné
        st.info("👈 Sélectionnez au moins un symbole dans la sidebar pour commencer l'analyse")
        
        # Afficher un exemple
        st.markdown("""
        ### 🚀 Bienvenue sur l'Analyseur Financier MC.PA
        
        Cette application vous permet d'analyser les actions du CAC 40 en temps réel.
        
        **Fonctionnalités:**
        - 📊 Visualisation des cours en temps réel
        - 📈 Graphiques interactifs (chandeliers, volumes)
        - 📉 Indicateurs techniques (moyennes mobiles, RSI, MACD)
        - 💰 Données de dividendes et ratios financiers
        - 🔄 Mise à jour automatique des données
        
        **Pour commencer:** Sélectionnez un ou plusieurs symboles dans la sidebar.
        """)
        
        # Exemple de graphique
        st.subheader("📊 Aperçu - LVMH (MC.PA)")
        sample_data = generate_sample_data("MC.PA")
        fig = ChartBuilder.create_candlestick_chart(sample_data, "MC.PA")
        st.plotly_chart(fig, use_container_width=True)
    
    # Pied de page
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.caption(f"© 2026 Analyseur Financier MC.PA | Données indicatives | v1.0.0")
        
        # Statut du marché
        market_status = "🟢 Ouvert" if 9 <= datetime.now().hour < 17.5 else "🔴 Fermé"
        st.caption(f"Marché Euronext Paris: {market_status}")
    
    # Rafraîchissement automatique
    if auto_refresh and 'refresh_interval' in locals():
        time.sleep(refresh_interval * 60)
        st.rerun()

if __name__ == "__main__":
    main()
