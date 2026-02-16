# repair_db.py
import sqlite3
from pathlib import Path

# Chemin vers la base de données
DB_PATH = Path(__file__).parent / "stock_data.db"

def repair_database():
    """Répare la structure de la base de données"""
    print("🔧 Réparation de la base de données...")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Vérifier la structure actuelle
        cursor.execute("PRAGMA table_info(stock_prices)")
        columns = cursor.fetchall()
        print("Structure actuelle:", columns)
        
        # Vérifier si la colonne source existe
        column_names = [col[1] for col in columns]
        
        if 'source' not in column_names:
            print("➕ Ajout de la colonne 'source'...")
            cursor.execute("ALTER TABLE stock_prices ADD COLUMN source TEXT DEFAULT 'Simulation'")
            print("✅ Colonne 'source' ajoutée")
        else:
            print("✅ La colonne 'source' existe déjà")
        
        conn.commit()
        
        # Vérifier la nouvelle structure
        cursor.execute("PRAGMA table_info(stock_prices)")
        new_columns = cursor.fetchall()
        print("Nouvelle structure:", new_columns)
        
        conn.close()
        print("🎉 Base de données réparée avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    repair_database()
