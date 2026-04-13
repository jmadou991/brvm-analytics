# BRVM Scraper - Scraping en temps réel de la BRVM

Ce projet permet de scraper automatiquement les données de la **Bourse Régionale des Valeurs Mobilières (BRVM)** depuis le site [brvm.org](https://www.brvm.org/fr/cours-des-actions/0/tableau).

## 📋 Fonctionnalités

- ✅ Scraping automatique toutes les 15 minutes
- ✅ Extraction des données : symbole, nom, prix, variation, volume, plus haut, plus bas
- ✅ Stockage dans une base de données SQLite (brvm.db)
- ✅ Logs horodatés pour chaque scraping
- ✅ Gestion des erreurs de connexion
- ✅ Démarrage immédiat au lancement

## 📁 Structure du projet

```
brvm-scraper/
│
├── scraper.py          # Module de scraping (BeautifulSoup + Requests)
├── database.py         # Gestion de la base de données SQLite
├── scheduler.py        # Planification automatique (APScheduler)
├── requirements.txt    # Dépendances Python
├── brvm.db            # Base de données SQLite (créée automatiquement)
└── README.md          # Documentation
```

## 🚀 Installation

1. **Installer les dépendances** :
```bash
pip install -r requirements.txt
```

## 📊 Utilisation

### Lancer le scraper automatique (toutes les 15 minutes)

```bash
python scheduler.py
```

Le scheduler va :
- Lancer un scraping immédiatement
- Programmer des scrapings toutes les 15 minutes
- Afficher des logs détaillés avec horodatage
- Tourner en boucle infinie (Ctrl+C pour arrêter)

### Tester le scraper manuellement

```bash
python scraper.py
```

### Tester la base de données

```bash
python database.py
```

## 🗄️ Structure de la base de données

**Table `cours`** :
- `id` : Identifiant unique (auto-incrémenté)
- `symbole` : Symbole de l'action (ex: BOAC, SGBC)
- `nom` : Nom complet de l'action
- `prix` : Prix actuel
- `variation` : Variation en pourcentage
- `volume` : Volume échangé
- `plus_haut` : Plus haut du jour
- `plus_bas` : Plus bas du jour
- `date_heure` : Date et heure du scraping

## 📦 Dépendances

- `requests` : Requêtes HTTP
- `beautifulsoup4` : Parsing HTML
- `apscheduler` : Planification des tâches
- `pandas` : Manipulation de données (optionnel)
- `python-dotenv` : Variables d'environnement (optionnel)

## 🛠️ Fonctionnalités avancées

### Récupérer les données depuis la base de données

```python
from database import BRVMDatabase

db = BRVMDatabase()

# Statistiques
stats = db.get_statistics()
print(f"Total d'enregistrements: {stats['total_records']}")

# Dernières données
latest = db.get_latest_data(10)

# Données par symbole
data = db.get_data_by_symbole('BOAC', limit=20)

db.close()
```

## ⚠️ Notes importantes

- Le scraper respecte le site web et utilise un User-Agent approprié
- Les erreurs de connexion sont gérées avec des try/except
- La base de données SQLite est créée automatiquement au premier lancement
- Les logs affichent l'heure exacte de chaque opération

## 🔧 Personnalisation

Pour modifier la fréquence de scraping, éditez `scheduler.py` :

```python
# Changer 'minutes=15' par la valeur souhaitée
self.scheduler.add_job(
    self.scrape_and_save,
    'interval',
    minutes=15,  # ← Modifier ici
    ...
)
```

## 📝 Licence

Ce projet est à usage éducatif et de recherche. Respectez les conditions d'utilisation du site BRVM.

## 👨‍💻 Auteur

Projet créé pour le scraping automatique de la BRVM.
