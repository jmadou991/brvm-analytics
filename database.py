"""
Module de gestion de la base de données SQLite pour stocker les données de la BRVM
"""

import sqlite3
from datetime import datetime
import os


class BRVMDatabase:
    """Classe pour gérer la base de données SQLite des cours de la BRVM"""
    
    def __init__(self, db_name='brvm.db'):
        """
        Initialise la connexion à la base de données
        
        Args:
            db_name (str): Nom du fichier de base de données
        """
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_table()
    
    def _connect(self):
        """Établit la connexion à la base de données"""
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Connexion à la base de données '{self.db_name}' établie")
        except sqlite3.Error as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur de connexion à la base de données: {e}")
    
    def _create_table(self):
        """Crée la table 'cours' si elle n'existe pas"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS cours (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbole TEXT NOT NULL,
                    nom TEXT NOT NULL,
                    prix REAL NOT NULL,
                    variation REAL,
                    volume INTEGER,
                    plus_haut REAL,
                    plus_bas REAL,
                    date_heure TIMESTAMP NOT NULL
                )
            ''')
            
            # Créer un index sur le symbole et la date pour améliorer les performances
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_symbole_date 
                ON cours(symbole, date_heure)
            ''')
            
            self.conn.commit()
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Table 'cours' vérifiée/créée avec succès")
        except sqlite3.Error as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors de la création de la table: {e}")
    
    def save_data(self, actions):
        """
        Sauvegarde les données des actions dans la base de données
        
        Args:
            actions (list): Liste de dictionnaires contenant les données des actions
            
        Returns:
            int: Nombre d'enregistrements insérés
        """
        if not actions:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Aucune donnée à sauvegarder")
            return 0
        
        try:
            count = 0
            for action in actions:
                self.cursor.execute('''
                    INSERT INTO cours (symbole, nom, prix, variation, volume, plus_haut, plus_bas, date_heure)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    action['symbole'],
                    action['nom'],
                    action['prix'],
                    action['variation'],
                    action['volume'],
                    action['plus_haut'],
                    action['plus_bas'],
                    action['date_heure']
                ))
                count += 1
            
            self.conn.commit()
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {count} enregistrements sauvegardés dans la base de données")
            return count
            
        except sqlite3.Error as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors de la sauvegarde: {e}")
            self.conn.rollback()
            return 0
    
    def get_latest_data(self, limit=10):
        """
        Récupère les dernières données enregistrées
        
        Args:
            limit (int): Nombre maximum d'enregistrements à récupérer
            
        Returns:
            list: Liste de tuples contenant les données
        """
        try:
            self.cursor.execute('''
                SELECT symbole, nom, prix, variation, volume, plus_haut, plus_bas, date_heure
                FROM cours
                ORDER BY date_heure DESC
                LIMIT ?
            ''', (limit,))
            
            results = self.cursor.fetchall()
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {len(results)} enregistrements récupérés")
            return results
            
        except sqlite3.Error as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors de la récupération: {e}")
            return []
    
    def get_data_by_symbole(self, symbole, limit=10):
        """
        Récupère les données pour un symbole spécifique
        
        Args:
            symbole (str): Symbole de l'action
            limit (int): Nombre maximum d'enregistrements à récupérer
            
        Returns:
            list: Liste de tuples contenant les données
        """
        try:
            self.cursor.execute('''
                SELECT symbole, nom, prix, variation, volume, plus_haut, plus_bas, date_heure
                FROM cours
                WHERE symbole = ?
                ORDER BY date_heure DESC
                LIMIT ?
            ''', (symbole, limit))
            
            results = self.cursor.fetchall()
            return results
            
        except sqlite3.Error as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors de la récupération: {e}")
            return []
    
    def get_all_symboles(self):
        """
        Récupère la liste de tous les symboles uniques
        
        Returns:
            list: Liste des symboles
        """
        try:
            self.cursor.execute('''
                SELECT DISTINCT symbole
                FROM cours
                ORDER BY symbole
            ''')
            
            results = [row[0] for row in self.cursor.fetchall()]
            return results
            
        except sqlite3.Error as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors de la récupération: {e}")
            return []
    
    def get_statistics(self):
        """
        Récupère des statistiques sur la base de données
        
        Returns:
            dict: Dictionnaire contenant les statistiques
        """
        try:
            # Nombre total d'enregistrements
            self.cursor.execute('SELECT COUNT(*) FROM cours')
            total_records = self.cursor.fetchone()[0]
            
            # Nombre de symboles uniques
            self.cursor.execute('SELECT COUNT(DISTINCT symbole) FROM cours')
            unique_symboles = self.cursor.fetchone()[0]
            
            # Date du premier et dernier enregistrement
            self.cursor.execute('SELECT MIN(date_heure), MAX(date_heure) FROM cours')
            first_date, last_date = self.cursor.fetchone()
            
            stats = {
                'total_records': total_records,
                'unique_symboles': unique_symboles,
                'first_date': first_date,
                'last_date': last_date
            }
            
            return stats
            
        except sqlite3.Error as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors de la récupération des statistiques: {e}")
            return {}
    
    def close(self):
        """Ferme la connexion à la base de données"""
        if self.conn:
            self.conn.close()
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Connexion à la base de données fermée")


if __name__ == "__main__":
    # Test de la base de données
    db = BRVMDatabase()
    
    # Afficher les statistiques
    stats = db.get_statistics()
    print(f"\n{'='*80}")
    print("Statistiques de la base de données:")
    print(f"{'='*80}")
    print(f"Total d'enregistrements: {stats.get('total_records', 0)}")
    print(f"Symboles uniques: {stats.get('unique_symboles', 0)}")
    print(f"Premier enregistrement: {stats.get('first_date', 'N/A')}")
    print(f"Dernier enregistrement: {stats.get('last_date', 'N/A')}")
    
    # Afficher les dernières données
    latest = db.get_latest_data(5)
    if latest:
        print(f"\n{'='*80}")
        print("Dernières données enregistrées:")
        print(f"{'='*80}")
        for row in latest:
            print(f"\nSymbole: {row[0]}, Nom: {row[1]}, Prix: {row[2]}, Variation: {row[3]}%, Date: {row[7]}")
    
    db.close()
