# api/client.py
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import streamlit as st
from config.settings import APIConfig

class FinancialAPIClient:
    def __init__(self):
        self.session = self._create_session()
        self.base_url = APIConfig.BASE_URL
    
    def _create_session(self):
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    @st.cache_data(ttl=3600)
    def get_stock_data(_self, symbol):
        # Version simulée pour le développement
        return {
            'price': 519.60,
            'change': -0.93,
            'volume': 26164
        }
