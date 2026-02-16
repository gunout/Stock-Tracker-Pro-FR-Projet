# app.py - Version avec iframe
import streamlit as st
import pandas as pd
import numpy as np
import json
from pathlib import Path

# Créer un dossier pour les fichiers statiques
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)

def create_standalone_dashboard():
    """Crée un fichier HTML standalone"""
    
    html_content = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Financier</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }
        .dashboard { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .symbol-title { font-size: 24px; font-weight: bold; color: #FF4B4B; }
        .last-update { color: #666; font-size: 14px; margin-top: 5px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .metric-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .metric-label { color: #666; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; }
        .metric-value { font-size: 28px; font-weight: bold; margin: 10px 0; }
        .metric-change { font-size: 14px; }
        .positive { color: #4CAF50; }
        .negative { color: #F44336; }
        .chart-container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 30px; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab { padding: 10px 20px; background: white; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; }
        .tab.active { background: #FF4B4B; color: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f8f9fa; font-weight: 600; }
        .footer { text-align: center; color: #666; font-size: 12px; margin-top: 30px; }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <div class="symbol-title" id="symbol-title">MC.PA - LVMH</div>
            <div class="last-update" id="last-update"></div>
        </div>
        
        <div class="metrics-grid" id="metrics">
            <!-- Rempli par JavaScript -->
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="showTab('chart')">Graphique</button>
            <button class="tab" onclick="showTab('historical')">Données historiques</button>
            <button class="tab" onclick="showTab('indicators')">Indicateurs</button>
        </div>
        
        <div id="chart" class="tab-content active">
            <div class="chart-container">
                <canvas id="mainChart" style="width:100%; height:400px;"></canvas>
            </div>
        </div>
        
        <div id="historical" class="tab-content">
            <div class="chart-container">
                <table id="historical-table">
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
                    <tbody id="historical-body"></tbody>
                </table>
            </div>
        </div>
        
        <div id="indicators" class="tab-content">
            <div class="chart-container">
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
                    <div>
                        <h3>RSI (14)</h3>
                        <canvas id="rsiChart" style="width:100%; height:200px;"></canvas>
                    </div>
                    <div>
                        <h3>MACD</h3>
                        <canvas id="macdChart" style="width:100%; height:200px;"></canvas>
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
        // État global
        let currentData = null;
        let mainChart = null;
        
        // Fonction pour mettre à jour les données
        async function fetchData() {
            // Simuler des données - à remplacer par des appels API réels
            const symbols = ['MC.PA', 'RMS.PA', 'KER.PA', 'CDI.PA'];
            const randomSymbol = symbols[Math.floor(Math.random() * symbols.length)];
            
            // Données simulées
            currentData = {
                symbol: randomSymbol,
                price: 500 + Math.random() * 100,
                change: (Math.random() - 0.5) * 4,
                volume: Math.floor(10000 + Math.random() * 90000),
                pe_ratio: 15 + Math.random() * 20,
                dividend: 10 + Math.random() * 8,
                dividend_yield: 1 + Math.random() * 3
            };
            
            updateUI();
        }
        
        // Mettre à jour l'interface
        function updateUI() {
            if (!currentData) return;
            
            // Mettre à jour le titre
            document.getElementById('symbol-title').textContent = 
                `${currentData.symbol} - ${currentData.symbol === 'MC.PA' ? 'LVMH' : 'Analyse'}`;
            
            // Mettre à jour la date
            document.getElementById('last-update').textContent = 
                `Dernière mise à jour: ${new Date().toLocaleString('fr-FR')}`;
            
            // Mettre à jour les métriques
            const metricsHtml = `
                <div class="metric-card">
                    <div class="metric-label">Cours</div>
                    <div class="metric-value">${currentData.price.toFixed(2)} €</div>
                    <div class="metric-change ${currentData.change >= 0 ? 'positive' : 'negative'}">
                        ${currentData.change >= 0 ? '+' : ''}${currentData.change.toFixed(2)}%
                    </div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Volume</div>
                    <div class="metric-value">${currentData.volume.toLocaleString()}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">P/E</div>
                    <div class="metric-value">${currentData.pe_ratio.toFixed(2)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Dividende</div>
                    <div class="metric-value">${currentData.dividend.toFixed(2)} €</div>
                    <div class="metric-change positive">${currentData.dividend_yield.toFixed(2)}%</div>
                </div>
            `;
            document.getElementById('metrics').innerHTML = metricsHtml;
            
            // Mettre à jour le graphique
            updateCharts();
            
            // Mettre à jour les données historiques
            updateHistoricalData();
        }
        
        // Mettre à jour les graphiques
        function updateCharts() {
            const ctx = document.getElementById('mainChart').getContext('2d');
            
            // Générer des données historiques
            const dates = [];
            const prices = [];
            let price = currentData.price;
            
            for (let i = 30; i >= 0; i--) {
                const date = new Date();
                date.setDate(date.getDate() - i);
                dates.push(date.toLocaleDateString('fr-FR'));
                
                price = price * (1 + (Math.random() - 0.5) * 0.02);
                prices.push(price);
            }
            
            if (mainChart) {
                mainChart.destroy();
            }
            
            mainChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: dates,
                    datasets: [{
                        label: 'Prix',
                        data: prices,
                        borderColor: '#FF4B4B',
                        backgroundColor: 'rgba(255, 75, 75, 0.1)',
                        tension: 0.1,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }
        
        // Mettre à jour les données historiques
        function updateHistoricalData() {
            const tbody = document.getElementById('historical-body');
            let html = '';
            
            for (let i = 0; i < 10; i++) {
                const date = new Date();
                date.setDate(date.getDate() - i);
                
                html += `
                    <tr>
                        <td>${date.toLocaleDateString('fr-FR')}</td>
                        <td>${(currentData.price * (1 + (Math.random() - 0.5) * 0.02)).toFixed(2)} €</td>
                        <td>${(currentData.price * (1 + Math.random() * 0.01)).toFixed(2)} €</td>
                        <td>${(currentData.price * (1 - Math.random() * 0.01)).toFixed(2)} €</td>
                        <td>${(currentData.price * (1 + (Math.random() - 0.5) * 0.01)).toFixed(2)} €</td>
                        <td>${Math.floor(10000 + Math.random() * 90000).toLocaleString()}</td>
                    </tr>
                `;
            }
            
            tbody.innerHTML = html;
        }
        
        // Changer d'onglet
        function showTab(tabId) {
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        }
        
        // Initialisation
        fetchData();
        setInterval(fetchData, 30000); // Mise à jour toutes les 30 secondes
    </script>
</body>
</html>
    """
    
    # Sauvegarder le fichier HTML
    with open(static_dir / "dashboard.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return static_dir / "dashboard.html"

def main():
    st.set_page_config(layout="wide")
    
    st.title("🎯 Dashboard Financier Avancé")
    
    # Créer le dashboard standalone
    dashboard_path = create_standalone_dashboard()
    
    # Sidebar
    with st.sidebar:
        st.header("Contrôles")
        
        # Mode d'affichage
        view_mode = st.selectbox(
            "Mode d'affichage",
            ["Dashboard Complet", "Streamlit + Dashboard", "Données brutes"]
        )
        
        # Symboles
        symbols = st.multiselect(
            "Symboles à surveiller",
            ["MC.PA", "RMS.PA", "KER.PA", "CDI.PA", "AI.PA", "OR.PA"],
            default=["MC.PA"]
        )
        
        # Actualisation
        auto_refresh = st.checkbox("Actualisation automatique", value=True)
        if auto_refresh:
            refresh_rate = st.slider("Fréquence (secondes)", 10, 60, 30)
    
    if view_mode == "Dashboard Complet":
        # Afficher le dashboard en plein écran
        st.components.v1.html(
            open(dashboard_path, encoding="utf-8").read(),
            height=1000,
            scrolling=True
        )
        
    elif view_mode == "Streamlit + Dashboard":
        # Split view
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Contrôles Streamlit")
            
            # Afficher les données en temps réel
            for symbol in symbols:
                with st.expander(f"📊 {symbol}", expanded=True):
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Cours", f"{500 + np.random.randn()*50:.2f} €")
                    with col_b:
                        st.metric("Volume", f"{np.random.randint(10000, 100000):,}")
                    with col_c:
                        st.metric("Variation", f"{np.random.randn()*2:.2f}%")
        
        with col2:
            st.subheader("🎨 Dashboard")
            st.components.v1.html(
                open(dashboard_path, encoding="utf-8").read(),
                height=600,
                scrolling=True
            )
    
    else:  # Données brutes
        st.subheader("📋 Données en temps réel")
        
        # Tableau de bord simple
        for symbol in symbols:
            data = {
                "Symbole": symbol,
                "Prix": f"{500 + np.random.randn()*50:.2f} €",
                "Variation": f"{np.random.randn()*2:.2f}%",
                "Volume": f"{np.random.randint(10000, 100000):,}",
                "Dernière mise à jour": datetime.now().strftime("%H:%M:%S")
            }
            
            df = pd.DataFrame([data])
            st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Actualisation automatique
    if auto_refresh and 'refresh_rate' in locals():
        st.markdown(f"🔄 Actualisation toutes les {refresh_rate} secondes")
        st.markdown(f"Dernière mise à jour: {datetime.now().strftime('%H:%M:%S')}")
        import time
        time.sleep(refresh_rate)
        st.rerun()

if __name__ == "__main__":
    main()
