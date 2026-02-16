# src/utils/validators.py
import re
from typing import Any, Optional, List, Dict, Union
from datetime import datetime
import pandas as pd
import numpy as np

class DataValidator:
    """Validateur de données financières"""
    
    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """Valide un symbole boursier"""
        if not symbol or not isinstance(symbol, str):
            return False
        
        # Format: lettres, point, lettres (ex: MC.PA, RMS.PA)
        pattern = r'^[A-Z]{2,4}\.[A-Z]{2}$'
        return bool(re.match(pattern, symbol))
    
    @staticmethod
    def validate_price(price: Any) -> bool:
        """Valide un prix"""
        try:
            price = float(price)
            return price > 0 and price < 1000000  # Prix raisonnable
        except (TypeError, ValueError):
            return False
    
    @staticmethod
    def validate_volume(volume: Any) -> bool:
        """Valide un volume de transactions"""
        try:
            volume = int(volume)
            return volume >= 0 and volume < 1e12  # Volume raisonnable
        except (TypeError, ValueError):
            return False
    
    @staticmethod
    def validate_date(date: Any, fmt: str = "%Y-%m-%d") -> bool:
        """Valide une date"""
        if isinstance(date, datetime):
            return True
        
        if isinstance(date, str):
            try:
                datetime.strptime(date, fmt)
                return True
            except ValueError:
                return False
        
        return False
    
    @staticmethod
    def validate_percentage(value: Any) -> bool:
        """Valide un pourcentage"""
        try:
            pct = float(value)
            return -100 <= pct <= 100  # Pourcentage entre -100% et 100%
        except (TypeError, ValueError):
            return False
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame, required_columns: List[str]) -> bool:
        """Valide un DataFrame"""
        if df is None or df.empty:
            return False
        
        # Vérifier les colonnes requises
        return all(col in df.columns for col in required_columns)


class FinancialValidator:
    """Validateur spécifique aux données financières"""
    
    @staticmethod
    def validate_pe_ratio(pe: Any) -> bool:
        """Valide un ratio P/E"""
        try:
            pe = float(pe)
            return 0 <= pe <= 100  # P/E généralement entre 0 et 100
        except (TypeError, ValueError):
            return False
    
    @staticmethod
    def validate_dividend_yield(yield_val: Any) -> bool:
        """Valide un rendement de dividende"""
        try:
            y = float(yield_val)
            return 0 <= y <= 20  # Rendement max 20%
        except (TypeError, ValueError):
            return False
    
    @staticmethod
    def validate_market_cap(cap: Any) -> bool:
        """Valide une capitalisation boursière"""
        try:
            cap = float(cap)
            return 1e6 <= cap <= 1e13  # Entre 1M et 10 000Mds
        except (TypeError, ValueError):
            return False


class InputValidator:
    """Validateur des entrées utilisateur"""
    
    @staticmethod
    def validate_symbol_input(symbol: str) -> tuple:
        """Valide et normalise un symbole entré par l'utilisateur"""
        if not symbol:
            return False, "Symbole requis"
        
        symbol = symbol.strip().upper()
        
        if not DataValidator.validate_symbol(symbol):
            return False, f"Format invalide: {symbol}. Format attendu: XX.XX (ex: MC.PA)"
        
        return True, symbol
    
    @staticmethod
    def validate_date_range(start_date: str, end_date: str) -> tuple:
        """Valide une plage de dates"""
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            
            if start > end:
                return False, "La date de début doit être antérieure à la date de fin"
            
            if end > datetime.now():
                return False, "La date de fin ne peut pas être dans le futur"
            
            return True, (start, end)
            
        except ValueError as e:
            return False, f"Format de date invalide: {str(e)}"
    
    @staticmethod
    def validate_number_input(value: Any, min_val: float = None, max_val: float = None) -> tuple:
        """Valide une entrée numérique"""
        try:
            num = float(value)
            
            if min_val is not None and num < min_val:
                return False, f"Valeur minimum: {min_val}"
            
            if max_val is not None and num > max_val:
                return False, f"Valeur maximum: {max_val}"
            
            return True, num
            
        except (TypeError, ValueError):
            return False, "Veuillez entrer un nombre valide"


class ResponseValidator:
    """Validateur des réponses API"""
    
    @staticmethod
    def validate_api_response(response: Dict, required_fields: List[str]) -> tuple:
        """Valide une réponse API"""
        if not response:
            return False, "Réponse vide"
        
        if not isinstance(response, dict):
            return False, "Format de réponse invalide"
        
        missing_fields = [field for field in required_fields if field not in response]
        
        if missing_fields:
            return False, f"Champs manquants: {', '.join(missing_fields)}"
        
        return True, response
    
    @staticmethod
    def validate_status_code(status_code: int) -> tuple:
        """Valide un code HTTP"""
        if status_code == 200:
            return True, "Succès"
        elif status_code == 429:
            return False, "Rate limit atteint"
        elif 400 <= status_code < 500:
            return False, f"Erreur client: {status_code}"
        elif 500 <= status_code < 600:
            return False, f"Erreur serveur: {status_code}"
        else:
            return False, f"Code inattendu: {status_code}"


def validate_all_inputs(symbol: str, start_date: str, end_date: str) -> Dict[str, Any]:
    """Valide tous les inputs d'un coup"""
    results = {
        "is_valid": True,
        "errors": {},
        "values": {}
    }
    
    # Valider le symbole
    valid, result = InputValidator.validate_symbol_input(symbol)
    if valid:
        results["values"]["symbol"] = result
    else:
        results["is_valid"] = False
        results["errors"]["symbol"] = result
    
    # Valider les dates
    valid, result = InputValidator.validate_date_range(start_date, end_date)
    if valid:
        results["values"]["start_date"], results["values"]["end_date"] = result
    else:
        results["is_valid"] = False
        results["errors"]["date_range"] = result
    
    return results