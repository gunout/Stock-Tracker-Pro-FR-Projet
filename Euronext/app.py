# app.py - Version simplifiée
import streamlit as st
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
import os

# Configuration de la page
st.set_page_config(
    page_title="Analyse Financière MC.PA",
    page_icon="📊",
    layout="wide"
)

# Imports simplifiés
from api.client import FinancialAPIClient
from api.rate_limiter import RateLimiter
from components.metrics import display_stock_metrics
from config.settings import AppConfig, DEFAULT_SYMBOLS

# Initialisation
@st.cache_resource
def init_api_client():
    return FinancialAPIClient()

@st.cache_resource
def init_rate_limiter():
    return RateLimiter(max_requests=30, time_window=60)

def generate_sample_data(symbol):
    """Données d'exemple"""
    dates = pd.date_range(start='2025-01-01', periods=100, freq='D')
    base_price = 519.60 if symbol == "MC.PA" else 100.00
    returns = np.random.randn(100) * 0.02
    price_series = base_price * (1 + np.cumsum(returns) / 10)
    
    return pd.DataFrame({
        'Date': dates,
        'Close': price_series,
        'Volume': np.random.randint(100000, 1000000, 100)
    })

def main():
    st.title(f"{AppConfig.APP_ICON} {AppConfig.APP_NAME}")
    st.caption(f"Dernière mise à jour: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        symbols = st.multiselect(
            "Symboles",
            DEFAULT_SYMBOLS,
            default=["MC.PA"]
        )
        refresh = st.button("🔄 Rafraîchir")
    
    # Corps principal
    if symbols:
        api_client = init_api_client()
        rate_limiter = init_rate_limiter()
        
        for symbol in symbols:
            st.subheader(f"📈 {symbol}")
            
            # Données simulées
            if symbol == "MC.PA":
                data = {
                    'price': 519.60,
                    'change': -0.93,
                    'volume': 26164,
                    'pe_ratio': 23.76,
                    'dividend': 13.00,
                    'dividend_yield': 2.48
                }
            elif symbol == "RMS.PA":
                data = {
                    'price': 2450.00,
                    'change': 0.85,
                    'volume': 15000,
                    'pe_ratio': 48.50,
                    'dividend': 15.00,
                    'dividend_yield': 0.61
                }
            else:
                data = {
                    'price': 100.00,
                    'change': 0.00,
                    'volume': 100000,
                    'pe_ratio': 15.00,
                    'dividend': 2.00,
                    'dividend_yield': 2.00
                }
            
            # Afficher les métriques
            display_stock_metrics(symbol, data)
            
            # Graphique simple
            hist_data = generate_sample_data(symbol)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist_data['Date'],
                y=hist_data['Close'],
                mode='lines',
                name=symbol
            ))
            fig.update_layout(
                title=f"Évolution {symbol}",
                height=400,
                xaxis_title="Date",
                yaxis_title="Prix (€)"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Petit tableau de données
            with st.expander("📋 Afficher les données"):
                st.dataframe(hist_data.tail(10))
            
            st.markdown("---")
    else:
        st.info("👈 Sélectionnez un symbole dans la sidebar pour commencer")
        
        # Exemple
        st.subheader("📊 Aperçu - LVMH (MC.PA)")
        sample_data = generate_sample_data("MC.PA")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=sample_data['Date'],
            y=sample_data['Close'],
            mode='lines',
            name="MC.PA"
        ))
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
