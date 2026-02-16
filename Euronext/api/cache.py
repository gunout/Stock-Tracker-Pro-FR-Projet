# src/api/cache.py
import streamlit as st
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
import pandas as pd

class CacheManager:
    """Gestionnaire de cache avancé avec différentes stratégies"""
    
    def __init__(self, default_ttl: int = 3600):
        self.default_ttl = default_ttl
        self._init_cache()
    
    def _init_cache(self):
        """Initialise le cache dans session_state"""
        if 'cache_store' not in st.session_state:
            st.session_state.cache_store = {}
        if 'cache_timestamps' not in st.session_state:
            st.session_state.cache_timestamps = {}
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Génère une clé de cache unique"""
        key_parts = [prefix]
        key_parts.extend([str(arg) for arg in args])
        key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache"""
        if key in st.session_state.cache_store:
            timestamp = st.session_state.cache_timestamps.get(key)
            if timestamp and datetime.now() < timestamp:
                return st.session_state.cache_store[key]
            else:
                # Expiré, on nettoie
                self.delete(key)
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Stocke une valeur dans le cache"""
        ttl = ttl or self.default_ttl
        st.session_state.cache_store[key] = value
        st.session_state.cache_timestamps[key] = datetime.now() + timedelta(seconds=ttl)
    
    def delete(self, key: str):
        """Supprime une entrée du cache"""
        if key in st.session_state.cache_store:
            del st.session_state.cache_store[key]
        if key in st.session_state.cache_timestamps:
            del st.session_state.cache_timestamps[key]
    
    def clear(self):
        """Vide tout le cache"""
        st.session_state.cache_store = {}
        st.session_state.cache_timestamps = {}
    
    def get_stats(self) -> Dict:
        """Retourne des statistiques sur le cache"""
        return {
            "total_entries": len(st.session_state.cache_store),
            "active_entries": sum(
                1 for ts in st.session_state.cache_timestamps.values() 
                if ts > datetime.now()
            ),
            "memory_estimate": sum(
                len(json.dumps(v, default=str)) for v in st.session_state.cache_store.values()
            )
        }
    
    @st.cache_data(ttl=300)
    def cache_dataframe(_self, df: pd.DataFrame, cache_key: str) -> pd.DataFrame:
        """Cache un DataFrame avec Streamlit"""
        return df.copy()


class FunctionCache:
    """Décorateur pour mettre en cache les résultats de fonctions"""
    
    def __init__(self, ttl: int = 3600, max_size: int = 100):
        self.ttl = ttl
        self.max_size = max_size
        self.cache = {}
        self.timestamps = {}
    
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            # Générer une clé
            key_parts = [func.__name__]
            key_parts.extend([str(arg) for arg in args])
            key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
            key = "|".join(key_parts)
            
            # Vérifier le cache
            if key in self.cache:
                timestamp = self.timestamps.get(key)
                if timestamp and datetime.now() < timestamp:
                    return self.cache[key]
            
            # Calculer le résultat
            result = func(*args, **kwargs)
            
            # Gérer la taille du cache
            if len(self.cache) >= self.max_size:
                # Supprimer l'entrée la plus ancienne
                oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
                del self.cache[oldest_key]
                del self.timestamps[oldest_key]
            
            # Mettre en cache
            self.cache[key] = result
            self.timestamps[key] = datetime.now() + timedelta(seconds=self.ttl)
            
            return result
        
        return wrapper