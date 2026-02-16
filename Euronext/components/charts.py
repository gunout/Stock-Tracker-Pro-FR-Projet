# components/charts.py - À ajouter progressivement
import plotly.graph_objects as go
import streamlit as st

def create_candlestick_chart(df, symbol):
    """Graphique en chandeliers"""
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
        height=500,
        template="plotly_white"
    )
    return fig

def create_volume_chart(df):
    """Graphique des volumes"""
    fig = go.Figure(data=[go.Bar(
        x=df['Date'],
        y=df['Volume'],
        name='Volume'
    )])
    fig.update_layout(height=200, showlegend=False)
    return fig
