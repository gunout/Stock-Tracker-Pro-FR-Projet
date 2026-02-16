# src/app.py
import streamlit as st
from datetime import datetime
import time

# Configuration de la page (DOIT être la première commande Streamlit)
st.set_page_config(
    page_title="Analyse Financière MC.PA",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Imports locaux
from src.api.client import FinancialAPIClient
from src.api.rate_limiter import RateLimiter
from src.components.metrics import display_stock_metrics, display_rate_limit_status
from src.config.settings import AppConfig, DEFAULT_SYMBOLS

# Initialisation des composants
@st.cache_resource
def init_api_client():
    """Initialise le client API (une seule fois)"""
    return FinancialAPIClient()

@st.cache_resource
def init_rate_limiter():
    """Initialise le rate limiter (une seule fois)"""
    return RateLimiter(max_requests=30, time_window=60)

def main():
    """Fonction principale de l'application"""
    
    # Titre
    st.title(f"{AppConfig.APP_ICON} {AppConfig.APP_NAME}")
    st.caption(f"Dernière mise à jour: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Initialisation
    api_client = init_api_client()
    rate_limiter = init_rate_limiter()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Sélection des symboles
        symbols = st.multiselect(
            "Symboles à analyser",
            options=DEFAULT_SYMBOLS + ["CDI.PA", "AI.PA", "OR.PA"],
            default=["MC.PA"]
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
                max_value=60,
                value=5
            )
        
        # Affichage du statut rate limiting
        display_rate_limit_status(rate_limiter)
    
    # Corps principal
    if symbols:
        # Vérification rate limiting
        if rate_limiter.can_proceed() or refresh:
            
            if refresh:
                rate_limiter.add_request()
            
            # Récupération des données
            data = api_client.get_multiple_stocks(symbols)
            
            # Affichage par symbole
            for symbol in symbols:
                if symbol in data and data[symbol]:
                    with st.container():
                        st.subheader(f"📈 {symbol}")
                        display_stock_metrics(symbol, data[symbol])
                        
                        # Graphique simulé
                        chart_data = pd.DataFrame({
                            'Date': pd.date_range(start='2025-01-01', periods=30, freq='D'),
                            'Prix': [data[symbol]['price'] * (1 + i/100) for i in range(30)]
                        })
                        st.line_chart(chart_data.set_index('Date'))
                        
                        st.markdown("---")
                else:
                    st.warning(f"⚠️ Données non disponibles pour {symbol}")
        else:
            wait = rate_limiter.get_wait_time()
            st.error(f"🔴 Limite de requêtes atteinte. Veuillez patienter {wait:.0f} secondes.")
            
            # Compte à rebours
            progress = 1 - (wait / 60)
            st.progress(progress)
            
            # Bouton pour forcer
            if st.button("Forcer la mise à jour"):
                st.session_state.request_history.clear()
                st.rerun()
    else:
        st.info("👈 Sélectionnez au moins un symbole dans la sidebar")
    
    # Rafraîchissement automatique
    if auto_refresh and 'refresh_interval' in locals():
        time.sleep(1)
        st.rerun()

if __name__ == "__main__":
    main()