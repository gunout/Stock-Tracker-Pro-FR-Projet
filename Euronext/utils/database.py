# utils/database.py - Nouveau fichier
import sqlite3
import pandas as pd
from datetime import datetime
import streamlit as st

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('stock_data.db', check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        """Crée les tables si elles n'existent pas"""
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS stock_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                date TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                UNIQUE(symbol, date)
            )
        ''')
        self.conn.commit()
    
    def save_prices(self, symbol, df):
        """Sauvegarde les prix historiques"""
        for _, row in df.iterrows():
            try:
                self.conn.execute('''
                    INSERT OR REPLACE INTO stock_prices 
                    (symbol, date, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    row['Date'].strftime('%Y-%m-%d'),
                    row['Open'],
                    row['High'],
                    row['Low'],
                    row['Close'],
                    row['Volume']
                ))
            except:
                pass
        self.conn.commit()
    
    def load_prices(self, symbol, start_date, end_date):
        """Charge les prix historiques"""
        query = '''
            SELECT * FROM stock_prices 
            WHERE symbol = ? AND date BETWEEN ? AND ?
            ORDER BY date
        '''
        df = pd.read_sql_query(query, self.conn, 
                               params=[symbol, start_date, end_date])
        if not df.empty:
            df['Date'] = pd.to_datetime(df['date'])
        return df
