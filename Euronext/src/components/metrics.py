# src/components/metrics.py
import streamlit as st
import pandas as pd

def display_stock_metrics(symbol: str, data: dict):
    """Affiche les métriques d'une action"""
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Cours",
            value=f"{data.get('price', 0):.2f} €",
            delta=f"{data.get('change', 0):.2f}%"
        )
    
    with col2:
        st.metric(
            label="Volume",
            value=f"{data.get('volume', 0):,}",
            delta=f"{data.get('volume_change', 0):.1f}%"
        )
    
    with col3:
        st.metric(
            label="P/E",
            value=f"{data.get('pe_ratio', 0):.2f}"
        )
    
    with col4:
        st.metric(
            label="Dividende",
            value=f"{data.get('dividend', 0):.2f} €",
            delta=f"{data.get('dividend_yield', 0):.2f}%"
        )

def display_rate_limit_status(limiter):
    """Affiche le statut du rate limiting"""
    
    remaining = limiter.get_remaining_requests()
    wait_time = limiter.get_wait_time()
    
    # Barre de progression
    progress = remaining / limiter.max_requests
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Statut API")
    
    # Jauge de requêtes
    st.sidebar.progress(progress)
    st.sidebar.caption(f"Requêtes restantes: {remaining}/{limiter.max_requests}")
    
    if wait_time > 0:
        st.sidebar.warning(f"⏳ Attendre {wait_time:.0f}s")
    
    # Historique
    if st.sidebar.checkbox("Afficher l'historique"):
        history = list(st.session_state.request_history)
        if history:
            df = pd.DataFrame({
                "Timestamp": history,
                "Âge (s)": [(datetime.now() - ts).total_seconds() for ts in history]
            })
            st.sidebar.dataframe(df)