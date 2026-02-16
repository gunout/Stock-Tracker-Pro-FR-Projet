# app.py - Version avec dashboard intégré
import streamlit as st
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json

st.set_page_config(
    page_title="Analyse Financière MC.PA",
    page_icon="📊",
    layout="wide"
)

# Imports
from api.client import FinancialAPIClient
from api.rate_limiter import RateLimiter
from components.metrics import display_stock_metrics
from config.settings import AppConfig, DEFAULT_SYMBOLS

# Fonction pour générer le dashboard HTML
def create_dashboard_html(data):
    """Crée le HTML du dashboard avec les données"""
    
    # Convertir les données en JSON pour JavaScript
    data_json = json.dumps(data)
    
    html = f"""
    <!doctype html>
    <html lang="fr">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width,initial-scale=1" />
        <title>Dashboard Financier</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
            .dashboard {{ padding: 20px; }}
            .metrics-container {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }}
            .metric-card {{
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                text-align: center;
            }}
            .metric-label {{ color: #666; font-size: 14px; margin-bottom: 5px; }}
            .metric-value {{ font-size: 24px; font-weight: bold; color: #333; }}
            .metric-change {{ font-size: 14px; margin-top: 5px; }}
            .positive {{ color: #4CAF50; }}
            .negative {{ color: #F44336; }}
            .chart-container {{ 
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-top: 20px;
            }}
            .symbol-header {{ 
                font-size: 28px; 
                font-weight: bold; 
                margin-bottom: 20px;
                color: #333;
                border-bottom: 2px solid #FF4B4B;
                padding-bottom: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="dashboard">
            <div class="symbol-header">{data['symbol']} - Analyse en temps réel</div>
            
            <div class="metrics-container" id="metrics">
                <div class="metric-card">
                    <div class="metric-label">Cours</div>
                    <div class="metric-value">{data['price']:.2f} €</div>
                    <div class="metric-change {'positive' if data['change'] >= 0 else 'negative'}">
                        {data['change']:+.2f}%
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Volume</div>
                    <div class="metric-value">{data['volume']:,}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">P/E</div>
                    <div class="metric-value">{data.get('pe_ratio', 23.76):.2f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Dividende</div>
                    <div class="metric-value">{data.get('dividend', 13.00):.2f} €</div>
                    <div class="metric-change positive">{data.get('dividend_yield', 2.48):.2f}%</div>
                </div>
            </div>

            <div class="chart-container">
                <canvas id="priceChart" style="width:100%; height:400px;"></canvas>
            </div>
        </div>

        <!-- Chart.js pour les graphiques -->
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            // Données reçues de Streamlit
            const stockData = {data_json};
            
            // Créer le graphique
            const ctx = document.getElementById('priceChart').getContext('2d');
            
            // Générer des données historiques simulées
            const dates = [];
            const prices = [];
            let currentPrice = stockData.price;
            
            for (let i = 30; i >= 0; i--) {{
                const date = new Date();
                date.setDate(date.getDate() - i);
                dates.push(date.toLocaleDateString('fr-FR'));
                
                // Prix avec variation aléatoire
                const change = (Math.random() - 0.5) * 2;
                currentPrice = currentPrice * (1 + change/100);
                prices.push(currentPrice);
            }}
            
            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: dates,
                    datasets: [{{
                        label: 'Prix',
                        data: prices,
                        borderColor: '#FF4B4B',
                        backgroundColor: 'rgba(255, 75, 75, 0.1)',
                        tension: 0.1,
                        fill: true
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            display: false
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: false,
                            grid: {{
                                color: 'rgba(0,0,0,0.05)'
                            }}
                        }}
                    }}
                }}
            }});
        </script>

        <!-- Scripts originaux du dashboard -->
        <script type="module" src="/-/build/assets/index-B59N3yFD.js"></script>
    </body>
    </html>
    """
    return html

def get_mock_data(symbol):
    """Données simulées"""
    mock_data = {
        'MC.PA': {
            'symbol': 'MC.PA',
            'price': 519.60,
            'change': -0.93,
            'volume': 26164,
            'pe_ratio': 23.76,
            'dividend': 13.00,
            'dividend_yield': 2.48,
            'market_cap': 257.87e9
        },
        'RMS.PA': {
            'symbol': 'RMS.PA',
            'price': 2450.00,
            'change': 0.85,
            'volume': 15000,
            'pe_ratio': 48.50,
            'dividend': 15.00,
            'dividend_yield': 0.61,
            'market_cap': 255.84e9
        },
        'KER.PA': {
            'symbol': 'KER.PA',
            'price': 320.00,
            'change': -1.20,
            'volume': 50000,
            'pe_ratio': 18.30,
            'dividend': 4.50,
            'dividend_yield': 1.40,
            'market_cap': 40.00e9
        }
    }
    return mock_data.get(symbol, mock_data['MC.PA'])

def main():
    st.title("📊 Dashboard Financier Intégré")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Mode d'affichage
        view_mode = st.radio(
            "Mode d'affichage",
            ["Streamlit Native", "Dashboard HTML", "Split View"],
            index=0
        )
        
        symbol = st.selectbox(
            "Symbole",
            options=["MC.PA", "RMS.PA", "KER.PA", "CDI.PA", "AI.PA"],
            index=0
        )
        
        period = st.selectbox(
            "Période",
            options=["1J", "1S", "1M", "3M", "1Y"],
            index=2
        )
        
        refresh = st.button("🔄 Rafraîchir")
    
    # Récupérer les données
    data = get_mock_data(symbol)
    
    # Affichage selon le mode choisi
    if view_mode == "Streamlit Native":
        # Interface Streamlit classique
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Cours", f"{data['price']:.2f} €", f"{data['change']:.2f}%")
        with col2:
            st.metric("Volume", f"{data['volume']:,}")
        with col3:
            st.metric("P/E", f"{data['pe_ratio']:.2f}")
        with col4:
            st.metric("Dividende", f"{data['dividend']:.2f} €", f"{data['dividend_yield']:.2f}%")
        
        # Graphique simple
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        prices = [data['price'] * (1 + np.random.randn()*0.02) for _ in range(30)]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=prices, mode='lines'))
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
    elif view_mode == "Dashboard HTML":
        # Dashboard HTML intégré
        st.components.v1.html(create_dashboard_html(data), height=800, scrolling=True)
        
    else:  # Split View
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Vue Streamlit")
            st.metric("Cours", f"{data['price']:.2f} €", f"{data['change']:.2f}%")
            st.metric("Volume", f"{data['volume']:,}")
            st.metric("P/E", f"{data['pe_ratio']:.2f}")
            
            # Petit graphique
            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            prices = [data['price'] * (1 + np.random.randn()*0.02) for _ in range(30)]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dates, y=prices, mode='lines'))
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🎨 Dashboard HTML")
            st.components.v1.html(create_dashboard_html(data), height=400, scrolling=True)

if __name__ == "__main__":
    main()
