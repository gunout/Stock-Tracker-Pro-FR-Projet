# src/components/status.py
import streamlit as st
from datetime import datetime
from typing import Optional, Dict, List
import time

class StatusDisplay:
    """Gestionnaire d'affichage des statuts"""
    
    @staticmethod
    def show_api_status(rate_limiter):
        """Affiche le statut de l'API"""
        with st.container():
            st.markdown("### 🌐 Statut API")
            
            remaining = rate_limiter.get_remaining_requests()
            wait_time = rate_limiter.get_wait_time()
            
            # Jauge de requêtes
            progress = remaining / rate_limiter.max_requests
            st.progress(progress)
            
            col1, col2 = st.columns(2)
            with col1:
                if remaining > 0:
                    st.success(f"✅ {remaining} requêtes restantes")
                else:
                    st.error("🔴 Plus de requêtes disponibles")
            
            with col2:
                if wait_time > 0:
                    st.warning(f"⏳ Attente: {wait_time:.0f}s")
                else:
                    st.info("🟢 Prêt")
    
    @staticmethod
    def show_connection_status(is_connected: bool, last_update: Optional[datetime] = None):
        """Affiche le statut de connexion"""
        if is_connected:
            st.sidebar.success("🟢 Connecté")
        else:
            st.sidebar.error("🔴 Déconnecté")
        
        if last_update:
            st.sidebar.caption(f"Dernière mise à jour: {last_update.strftime('%H:%M:%S')}")
    
    @staticmethod
    def show_error_message(error: Exception, context: str = ""):
        """Affiche un message d'erreur stylisé"""
        with st.container():
            st.markdown("""
            <style>
            .error-box {
                padding: 1rem;
                border-radius: 0.5rem;
                background-color: #ffebee;
                border-left: 4px solid #f44336;
                margin: 1rem 0;
            }
            </style>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="error-box">
                <strong>❌ Erreur</strong><br>
                {context}<br>
                <small>{str(error)}</small>
            </div>
            """, unsafe_allow_html=True)
    
    @staticmethod
    def show_success_message(message: str, duration: int = 3):
        """Affiche un message de succès temporaire"""
        placeholder = st.empty()
        placeholder.success(f"✅ {message}")
        time.sleep(duration)
        placeholder.empty()
    
    @staticmethod
    def show_loading_state(message: str = "Chargement en cours..."):
        """Affiche un état de chargement"""
        return st.status(message, expanded=True)
    
    @staticmethod
    def show_data_quality_indicator(completeness: float, timeliness: float):
        """Affiche des indicateurs de qualité des données"""
        cols = st.columns(3)
        
        with cols[0]:
            if completeness > 0.95:
                st.markdown("🟢 **Complétude**")
            elif completeness > 0.8:
                st.markdown("🟡 **Complétude**")
            else:
                st.markdown("🔴 **Complétude**")
            st.progress(completeness)
        
        with cols[1]:
            if timeliness > 0.95:
                st.markdown("🟢 **Actualité**")
            elif timeliness > 0.8:
                st.markdown("🟡 **Actualité**")
            else:
                st.markdown("🔴 **Actualité**")
            st.progress(timeliness)


class NotificationManager:
    """Gestionnaire de notifications"""
    
    def __init__(self):
        if 'notifications' not in st.session_state:
            st.session_state.notifications = []
    
    def add_notification(self, message: str, type: str = "info", timeout: int = 5):
        """Ajoute une notification"""
        notification = {
            "message": message,
            "type": type,
            "timestamp": datetime.now(),
            "timeout": timeout
        }
        st.session_state.notifications.append(notification)
    
    def display_notifications(self):
        """Affiche toutes les notifications"""
        for notification in st.session_state.notifications[:]:
            age = (datetime.now() - notification["timestamp"]).seconds
            
            if age < notification["timeout"]:
                if notification["type"] == "success":
                    st.success(notification["message"])
                elif notification["type"] == "error":
                    st.error(notification["message"])
                elif notification["type"] == "warning":
                    st.warning(notification["message"])
                else:
                    st.info(notification["message"])
            else:
                st.session_state.notifications.remove(notification)
    
    def clear_all(self):
        """Supprime toutes les notifications"""
        st.session_state.notifications = []


def display_system_health(metrics: Dict):
    """Affiche la santé globale du système"""
    
    st.markdown("### 🏥 Santé du système")
    
    cols = st.columns(4)
    
    with cols[0]:
        if metrics.get('cpu_usage', 0) < 50:
            st.markdown("🟢 CPU")
        elif metrics.get('cpu_usage', 0) < 80:
            st.markdown("🟡 CPU")
        else:
            st.markdown("🔴 CPU")
        st.caption(f"{metrics.get('cpu_usage', 0)}%")
    
    with cols[1]:
        if metrics.get('memory_usage', 0) < 50:
            st.markdown("🟢 Mémoire")
        elif metrics.get('memory_usage', 0) < 80:
            st.markdown("🟡 Mémoire")
        else:
            st.markdown("🔴 Mémoire")
        st.caption(f"{metrics.get('memory_usage', 0)}%")
    
    with cols[2]:
        uptime = metrics.get('uptime', 0)
        st.markdown("🕐 Uptime")
        st.caption(f"{uptime:.1f}h")
    
    with cols[3]:
        response_time = metrics.get('response_time', 0)
        if response_time < 100:
            st.markdown("🟢 Latence")
        elif response_time < 300:
            st.markdown("🟡 Latence")
        else:
            st.markdown("🔴 Latence")
        st.caption(f"{response_time}ms")