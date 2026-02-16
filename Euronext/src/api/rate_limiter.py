# src/api/rate_limiter.py
from datetime import datetime, timedelta
from collections import deque
import streamlit as st

class RateLimiter:
    """Gestionnaire de rate limiting avec session state"""
    
    def __init__(self, max_requests: int = 30, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        
        # Initialisation dans session_state
        if 'request_history' not in st.session_state:
            st.session_state.request_history = deque()
    
    def can_proceed(self) -> bool:
        """Vérifie si une requête est autorisée"""
        now = datetime.now()
        
        # Nettoyer les requêtes anciennes
        while (st.session_state.request_history and 
               st.session_state.request_history[0] < now - timedelta(seconds=self.time_window)):
            st.session_state.request_history.popleft()
        
        return len(st.session_state.request_history) < self.max_requests
    
    def add_request(self):
        """Enregistre une nouvelle requête"""
        st.session_state.request_history.append(datetime.now())
    
    def get_wait_time(self) -> float:
        """Calcule le temps d'attente nécessaire"""
        if len(st.session_state.request_history) >= self.max_requests:
            oldest = st.session_state.request_history[0]
            wait = (oldest + timedelta(seconds=self.time_window) - datetime.now()).total_seconds()
            return max(0, wait)
        return 0
    
    def get_remaining_requests(self) -> int:
        """Nombre de requêtes restantes"""
        return max(0, self.max_requests - len(st.session_state.request_history))