# app.py - Version avec graphiques fixes
import streamlit as st
from datetime import datetime
import pandas as pd
import numpy as np
import json
import time

# Configuration de la page
st.set_page_config(
    page_title="Dashboard Financier MC.PA",
    page_icon="📊",
    layout="wide"
)

def create_dashboard_html(data):
    """Crée le HTML du dashboard avec graphiques fixes"""
    
    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard Financier</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }}
            body {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            .dashboard {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            .header {{
                background: white;
                padding: 25px;
                border-radius: 15px;
                margin-bottom: 20px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            }}
            .symbol-title {{
                font-size: 28px;
                font-weight: bold;
                color: #333;
                margin-bottom: 10px;
            }}
            .symbol-title span {{
                color: #667eea;
            }}
            .last-update {{
                color: #666;
                font-size: 14px;
            }}
            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 20px;
                margin-bottom: 30px;
            }}
            .metric-card {{
                background: white;
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.1);
                transition: transform 0.3s ease;
            }}
            .metric-card:hover {{
                transform: translateY(-5px);
            }}
            .metric-label {{
                color: #666;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 10px;
            }}
            .metric-value {{
                font-size: 28px;
                font-weight: bold;
                color: #333;
                margin-bottom: 5px;
            }}
            .metric-change {{
                font-size: 14px;
            }}
            .positive {{ color: #4CAF50; }}
            .negative {{ color: #F44336; }}
            .chart-container {{
                background: white;
                padding: 25px;
                border-radius: 15px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.1);
                margin-bottom: 30px;
                position: relative;
                width: 100%;
            }}
            .chart-wrapper {{
                position: relative;
                width: 100%;
                height: 400px;  /* Hauteur fixe */
                margin: 0 auto;
            }}
            .chart-title {{
                font-size: 18px;
                font-weight: bold;
                color: #333;
                margin-bottom: 20px;
            }}
            .tabs {{
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
                flex-wrap: wrap;
            }}
            .tab {{
                padding: 10px 20px;
                background: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                color: #666;
                transition: all 0.3s ease;
            }}
            .tab:hover {{
                background: #667eea;
                color: white;
            }}
            .tab.active {{
                background: #667eea;
                color: white;
            }}
            .tab-content {{
                display: none;
            }}
            .tab-content.active {{
                display: block;
            }}
            .indicators-grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 20px;
            }}
            .indicator-chart {{
                position: relative;
                width: 100%;
                height: 250px;  /* Hauteur fixe pour les petits graphiques */
            }}
            .historical-table {{
                width: 100%;
                border-collapse: collapse;
            }}
            .historical-table th,
            .historical-table td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #eee;
            }}
            .historical-table th {{
                background: #f8f9fa;
                font-weight: 600;
                color: #333;
            }}
            .historical-table tr:hover {{
                background: #f5f5f5;
            }}
            .footer {{
                text-align: center;
                color: white;
                font-size: 12px;
                margin-top: 30px;
                opacity: 0.8;
            }}
            .market-status {{
                display: inline-block;
                padding: 5px 10px;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
                margin-left: 10px;
            }}
            .open {{
                background: #4CAF50;
                color: white;
            }}
            .closed {{
                background: #F44336;
                color: white;
            }}
            canvas {{
                display: block;
                width: 100% !important;
                height: 100% !important;
            }}
        </style>
    </head>
    <body>
        <div class="dashboard">
            <div class="header">
                <div class="symbol-title">
                    {data['symbol']} <span>• Analyse en temps réel</span>
                    <span class="market-status {'open' if data['market_open'] else 'closed'}">
                        {'🟢 Ouvert' if data['market_open'] else '🔴 Fermé'}
                    </span>
                </div>
                <div class="last-update">Dernière mise à jour: {data['last_update']}</div>
            </div>
            
            <div class="metrics-grid">
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
                    <div class="metric-value">{data['pe_ratio']:.2f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Dividende</div>
                    <div class="metric-value">{data['dividend']:.2f} €</div>
                    <div class="metric-change positive">{data['dividend_yield']:.2f}%</div>
                </div>
            </div>

            <div class="tabs">
                <button class="tab active" onclick="showTab('chart')">📈 Graphique</button>
                <button class="tab" onclick="showTab('historical')">📊 Données historiques</button>
                <button class="tab" onclick="showTab('indicators')">📉 Indicateurs</button>
            </div>
            
            <div id="chart" class="tab-content active">
                <div class="chart-container">
                    <div class="chart-title">Évolution du cours - {data['period']}</div>
                    <div class="chart-wrapper">
                        <canvas id="priceChart"></canvas>
                    </div>
                </div>
            </div>
            
            <div id="historical" class="tab-content">
                <div class="chart-container">
                    <table class="historical-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Ouverture</th>
                                <th>Plus haut</th>
                                <th>Plus bas</th>
                                <th>Clôture</th>
                                <th>Volume</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(data['historical_rows'])}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div id="indicators" class="tab-content">
                <div class="chart-container">
                    <div class="indicators-grid">
                        <div>
                            <div class="chart-title">RSI (14)</div>
                            <div class="indicator-chart">
                                <canvas id="rsiChart"></canvas>
                            </div>
                        </div>
                        <div>
                            <div class="chart-title">MACD</div>
                            <div class="indicator-chart">
                                <canvas id="macdChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                © 2026 Dashboard Financier - Données en temps réel
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            let priceChart, rsiChart, macdChart;
            
            function showTab(tabId) {{
                document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
                
                event.target.classList.add('active');
                document.getElementById(tabId).classList.add('active');
                
                // Redessiner les graphiques après le changement d'onglet
                setTimeout(() => {{
                    if (tabId === 'chart' && priceChart) {{
                        priceChart.update();
                    }} else if (tabId === 'indicators') {{
                        if (rsiChart) rsiChart.update();
                        if (macdChart) macdChart.update();
                    }}
                }}, 100);
            }}
            
            // Données reçues
            const stockData = {json.dumps(data)};
            
            // Générer des données pour les graphiques
            function generateChartData() {{
                const dates = [];
                const prices = [];
                const volumes = [];
                let currentPrice = stockData.price;
                
                for (let i = 30; i >= 0; i--) {{
                    const date = new Date();
                    date.setDate(date.getDate() - i);
                    dates.push(date.toLocaleDateString('fr-FR'));
                    
                    // Variation aléatoire pour simuler le marché
                    const change = (Math.random() - 0.5) * 0.03;
                    currentPrice = currentPrice * (1 + change);
                    prices.push(currentPrice);
                    
                    // Volume aléatoire
                    volumes.push(Math.floor(20000 + Math.random() * 30000));
                }}
                
                return {{ dates, prices, volumes }};
            }}
            
            // Créer le graphique principal
            function createPriceChart() {{
                const ctx = document.getElementById('priceChart').getContext('2d');
                const {{ dates, prices }} = generateChartData();
                
                if (priceChart) {{
                    priceChart.destroy();
                }}
                
                priceChart = new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: dates,
                        datasets: [{{
                            label: 'Prix',
                            data: prices,
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102, 126, 234, 0.1)',
                            tension: 0.1,
                            fill: true,
                            pointRadius: 3,
                            pointHoverRadius: 5,
                            borderWidth: 2
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
                                    color: 'rgba(0,0,0,0.05)',
                                    drawBorder: true
                                }},
                                ticks: {{
                                    callback: function(value, index, values) {{
                                        return value.toFixed(2) + ' €';
                                    }}
                                }}
                            }},
                            x: {{
                                grid: {{
                                    display: false
                                }}
                            }}
                        }},
                        interaction: {{
                            intersect: false,
                            mode: 'index'
                        }}
                    }}
                }});
            }}
            
            // Créer le graphique RSI
            function createRSIChart() {{
                const ctx = document.getElementById('rsiChart').getContext('2d');
                const {{ dates }} = generateChartData();
                const rsiData = Array.from({{length: 31}}, () => 30 + Math.random() * 40);
                
                if (rsiChart) {{
                    rsiChart.destroy();
                }}
                
                rsiChart = new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: dates,
                        datasets: [{{
                            label: 'RSI',
                            data: rsiData,
                            borderColor: '#FF9800',
                            backgroundColor: 'rgba(255, 152, 0, 0.1)',
                            tension: 0.1,
                            fill: true,
                            borderWidth: 2
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                display: false
                            }},
                            annotation: {{
                                annotations: {{
                                    line70: {{
                                        type: 'line',
                                        yMin: 70,
                                        yMax: 70,
                                        borderColor: '#F44336',
                                        borderWidth: 2,
                                        borderDash: [6, 6],
                                        label: {{
                                            content: 'Surachaté (70)',
                                            enabled: true,
                                            position: 'end'
                                        }}
                                    }},
                                    line30: {{
                                        type: 'line',
                                        yMin: 30,
                                        yMax: 30,
                                        borderColor: '#4CAF50',
                                        borderWidth: 2,
                                        borderDash: [6, 6],
                                        label: {{
                                            content: 'Survendu (30)',
                                            enabled: true,
                                            position: 'end'
                                        }}
                                    }}
                                }}
                            }}
                        }},
                        scales: {{
                            y: {{
                                min: 0,
                                max: 100,
                                grid: {{
                                    color: 'rgba(0,0,0,0.05)'
                                }}
                            }},
                            x: {{
                                grid: {{
                                    display: false
                                }}
                            }}
                        }}
                    }}
                }});
            }}
            
            // Créer le graphique MACD
            function createMACDChart() {{
                const ctx = document.getElementById('macdChart').getContext('2d');
                const {{ dates }} = generateChartData();
                
                // Générer des données MACD simulées
                const macdData = [];
                const signalData = [];
                let macd = 0;
                
                for (let i = 0; i < 31; i++) {{
                    macd = Math.sin(i / 5) * 2 + Math.random() * 0.5;
                    macdData.push(macd);
                    signalData.push(macd * 0.8 + Math.random() * 0.2);
                }}
                
                if (macdChart) {{
                    macdChart.destroy();
                }}
                
                macdChart = new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: dates,
                        datasets: [
                            {{
                                label: 'MACD',
                                data: macdData,
                                borderColor: '#2196F3',
                                backgroundColor: 'transparent',
                                tension: 0.1,
                                borderWidth: 2
                            }},
                            {{
                                label: 'Signal',
                                data: signalData,
                                borderColor: '#FF9800',
                                backgroundColor: 'transparent',
                                tension: 0.1,
                                borderWidth: 2
                            }}
                        ]
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
                                grid: {{
                                    color: 'rgba(0,0,0,0.05)'
                                }}
                            }},
                            x: {{
                                grid: {{
                                    display: false
                                }}
                            }}
                        }}
                    }}
                }});
            }}
            
            // Initialiser les graphiques
            window.onload = function() {{
                createPriceChart();
                createRSIChart();
                createMACDChart();
            }};
            
            // Redimensionner les graphiques quand la fenêtre change
            window.addEventListener('resize', function() {{
                if (priceChart) {{
                    priceChart.resize();
                }}
                if (rsiChart) {{
                    rsiChart.resize();
                }}
                if (macdChart) {{
                    macdChart.resize();
                }}
            }});
        </script>
    </body>
    </html>
    """
    return html

def generate_mock_data(symbol):
    """Génère des données simulées"""
    mock_data = {
        'MC.PA': {
            'symbol': 'MC.PA',
            'price': 519.60,
            'change': -0.93,
            'volume': 26164,
            'pe_ratio': 23.76,
            'dividend': 13.00,
            'dividend_yield': 2.48
        },
        'RMS.PA': {
            'symbol': 'RMS.PA',
            'price': 2450.00,
            'change': 0.85,
            'volume': 15000,
            'pe_ratio': 48.50,
            'dividend': 15.00,
            'dividend_yield': 0.61
        },
        'KER.PA': {
            'symbol': 'KER.PA',
            'price': 320.00,
            'change': -1.20,
            'volume': 50000,
            'pe_ratio': 18.30,
            'dividend': 4.50,
            'dividend_yield': 1.40
        }
    }
    return mock_data.get(symbol, mock_data['MC.PA'])

def generate_historical_rows():
    """Génère les lignes du tableau historique"""
    rows = []
    for i in range(10):
        date = datetime.now()
        date = date.replace(day=date.day - i)
        rows.append(f"""
            <tr>
                <td>{date.strftime('%d/%m/%Y')}</td>
                <td>{500 + np.random.randn()*10:.2f} €</td>
                <td>{520 + np.random.randn()*10:.2f} €</td>
                <td>{480 + np.random.randn()*10:.2f} €</td>
                <td>{510 + np.random.randn()*10:.2f} €</td>
                <td>{np.random.randint(20000, 30000):,}</td>
            </tr>
        """)
    return rows

def main():
    st.title("📊 Dashboard Financier - Graphiques Fixes")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        symbol = st.selectbox(
            "Symbole",
            options=["MC.PA", "RMS.PA", "KER.PA", "CDI.PA", "AI.PA", "OR.PA"],
            index=0
        )
        
        period = st.selectbox(
            "Période",
            options=["1J", "1S", "1M", "3M", "1Y"],
            index=2
        )
        
        chart_height = st.slider(
            "Hauteur du graphique",
            min_value=300,
            max_value=600,
            value=400,
            step=50
        )
        
        refresh = st.button("🔄 Rafraîchir")
    
    # Récupérer les données
    stock_data = generate_mock_data(symbol)
    
    # Préparer les données pour le dashboard
    market_hour = datetime.now().hour
    market_open = 9 <= market_hour < 17
    
    dashboard_data = {
        'symbol': symbol,
        'price': stock_data['price'],
        'change': stock_data['change'],
        'volume': stock_data['volume'],
        'pe_ratio': stock_data['pe_ratio'],
        'dividend': stock_data['dividend'],
        'dividend_yield': stock_data['dividend_yield'],
        'last_update': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        'market_open': market_open,
        'period': period,
        'historical_rows': generate_historical_rows()
    }
    
    # Afficher le dashboard
    st.components.v1.html(
        create_dashboard_html(dashboard_data),
        height=1200,
        scrolling=True
    )
    
    # Métriques en bas
    with st.expander("📊 Données en temps réel"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Cours", f"{stock_data['price']:.2f} €", f"{stock_data['change']:.2f}%")
        with col2:
            st.metric("Volume", f"{stock_data['volume']:,}")
        with col3:
            st.metric("P/E", f"{stock_data['pe_ratio']:.2f}")
        with col4:
            st.metric("Dividende", f"{stock_data['dividend']:.2f} €")

if __name__ == "__main__":
    main()
