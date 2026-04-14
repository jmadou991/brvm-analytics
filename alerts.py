"""
Module de gestion des alertes email pour le BRVM Analytics
Envoie des notifications par email quand un prix cible est atteint
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os
from dotenv import load_dotenv
from database import get_connection, release_connection

load_dotenv()


class AlertManager:
    """Gestionnaire d'alertes email pour les actions BRVM"""
    
    def __init__(self):
        """Initialise le gestionnaire d'alertes"""
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_user)
        
        # Créer la table des alertes si elle n'existe pas
        self._create_alerts_table()
    
    def _create_alerts_table(self):
        """Crée la table des alertes dans la base de données"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alertes (
                    id SERIAL PRIMARY KEY,
                    symbole TEXT NOT NULL,
                    email TEXT NOT NULL,
                    prix_cible REAL NOT NULL,
                    direction TEXT NOT NULL,
                    active INTEGER DEFAULT 1,
                    date_creation TEXT NOT NULL,
                    date_declenchement TEXT
                )
            ''')
            
            conn.commit()
            cursor.close()
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors de la création de la table alertes: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                release_connection(conn)
    
    def create_alert(self, symbole: str, email: str, prix_cible: float, direction: str):
        """
        Crée une nouvelle alerte
        
        Args:
            symbole: Symbole de l'action
            email: Email de l'utilisateur
            prix_cible: Prix cible pour déclencher l'alerte
            direction: 'hausse' ou 'baisse'
        
        Returns:
            int: ID de l'alerte créée
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO alertes (symbole, email, prix_cible, direction, date_creation)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            ''', (symbole, email, prix_cible, direction, datetime.now().isoformat()))
            
            alert_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Alerte créée: {symbole} @ {prix_cible} FCFA ({direction}) pour {email}")
            
            return alert_id
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors de la création de l'alerte: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                release_connection(conn)
    
    def get_active_alerts(self):
        """
        Récupère toutes les alertes actives
        
        Returns:
            list: Liste des alertes actives
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute('''
                SELECT * FROM alertes WHERE active = 1
            ''')
            
            alerts = [dict(row) for row in cursor.fetchall()]
            cursor.close()
            
            return alerts
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors de la récupération des alertes actives: {e}")
            return []
        finally:
            if conn:
                release_connection(conn)
    
    def get_user_alerts(self, email: str):
        """
        Récupère les alertes d'un utilisateur
        
        Args:
            email: Email de l'utilisateur
        
        Returns:
            list: Liste des alertes de l'utilisateur
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute('''
                SELECT * FROM alertes WHERE email = %s ORDER BY date_creation DESC
            ''', (email,))
            
            alerts = [dict(row) for row in cursor.fetchall()]
            cursor.close()
            
            return alerts
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors de la récupération des alertes utilisateur: {e}")
            return []
        finally:
            if conn:
                release_connection(conn)
    
    def deactivate_alert(self, alert_id: int):
        """
        Désactive une alerte
        
        Args:
            alert_id: ID de l'alerte à désactiver
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE alertes 
                SET active = 0, date_declenchement = %s
                WHERE id = %s
            ''', (datetime.now().isoformat(), alert_id))
            
            conn.commit()
            cursor.close()
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors de la désactivation de l'alerte: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                release_connection(conn)
    
    def delete_alert(self, alert_id: int):
        """
        Supprime une alerte
        
        Args:
            alert_id: ID de l'alerte à supprimer
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM alertes WHERE id = %s', (alert_id,))
            
            conn.commit()
            cursor.close()
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors de la suppression de l'alerte: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                release_connection(conn)
    
    def check_alerts(self, actions_data: list):
        """
        Vérifie si des alertes doivent être déclenchées
        
        Args:
            actions_data: Liste des données d'actions actuelles
        """
        alerts = self.get_active_alerts()
        
        if not alerts:
            return
        
        # Créer un dictionnaire des prix actuels
        prix_actuels = {action['symbole']: action['prix'] for action in actions_data}
        
        for alert in alerts:
            symbole = alert['symbole']
            prix_cible = alert['prix_cible']
            direction = alert['direction']
            email = alert['email']
            
            if symbole not in prix_actuels:
                continue
            
            prix_actuel = prix_actuels[symbole]
            
            # Vérifier si l'alerte doit être déclenchée
            should_trigger = False
            
            if direction == 'hausse' and prix_actuel >= prix_cible:
                should_trigger = True
            elif direction == 'baisse' and prix_actuel <= prix_cible:
                should_trigger = True
            
            if should_trigger:
                # Envoyer l'email
                self.send_alert_email(
                    email=email,
                    symbole=symbole,
                    prix_actuel=prix_actuel,
                    prix_cible=prix_cible,
                    direction=direction
                )
                
                # Désactiver l'alerte
                self.deactivate_alert(alert['id'])
                
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Alerte déclenchée: {symbole} @ {prix_actuel} FCFA pour {email}")
    
    def send_alert_email(self, email: str, symbole: str, prix_actuel: float, prix_cible: float, direction: str):
        """
        Envoie un email d'alerte
        
        Args:
            email: Email du destinataire
            symbole: Symbole de l'action
            prix_actuel: Prix actuel de l'action
            prix_cible: Prix cible défini
            direction: Direction de l'alerte (hausse/baisse)
        """
        if not self.smtp_user or not self.smtp_password:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Configuration SMTP manquante - Email non envoyé")
            return
        
        try:
            # Créer le message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🔔 Alerte BRVM: {symbole} a atteint {prix_actuel} FCFA"
            msg['From'] = self.from_email
            msg['To'] = email
            
            # Texte de l'email
            direction_text = "dépassé" if direction == "hausse" else "descendu sous"
            emoji = "📈" if direction == "hausse" else "📉"
            
            text = f"""
Alerte BRVM Analytics
=====================

{emoji} L'action {symbole} a {direction_text} votre prix cible !

Prix cible: {prix_cible:,.0f} FCFA
Prix actuel: {prix_actuel:,.0f} FCFA
Direction: {direction.upper()}

Consultez votre dashboard pour plus de détails:
https://brvm-analytics-production.up.railway.app

---
BRVM Analytics - Powered by Claude AI
            """
            
            # HTML de l'email
            html = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                        .container {{ background-color: white; padding: 30px; border-radius: 10px; max-width: 600px; margin: 0 auto; }}
                        .header {{ background: linear-gradient(135deg, #00d4ff, #7c3aed); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
                        .content {{ padding: 20px 0; }}
                        .alert-box {{ background-color: {'#d4edda' if direction == 'hausse' else '#f8d7da'}; border: 2px solid {'#28a745' if direction == 'hausse' else '#dc3545'}; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                        .price {{ font-size: 24px; font-weight: bold; color: {'#28a745' if direction == 'hausse' else '#dc3545'}; }}
                        .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; }}
                        .btn {{ display: inline-block; background: linear-gradient(135deg, #00d4ff, #7c3aed); color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>{emoji} Alerte BRVM</h1>
                        </div>
                        <div class="content">
                            <h2>L'action {symbole} a {direction_text} votre prix cible !</h2>
                            
                            <div class="alert-box">
                                <p><strong>Symbole:</strong> {symbole}</p>
                                <p><strong>Prix cible:</strong> {prix_cible:,.0f} FCFA</p>
                                <p><strong>Prix actuel:</strong> <span class="price">{prix_actuel:,.0f} FCFA</span></p>
                                <p><strong>Direction:</strong> {direction.upper()}</p>
                            </div>
                            
                            <p>Consultez votre dashboard pour analyser cette opportunité avec l'IA Claude.</p>
                            
                            <a href="https://brvm-analytics-production.up.railway.app" class="btn">Voir le Dashboard</a>
                        </div>
                        <div class="footer">
                            <p>BRVM Analytics - Powered by Claude AI</p>
                            <p>Cet email a été envoyé automatiquement suite à votre alerte configurée.</p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            # Attacher les parties texte et HTML
            part1 = MIMEText(text, 'plain')
            part2 = MIMEText(html, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Envoyer l'email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Email d'alerte envoyé à {email}")
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors de l'envoi de l'email: {e}")


if __name__ == "__main__":
    # Test du système d'alertes
    manager = AlertManager()
    
    # Créer une alerte de test
    alert_id = manager.create_alert(
        symbole="BOAC",
        email="test@example.com",
        prix_cible=8500.0,
        direction="hausse"
    )
    
    print(f"Alerte créée avec l'ID: {alert_id}")
    
    # Afficher les alertes actives
    alerts = manager.get_active_alerts()
    print(f"\nAlertes actives: {len(alerts)}")
    for alert in alerts:
        print(f"  - {alert['symbole']} @ {alert['prix_cible']} FCFA ({alert['direction']}) pour {alert['email']}")
