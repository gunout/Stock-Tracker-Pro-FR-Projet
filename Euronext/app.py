# app.py - Version complète avec toutes les fonctionnalités
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
import time
import sqlite3
import requests
import os
from pathlib import Path
from streamlit.components.v1 import html
import plotly.graph_objects as go
import plotly.express as px

# ==================== CONFIGURATION DE LA PAGE ====================
st.set_page_config(
    page_title="Dashboard Financier Pro MC.PA",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== INITIALISATION SESSION STATE ====================
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()
if 'data_history' not in st.session_state:
    st.session_state.data_history = []
if 'update_counter' not in st.session_state:
    st.session_state.update_counter = 0
if 'current_symbols' not in st.session_state:
    st.session_state.current_symbols = ["MC.PA"]
if 'paused' not in st.session_state:
    st.session_state.paused = False
if 'alerts' not in st.session_state:
    st.session_state.alerts = []
if 'api_source' not in st.session_state:
    st.session_state.api_source = "Simulation"
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = False
if 'comparison_mode' not in st.session_state:
    st.session_state.comparison_mode = False
if 'favorites' not in st.session_state:
    st.session_state.favorites = []

# ==================== CONFIGURATION DES CHEMINS ====================
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "stock_data.db"
EXPORT_DIR = BASE_DIR / "exports"
EXPORT_DIR.mkdir(exist_ok=True)

# ==================== BASE DE DONNÉES ====================
class DatabaseManager:
    """Gestionnaire de base de données SQLite avec gestion des migrations"""
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialise les tables de la base de données avec gestion des migrations"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Table des prix historiques
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    price REAL NOT NULL,
                    change REAL,
                    volume INTEGER,
                    pe_ratio REAL,
                    dividend REAL,
                    dividend_yield REAL,
                    UNIQUE(symbol, timestamp)
                )
            ''')
            
            # Vérifier si la colonne 'source' existe déjà
            cursor.execute("PRAGMA table_info(stock_prices)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Ajouter la colonne 'source' si elle n'existe pas
            if 'source' not in columns:
                try:
                    cursor.execute('''
                        ALTER TABLE stock_prices 
                        ADD COLUMN source TEXT DEFAULT 'Simulation'
                    ''')
                    print("✅ Colonne 'source' ajoutée à la table stock_prices")
                except Exception as e:
                    print(f"⚠️ Erreur lors de l'ajout de la colonne source: {e}")
            
            # Table des alertes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    threshold REAL NOT NULL,
                    condition TEXT NOT NULL,
                    active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_triggered DATETIME
                )
            ''')
            
            # Table des favoris
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL UNIQUE,
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            st.session_state.db_initialized = True
            print("✅ Base de données initialisée avec succès")
            
        except Exception as e:
            st.error(f"Erreur initialisation BDD: {e}")
            print(f"❌ Erreur détaillée: {e}")
    
    def save_price(self, symbol, data):
        """Sauvegarde un prix dans la base de données (version robuste)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Vérifier si la colonne source existe
            cursor.execute("PRAGMA table_info(stock_prices)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Préparer les données avec des valeurs par défaut
            timestamp = datetime.now().isoformat()
            price = data.get('price', 0)
            change = data.get('change', 0)
            volume = data.get('volume', 0)
            pe_ratio = data.get('pe_ratio', 0)
            dividend = data.get('dividend', 0)
            dividend_yield = data.get('dividend_yield', 0)
            source = data.get('source', 'Simulation')
            
            if 'source' in columns:
                # Version avec source
                cursor.execute('''
                    INSERT OR REPLACE INTO stock_prices 
                    (symbol, timestamp, price, change, volume, pe_ratio, dividend, dividend_yield, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    timestamp,
                    price,
                    change,
                    volume,
                    pe_ratio,
                    dividend,
                    dividend_yield,
                    source
                ))
            else:
                # Version sans source (compatible avec ancienne structure)
                cursor.execute('''
                    INSERT OR REPLACE INTO stock_prices 
                    (symbol, timestamp, price, change, volume, pe_ratio, dividend, dividend_yield)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    timestamp,
                    price,
                    change,
                    volume,
                    pe_ratio,
                    dividend,
                    dividend_yield
                ))
            
            conn.commit()
            conn.close()
            return True
            
        except sqlite3.OperationalError as e:
            error_msg = str(e)
            if "no such column: source" in error_msg:
                st.warning("🔄 Mise à jour de la structure de la base de données...")
                if self.migrate_database():
                    return self.save_price(symbol, data)
                else:
                    st.error("❌ Échec de la migration de la base de données")
                    return False
            else:
                st.error(f"Erreur sauvegarde BDD: {e}")
                return False
        except Exception as e:
            st.error(f"Erreur sauvegarde BDD: {e}")
            return False
    
    def migrate_database(self):
        """Migre la base de données vers la nouvelle structure"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Vérifier si la table existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_prices'")
            if not cursor.fetchone():
                cursor.execute('''
                    CREATE TABLE stock_prices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        price REAL NOT NULL,
                        change REAL,
                        volume INTEGER,
                        pe_ratio REAL,
                        dividend REAL,
                        dividend_yield REAL,
                        source TEXT DEFAULT 'Simulation',
                        UNIQUE(symbol, timestamp)
                    )
                ''')
                conn.commit()
                conn.close()
                return True
            
            # Créer une table temporaire
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_prices_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    price REAL NOT NULL,
                    change REAL,
                    volume INTEGER,
                    pe_ratio REAL,
                    dividend REAL,
                    dividend_yield REAL,
                    source TEXT DEFAULT 'Simulation',
                    UNIQUE(symbol, timestamp)
                )
            ''')
            
            # Copier les données existantes
            try:
                cursor.execute('''
                    INSERT INTO stock_prices_new 
                    (symbol, timestamp, price, change, volume, pe_ratio, dividend, dividend_yield, source)
                    SELECT 
                        symbol, timestamp, price, change, volume, pe_ratio, dividend, dividend_yield, 'Simulation'
                    FROM stock_prices
                ''')
            except sqlite3.OperationalError:
                cursor.execute('''
                    INSERT INTO stock_prices_new 
                    (symbol, timestamp, price, change, volume, pe_ratio, dividend, dividend_yield, source)
                    SELECT 
                        symbol, timestamp, price, 
                        COALESCE(change, 0), 
                        COALESCE(volume, 0), 
                        COALESCE(pe_ratio, 0), 
                        COALESCE(dividend, 0), 
                        COALESCE(dividend_yield, 0), 
                        'Simulation'
                    FROM stock_prices
                ''')
            
            cursor.execute('DROP TABLE IF EXISTS stock_prices')
            cursor.execute('ALTER TABLE stock_prices_new RENAME TO stock_prices')
            
            conn.commit()
            conn.close()
            st.success("✅ Base de données migrée avec succès")
            return True
            
        except Exception as e:
            st.error(f"Erreur migration BDD: {e}")
            return False
    
    def get_history(self, symbol, days=30):
        """Récupère l'historique des prix"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = '''
                SELECT * FROM stock_prices 
                WHERE symbol = ? 
                AND datetime(timestamp) >= datetime('now', '-' || ? || ' days')
                ORDER BY timestamp DESC
            '''
            df = pd.read_sql_query(query, conn, params=[symbol, days])
            conn.close()
            return df
        except Exception as e:
            st.error(f"Erreur lecture historique: {e}")
            return pd.DataFrame()
    
    def add_alert(self, symbol, alert_type, threshold, condition):
        """Ajoute une alerte"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO alerts (symbol, alert_type, threshold, condition)
                VALUES (?, ?, ?, ?)
            ''', (symbol, alert_type, threshold, condition))
            
            conn.commit()
            alert_id = cursor.lastrowid
            conn.close()
            return alert_id
        except Exception as e:
            st.error(f"Erreur ajout alerte: {e}")
            return None
    
    def get_active_alerts(self):
        """Récupère les alertes actives"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM alerts WHERE active = 1 ORDER BY created_at DESC
            ''')
            
            alerts = cursor.fetchall()
            conn.close()
            return alerts
        except Exception as e:
            st.error(f"Erreur lecture alertes: {e}")
            return []
    
    def check_alerts(self, symbol, price):
        """Vérifie si une alerte doit être déclenchée"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM alerts 
                WHERE symbol = ? AND active = 1
            ''', (symbol,))
            
            alerts = cursor.fetchall()
            triggered = []
            
            for alert in alerts:
                alert_id, sym, a_type, threshold, condition, active, created, last = alert
                
                if condition == 'above' and price > threshold:
                    triggered.append(alert)
                    cursor.execute('''
                        UPDATE alerts SET last_triggered = ? WHERE id = ?
                    ''', (datetime.now().isoformat(), alert_id))
                elif condition == 'below' and price < threshold:
                    triggered.append(alert)
                    cursor.execute('''
                        UPDATE alerts SET last_triggered = ? WHERE id = ?
                    ''', (datetime.now().isoformat(), alert_id))
            
            conn.commit()
            conn.close()
            return triggered
        except Exception as e:
            st.error(f"Erreur vérification alertes: {e}")
            return []
    
    def delete_alert(self, alert_id):
        """Supprime une alerte"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM alerts WHERE id = ?', (alert_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Erreur suppression alerte: {e}")
            return False
    
    def toggle_alert(self, alert_id, active=True):
        """Active ou désactive une alerte"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('UPDATE alerts SET active = ? WHERE id = ?', (1 if active else 0, alert_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Erreur modification alerte: {e}")
            return False
    
    def add_favorite(self, symbol):
        """Ajoute un symbole aux favoris"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO favorites (symbol)
                VALUES (?)
            ''', (symbol,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Erreur ajout favori: {e}")
            return False
    
    def remove_favorite(self, symbol):
        """Supprime un symbole des favoris"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM favorites WHERE symbol = ?', (symbol,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Erreur suppression favori: {e}")
            return False
    
    def get_favorites(self):
        """Récupère la liste des favoris"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT symbol FROM favorites ORDER BY added_at DESC')
            
            favorites = [row[0] for row in cursor.fetchall()]
            conn.close()
            return favorites
        except Exception as e:
            st.error(f"Erreur lecture favoris: {e}")
            return []
    
    def cleanup_old_data(self, days=30):
        """Supprime les données plus anciennes que 'days' jours"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM stock_prices 
                WHERE datetime(timestamp) < datetime('now', '-' || ? || ' days')
            ''', (days,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            return deleted_count
        except Exception as e:
            st.error(f"Erreur nettoyage BDD: {e}")
            return 0
    
    def get_database_stats(self):
        """Retourne des statistiques sur la base de données"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            
            cursor.execute('SELECT COUNT(*) FROM stock_prices')
            stats['total_records'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT symbol) FROM stock_prices')
            stats['unique_symbols'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT MIN(timestamp) FROM stock_prices')
            stats['first_record'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT MAX(timestamp) FROM stock_prices')
            stats['last_record'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM alerts')
            stats['total_alerts'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM alerts WHERE active = 1')
            stats['active_alerts'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM favorites')
            stats['total_favorites'] = cursor.fetchone()[0]
            
            conn.close()
            return stats
        except Exception as e:
            st.error(f"Erreur statistiques BDD: {e}")
            return {}

# ==================== API RÉELLES ====================
class APIManager:
    """Gestionnaire d'APIs financières"""
    
    @staticmethod
    def get_yahoo_finance_data(symbol):
        """Récupère les données via Yahoo Finance"""
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                    result = data['chart']['result'][0]
                    meta = result.get('meta', {})
                    
                    price = meta.get('regularMarketPrice', 0)
                    previous_close = meta.get('previousClose', price)
                    change = ((price - previous_close) / previous_close) * 100 if previous_close > 0 else 0
                    
                    return {
                        'price': round(price, 2),
                        'change': round(change, 2),
                        'volume': meta.get('regularMarketVolume', 0),
                        'source': 'Yahoo Finance',
                        'pe_ratio': 0,
                        'dividend': 0,
                        'dividend_yield': 0
                    }
            return None
        except Exception as e:
            st.warning(f"Erreur Yahoo Finance: {e}")
            return None
    
    @staticmethod
    def get_alpha_vantage_data(symbol, api_key):
        """Récupère les données via Alpha Vantage"""
        if not api_key:
            return None
        
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                quote = data.get('Global Quote', {})
                
                if quote:
                    change_percent = quote.get('10. change percent', '0%').replace('%', '')
                    return {
                        'price': float(quote.get('05. price', 0)),
                        'change': float(change_percent),
                        'volume': int(quote.get('06. volume', 0)),
                        'source': 'Alpha Vantage',
                        'pe_ratio': 0,
                        'dividend': 0,
                        'dividend_yield': 0
                    }
            return None
        except Exception as e:
            st.warning(f"Erreur Alpha Vantage: {e}")
            return None

# ==================== GÉNÉRATION DE DONNÉES ====================
def generate_live_data(symbol, api_source="Simulation", api_key=""):
    """Génère des données en direct avec API réelle ou simulation"""
    
    if api_source == "Yahoo Finance":
        real_data = APIManager.get_yahoo_finance_data(symbol)
        if real_data:
            return real_data
    
    elif api_source == "Alpha Vantage" and api_key:
        real_data = APIManager.get_alpha_vantage_data(symbol, api_key)
        if real_data:
            return real_data
    
    # Données simulées
    base_prices = {
        'MC.PA': 519.60, 'RMS.PA': 2450.00, 'KER.PA': 320.00,
        'CDI.PA': 65.50, 'AI.PA': 180.30, 'OR.PA': 95.20,
        'BNP.PA': 62.40, 'SAN.PA': 89.70, 'TOT.PA': 58.30
    }
    
    base_volumes = {
        'MC.PA': 26164, 'RMS.PA': 15000, 'KER.PA': 50000,
        'CDI.PA': 35000, 'AI.PA': 28000, 'OR.PA': 42000,
        'BNP.PA': 45000, 'SAN.PA': 38000, 'TOT.PA': 52000
    }
    
    base_pe = {
        'MC.PA': 23.76, 'RMS.PA': 48.50, 'KER.PA': 18.30,
        'CDI.PA': 15.20, 'AI.PA': 22.10, 'OR.PA': 14.80,
        'BNP.PA': 9.50, 'SAN.PA': 16.40, 'TOT.PA': 8.70
    }
    
    base_dividend = {
        'MC.PA': 13.00, 'RMS.PA': 15.00, 'KER.PA': 4.50,
        'CDI.PA': 2.80, 'AI.PA': 3.20, 'OR.PA': 1.90,
        'BNP.PA': 3.40, 'SAN.PA': 2.60, 'TOT.PA': 2.90
    }
    
    base_yield = {
        'MC.PA': 2.48, 'RMS.PA': 0.61, 'KER.PA': 1.40,
        'CDI.PA': 4.27, 'AI.PA': 1.77, 'OR.PA': 2.00,
        'BNP.PA': 5.45, 'SAN.PA': 2.90, 'TOT.PA': 4.98
    }
    
    base_price = base_prices.get(symbol, 100.00)
    base_volume = base_volumes.get(symbol, 20000)
    
    price_change = np.random.uniform(-2.0, 2.0)
    new_price = base_price * (1 + price_change/100)
    volume_change = np.random.uniform(-15, 15)
    new_volume = int(base_volume * (1 + volume_change/100))
    
    pe_ratio = base_pe.get(symbol, 15.0) * (1 + np.random.uniform(-0.05, 0.05))
    dividend = base_dividend.get(symbol, 2.0) * (1 + np.random.uniform(-0.03, 0.03))
    dividend_yield = base_yield.get(symbol, 2.0) * (1 + np.random.uniform(-0.05, 0.05))
    
    return {
        'symbol': symbol,
        'price': round(new_price, 2),
        'change': round(price_change, 2),
        'volume': new_volume,
        'pe_ratio': round(pe_ratio, 2),
        'dividend': round(dividend, 2),
        'dividend_yield': round(dividend_yield, 2),
        'timestamp': datetime.now().isoformat(),
        'source': 'Simulation'
    }

def generate_historical_rows(data, count=10):
    """Génère les lignes du tableau historique"""
    rows = []
    now = datetime.now()
    
    for i in range(count):
        date = now - timedelta(seconds=i*30)
        price_variation = np.random.uniform(-5, 5)
        historical_price = data['price'] * (1 + price_variation/100)
        
        rows.append(f"""
            <tr>
                <td>{date.strftime('%H:%M:%S')}</td>
                <td>{historical_price - np.random.uniform(0.5, 2):.2f} €</td>
                <td>{historical_price + np.random.uniform(0.5, 2):.2f} €</td>
                <td>{historical_price - np.random.uniform(1, 3):.2f} €</td>
                <td>{historical_price:.2f} €</td>
                <td>{int(data['volume'] * np.random.uniform(0.8, 1.2)):,}</td>
            </tr>
        """)
    return rows

# ==================== COMPOSANTS D'EXPORT ====================
class ExportManager:
    """Gestionnaire d'export de données"""
    
    @staticmethod
    def to_csv(data, symbol, filename=None):
        if filename is None:
            filename = EXPORT_DIR / f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df = pd.DataFrame([data])
        df.to_csv(filename, index=False, encoding='utf-8')
        return filename
    
    @staticmethod
    def to_excel(data, symbol, filename=None):
        if filename is None:
            filename = EXPORT_DIR / f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df = pd.DataFrame([data])
        df.to_excel(filename, index=False)
        return filename
    
    @staticmethod
    def to_json(data, symbol, filename=None):
        if filename is None:
            filename = EXPORT_DIR / f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return filename

# ==================== GRAPHIQUES DE COMPARAISON ====================
def create_comparison_chart(symbols_data):
    """Crée un graphique comparatif de plusieurs symboles"""
    fig = go.Figure()
    
    for symbol, data in symbols_data.items():
        dates = pd.date_range(end=datetime.now(), periods=50, freq='H')
        prices = []
        current_price = data['price']
        
        for i in range(50):
            variation = np.random.uniform(-1, 1)
            current_price = current_price * (1 + variation/100)
            prices.append(current_price)
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=prices,
            mode='lines',
            name=symbol,
            line=dict(width=2)
        ))
    
    fig.update_layout(
        title="Comparaison des performances",
        xaxis_title="Date",
        yaxis_title="Prix (€)",
        hovermode='x unified',
        template='plotly_white',
        height=500
    )
    
    return fig

# ==================== DASHBOARD HTML ====================
def create_dashboard_html(data, update_counter, comparison_mode=False):
    """Crée le HTML du dashboard"""
    
    title = "Mode Comparaison - Multi-symboles" if comparison_mode else f"Trading en direct - {data['symbol']}"
    
    html_code = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard Financier Pro</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }}
            body {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            .dashboard {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ background: white; padding: 25px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }}
            .symbol-title {{ font-size: 28px; font-weight: bold; color: #333; margin-bottom: 10px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
            .live-badge {{ background: #ff4444; color: white; padding: 5px 15px; border-radius: 20px; font-size: 14px; display: inline-flex; align-items: center; gap: 5px; animation: pulse 2s infinite; }}
            @keyframes pulse {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.7; }} 100% {{ opacity: 1; }} }}
            .update-counter {{ background: #667eea; color: white; padding: 5px 15px; border-radius: 20px; font-size: 14px; margin-left: 10px; }}
            .connection-status {{ display: inline-flex; align-items: center; gap: 5px; padding: 5px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-left: 10px; }}
            .connected {{ background: #4CAF50; color: white; }}
            .metrics-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }}
            .metric-card {{ background: white; padding: 20px; border-radius: 15px; box-shadow: 0 5px 20px rgba(0,0,0,0.1); transition: all 0.3s ease; position: relative; overflow: hidden; }}
            .metric-card.updating {{ transform: scale(1.02); box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3); }}
            .metric-card.updating::after {{ content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 3px; background: linear-gradient(90deg, transparent, #667eea, transparent); animation: loading 1.5s infinite; }}
            @keyframes loading {{ 0% {{ left: -100%; }} 100% {{ left: 100%; }} }}
            .metric-label {{ color: #666; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }}
            .metric-value {{ font-size: 28px; font-weight: bold; color: #333; margin-bottom: 5px; transition: color 0.3s ease; }}
            .metric-value.changed {{ color: #667eea; }}
            .metric-change {{ font-size: 14px; transition: all 0.3s ease; }}
            .positive {{ color: #4CAF50; }}
            .negative {{ color: #F44336; }}
            .chart-container {{ background: white; padding: 25px; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); margin-bottom: 30px; width: 100%; }}
            .chart-wrapper {{ position: relative; width: 100%; height: 400px; margin: 0 auto; }}
            .chart-title {{ font-size: 18px; font-weight: bold; color: #333; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }}
            .timer {{ font-family: monospace; font-size: 16px; color: #667eea; background: #f0f0f0; padding: 5px 10px; border-radius: 5px; }}
            .controls {{ display: flex; gap: 10px; align-items: center; }}
            .refresh-btn {{ background: #667eea; color: white; border: none; padding: 8px 20px; border-radius: 5px; cursor: pointer; font-size: 14px; transition: all 0.3s ease; }}
            .refresh-btn:hover {{ background: #5a67d8; transform: scale(1.05); }}
            .refresh-btn:disabled {{ background: #ccc; cursor: not-allowed; transform: none; }}
            .tabs {{ display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }}
            .tab {{ padding: 10px 20px; background: white; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 500; color: #666; transition: all 0.3s ease; }}
            .tab:hover {{ background: #667eea; color: white; }}
            .tab.active {{ background: #667eea; color: white; }}
            .tab-content {{ display: none; }}
            .tab-content.active {{ display: block; }}
            .indicators-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }}
            .indicator-chart {{ position: relative; width: 100%; height: 250px; }}
            .historical-table {{ width: 100%; border-collapse: collapse; }}
            .historical-table th, .historical-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
            .historical-table th {{ background: #f8f9fa; font-weight: 600; color: #333; }}
            .historical-table tr:hover {{ background: #f5f5f5; }}
            .footer {{ text-align: center; color: white; font-size: 12px; margin-top: 30px; opacity: 0.8; }}
            .market-status {{ display: inline-block; padding: 5px 10px; border-radius: 5px; font-size: 12px; font-weight: bold; }}
            .open {{ background: #4CAF50; color: white; }}
            .closed {{ background: #F44336; color: white; }}
            canvas {{ display: block; width: 100% !important; height: 100% !important; }}
            .toast {{ position: fixed; bottom: 20px; right: 20px; background: white; padding: 15px 25px; border-radius: 10px; box-shadow: 0 5px 20px rgba(0,0,0,0.2); transform: translateX(400px); transition: transform 0.3s ease; z-index: 1000; }}
            .toast.show {{ transform: translateX(0); }}
            .toast.success {{ border-left: 4px solid #4CAF50; }}
            .toast.error {{ border-left: 4px solid #F44336; }}
            .toast.warning {{ border-left: 4px solid #FF9800; }}
            .toast.info {{ border-left: 4px solid #2196F3; }}
        </style>
    </head>
    <body>
        <div class="dashboard">
            <div class="header">
                <div class="symbol-title">
                    <span id="symbol">{data['symbol'] if not comparison_mode else 'Mode Comparaison'}</span> 
                    <span>• {title}</span>
                    <span class="live-badge"><span>🔴 LIVE</span></span>
                    <span id="updateCounter" class="update-counter">Mise à jour #{update_counter}</span>
                    <span id="connectionStatus" class="connection-status connected">📡 Connecté</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div class="last-update" id="lastUpdate">
                        Dernière mise à jour: {data.get('last_update', datetime.now().strftime('%H:%M:%S'))}
                    </div>
                    <div class="timer" id="timer">Prochaine mise à jour dans 3s</div>
                </div>
            </div>
            
            {f'''
            <div class="metrics-grid" id="metricsGrid">
                <div class="metric-card" id="priceCard">
                    <div class="metric-label">Cours</div>
                    <div class="metric-value" id="price">{data.get('price', 0):.2f} €</div>
                    <div class="metric-change" id="priceChange" class="{'positive' if data.get('change', 0) >= 0 else 'negative'}">
                        {data.get('change', 0):+.2f}%
                    </div>
                </div>
                <div class="metric-card" id="volumeCard">
                    <div class="metric-label">Volume</div>
                    <div class="metric-value" id="volume">{data.get('volume', 0):,}</div>
                </div>
                <div class="metric-card" id="peCard">
                    <div class="metric-label">P/E</div>
                    <div class="metric-value" id="pe">{data.get('pe_ratio', 0):.2f}</div>
                </div>
                <div class="metric-card" id="dividendCard">
                    <div class="metric-label">Dividende</div>
                    <div class="metric-value" id="dividend">{data.get('dividend', 0):.2f} €</div>
                    <div class="metric-change positive" id="yield">{data.get('dividend_yield', 0):.2f}%</div>
                </div>
            </div>
            ''' if not comparison_mode else ''}
            
            <div class="tabs">
                <button class="tab active" onclick="showTab('chart')">📈 Graphique</button>
                <button class="tab" onclick="showTab('historical')">📊 Données historiques</button>
                <button class="tab" onclick="showTab('indicators')">📉 Indicateurs</button>
            </div>
            
            <div id="chart" class="tab-content active">
                <div class="chart-container">
                    <div class="chart-title">
                        <span>Évolution en direct - <span id="period">{data.get('period', '1H')}</span></span>
                        <div class="controls">
                            <button class="refresh-btn" onclick="forceRefresh()" id="refreshBtn">🔄 Rafraîchir maintenant</button>
                        </div>
                    </div>
                    <div class="chart-wrapper">
                        <canvas id="priceChart"></canvas>
                    </div>
                </div>
            </div>
            
            <div id="historical" class="tab-content">
                <div class="chart-container">
                    <div class="chart-title">
                        <span>Transactions récentes</span>
                        <span class="live-badge" style="font-size: 12px;">Mise à jour en direct</span>
                    </div>
                    <table class="historical-table" id="historicalTable">
                        <thead>
                            <tr><th>Heure</th><th>Ouverture</th><th>Plus haut</th><th>Plus bas</th><th>Clôture</th><th>Volume</th></tr>
                        </thead>
                        <tbody id="historicalBody">
                            {''.join(data.get('historical_rows', []))}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div id="indicators" class="tab-content">
                <div class="chart-container">
                    <div class="indicators-grid">
                        <div><div class="chart-title">RSI (14) - Direct</div><div class="indicator-chart"><canvas id="rsiChart"></canvas></div></div>
                        <div><div class="chart-title">MACD - Direct</div><div class="indicator-chart"><canvas id="macdChart"></canvas></div></div>
                    </div>
                </div>
            </div>
            
            <div class="footer">© 2026 Dashboard Financier Pro - Toutes les fonctionnalités incluses</div>
        </div>

        <div id="toast" class="toast"></div>

        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            let priceChart, rsiChart, macdChart;
            let countdown = 3;
            let isRefreshing = false;
            let lastData = {json.dumps(data)};
            let updateCounter = {update_counter};
            let timerInterval;
            
            function sendToStreamlit(type, data) {{
                const message = {{ type: type, data: data, counter: updateCounter, timestamp: new Date().toISOString() }};
                if (window.parent) window.parent.postMessage({{ type: 'streamlit:message', data: message }}, '*');
            }}
            
            function requestDataUpdate() {{
                if (isRefreshing) return;
                isRefreshing = true;
                updateCounter++;
                document.getElementById('updateCounter').textContent = `Mise à jour #${{updateCounter}}`;
                document.querySelectorAll('.metric-card').forEach(c => c.classList.add('updating'));
                sendToStreamlit('request_update', {{ symbol: lastData.symbol, counter: updateCounter }});
                setTimeout(() => {{
                    document.querySelectorAll('.metric-card').forEach(c => c.classList.remove('updating'));
                    isRefreshing = false;
                }}, 500);
            }}
            
            function updateDashboard(newData) {{
                if (!{json.dumps(comparison_mode)}) {{
                    updateMetricWithAnimation('price', (newData.price || 0).toFixed(2) + ' €');
                    updateMetricWithAnimation('volume', (newData.volume || 0).toLocaleString());
                    updateMetricWithAnimation('pe', (newData.pe_ratio || 0).toFixed(2));
                    updateMetricWithAnimation('dividend', (newData.dividend || 0).toFixed(2) + ' €');
                    
                    const changeEl = document.getElementById('priceChange');
                    changeEl.textContent = (newData.change >= 0 ? '+' : '') + (newData.change || 0).toFixed(2) + '%';
                    changeEl.className = 'metric-change ' + (newData.change >= 0 ? 'positive' : 'negative');
                    
                    document.getElementById('yield').textContent = (newData.dividend_yield || 0).toFixed(2) + '%';
                }}
                
                document.getElementById('lastUpdate').textContent = `Dernière mise à jour: ${{newData.last_update}}`;
                if (newData.historical_rows) document.getElementById('historicalBody').innerHTML = newData.historical_rows.join('');
                
                updateCharts(newData);
                lastData = newData;
                document.querySelectorAll('.metric-card').forEach(c => c.classList.remove('updating'));
                isRefreshing = false;
                showToast('Données mises à jour', 'success');
            }}
            
            function updateMetricWithAnimation(id, newValue) {{
                const el = document.getElementById(id);
                if (el && el.textContent !== newValue) {{
                    el.textContent = newValue;
                    el.classList.add('changed');
                    setTimeout(() => el.classList.remove('changed'), 500);
                }}
            }}
            
            function generateChartData(basePrice) {{
                const dates = [], prices = [];
                let currentPrice = basePrice || 100;
                for (let i = 30; i >= 0; i--) {{
                    const date = new Date(); date.setSeconds(date.getSeconds() - i * 3);
                    dates.push(date.toLocaleTimeString('fr-FR'));
                    if (i > 0) currentPrice = currentPrice * (1 + (Math.random() - 0.5) * 0.02);
                    prices.push(currentPrice);
                }}
                return {{ dates, prices }};
            }}
            
            function createPriceChart() {{
                const ctx = document.getElementById('priceChart').getContext('2d');
                const {{ dates, prices }} = generateChartData(lastData.price);
                if (priceChart) priceChart.destroy();
                priceChart = new Chart(ctx, {{
                    type: 'line',
                    data: {{ labels: dates, datasets: [{{ data: prices, borderColor: '#667eea', backgroundColor: 'rgba(102,126,234,0.1)', tension: 0.1, fill: true, pointRadius: 2, borderWidth: 2 }}] }},
                    options: {{ responsive: true, maintainAspectRatio: false, animation: {{ duration: 300 }}, plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ ticks: {{ callback: v => v.toFixed(2) + ' €' }} }} }} }}
                }});
            }}
            
            function createRSIChart() {{
                const ctx = document.getElementById('rsiChart').getContext('2d');
                const {{ dates }} = generateChartData(100);
                const rsiData = Array.from({{length: 31}}, () => 30 + Math.random() * 40);
                if (rsiChart) rsiChart.destroy();
                rsiChart = new Chart(ctx, {{
                    type: 'line',
                    data: {{ labels: dates, datasets: [{{ data: rsiData, borderColor: '#FF9800', backgroundColor: 'rgba(255,152,0,0.1)', tension: 0.1, fill: true, borderWidth: 2 }}] }},
                    options: {{ responsive: true, maintainAspectRatio: false, animation: {{ duration: 300 }}, plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ min: 0, max: 100 }} }} }}
                }});
            }}
            
            function createMACDChart() {{
                const ctx = document.getElementById('macdChart').getContext('2d');
                const {{ dates }} = generateChartData(100);
                const macdData = [], signalData = [];
                for (let i = 0; i < 31; i++) {{
                    macdData.push(Math.sin(i / 5) * 2 + Math.random() * 0.3);
                    signalData.push(macdData[i] * 0.8 + Math.random() * 0.2);
                }}
                if (macdChart) macdChart.destroy();
                macdChart = new Chart(ctx, {{
                    type: 'line',
                    data: {{ labels: dates, datasets: [{{ data: macdData, borderColor: '#2196F3', borderWidth: 2 }}, {{ data: signalData, borderColor: '#FF9800', borderWidth: 2 }}] }},
                    options: {{ responsive: true, maintainAspectRatio: false, animation: {{ duration: 300 }}, plugins: {{ legend: {{ display: false }} }} }}
                }});
            }}
            
            function updateCharts(data) {{
                if (priceChart) {{ const {{ dates, prices }} = generateChartData(data.price); priceChart.data.labels = dates; priceChart.data.datasets[0].data = prices; priceChart.update(); }}
                if (rsiChart) {{ const {{ dates }} = generateChartData(100); rsiChart.data.labels = dates; rsiChart.update(); }}
                if (macdChart) {{ const {{ dates }} = generateChartData(100); macdChart.data.labels = dates; macdChart.update(); }}
            }}
            
            function startTimer() {{
                const timerEl = document.getElementById('timer');
                countdown = 3;
                if (timerInterval) clearInterval(timerInterval);
                timerInterval = setInterval(() => {{
                    countdown--;
                    timerEl.textContent = `Prochaine mise à jour dans ${{countdown}}s`;
                    if (countdown <= 0) {{ countdown = 3; requestDataUpdate(); }}
                }}, 1000);
            }}
            
            function showTab(tabId) {{
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                event.target.classList.add('active');
                document.getElementById(tabId).classList.add('active');
                sendToStreamlit('tab_change', {{ tab: tabId }});
            }}
            
            function forceRefresh() {{
                const btn = document.getElementById('refreshBtn');
                btn.disabled = true; btn.textContent = '⏳ Chargement...';
                requestDataUpdate();
                setTimeout(() => {{ btn.disabled = false; btn.textContent = '🔄 Rafraîchir maintenant'; }}, 1000);
            }}
            
            function showToast(message, type = 'info') {{
                const toast = document.getElementById('toast');
                toast.textContent = message;
                toast.className = `toast ${{type}} show`;
                setTimeout(() => toast.classList.remove('show'), 2000);
            }}
            
            window.onload = function() {{
                createPriceChart(); createRSIChart(); createMACDChart(); startTimer();
                sendToStreamlit('dashboard_ready', {{ symbol: lastData.symbol, message: 'Dashboard prêt' }});
            }};
            
            window.addEventListener('resize', () => [priceChart, rsiChart, macdChart].forEach(c => c?.resize()));
            window.addEventListener('message', (e) => {{ if (e.data.type === 'streamlit:update') updateDashboard(e.data.data); }});
        </script>
    </body>
    </html>
    """
    return html_code

# ==================== INTERFACE PRINCIPALE ====================
def main():
    st.title("📊 Dashboard Financier Pro")
    st.caption("Toutes les fonctionnalités: API réelles, BDD, Alertes, Multi-symboles, Export")
    
    db = DatabaseManager()
    
    with st.sidebar:
        st.header("⚙️ Configuration")
        config_tab = st.tabs(["📈 Symboles", "🔌 API", "🔔 Alertes", "💾 BDD", "📤 Export"])
        
        with config_tab[0]:
            st.subheader("Sélection des symboles")
            comparison_mode = st.checkbox("Mode comparaison (multi-symboles)", value=st.session_state.comparison_mode)
            st.session_state.comparison_mode = comparison_mode
            
            all_symbols = ["MC.PA", "RMS.PA", "KER.PA", "CDI.PA", "AI.PA", "OR.PA", "BNP.PA", "SAN.PA", "TOT.PA"]
            
            if comparison_mode:
                symbols = st.multiselect("Symboles à comparer", all_symbols, default=st.session_state.current_symbols)
                st.session_state.current_symbols = symbols if symbols else ["MC.PA"]
            else:
                symbol = st.selectbox("Symbole principal", all_symbols, index=0)
                st.session_state.current_symbols = [symbol]
            
            period = st.selectbox("Période", ["1H", "4H", "1J", "1S", "1M", "3M", "1Y"], index=2)
        
        with config_tab[1]:
            st.subheader("Source des données")
            api_source = st.radio("API à utiliser", ["Simulation", "Yahoo Finance", "Alpha Vantage"], index=0)
            st.session_state.api_source = api_source
            if api_source == "Alpha Vantage":
                api_key = st.text_input("Clé API Alpha Vantage", type="password")
                st.session_state.api_key = api_key
        
        with config_tab[2]:
            st.subheader("Gestion des alertes")
            with st.expander("➕ Nouvelle alerte"):
                alert_symbol = st.selectbox("Symbole", st.session_state.current_symbols, key="alert_symbol")
                alert_type = st.selectbox("Type", ["Prix", "Volume", "Variation %"])
                condition = st.selectbox("Condition", ["Au-dessus de", "En-dessous de"])
                threshold = st.number_input("Seuil", min_value=0.0, value=500.0, step=10.0)
                
                if st.button("Créer l'alerte", use_container_width=True):
                    cond = "above" if condition == "Au-dessus de" else "below"
                    alert_id = db.add_alert(alert_symbol, alert_type.lower(), threshold, cond)
                    if alert_id:
                        st.success(f"Alerte créée (ID: {alert_id})")
                        st.balloons()
            
            alerts = db.get_active_alerts()
            if alerts:
                for alert in alerts[-5:]:
                    alert_id, sym, a_type, threshold, condition, active, created, last = alert
                    st.info(f"{sym} - {a_type} {condition} {threshold}")
        
        with config_tab[3]:
            st.subheader("Base de données")
            if st.session_state.db_initialized:
                st.success("✅ BDD initialisée")
                stats = db.get_database_stats()
                if stats:
                    st.metric("Enregistrements", stats.get('total_records', 0))
                    st.metric("Symboles", stats.get('unique_symbols', 0))
        
        with config_tab[4]:
            st.subheader("Export des données")
            export_format = st.selectbox("Format", ["CSV", "Excel", "JSON"])
            if st.button("📥 Exporter", use_container_width=True):
                for symbol in st.session_state.current_symbols:
                    data = generate_live_data(symbol, st.session_state.api_source, st.session_state.api_key)
                    if export_format == "CSV":
                        filepath = ExportManager.to_csv(data, symbol)
                    elif export_format == "Excel":
                        filepath = ExportManager.to_excel(data, symbol)
                    else:
                        filepath = ExportManager.to_json(data, symbol)
                    st.success(f"Exporté: {filepath.name}")
                st.balloons()
        
        st.markdown("---")
        st.metric("Mises à jour", st.session_state.update_counter, "+1/3s")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⏸️ Pause", use_container_width=True):
                st.session_state.paused = True
        with col2:
            if st.button("▶️ Reprendre", use_container_width=True):
                st.session_state.paused = False
    
    if st.session_state.comparison_mode:
        st.subheader("📈 Mode Comparaison Multi-symboles")
        all_data = {}
        for symbol in st.session_state.current_symbols:
            data = generate_live_data(symbol, st.session_state.api_source, st.session_state.api_key)
            all_data[symbol] = data
            db.save_price(symbol, data)
            triggered = db.check_alerts(symbol, data['price'])
            if triggered:
                st.warning(f"🔔 Alerte {symbol}: {data['price']} €")
        
        fig = create_comparison_chart(all_data)
        st.plotly_chart(fig, use_container_width=True)
        
        comparison_data = []
        for symbol, data in all_data.items():
            comparison_data.append({
                "Symbole": symbol,
                "Prix": f"{data['price']:.2f} €",
                "Var": f"{data['change']:+.2f}%",
                "Volume": f"{data['volume']:,}",
                "P/E": f"{data.get('pe_ratio', 0):.2f}",
                "Dividende": f"{data.get('dividend', 0):.2f} €"
            })
        st.dataframe(pd.DataFrame(comparison_data), use_container_width=True, hide_index=True)
    
    else:
        symbol = st.session_state.current_symbols[0]
        data = generate_live_data(symbol, st.session_state.api_source, st.session_state.api_key)
        st.session_state.update_counter += 1
        st.session_state.last_update = datetime.now()
        
        db.save_price(symbol, data)
        triggered = db.check_alerts(symbol, data['price'])
        if triggered:
            st.warning(f"🔔 Alerte {symbol}: {data['price']} €")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Cours", f"{data['price']:.2f} €", f"{data['change']:+.2f}%")
        with col2:
            st.metric("Volume", f"{data['volume']:,}")
        with col3:
            pe = data.get('pe_ratio', 0)
            st.metric("P/E", f"{pe:.2f}" if pe > 0 else "N/A")
        with col4:
            div = data.get('dividend', 0)
            yield_val = data.get('dividend_yield', 0)
            st.metric("Dividende", f"{div:.2f} €" if div > 0 else "N/A", f"{yield_val:.2f}%" if yield_val > 0 else None)
        
        st.caption(f"Source: {data.get('source', 'Simulation')}")
        
        market_hour = datetime.now().hour
        market_open = 9 <= market_hour < 17
        
        dashboard_data = {
            'symbol': symbol,
            'price': data['price'],
            'change': data['change'],
            'volume': data['volume'],
            'pe_ratio': data.get('pe_ratio', 0),
            'dividend': data.get('dividend', 0),
            'dividend_yield': data.get('dividend_yield', 0),
            'last_update': datetime.now().strftime('%H:%M:%S'),
            'market_open': market_open,
            'period': period,
            'historical_rows': generate_historical_rows(data)
        }
        
        html(dashboard_data, height=1200)
        
        with st.expander("📊 Historique"):
            history = db.get_history(symbol, days=1)
            if not history.empty:
                st.dataframe(history[['timestamp', 'price', 'change', 'volume']], use_container_width=True)
    
    if not st.session_state.get('paused', False):
        time.sleep(3)
        st.rerun()

if __name__ == "__main__":
    main()
