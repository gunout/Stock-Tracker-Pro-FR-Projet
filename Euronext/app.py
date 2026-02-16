# app.py - Version avec mise à jour toutes les 3 secondes
import streamlit as st
from datetime import datetime
import pandas as pd
import numpy as np
import json
import time
import threading
from streamlit.components.v1 import html

# Configuration de la page
st.set_page_config(
    page_title="Dashboard Financier Live MC.PA",
    page_icon="📊",
    layout="wide"
)

# Initialisation du session state
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()
if 'data_history' not in st.session_state:
    st.session_state.data_history = []
if 'update_counter' not in st.session_state:
    st.session_state.update_counter = 0
if 'current_symbol' not in st.session_state:
    st.session_state.current_symbol = "MC.PA"

def generate_live_data(symbol):
    """Génère des données en direct avec variations réalistes"""
    base_prices = {
        'MC.PA': 519.60,
        'RMS.PA': 2450.00,
        'KER.PA': 320.00,
        'CDI.PA': 65.50,
        'AI.PA': 180.30,
        'OR.PA': 95.20
    }
    
    base_volumes = {
        'MC.PA': 26164,
        'RMS.PA': 15000,
        'KER.PA': 50000,
        'CDI.PA': 35000,
        'AI.PA': 28000,
        'OR.PA': 42000
    }
    
    base_price = base_prices.get(symbol, 100.00)
    base_volume = base_volumes.get(symbol, 20000)
    
    # Variation aléatoire réaliste (entre -2% et +2%)
    price_change = np.random.uniform(-2.0, 2.0)
    new_price = base_price * (1 + price_change/100)
    
    # Variation du volume
    volume_change = np.random.uniform(-15, 15)
    new_volume = int(base_volume * (1 + volume_change/100))
    
    # Calcul des autres métriques
    pe_ratio = new_price / np.random.uniform(15, 25)
    dividend = new_price * np.random.uniform(0.02, 0.04)
    
    return {
        'symbol': symbol,
        'price': round(new_price, 2),
        'change': round(price_change, 2),
        'volume': new_volume,
        'pe_ratio': round(pe_ratio, 2),
        'dividend': round(dividend, 2),
        'dividend_yield': round((dividend / new_price) * 100, 2),
        'timestamp': datetime.now().isoformat()
    }

def generate_historical_rows(data):
    """Génère les lignes du tableau historique en direct"""
    rows = []
    for i in range(10):
        date = datetime.now()
        date = date.replace(second=date.second - i*30)  # Espacement de 30 secondes
        
        # Variation autour du prix actuel
        price_variation = np.random.uniform(-5, 5)
        historical_price = data['price'] * (1 + price_variation/100)
        
        rows.append(f"""
            <tr>
                <td>{date.strftime('%H:%M:%S')}</td>
                <td>{historical_price - np.random.uniform(0.5, 2):.2f} €</td>
                <td>{historical_price + np.random.uniform(0.5, 2):.2f} €</td>
                <td>{historical_price - np.random.uniform(1, 3):.2f} €</td>
                <td>{historical_price:.2f} €</td>
                <td>{int(data['volume'] * np.random.uniform(0.8, 1.2)):,}</td>
            </tr>
        """)
    return rows

def create_dashboard_html(data, update_counter):
    """Crée le HTML du dashboard avec mise à jour automatique"""
    
    html_code = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard Financier Live</title>
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
                display: flex;
                align-items: center;
                gap: 10px;
                flex-wrap: wrap;
            }}
            .live-badge {{
                background: #ff4444;
                color: white;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 14px;
                display: inline-flex;
                align-items: center;
                gap: 5px;
                animation: pulse 2s infinite;
            }}
            @keyframes pulse {{
                0% {{ opacity: 1; }}
                50% {{ opacity: 0.7; }}
                100% {{ opacity: 1; }}
            }}
            .update-counter {{
                background: #667eea;
                color: white;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 14px;
                margin-left: 10px;
            }}
            .connection-status {{
                display: inline-flex;
                align-items: center;
                gap: 5px;
                padding: 5px 10px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
                margin-left: 10px;
            }}
            .connected {{
                background: #4CAF50;
                color: white;
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
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }}
            .metric-card.updating {{
                transform: scale(1.02);
                box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
            }}
            .metric-card.updating::after {{
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 3px;
                background: linear-gradient(90deg, transparent, #667eea, transparent);
                animation: loading 1.5s infinite;
            }}
            @keyframes loading {{
                0% {{ left: -100%; }}
                100% {{ left: 100%; }}
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
                transition: color 0.3s ease;
            }}
            .metric-value.changed {{
                color: #667eea;
            }}
            .metric-change {{
                font-size: 14px;
                transition: all 0.3s ease;
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
                height: 400px;
                margin: 0 auto;
            }}
            .chart-title {{
                font-size: 18px;
                font-weight: bold;
                color: #333;
                margin-bottom: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .timer {{
                font-family: monospace;
                font-size: 16px;
                color: #667eea;
                background: #f0f0f0;
                padding: 5px 10px;
                border-radius: 5px;
            }}
            .controls {{
                display: flex;
                gap: 10px;
                align-items: center;
            }}
            .refresh-btn {{
                background: #667eea;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
                transition: all 0.3s ease;
            }}
            .refresh-btn:hover {{
                background: #5a67d8;
                transform: scale(1.05);
            }}
            .refresh-btn:disabled {{
                background: #ccc;
                cursor: not-allowed;
                transform: none;
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
                height: 250px;
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
            .toast {{
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: white;
                padding: 15px 25px;
                border-radius: 10px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.2);
                transform: translateX(400px);
                transition: transform 0.3s ease;
                z-index: 1000;
            }}
            .toast.show {{
                transform: translateX(0);
            }}
            .toast.success {{ border-left: 4px solid #4CAF50; }}
            .toast.error {{ border-left: 4px solid #F44336; }}
            .toast.warning {{ border-left: 4px solid #FF9800; }}
            .toast.info {{ border-left: 4px solid #2196F3; }}
        </style>
    </head>
    <body>
        <div class="dashboard">
            <div class="header">
                <div class="symbol-title">
                    <span id="symbol">{data['symbol']}</span> 
                    <span>• Trading en direct</span>
                    <span class="live-badge">
                        <span>🔴 LIVE</span>
                    </span>
                    <span id="updateCounter" class="update-counter">Mise à jour #{update_counter}</span>
                    <span id="connectionStatus" class="connection-status connected">
                        📡 Connecté
                    </span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div class="last-update" id="lastUpdate">
                        Dernière mise à jour: {data['last_update']}
                    </div>
                    <div class="timer" id="timer">Prochaine mise à jour dans 3s</div>
                </div>
            </div>
            
            <div class="metrics-grid" id="metricsGrid">
                <div class="metric-card" id="priceCard">
                    <div class="metric-label">Cours</div>
                    <div class="metric-value" id="price">{data['price']:.2f} €</div>
                    <div class="metric-change" id="priceChange" class="{'positive' if data['change'] >= 0 else 'negative'}">
                        {data['change']:+.2f}%
                    </div>
                </div>
                <div class="metric-card" id="volumeCard">
                    <div class="metric-label">Volume</div>
                    <div class="metric-value" id="volume">{data['volume']:,}</div>
                </div>
                <div class="metric-card" id="peCard">
                    <div class="metric-label">P/E</div>
                    <div class="metric-value" id="pe">{data['pe_ratio']:.2f}</div>
                </div>
                <div class="metric-card" id="dividendCard">
                    <div class="metric-label">Dividende</div>
                    <div class="metric-value" id="dividend">{data['dividend']:.2f} €</div>
                    <div class="metric-change positive" id="yield">{data['dividend_yield']:.2f}%</div>
                </div>
            </div>

            <div class="tabs">
                <button class="tab active" onclick="showTab('chart')">📈 Graphique</button>
                <button class="tab" onclick="showTab('historical')">📊 Données historiques</button>
                <button class="tab" onclick="showTab('indicators')">📉 Indicateurs</button>
            </div>
            
            <div id="chart" class="tab-content active">
                <div class="chart-container">
                    <div class="chart-title">
                        <span>Évolution en direct - <span id="period">{data['period']}</span></span>
                        <div class="controls">
                            <button class="refresh-btn" onclick="forceRefresh()" id="refreshBtn">🔄 Rafraîchir maintenant</button>
                        </div>
                    </div>
                    <div class="chart-wrapper">
                        <canvas id="priceChart"></canvas>
                    </div>
                </div>
            </div>
            
            <div id="historical" class="tab-content">
                <div class="chart-container">
                    <div class="chart-title">
                        <span>Transactions récentes</span>
                        <span class="live-badge" style="font-size: 12px;">Mise à jour en direct</span>
                    </div>
                    <table class="historical-table" id="historicalTable">
                        <thead>
                            <tr>
                                <th>Heure</th>
                                <th>Ouverture</th>
                                <th>Plus haut</th>
                                <th>Plus bas</th>
                                <th>Clôture</th>
                                <th>Volume</th>
                            </tr>
                        </thead>
                        <tbody id="historicalBody">
                            {''.join(data['historical_rows'])}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div id="indicators" class="tab-content">
                <div class="chart-container">
                    <div class="indicators-grid">
                        <div>
                            <div class="chart-title">RSI (14) - Direct</div>
                            <div class="indicator-chart">
                                <canvas id="rsiChart"></canvas>
                            </div>
                        </div>
                        <div>
                            <div class="chart-title">MACD - Direct</div>
                            <div class="indicator-chart">
                                <canvas id="macdChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                © 2026 Dashboard Financier - Mise à jour toutes les 3 secondes
            </div>
        </div>

        <div id="toast" class="toast"></div>

        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            // ==================== CONFIGURATION ====================
            let priceChart, rsiChart, macdChart;
            let updateInterval = 3000; // 3 secondes
            let countdown = 3;
            let isRefreshing = false;
            let lastData = {json.dumps(data)};
            let updateCounter = {update_counter};
            
            // ==================== COMMUNICATION AVEC STREAMLIT ====================
            
            function sendToStreamlit(type, data) {{
                const message = {{
                    type: type,
                    data: data,
                    counter: updateCounter,
                    timestamp: new Date().toISOString()
                }};
                
                console.log('📤 Envoi à Streamlit:', message);
                
                if (window.parent) {{
                    window.parent.postMessage({{
                        type: 'streamlit:message',
                        data: message
                    }}, '*');
                }}
            }}
            
            // ==================== MISE À JOUR DES DONNÉES ====================
            
            function requestDataUpdate() {{
                if (isRefreshing) return;
                
                isRefreshing = true;
                updateCounter++;
                
                // Mettre à jour le compteur
                document.getElementById('updateCounter').textContent = `Mise à jour #{updateCounter}`;
                
                // Animation des cartes
                document.querySelectorAll('.metric-card').forEach(card => {{
                    card.classList.add('updating');
                }});
                
                // Envoyer la requête à Streamlit
                sendToStreamlit('request_update', {{
                    symbol: lastData.symbol,
                    counter: updateCounter
                }});
                
                // Reset après animation
                setTimeout(() => {{
                    document.querySelectorAll('.metric-card').forEach(card => {{
                        card.classList.remove('updating');
                    }});
                    isRefreshing = false;
                }}, 500);
            }}
            
            function updateDashboard(newData) {{
                console.log('📥 Réception nouvelles données:', newData);
                
                // Mettre à jour les métriques avec animation
                updateMetricWithAnimation('price', newData.price.toFixed(2) + ' €');
                updateMetricWithAnimation('volume', newData.volume.toLocaleString());
                updateMetricWithAnimation('pe', newData.pe_ratio.toFixed(2));
                updateMetricWithAnimation('dividend', newData.dividend.toFixed(2) + ' €');
                
                // Mettre à jour la variation
                const changeEl = document.getElementById('priceChange');
                changeEl.textContent = (newData.change >= 0 ? '+' : '') + newData.change.toFixed(2) + '%';
                changeEl.className = 'metric-change ' + (newData.change >= 0 ? 'positive' : 'negative');
                
                // Mettre à jour le rendement
                document.getElementById('yield').textContent = newData.dividend_yield.toFixed(2) + '%';
                
                // Mettre à jour la date
                document.getElementById('lastUpdate').textContent = 
                    `Dernière mise à jour: ${{newData.last_update}}`;
                
                // Mettre à jour le tableau historique
                if (newData.historical_rows) {{
                    document.getElementById('historicalBody').innerHTML = newData.historical_rows.join('');
                }}
                
                // Mettre à jour les graphiques
                updateCharts(newData);
                
                // Sauvegarder les données
                lastData = newData;
                
                // Notification
                showToast('Données mises à jour en direct', 'success');
            }}
            
            function updateMetricWithAnimation(id, newValue) {{
                const el = document.getElementById(id);
                if (el && el.textContent !== newValue) {{
                    el.textContent = newValue;
                    el.classList.add('changed');
                    setTimeout(() => el.classList.remove('changed'), 500);
                }}
            }}
            
            // ==================== GRAPHIQUES ====================
            
            function generateChartData(basePrice) {{
                const points = 30;
                const dates = [];
                const prices = [];
                let currentPrice = basePrice;
                
                for (let i = points; i >= 0; i--) {{
                    const date = new Date();
                    date.setSeconds(date.getSeconds() - i * 3);
                    dates.push(date.toLocaleTimeString('fr-FR'));
                    
                    if (i > 0) {{
                        const change = (Math.random() - 0.5) * 0.02;
                        currentPrice = currentPrice * (1 + change);
                    }}
                    prices.push(currentPrice);
                }}
                
                return {{ dates, prices }};
            }}
            
            function createPriceChart() {{
                const ctx = document.getElementById('priceChart').getContext('2d');
                const {{ dates, prices }} = generateChartData(lastData.price);
                
                if (priceChart) priceChart.destroy();
                
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
                            pointRadius: 2,
                            pointHoverRadius: 4,
                            borderWidth: 2
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        animation: {{ duration: 300 }},
                        plugins: {{ legend: {{ display: false }} }},
                        scales: {{
                            y: {{
                                ticks: {{ callback: v => v.toFixed(2) + ' €' }}
                            }}
                        }}
                    }}
                }});
            }}
            
            function createRSIChart() {{
                const ctx = document.getElementById('rsiChart').getContext('2d');
                const {{ dates }} = generateChartData(lastData.price);
                const rsiData = Array.from({{length: 31}}, () => 30 + Math.random() * 40);
                
                if (rsiChart) rsiChart.destroy();
                
                rsiChart = new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: dates,
                        datasets: [{{
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
                        animation: {{ duration: 300 }},
                        plugins: {{ legend: {{ display: false }} }},
                        scales: {{ y: {{ min: 0, max: 100 }} }}
                    }}
                }});
            }}
            
            function createMACDChart() {{
                const ctx = document.getElementById('macdChart').getContext('2d');
                const {{ dates }} = generateChartData(lastData.price);
                
                const macdData = [];
                const signalData = [];
                for (let i = 0; i < 31; i++) {{
                    macdData.push(Math.sin(i / 5) * 2 + Math.random() * 0.3);
                    signalData.push(macdData[i] * 0.8 + Math.random() * 0.2);
                }}
                
                if (macdChart) macdChart.destroy();
                
                macdChart = new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: dates,
                        datasets: [
                            {{ data: macdData, borderColor: '#2196F3', borderWidth: 2 }},
                            {{ data: signalData, borderColor: '#FF9800', borderWidth: 2 }}
                        ]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        animation: {{ duration: 300 }},
                        plugins: {{ legend: {{ display: false }} }}
                    }}
                }});
            }}
            
            function updateCharts(data) {{
                if (priceChart) {{
                    const {{ dates, prices }} = generateChartData(data.price);
                    priceChart.data.labels = dates;
                    priceChart.data.datasets[0].data = prices;
                    priceChart.update();
                }}
                
                if (rsiChart) {{
                    const {{ dates }} = generateChartData(data.price);
                    rsiChart.data.labels = dates;
                    rsiChart.update();
                }}
                
                if (macdChart) {{
                    const {{ dates }} = generateChartData(data.price);
                    macdChart.data.labels = dates;
                    macdChart.update();
                }}
            }}
            
            // ==================== TIMER ====================
            
            function startTimer() {{
                const timerEl = document.getElementById('timer');
                countdown = 3;
                
                const timer = setInterval(() => {{
                    countdown--;
                    timerEl.textContent = `Prochaine mise à jour dans ${countdown}s`;
                    
                    if (countdown <= 0) {{
                        countdown = 3;
                        requestDataUpdate();
                    }}
                }}, 1000);
                
                return timer;
            }}
            
            // ==================== INTERACTIONS ====================
            
            function showTab(tabId) {{
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                
                event.target.classList.add('active');
                document.getElementById(tabId).classList.add('active');
                
                sendToStreamlit('tab_change', {{ tab: tabId }});
            }}
            
            function forceRefresh() {{
                const btn = document.getElementById('refreshBtn');
                btn.disabled = true;
                btn.textContent = '⏳ Chargement...';
                
                requestDataUpdate();
                
                setTimeout(() => {{
                    btn.disabled = false;
                    btn.textContent = '🔄 Rafraîchir maintenant';
                }}, 1000);
            }}
            
            function showToast(message, type = 'info') {{
                const toast = document.getElementById('toast');
                toast.textContent = message;
                toast.className = `toast ${{type}} show`;
                
                setTimeout(() => {{
                    toast.classList.remove('show');
                }}, 2000);
            }}
            
            // ==================== INITIALISATION ====================
            
            window.onload = function() {{
                createPriceChart();
                createRSIChart();
                createMACDChart();
                
                // Démarrer le timer
                const timer = startTimer();
                
                // Envoyer un message d'initialisation
                sendToStreamlit('dashboard_ready', {{
                    symbol: lastData.symbol,
                    message: 'Dashboard prêt - Mise à jour toutes les 3s'
                }});
                
                console.log('✅ Dashboard live initialisé - Mise à jour toutes les 3s');
            }};
            
            window.addEventListener('resize', function() {{
                [priceChart, rsiChart, macdChart].forEach(chart => {{
                    if (chart) chart.resize();
                }});
            }});
            
            // ==================== RÉCEPTION DES DONNÉES ====================
            
            window.addEventListener('message', function(event) {{
                if (event.data.type === 'streamlit:update') {{
                    updateDashboard(event.data.data);
                }}
            }});
        </script>
    </body>
    </html>
    """
    return html_code

def main():
    st.title("📈 Trading en Direct - Mise à jour toutes les 3 secondes")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration Live")
        
        symbol = st.selectbox(
            "Symbole",
            options=["MC.PA", "RMS.PA", "KER.PA", "CDI.PA", "AI.PA", "OR.PA"],
            index=0,
            key="symbol_selector"
        )
        
        st.session_state.current_symbol = symbol
        
        period = st.selectbox(
            "Période d'affichage",
            options=["1H", "4H", "1J", "1S", "1M"],
            index=2
        )
        
        st.markdown("---")
        st.subheader("📊 Statistiques live")
        
        # Afficher le compteur de mises à jour
        st.metric(
            "Mises à jour effectuées",
            st.session_state.update_counter,
            delta="+1 toutes les 3s"
        )
        
        # Dernière mise à jour
        st.caption(f"Dernière mise à jour: {st.session_state.last_update.strftime('%H:%M:%S')}")
        
        # Bouton de contrôle
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⏸️ Pause", use_container_width=True):
                st.session_state.paused = True
        with col2:
            if st.button("▶️ Reprendre", use_container_width=True):
                st.session_state.paused = False
        
        st.markdown("---")
        st.info("""
        **🔄 Mise à jour automatique**
        - Intervalle: 3 secondes
        - Données en temps réel
        - Graphiques dynamiques
        """)
    
    # Générer les données en direct
    data = generate_live_data(symbol)
    st.session_state.update_counter += 1
    st.session_state.last_update = datetime.now()
    
    # Préparer les données pour le dashboard
    market_hour = datetime.now().hour
    market_open = 9 <= market_hour < 17
    
    dashboard_data = {
        'symbol': symbol,
        'price': data['price'],
        'change': data['change'],
        'volume': data['volume'],
        'pe_ratio': data['pe_ratio'],
        'dividend': data['dividend'],
        'dividend_yield': data['dividend_yield'],
        'last_update': datetime.now().strftime('%H:%M:%S'),
        'market_open': market_open,
        'period': period,
        'historical_rows': generate_historical_rows(data)
    }
    
    # Afficher le dashboard
    dashboard_html = create_dashboard_html(dashboard_data, st.session_state.update_counter)
    html(dashboard_html, height=1200)
    
    # Zone de debug pour les messages
    with st.expander("📨 Messages reçus du JavaScript"):
        if 'js_messages' not in st.session_state:
            st.session_state.js_messages = []
        
        # Simuler la réception de messages (dans une vraie app, utilisez st.query_params)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📤 Simuler envoi au JS"):
                st.components.v1.html("""
                <script>
                    window.parent.postMessage({
                        type: 'streamlit:update',
                        data: {
                            price: 520.50,
                            change: 0.75,
                            volume: 28150,
                            last_update: new Date().toLocaleTimeString('fr-FR')
                        }
                    }, '*');
                </script>
                """, height=0)
        
        with col2:
            if st.button("🗑️ Effacer les messages"):
                st.session_state.js_messages = []
        
        # Afficher les derniers messages
        for msg in st.session_state.js_messages[-5:]:
            st.json(msg)
    
    # Auto-refresh toutes les 3 secondes
    if not st.session_state.get('paused', False):
        time.sleep(3)
        st.rerun()

if __name__ == "__main__":
    main()
