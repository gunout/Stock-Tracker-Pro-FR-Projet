# api/rate_limiter.py
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
            st.session_state.request_history = deque(maxlen=max_requests * 2)
    
    def can_proceed(self) -> bool:
        """Vérifie si une requête est autorisée"""
        self._clean_old_requests()
        return len(st.session_state.request_history) < self.max_requests
    
    def _clean_old_requests(self):
        """Nettoie les requêtes anciennes"""
        now = datetime.now()
        # Créer une nouvelle deque avec seulement les requêtes récentes
        valid_requests = deque(maxlen=self.max_requests * 2)
        for timestamp in st.session_state.request_history:
            if timestamp > now - timedelta(seconds=self.time_window):
                valid_requests.append(timestamp)
        st.session_state.request_history = valid_requests
    
    def add_request(self):
        """Enregistre une nouvelle requête"""
        self._clean_old_requests()
        st.session_state.request_history.append(datetime.now())
    
    def get_wait_time(self) -> float:
        """Calcule le temps d'attente nécessaire"""
        self._clean_old_requests()
        if len(st.session_state.request_history) >= self.max_requests:
            # Trouver la requête la plus ancienne dans la fenêtre
            oldest = min(st.session_state.request_history)
            wait = (oldest + timedelta(seconds=self.time_window) - datetime.now()).total_seconds()
            return max(0, wait)
        return 0
    
    def get_remaining_requests(self) -> int:
        """Nombre de requêtes restantes"""
        self._clean_old_requests()
        return max(0, self.max_requests - len(st.session_state.request_history))
    
    def get_request_count(self) -> int:
        """Nombre de requêtes dans la fenêtre actuelle"""
        self._clean_old_requests()
        return len(st.session_state.request_history)
    
    def clear_history(self):
        """Efface l'historique des requêtes"""
        st.session_state.request_history = deque(maxlen=self.max_requests * 2)
    
    def get_stats(self) -> dict:
        """Retourne des statistiques sur l'utilisation"""
        self._clean_old_requests()
        return {
            "current_requests": len(st.session_state.request_history),
            "max_requests": self.max_requests,
            "time_window": self.time_window,
            "wait_time": self.get_wait_time(),
            "remaining": self.get_remaining_requests()
        }
