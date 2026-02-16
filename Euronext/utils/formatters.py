# utils/formatters.py
from datetime import datetime, timedelta
from typing import Any, Union, Optional, Dict, List
import pandas as pd
import numpy as np

class DataFormatter:
    """Formateur de données générales"""
    
    @staticmethod
    def format_currency(value: Any, currency: str = "€", decimals: int = 2) -> str:
        """Formate une valeur en devise"""
        try:
            num = float(value)
            if abs(num) >= 1e9:
                return f"{num/1e9:.{decimals}f} Md{currency}"
            elif abs(num) >= 1e6:
                return f"{num/1e6:.{decimals}f} M{currency}"
            elif abs(num) >= 1e3:
                return f"{num/1e3:.{decimals}f} k{currency}"
            else:
                return f"{num:.{decimals}f} {currency}"
        except (TypeError, ValueError):
            return f"N/A {currency}"
    
    @staticmethod
    def format_percentage(value: Any, decimals: int = 2) -> str:
        """Formate un pourcentage"""
        try:
            num = float(value)
            sign = "+" if num > 0 else ""
            return f"{sign}{num:.{decimals}f}%"
        except (TypeError, ValueError):
            return "N/A%"
    
    @staticmethod
    def format_number(value: Any, decimals: int = 0) -> str:
        """Formate un nombre avec séparateurs"""
        try:
            num = float(value)
            if num.is_integer():
                return f"{int(num):,}".replace(",", " ")
            else:
                return f"{num:,.{decimals}f}".replace(",", " ")
        except (TypeError, ValueError):
            return "N/A"
    
    @staticmethod
    def format_date(date: Any, fmt: str = "%d/%m/%Y") -> str:
        """Formate une date"""
        if isinstance(date, datetime):
            return date.strftime(fmt)
        elif isinstance(date, str):
            try:
                dt = datetime.fromisoformat(date)
                return dt.strftime(fmt)
            except ValueError:
                return date
        else:
            return str(date)
    
    @staticmethod
    def format_timedelta(td: timedelta) -> str:
        """Formate une durée"""
        total_seconds = int(td.total_seconds())
        
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        parts = []
        if days > 0:
            parts.append(f"{days}j")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}min")
        if seconds > 0 and not parts:
            parts.append(f"{seconds}s")
        
        return " ".join(parts) if parts else "0s"


class StockFormatter:
    """Formateur spécifique aux actions"""
    
    @staticmethod
    def format_stock_data(data: Dict) -> Dict:
        """Formate toutes les données d'une action"""
        formatted = {}
        
        # Prix
        if 'price' in data:
            formatted['price_display'] = DataFormatter.format_currency(data['price'])
        
        # Variation
        if 'change' in data:
            formatted['change_display'] = DataFormatter.format_percentage(data['change'])
            # Couleur pour la variation
            formatted['change_color'] = "green" if data['change'] >= 0 else "red"
        
        # Volume
        if 'volume' in data:
            formatted['volume_display'] = DataFormatter.format_number(data['volume'])
        
        # Capitalisation
        if 'market_cap' in data:
            formatted['market_cap_display'] = DataFormatter.format_currency(
                data['market_cap'], "€", 2
            )
        
        # Ratios
        if 'pe_ratio' in data:
            formatted['pe_display'] = f"{data['pe_ratio']:.2f}"
        
        if 'dividend_yield' in data:
            formatted['yield_display'] = DataFormatter.format_percentage(
                data['dividend_yield']
            )
        
        return formatted
    
    @staticmethod
    def format_historical_data(df: pd.DataFrame) -> pd.DataFrame:
        """Formate un DataFrame historique"""
        formatted = df.copy()
        
        # Renommer les colonnes
        column_mapping = {
            'Open': 'Ouverture',
            'High': 'Plus haut',
            'Low': 'Plus bas',
            'Close': 'Clôture',
            'Volume': 'Volume',
            'Date': 'Date'
        }
        
        formatted = formatted.rename(columns=column_mapping)
        
        # Formater les dates
        if 'Date' in formatted.columns:
            formatted['Date'] = formatted['Date'].apply(
                lambda x: DataFormatter.format_date(x)
            )
        
        # Formater les prix
        price_columns = ['Ouverture', 'Plus haut', 'Plus bas', 'Clôture']
        for col in price_columns:
            if col in formatted.columns:
                formatted[col] = formatted[col].apply(
                    lambda x: DataFormatter.format_currency(x, "€", 2)
                )
        
        # Formater le volume
        if 'Volume' in formatted.columns:
            formatted['Volume'] = formatted['Volume'].apply(
                lambda x: DataFormatter.format_number(x)
            )
        
        return formatted


class DataFrameFormatter:
    """Formateur pour DataFrames pandas"""
    
    @staticmethod
    def style_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Applique des styles à un DataFrame"""
        def color_negative_red(val):
            color = 'red' if isinstance(val, (int, float)) and val < 0 else 'black'
            return f'color: {color}'
        
        def highlight_positive(val):
            color = 'lightgreen' if isinstance(val, (int, float)) and val > 0 else ''
            return f'background-color: {color}'
        
        styled = df.style \
            .applymap(color_negative_red) \
            .applymap(highlight_positive) \
            .format(precision=2, thousands=" ", decimal=",")
        
        return styled
    
    @staticmethod
    def prepare_for_display(df: pd.DataFrame, max_rows: int = 100) -> pd.DataFrame:
        """Prépare un DataFrame pour l'affichage"""
        if len(df) > max_rows:
            # Échantillonnage si trop de lignes
            indices = np.linspace(0, len(df)-1, max_rows, dtype=int)
            df = df.iloc[indices]
        
        return df


class JSONFormatter:
    """Formateur pour données JSON"""
    
    @staticmethod
    def pretty_print(data: Any, indent: int = 2) -> str:
        """Formate joliment du JSON"""
        import json
        try:
            return json.dumps(data, indent=indent, ensure_ascii=False, default=str)
        except:
            return str(data)
    
    @staticmethod
    def flatten_json(data: Dict, parent_key: str = '', sep: str = '.') -> Dict:
        """Aplatit un JSON imbriqué"""
        items = []
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(JSONFormatter.flatten_json(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(
                            JSONFormatter.flatten_json(
                                item, f"{new_key}[{i}]", sep=sep
                            ).items()
                        )
                    else:
                        items.append((f"{new_key}[{i}]", item))
            else:
                items.append((new_key, v))
        
        return dict(items)


def format_for_display(data: Any, data_type: str = "auto") -> str:
    """Formate automatiquement selon le type de données"""
    
    if data_type == "auto":
        if isinstance(data, (int, float)):
            if abs(data) > 1000000:
                return DataFormatter.format_currency(data)
            elif isinstance(data, float):
                return f"{data:.2f}"
            else:
                return str(data)
        elif isinstance(data, datetime):
            return DataFormatter.format_date(data)
        elif isinstance(data, dict):
            stock_formatter = StockFormatter()
            return str(stock_formatter.format_stock_data(data))
        else:
            return str(data)
    
    formatters = {
        "currency": lambda x: DataFormatter.format_currency(x),
        "percentage": lambda x: DataFormatter.format_percentage(x),
        "number": lambda x: DataFormatter.format_number(x),
        "date": lambda x: DataFormatter.format_date(x),
        "stock": lambda x: str(StockFormatter.format_stock_data(x))
    }
    
    formatter = formatters.get(data_type, str)
    return formatter(data)
