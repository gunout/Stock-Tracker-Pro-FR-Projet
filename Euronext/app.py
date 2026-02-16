# app.py - Version avec communication JavaScript ↔ Python
import streamlit as st
import pandas as pd
import numpy as np
import json
import time
from datetime import datetime

st.set_page_config(layout="wide")

# CSS personnalisé
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .dashboard-container {
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

def create_interactive_dashboard():
    """Crée un dashboard avec communication bidirectionnelle"""
    
    html = """
    <div class="dashboard-container">
        <div id="dashboard-root">
            <!-- Le dashboard React sera monté ici -->
        </div>
    </div>

    <script>
        // Configuration de la communication avec Streamlit
        function sendToStreamlit(data) {
            const event = new CustomEvent("streamlit:message", {
                detail: { data: data }
            });
            window.dispatchEvent(event);
        }

        // Recevoir les données de Streamlit
        window.addEventListener("message", function(event) {
            if (event.data.type === "streamlit:data") {
                updateDashboard(event.data.payload);
            }
        });

        // Mettre à jour le dashboard
        function updateDashboard(data) {
            console.log("Données reçues:", data);
            
            // Mettre à jour les métriques
            const metrics = data.metrics;
            document.querySelectorAll('.metric-value').forEach((el, index) => {
                if (index === 0) el.textContent = metrics.price + ' €';
                if (index === 1) el.textContent = metrics.volume;
                if (index === 2) el.textContent = metrics.pe;
                if (index === 3) el.textContent = metrics.dividend + ' €';
            });
            
            // Mettre à jour le graphique si Chart.js est chargé
            if (window.priceChart) {
                window.priceChart.data.datasets[0].data = data.chartData.prices;
                window.priceChart.update();
            }
        }

        // Initialiser le dashboard
        window.onload = function() {
            // Demander les données initiales
            sendToStreamlit({ action: "getInitialData" });
            
            // Configurer les événements
            document.getElementById('refreshBtn').addEventListener('click', function() {
                sendToStreamlit({ action: "refreshData" });
            });
        };
    </script>
    """
    
    return html

def get_real_time_data(symbol):
    """Simule des données en temps réel"""
    return {
        'price': 500 + np.random.randn() * 50,
        'volume': np.random.randint(10000, 100000),
        'pe': 15 + np.random.randn() * 5,
        'dividend': 10 + np.random.randn() * 2
    }

def main():
    st.title("🚀 Dashboard Financier Interactif")
    
    # Sidebar avec contrôles
    with st.sidebar:
        st.header("🎮 Contrôles")
        
        symbol = st.selectbox(
            "Symbole",
            ["MC.PA", "RMS.PA", "KER.PA", "CDI.PA"],
            index=0
        )
        
        refresh_rate = st.slider("Fréquence de mise à jour (s)", 1, 10, 3)
        
        st.markdown("---")
        
        # Métriques en temps réel
        st.subheader("📊 Données actuelles")
        data_placeholder = st.empty()
        
        # Historique des requêtes
        st.subheader("📝 Log")
        log_placeholder = st.empty()
    
    # Zone principale avec le dashboard
    st.components.v1.html(create_interactive_dashboard(), height=800)
    
    # Simulation de données en temps réel
    log = []
    
    for i in range(100):  # Boucle infinie en production
        # Mettre à jour les données
        data = get_real_time_data(symbol)
        
        # Mettre à jour la sidebar
        with data_placeholder.container():
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Prix", f"{data['price']:.2f} €")
                st.metric("P/E", f"{data['pe']:.2f}")
            with col2:
                st.metric("Volume", f"{data['volume']:,}")
                st.metric("Dividende", f"{data['dividend']:.2f} €")
        
        # Mettre à jour le log
        log.append(f"{datetime.now().strftime('%H:%M:%S')} - Données mises à jour")
        if len(log) > 5:
            log.pop(0)
        
        with log_placeholder.container():
            for entry in log:
                st.text(entry)
        
        # Envoyer les données au dashboard via iframe (simulé)
        # Dans une vraie implémentation, vous utiliseriez st.experimental_rerun()
        # ou une websocket
        
        time.sleep(refresh_rate)
        st.rerun()

if __name__ == "__main__":
    main()
