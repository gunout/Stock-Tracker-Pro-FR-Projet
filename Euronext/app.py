# app.py - Version avec communication JavaScript
import streamlit as st
from datetime import datetime
import pandas as pd
import numpy as np
import json
import time
import random

# Configuration de la page
st.set_page_config(
    page_title="Dashboard Financier MC.PA",
    page_icon="📊",
    layout="wide"
)

def create_dashboard_html(data):
    """Crée le HTML du dashboard avec communication JavaScript"""
    
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
                display: flex;
                align-items: center;
                gap: 10px;
                flex-wrap: wrap;
            }}
            .symbol-title span {{
                color: #667eea;
            }}
            .last-update {{
                color: #666;
                font-size: 14px;
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
            .disconnected {{
                background: #F44336;
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
                transition: transform 0.3s ease;
                position: relative;
                overflow: hidden;
            }}
            .metric-card:hover {{
                transform: translateY(-5px);
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
            .controls {{
                display: flex;
                gap: 10px;
                align-items: center;
            }}
            .refresh-btn {{
                background: #667eea;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 12px;
                transition: background 0.3s ease;
            }}
            .refresh-btn:hover {{
                background: #5a67d8;
            }}
            .refresh-btn:disabled {{
                background: #ccc;
                cursor: not-allowed;
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
        </style>
    </head>
    <body>
        <div class="dashboard">
            <div class="header">
                <div class="symbol-title">
                    <span id="symbol">{data['symbol']}</span> 
                    <span>• Analyse en temps réel</span>
                    <span id="marketStatus" class="market-status {'open' if data['market_open'] else 'closed'}">
                        {'🟢 Ouvert' if data['market_open'] else '🔴 Fermé'}
                    </span>
                    <span id="connectionStatus" class="connection-status connected">
                        <span class="dot"></span> Connecté
                    </span>
                </div>
                <div class="last-update" id="lastUpdate">Dernière mise à jour: {data['last_update']}</div>
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
                        <span>Évolution du cours - <span id="period">{data['period']}</span></span>
                        <div class="controls">
                            <button class="refresh-btn" onclick="requestRefresh()" id="refreshBtn">🔄 Rafraîchir</button>
                        </div>
                    </div>
                    <div class="chart-wrapper">
                        <canvas id="priceChart"></canvas>
                    </div>
                </div>
            </div>
            
            <div id="historical" class="tab-content">
                <div class="chart-container">
                    <table class="historical-table" id="historicalTable">
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
                © 2026 Dashboard Financier - Communication JavaScript active
            </div>
        </div>

        <div id="toast" class="toast"></div>

        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            // ==================== CONFIGURATION ====================
            const DEBUG = true;
            let priceChart, rsiChart, macdChart;
            let autoRefreshInterval = null;
            let isRefreshing = false;
            let lastData = {json.dumps(data)};
            
            // ==================== COMMUNICATION STREAMLIT ====================
            
            // Envoyer des données à Streamlit
            function sendToStreamlit(type, data) {{
                const message = {{
                    type: type,
                    data: data,
                    timestamp: new Date().toISOString()
                }};
                
                if (DEBUG) console.log('📤 Envoi à Streamlit:', message);
                
                // Utiliser l'API de communication de Streamlit
                if (window.Streamlit) {{
                    window.Streamlit.setComponentValue(message);
                }} else {{
                    // Fallback pour le développement
                    if (DEBUG) console.log('⚠️ Streamlit API non disponible');
                }}
            }}
            
            // Recevoir des données de Streamlit
            window.addEventListener('message', function(event) {{
                if (event.data.type === 'streamlit:data') {{
                    const newData = event.data.data;
                    if (DEBUG) console.log('📥 Réception de Streamlit:', newData);
                    updateDashboard(newData);
                }}
            }});
            
            // ==================== MISE À JOUR DU DASHBOARD ====================
            
            function updateDashboard(newData) {{
                if (DEBUG) console.log('🔄 Mise à jour du dashboard avec:', newData);
                
                // Mettre à jour les métriques
                updateMetrics(newData);
                
                // Mettre à jour les graphiques
                updateCharts(newData);
                
                // Mettre à jour la table historique
                if (newData.historical_rows) {{
                    updateHistoricalTable(newData.historical_rows);
                }}
                
                // Mettre à jour la date
                document.getElementById('lastUpdate').textContent = 
                    `Dernière mise à jour: ${{newData.last_update || new Date().toLocaleString('fr-FR')}}`;
                
                // Mettre à jour le statut du marché
                updateMarketStatus(newData.market_open);
                
                // Sauvegarder les dernières données
                lastData = newData;
                
                // Afficher une notification
                showToast('Données mises à jour', 'success');
            }}
            
            function updateMetrics(data) {{
                // Prix
                const priceEl = document.getElementById('price');
                const priceChangeEl = document.getElementById('priceChange');
                if (priceEl) {{
                    priceEl.textContent = data.price.toFixed(2) + ' €';
                    priceEl.classList.add('updating');
                    setTimeout(() => priceEl.classList.remove('updating'), 500);
                }}
                if (priceChangeEl) {{
                    priceChangeEl.textContent = (data.change >= 0 ? '+' : '') + data.change.toFixed(2) + '%';
                    priceChangeEl.className = 'metric-change ' + (data.change >= 0 ? 'positive' : 'negative');
                }}
                
                // Volume
                const volumeEl = document.getElementById('volume');
                if (volumeEl) {{
                    volumeEl.textContent = data.volume.toLocaleString();
                    volumeEl.classList.add('updating');
                    setTimeout(() => volumeEl.classList.remove('updating'), 500);
                }}
                
                // P/E
                const peEl = document.getElementById('pe');
                if (peEl) {{
                    peEl.textContent = data.pe_ratio.toFixed(2);
                    peEl.classList.add('updating');
                    setTimeout(() => peEl.classList.remove('updating'), 500);
                }}
                
                // Dividende
                const dividendEl = document.getElementById('dividend');
                const yieldEl = document.getElementById('yield');
                if (dividendEl) {{
                    dividendEl.textContent = data.dividend.toFixed(2) + ' €';
                    dividendEl.classList.add('updating');
                    setTimeout(() => dividendEl.classList.remove('updating'), 500);
                }}
                if (yieldEl) {{
                    yieldEl.textContent = data.dividend_yield.toFixed(2) + '%';
                }}
            }}
            
            function updateMarketStatus(isOpen) {{
                const statusEl = document.getElementById('marketStatus');
                if (statusEl) {{
                    statusEl.textContent = isOpen ? '🟢 Ouvert' : '🔴 Fermé';
                    statusEl.className = 'market-status ' + (isOpen ? 'open' : 'closed');
                }}
            }}
            
            function updateHistoricalTable(rows) {{
                const tbody = document.getElementById('historicalBody');
                if (tbody && rows) {{
                    tbody.innerHTML = rows.join('');
                }}
            }}
            
            // ==================== GRAPHIQUES ====================
            
            function generateChartData(basePrice) {{
                const dates = [];
                const prices = [];
                let currentPrice = basePrice;
                
                for (let i = 30; i >= 0; i--) {{
                    const date = new Date();
                    date.setDate(date.getDate() - i);
                    dates.push(date.toLocaleDateString('fr-FR'));
                    
                    const change = (Math.random() - 0.5) * 0.03;
                    currentPrice = currentPrice * (1 + change);
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
                            pointRadius: 3,
                            pointHoverRadius: 5,
                            borderWidth: 2
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ display: false }} }},
                        scales: {{
                            y: {{
                                beginAtZero: false,
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
                    macdData.push(Math.sin(i / 5) * 2 + Math.random() * 0.5);
                    signalData.push(macdData[i] * 0.8 + Math.random() * 0.2);
                }}
                
                if (macdChart) macdChart.destroy();
                
                macdChart = new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: dates,
                        datasets: [
                            {{ label: 'MACD', data: macdData, borderColor: '#2196F3', borderWidth: 2 }},
                            {{ label: 'Signal', data: signalData, borderColor: '#FF9800', borderWidth: 2 }}
                        ]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
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
            }}
            
            // ==================== INTERACTIONS ====================
            
            function showTab(tabId) {{
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                
                event.target.classList.add('active');
                document.getElementById(tabId).classList.add('active');
                
                sendToStreamlit('tab_change', {{ tab: tabId }});
            }}
            
            function requestRefresh() {{
                if (isRefreshing) return;
                
                isRefreshing = true;
                const btn = document.getElementById('refreshBtn');
                btn.disabled = true;
                btn.textContent = '⏳ Chargement...';
                
                sendToStreamlit('refresh_request', {{ 
                    symbol: lastData.symbol,
                    timestamp: new Date().toISOString()
                }});
                
                setTimeout(() => {{
                    isRefreshing = false;
                    btn.disabled = false;
                    btn.textContent = '🔄 Rafraîchir';
                }}, 2000);
            }}
            
            function showToast(message, type = 'info') {{
                const toast = document.getElementById('toast');
                toast.textContent = message;
                toast.className = `toast ${{type}} show`;
                
                setTimeout(() => {{
                    toast.classList.remove('show');
                }}, 3000);
            }}
            
            // ==================== AUTO-REFRESH ====================
            
            function startAutoRefresh(seconds) {{
                if (autoRefreshInterval) clearInterval(autoRefreshInterval);
                autoRefreshInterval = setInterval(() => {{
                    requestRefresh();
                }}, seconds * 1000);
                showToast(`Auto-refresh toutes les ${{seconds}}s`, 'info');
            }}
            
            function stopAutoRefresh() {{
                if (autoRefreshInterval) {{
                    clearInterval(autoRefreshInterval);
                    autoRefreshInterval = null;
                    showToast('Auto-refresh arrêté', 'warning');
                }}
            }}
            
            // ==================== INITIALISATION ====================
            
            window.onload = function() {{
                createPriceChart();
                createRSIChart();
                createMACDChart();
                
                // Envoyer un message d'initialisation
                sendToStreamlit('dashboard_ready', {{
                    symbol: lastData.symbol,
                    timestamp: new Date().toISOString()
                }});
                
                if (DEBUG) console.log('✅ Dashboard initialisé');
            }};
            
            window.addEventListener('resize', function() {{
                [priceChart, rsiChart, macdChart].forEach(chart => {{
                    if (chart) chart.resize();
                }});
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
    st.title("📊 Dashboard Financier - Communication JavaScript")
    
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
        
        auto_refresh = st.checkbox("Auto-refresh", value=False)
        if auto_refresh:
            refresh_rate = st.slider("Fréquence (s)", 5, 60, 30)
        
        st.markdown("---")
        st.subheader("📡 Communication")
        st.info("""
        **Événements JavaScript:**
        - 🟢 Dashboard prêt
        - 🔄 Rafraîchissement
        - 📊 Changement d'onglet
        - 📈 Mise à jour données
        """)
    
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
    dashboard_html = create_dashboard_html(dashboard_data)
    st.components.v1.html(dashboard_html, height=1200, scrolling=True)
    
    # Zone pour les messages JavaScript
    with st.expander("📨 Messages reçus du JavaScript"):
        message_placeholder = st.empty()
        
        # Simuler la réception de messages (dans une vraie app, utilisez st.session_state)
        if 'js_messages' not in st.session_state:
            st.session_state.js_messages = []
        
        # Afficher les derniers messages
        for msg in st.session_state.js_messages[-5:]:
            st.json(msg)

if __name__ == "__main__":
    main()
