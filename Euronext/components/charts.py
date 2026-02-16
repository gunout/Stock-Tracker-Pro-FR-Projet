# src/components/charts.py
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple

class ChartBuilder:
    """Constructeur de graphiques interactifs"""
    
    @staticmethod
    def create_candlestick_chart(df: pd.DataFrame, symbol: str) -> go.Figure:
        """Crée un graphique en chandeliers japonais"""
        fig = go.Figure(data=[go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name=symbol
        )])
        
        fig.update_layout(
            title=f"Évolution {symbol}",
            yaxis_title="Prix (€)",
            xaxis_title="Date",
            template="plotly_white",
            height=600,
            showlegend=True
        )
        
        # Ajouter les moyennes mobiles
        if 'MA20' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['Date'], y=df['MA20'],
                mode='lines', name='MM20',
                line=dict(color='orange', width=1)
            ))
        
        if 'MA50' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['Date'], y=df['MA50'],
                mode='lines', name='MM50',
                line=dict(color='blue', width=1)
            ))
        
        return fig
    
    @staticmethod
    def create_volume_chart(df: pd.DataFrame) -> go.Figure:
        """Crée un graphique de volumes"""
        colors = ['red' if row['Close'] < row['Open'] else 'green' 
                 for _, row in df.iterrows()]
        
        fig = go.Figure(data=[go.Bar(
            x=df['Date'],
            y=df['Volume'],
            marker_color=colors,
            name='Volume'
        )])
        
        fig.update_layout(
            title="Volume de transactions",
            yaxis_title="Volume",
            xaxis_title="Date",
            template="plotly_white",
            height=300,
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def create_comparison_chart(data: Dict[str, pd.Series]) -> go.Figure:
        """Compare plusieurs actions"""
        fig = go.Figure()
        
        for symbol, prices in data.items():
            fig.add_trace(go.Scatter(
                x=prices.index,
                y=prices,
                mode='lines',
                name=symbol,
                line=dict(width=2)
            ))
        
        fig.update_layout(
            title="Comparaison des performances",
            yaxis_title="Prix normalisés (base 100)",
            xaxis_title="Date",
            template="plotly_white",
            height=500,
            hovermode='x unified'
        )
        
        return fig
    
    @staticmethod
    def create_heatmap(correlation_matrix: pd.DataFrame) -> go.Figure:
        """Crée une heatmap de corrélation"""
        fig = go.Figure(data=go.Heatmap(
            z=correlation_matrix.values,
            x=correlation_matrix.columns,
            y=correlation_matrix.index,
            colorscale='RdBu',
            zmin=-1, zmax=1,
            text=np.round(correlation_matrix.values, 2),
            texttemplate='%{text}',
            textfont={"size": 10},
            hoverongaps=False
        ))
        
        fig.update_layout(
            title="Matrice de corrélation",
            height=600,
            template="plotly_white"
        )
        
        return fig
    
    @staticmethod
    def create_pie_chart(data: Dict[str, float], title: str) -> go.Figure:
        """Crée un diagramme circulaire"""
        fig = go.Figure(data=[go.Pie(
            labels=list(data.keys()),
            values=list(data.values()),
            hole=0.3
        )])
        
        fig.update_layout(
            title=title,
            height=400,
            template="plotly_white"
        )
        
        return fig


def display_advanced_charts(symbol: str, historical_data: pd.DataFrame):
    """Affiche une combinaison de graphiques"""
    
    tab1, tab2, tab3 = st.tabs(["📈 Prix", "📊 Volumes", "📉 Indicateurs"])
    
    with tab1:
        # Graphique principal
        fig_price = ChartBuilder.create_candlestick_chart(historical_data, symbol)
        st.plotly_chart(fig_price, use_container_width=True)
        
        # Options supplémentaires
        with st.expander("Options d'affichage"):
            col1, col2 = st.columns(2)
            with col1:
                show_ma = st.checkbox("Moyennes mobiles", value=True)
            with col2:
                show_bb = st.checkbox("Bollinger Bands", value=False)
    
    with tab2:
        # Graphique des volumes
        fig_volume = ChartBuilder.create_volume_chart(historical_data)
        st.plotly_chart(fig_volume, use_container_width=True)
        
        # Statistiques des volumes
        col1, col2, col3 = st.columns(3)
        col1.metric("Volume moyen", f"{historical_data['Volume'].mean():,.0f}")
        col2.metric("Volume max", f"{historical_data['Volume'].max():,.0f}")
        col3.metric("Volume min", f"{historical_data['Volume'].min():,.0f}")
    
    with tab3:
        # Indicateurs techniques
        col1, col2 = st.columns(2)
        
        with col1:
            # RSI
            rsi = calculate_rsi(historical_data['Close'])
            fig_rsi = go.Figure(data=[go.Scatter(
                x=historical_data['Date'], y=rsi,
                mode='lines', name='RSI'
            )])
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
            fig_rsi.update_layout(title="RSI (14)", height=300)
            st.plotly_chart(fig_rsi, use_container_width=True)
        
        with col2:
            # MACD
            macd, signal = calculate_macd(historical_data['Close'])
            fig_macd = go.Figure()
            fig_macd.add_trace(go.Scatter(x=historical_data['Date'], y=macd, name='MACD'))
            fig_macd.add_trace(go.Scatter(x=historical_data['Date'], y=signal, name='Signal'))
            fig_macd.update_layout(title="MACD", height=300)
            st.plotly_chart(fig_macd, use_container_width=True)


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calcule le RSI"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(prices: pd.Series) -> Tuple[pd.Series, pd.Series]:
    """Calcule le MACD"""
    exp1 = prices.ewm(span=12, adjust=False).mean()
    exp2 = prices.ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal