"""
Module de scraping de la BRVM (Bourse Régionale des Valeurs Mobilières)
Extrait les données des actions depuis https://www.brvm.org avec Selenium
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time


class BRVMScraper:
    """Classe pour scraper les données de la BRVM avec Selenium"""
    
    def __init__(self):
        self.url = "https://www.brvm.org/fr/cours-actions/0/tableau"
        self.driver = None
    
    def _init_driver(self):
        """Initialise le driver Chrome en mode headless"""
        try:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Initialisation du driver Chrome...")
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Mode sans fenêtre
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Installer et configurer le driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Driver Chrome initialisé avec succès")
            return True
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors de l'initialisation du driver: {e}")
            return False
    
    def scrape(self):
        """
        Scrape les données des actions de la BRVM
        
        Returns:
            list: Liste de dictionnaires contenant les données des actions
        """
        actions = []
        
        try:
            # Initialiser le driver
            if not self._init_driver():
                return []
            
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Accès à {self.url}")
            
            # Charger la page
            self.driver.get(self.url)
            
            # Attendre que le tableau se charge (max 15 secondes)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Attente du chargement du tableau...")
            wait = WebDriverWait(self.driver, 15)
            
            # Essayer différents sélecteurs pour trouver le tableau
            table_found = False
            selectors = [
                "table tbody tr",
                "tr.odd, tr.even",
                "table.table tbody tr",
                ".dataTables_wrapper tbody tr"
            ]
            
            rows = []
            for selector in selectors:
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    rows = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if rows:
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Tableau trouvé avec le sélecteur: {selector}")
                        table_found = True
                        break
                except:
                    continue
            
            if not table_found or not rows:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur: Tableau non trouvé sur la page")
                return []
            
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {len(rows)} lignes trouvées dans le tableau")
            
            # Extraire les données de chaque ligne
            # Le tableau 4 contient les données des actions avec 7 colonnes:
            # 0: Symbole, 1: Nom, 2: Volume, 3: Cours veille, 4: Cours Ouverture, 5: Cours Clôture, 6: Variation (%)
            for row in rows:
                try:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    
                    if len(cols) >= 7:
                        symbole = cols[0].text.strip()
                        nom = cols[1].text.strip() if len(cols) > 1 else symbole
                        volume = self._clean_number(cols[2].text.strip(), is_int=True) if len(cols) > 2 else 0
                        cours_veille = self._clean_number(cols[3].text.strip()) if len(cols) > 3 else 0.0
                        cours_ouverture = self._clean_number(cols[4].text.strip()) if len(cols) > 4 else 0.0
                        prix = self._clean_number(cols[5].text.strip()) if len(cols) > 5 else 0.0  # Cours Clôture = Prix actuel
                        variation = self._clean_number(cols[6].text.strip()) if len(cols) > 6 else 0.0
                        
                        # Calculer plus haut et plus bas à partir des cours disponibles
                        cours_list = [c for c in [cours_veille, cours_ouverture, prix] if c > 0]
                        plus_haut = max(cours_list) if cours_list else prix
                        plus_bas = min(cours_list) if cours_list else prix
                        
                        # Ignorer les lignes vides
                        if symbole and symbole != '-':
                            action = {
                                'symbole': symbole,
                                'nom': nom,
                                'prix': prix,
                                'variation': variation,
                                'volume': volume,
                                'plus_haut': plus_haut,
                                'plus_bas': plus_bas,
                                'date_heure': datetime.now()
                            }
                            
                            actions.append(action)
                            
                except Exception as e:
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors du traitement d'une ligne: {e}")
                    continue
            
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scraping terminé: {len(actions)} actions récupérées")
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors du scraping: {e}")
            
        finally:
            # Fermer le driver
            if self.driver:
                self.driver.quit()
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Driver Chrome fermé")
        
        return actions
    
    def _clean_number(self, text, is_int=False):
        """
        Nettoie et convertit une chaîne en nombre
        
        Args:
            text (str): Texte à convertir
            is_int (bool): Si True, retourne un entier, sinon un float
            
        Returns:
            float ou int: Nombre nettoyé
        """
        try:
            # Supprimer les espaces, symboles de pourcentage et autres caractères
            cleaned = text.replace(' ', '').replace('%', '').replace(',', '.').replace('\xa0', '').replace('\u202f', '')
            
            # Supprimer les caractères non numériques sauf le point et le signe moins
            cleaned = ''.join(c for c in cleaned if c.isdigit() or c in ['.', '-'])
            
            if not cleaned or cleaned == '-':
                return 0 if is_int else 0.0
            
            if is_int:
                return int(float(cleaned))
            else:
                return float(cleaned)
        except (ValueError, AttributeError):
            return 0 if is_int else 0.0


if __name__ == "__main__":
    # Test du scraper
    scraper = BRVMScraper()
    data = scraper.scrape()
    
    if data:
        print(f"\n{'='*80}")
        print(f"Exemple de données récupérées ({len(data)} actions):")
        print(f"{'='*80}")
        for action in data[:5]:  # Afficher les 5 premières
            print(f"\nSymbole: {action['symbole']}")
            print(f"Nom: {action['nom']}")
            print(f"Prix: {action['prix']}")
            print(f"Variation: {action['variation']}%")
            print(f"Volume: {action['volume']}")
            print(f"Plus haut: {action['plus_haut']}")
            print(f"Plus bas: {action['plus_bas']}")
    else:
        print("\nAucune donnée récupérée")
