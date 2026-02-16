# app.py - Version évolutive
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Analyse Financière", page_icon="📊", layout="wide")

# Imports conditionnels (avec fallback)
try:
    from api.client import FinancialAPIClient
    API_DISPONIBLE = True
except ImportError:
    API_DISPONIBLE = False
    st.warning("Module API non disponible, utilisation des données simulées")

try:
    from components.charts import create_candlestick_chart, create_volume_chart
    CHARTS_DISPONIBLE = True
except ImportError:
    CHARTS_DISPONIBLE = False

try:
    from utils.indicators import calculate_rsi, calculate_macd
    INDICATORS_DISPONIBLE = True
except ImportError:
    INDICATORS_DISPONIBLE = False

# Fonction de données simulées (toujours disponible)
def get_mock_data(symbol, days=100):
    """Génère des données simulées"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    base_price = 519.60 if symbol == "MC.PA" else 100.00
    returns = pd.Series(np.random.randn(days) * 0.02)
    price_series = base_price * (1 + returns.cumsum() / 10)
    
    return pd.DataFrame({
        'Date': dates,
        'Open': price_series * (1 + np.random.randn(days) * 0.005),
        'High': price_series * (1 + abs(np.random.randn(days)) * 0.01),
        'Low': price_series * (1 - abs(np.random.randn(days)) * 0.01),
        'Close': price_series,
        'Volume': np.random.randint(100000, 1000000, days)
    })

def main():
    st.title("📊 Analyse Financière")
    
    # Sidebar avec options progressives
    with st.sidebar:
        st.header("Configuration")
        
        # Option 1: Symboles (toujours disponible)
        symbol = st.selectbox("Symbole", ["MC.PA", "RMS.PA", "KER.PA", "CDI.PA"])
        
        # Option 2: Période (toujours disponible)
        period = st.selectbox("Période", ["1M", "3M", "6M", "1Y"], index=1)
        days_map = {"1M": 30, "3M": 90, "6M": 180, "1Y": 365}
        days = days_map[period]
        
        # Option 3: Type de graphique (évolutif)
        chart_type = st.radio(
            "Type de graphique",
            ["Ligne", "Chandelier"] if CHARTS_DISPONIBLE else ["Ligne"]
        )
        
        # Option 4: Indicateurs (évolutif)
        if INDICATORS_DISPONIBLE:
            with st.expander("Indicateurs techniques"):
                show_rsi = st.checkbox("RSI")
                show_macd = st.checkbox("MACD")
                show_bollinger = st.checkbox("Bollinger Bands")
        
        # Bouton rafraîchir
        refresh = st.button("🔄 Rafraîchir")
    
    # Corps principal
    col1, col2, col3 = st.columns(3)
    
    # Métriques en temps réel
    if API_DISPONIBLE:
        client = FinancialAPIClient()
        current_data = client.get_stock_data(symbol)
    else:
        # Données simulées
        mock_data = {
            'MC.PA': {'price': 519.60, 'change': -0.93, 'volume': 26164},
            'RMS.PA': {'price': 2450.00, 'change': 0.85, 'volume': 15000}
        }
        current_data = mock_data.get(symbol, {'price': 100.00, 'change': 0, 'volume': 0})
    
    with col1:
        st.metric("Cours", f"{current_data.get('price', 0):.2f} €", 
                 f"{current_data.get('change', 0):.2f}%")
    with col2:
        st.metric("Volume", f"{current_data.get('volume', 0):,}")
    with col3:
        st.metric("Variation", f"{current_data.get('change', 0):.2f}%")
    
    # Données historiques
    data = get_mock_data(symbol, days)
    
    # Graphique principal
    if chart_type == "Chandelier" and CHARTS_DISPONIBLE:
        fig = create_candlestick_chart(data, symbol)
    else:
        # Graphique ligne simple
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data['Date'], y=data['Close'], mode='lines'))
        fig.update_layout(title=f"{symbol} - {period}")
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Indicateurs techniques (si disponibles)
    if INDICATORS_DISPONIBLE:
        tabs = st.tabs(["Indicateurs", "Données"])
        
        with tabs[0]:
            if show_rsi:
                rsi = calculate_rsi(data['Close'])
                fig_rsi = go.Figure()
                fig_rsi.add_trace(go.Scatter(x=data['Date'], y=rsi))
                fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
                fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
                fig_rsi.update_layout(title="RSI (14)", height=300)
                st.plotly_chart(fig_rsi, use_container_width=True)
            
            if show_macd:
                macd, signal = calculate_macd(data['Close'])
                fig_macd = go.Figure()
                fig_macd.add_trace(go.Scatter(x=data['Date'], y=macd, name='MACD'))
                fig_macd.add_trace(go.Scatter(x=data['Date'], y=signal, name='Signal'))
                fig_macd.update_layout(title="MACD", height=300)
                st.plotly_chart(fig_macd, use_container_width=True)
        
        with tabs[1]:
            st.dataframe(data.tail(10))
    
    # Export des données
    if st.button("📥 Exporter en CSV"):
        csv = data.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Télécharger",
            csv,
            f"{symbol}_data.csv",
            "text/csv"
        )

if __name__ == "__main__":
    main()
