# api/rate_limiter.py
from datetime import datetime, timedelta
from collections import deque
import streamlit as st

class RateLimiter:
    def __init__(self, max_requests=30, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        
        if 'request_history' not in st.session_state:
            st.session_state.request_history = deque()
    
    def _clean_old_requests(self):
        now = datetime.now()
        valid_requests = deque()
        for ts in st.session_state.request_history:
            if ts > now - timedelta(seconds=self.time_window):
                valid_requests.append(ts)
        st.session_state.request_history = valid_requests
    
    def can_proceed(self):
        self._clean_old_requests()
        return len(st.session_state.request_history) < self.max_requests
    
    def add_request(self):
        self._clean_old_requests()
        st.session_state.request_history.append(datetime.now())
    
    def get_remaining_requests(self):
        self._clean_old_requests()
        return max(0, self.max_requests - len(st.session_state.request_history))
    
    def get_wait_time(self):
        self._clean_old_requests()
        if len(st.session_state.request_history) >= self.max_requests:
            oldest = min(st.session_state.request_history)
            wait = (oldest + timedelta(seconds=self.time_window) - datetime.now()).total_seconds()
            return max(0, wait)
        return 0
    
    def clear_history(self):
        st.session_state.request_history = deque()
