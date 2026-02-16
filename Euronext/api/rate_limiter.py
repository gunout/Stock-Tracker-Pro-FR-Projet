# test_rate_limiter.py
import streamlit as st
from api.rate_limiter import RateLimiter

st.set_page_config(page_title="Test Rate Limiter", page_icon="🧪")

st.title("🧪 Test du Rate Limiter")

# Initialisation
if 'test_limiter' not in st.session_state:
    st.session_state.test_limiter = RateLimiter(max_requests=5, time_window=10)

limiter = st.session_state.test_limiter

# Affichage des stats
st.subheader("Statistiques")
stats = limiter.get_stats()
col1, col2, col3 = st.columns(3)
col1.metric("Requêtes actuelles", stats['current_requests'])
col2.metric("Maximum", stats['max_requests'])
col3.metric("Attente", f"{stats['wait_time']:.1f}s")

# Boutons de test
col1, col2 = st.columns(2)
with col1:
    if st.button("➕ Ajouter une requête"):
        if limiter.can_proceed():
            limiter.add_request()
            st.success("Requête ajoutée !")
        else:
            st.error(f"Rate limit atteint ! Attendez {limiter.get_wait_time():.1f}s")
    st.rerun()

with col2:
    if st.button("🗑️ Effacer historique"):
        limiter.clear_history()
        st.success("Historique effacé !")
        st.rerun()

# Afficher l'historique
st.subheader("Historique des requêtes")
if st.session_state.request_history:
    for i, ts in enumerate(st.session_state.request_history):
        st.write(f"{i+1}. {ts.strftime('%H:%M:%S')}")
else:
    st.info("Aucune requête dans l'historique")
