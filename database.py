"""
Module de gestion de la base de données PostgreSQL pour stocker les données de la BRVM
"""

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


class BRVMDatabase:
    """Classe pour gérer la base de données PostgreSQL des cours de la BRVM"""
    
    def __init__(self):
        """
        Initialise le pool de connexions à la base de données PostgreSQL
        """
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL n'est pas définie dans les variables d'environnement")
        
        # Créer le pool de connexions
        try:
            self.pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=self.database_url
            )
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Pool de connexions PostgreSQL créé avec succès")
            self._create_table()
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors de la création du pool: {e}")
            raise
    
    def get_connection(self):
        """Obtient une connexion du pool"""
        return self.pool.getconn()
    
    def release_connection(self, conn):
        """Libère une connexion vers le pool"""
        self.pool.putconn(conn)
    
    def _create_table(self):
        """Crée la table 'cours' si elle n'existe pas"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cours (
                    id SERIAL PRIMARY KEY,
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
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_symbole_date 
                ON cours(symbole, date_heure)
            ''')
            
            conn.commit()
            cursor.close()
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Table 'cours' vérifiée/créée avec succès")
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors de la création de la table: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                self.release_connection(conn)
    
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
        
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            count = 0
            
            for action in actions:
                cursor.execute('''
                    INSERT INTO cours (symbole, nom, prix, variation, volume, plus_haut, plus_bas, date_heure)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
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
            
            conn.commit()
            cursor.close()
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {count} enregistrements sauvegardés dans la base de données")
            return count
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors de la sauvegarde: {e}")
            if conn:
                conn.rollback()
            return 0
        finally:
            if conn:
                self.release_connection(conn)
    
    def get_latest_data(self, limit=10):
        """
        Récupère les dernières données enregistrées
        
        Args:
            limit (int): Nombre maximum d'enregistrements à récupérer
            
        Returns:
            list: Liste de tuples contenant les données
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT symbole, nom, prix, variation, volume, plus_haut, plus_bas, date_heure
                FROM cours
                ORDER BY date_heure DESC
                LIMIT %s
            ''', (limit,))
            
            results = cursor.fetchall()
            cursor.close()
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {len(results)} enregistrements récupérés")
            return results
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors de la récupération: {e}")
            return []
        finally:
            if conn:
                self.release_connection(conn)
    
    def get_data_by_symbole(self, symbole, limit=10):
        """
        Récupère les données pour un symbole spécifique
        
        Args:
            symbole (str): Symbole de l'action
            limit (int): Nombre maximum d'enregistrements à récupérer
            
        Returns:
            list: Liste de tuples contenant les données
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT symbole, nom, prix, variation, volume, plus_haut, plus_bas, date_heure
                FROM cours
                WHERE symbole = %s
                ORDER BY date_heure DESC
                LIMIT %s
            ''', (symbole, limit))
            
            results = cursor.fetchall()
            cursor.close()
            return results
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors de la récupération: {e}")
            return []
        finally:
            if conn:
                self.release_connection(conn)
    
    def get_all_symboles(self):
        """
        Récupère la liste de tous les symboles uniques
        
        Returns:
            list: Liste des symboles
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT DISTINCT symbole
                FROM cours
                ORDER BY symbole
            ''')
            
            results = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return results
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors de la récupération: {e}")
            return []
        finally:
            if conn:
                self.release_connection(conn)
    
    def get_statistics(self):
        """
        Récupère des statistiques sur la base de données
        
        Returns:
            dict: Dictionnaire contenant les statistiques
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Nombre total d'enregistrements
            cursor.execute('SELECT COUNT(*) FROM cours')
            total_records = cursor.fetchone()[0]
            
            # Nombre de symboles uniques
            cursor.execute('SELECT COUNT(DISTINCT symbole) FROM cours')
            unique_symboles = cursor.fetchone()[0]
            
            # Date du premier et dernier enregistrement
            cursor.execute('SELECT MIN(date_heure), MAX(date_heure) FROM cours')
            first_date, last_date = cursor.fetchone()
            
            cursor.close()
            
            stats = {
                'total_records': total_records,
                'unique_symboles': unique_symboles,
                'first_date': first_date,
                'last_date': last_date
            }
            
            return stats
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors de la récupération des statistiques: {e}")
            return {}
        finally:
            if conn:
                self.release_connection(conn)
    
    def get_latest_cours(self):
        """
        Récupère les derniers cours pour chaque action en utilisant DISTINCT ON
        
        Returns:
            list: Liste de dictionnaires contenant les derniers cours
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute('''
                SELECT DISTINCT ON (symbole) 
                    symbole, nom, prix, variation, volume, plus_haut, plus_bas, date_heure
                FROM cours
                ORDER BY symbole, date_heure DESC
            ''')
            
            results = [dict(row) for row in cursor.fetchall()]
            cursor.close()
            return results
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors de la récupération des derniers cours: {e}")
            return []
        finally:
            if conn:
                self.release_connection(conn)
    
    def get_historique_action(self, symbole, limit=30):
        """
        Récupère l'historique d'une action
        
        Args:
            symbole (str): Symbole de l'action
            limit (int): Nombre maximum d'enregistrements à récupérer
            
        Returns:
            list: Liste de dictionnaires contenant l'historique
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute('''
                SELECT symbole, nom, prix, variation, volume, plus_haut, plus_bas, date_heure
                FROM cours
                WHERE symbole = %s
                ORDER BY date_heure DESC
                LIMIT %s
            ''', (symbole, limit))
            
            results = [dict(row) for row in cursor.fetchall()]
            cursor.close()
            return results
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors de la récupération de l'historique: {e}")
            return []
        finally:
            if conn:
                self.release_connection(conn)
    
    def close(self):
        """Ferme toutes les connexions du pool"""
        if self.pool:
            self.pool.closeall()
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Pool de connexions fermé")


# Fonctions utilitaires pour les autres modules
def get_connection():
    """Fonction utilitaire pour obtenir une connexion du pool global"""
    if not hasattr(get_connection, 'pool'):
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL n'est pas définie")
        get_connection.pool = ThreadedConnectionPool(minconn=1, maxconn=10, dsn=database_url)
    return get_connection.pool.getconn()


def release_connection(conn):
    """Fonction utilitaire pour libérer une connexion vers le pool global"""
    if hasattr(get_connection, 'pool'):
        get_connection.pool.putconn(conn)


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
