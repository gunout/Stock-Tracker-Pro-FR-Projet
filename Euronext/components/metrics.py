import streamlit as st

def display_stock_metrics(symbol, data):
    """Affiche les métriques d'une action"""
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
            value=f"{data.get('volume', 0):,}"
        )
    
    with col3:
        st.metric(
            label="P/E",
            value=f"{data.get('pe_ratio', 0):.2f}"
        )
    
    with col4:
        st.metric(
            label="Dividende",
            value=f"{data.get('dividend', 0):.2f} €"
        )

def display_rate_limit_status(limiter):
    """Version simplifiée"""
    try:
        remaining = limiter.get_remaining_requests()
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 Statut API")
        st.sidebar.info(f"Requêtes restantes: {remaining}")
    except:
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 Statut API")
        st.sidebar.info("API prête")
