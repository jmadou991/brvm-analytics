# 🚀 Guide de Déploiement BRVM Analytics sur Railway.app

Ce guide vous explique comment déployer votre application BRVM Analytics sur Railway.app (plateforme gratuite).

## 📋 Prérequis

- Un compte GitHub
- Un compte Railway.app (gratuit)
- Votre code BRVM Analytics sur GitHub

---

## 🔧 Étape 1: Préparer votre projet

### 1.1 Créer un fichier `Procfile`

Créez un fichier `Procfile` à la racine du projet (sans extension) :

```
web: uvicorn api:app --host 0.0.0.0 --port $PORT
```

### 1.2 Vérifier `requirements.txt`

Assurez-vous que tous les packages sont listés :

```txt
fastapi
uvicorn[standard]
selenium
webdriver-manager
anthropic
python-dotenv
apscheduler
```

### 1.3 Créer `.gitignore`

```
__pycache__/
*.pyc
*.pyo
*.db
.env
brvm.db
chromedriver
```

---

## 🌐 Étape 2: Pousser sur GitHub

```bash
# Initialiser git (si pas déjà fait)
git init

# Ajouter tous les fichiers
git add .

# Commit
git commit -m "Initial commit - BRVM Analytics"

# Créer un repo sur GitHub puis :
git remote add origin https://github.com/VOTRE_USERNAME/brvm-scraper.git
git branch -M main
git push -u origin main
```

---

## 🚂 Étape 3: Déployer sur Railway

### 3.1 Créer un nouveau projet

1. Allez sur [railway.app](https://railway.app)
2. Cliquez sur **"New Project"**
3. Sélectionnez **"Deploy from GitHub repo"**
4. Autorisez Railway à accéder à votre GitHub
5. Sélectionnez votre repository `brvm-scraper`

### 3.2 Configurer les variables d'environnement

Dans le dashboard Railway, allez dans **Variables** et ajoutez :

```env
# API Claude (OBLIGATOIRE)
ANTHROPIC_API_KEY=votre_clé_api_claude

# Configuration Email (OPTIONNEL - pour les alertes)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=votre_email@gmail.com
SMTP_PASSWORD=votre_mot_de_passe_app
FROM_EMAIL=votre_email@gmail.com

# Configuration Serveur (Railway gère automatiquement PORT)
HOST=0.0.0.0
```

### 3.3 Configurer le Build

Railway détecte automatiquement Python et installe les dépendances depuis `requirements.txt`.

Si besoin, vous pouvez personnaliser dans **Settings** :
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn api:app --host 0.0.0.0 --port $PORT`

---

## ⚙️ Étape 4: Configuration Selenium pour Railway

Railway ne supporte pas Chrome/Selenium par défaut. Vous avez 2 options :

### Option A: Utiliser une API de scraping externe (Recommandé)

Remplacez Selenium par une API comme ScraperAPI ou Bright Data pour le scraping.

### Option B: Utiliser un service Selenium externe

Utilisez un service comme:
- **Selenium Grid** hébergé séparément
- **BrowserStack** ou **Sauce Labs**

### Option C: Modifier pour utiliser requests + BeautifulSoup

Si le site BRVM n'a pas de JavaScript complexe, remplacez Selenium par `requests` + `BeautifulSoup4`.

---

## 🔒 Étape 5: Configurer la base de données

Railway offre PostgreSQL gratuit. Pour migrer de SQLite à PostgreSQL :

### 5.1 Ajouter PostgreSQL

1. Dans votre projet Railway, cliquez sur **"New"**
2. Sélectionnez **"Database" → "PostgreSQL"**
3. Railway créera automatiquement la variable `DATABASE_URL`

### 5.2 Modifier `database.py`

Remplacez SQLite par PostgreSQL :

```python
import psycopg2
from psycopg2.extras import RealDictCursor
import os

DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn
```

### 5.3 Mettre à jour `requirements.txt`

```txt
psycopg2-binary
```

---

## 🌍 Étape 6: Accéder à votre application

1. Railway génère automatiquement une URL : `https://votre-app.up.railway.app`
2. Trouvez-la dans **Settings → Domains**
3. Vous pouvez aussi ajouter un domaine personnalisé

---

## 📊 Étape 7: Monitoring et Logs

### Voir les logs

Dans Railway, allez dans **Deployments** → Cliquez sur le déploiement actif → **View Logs**

### Métriques

Railway affiche automatiquement :
- CPU usage
- Memory usage
- Network traffic

---

## 🔄 Étape 8: Mises à jour automatiques

Railway redéploie automatiquement à chaque push sur GitHub :

```bash
# Faire des modifications
git add .
git commit -m "Update: nouvelle fonctionnalité"
git push

# Railway redéploie automatiquement !
```

---

## 💰 Limites du plan gratuit Railway

- **500 heures/mois** d'exécution
- **100 GB** de bande passante
- **1 GB** de RAM
- **1 GB** de stockage PostgreSQL

Pour une utilisation 24/7, vous aurez besoin du plan payant ($5/mois).

---

## 🛠️ Dépannage

### Problème: L'application ne démarre pas

**Solution**: Vérifiez les logs dans Railway. Souvent c'est :
- Une variable d'environnement manquante
- Une dépendance manquante dans `requirements.txt`

### Problème: Selenium ne fonctionne pas

**Solution**: Railway ne supporte pas Chrome. Utilisez une des options mentionnées à l'Étape 4.

### Problème: Base de données vide

**Solution**: Assurez-vous que le scraping fonctionne. Vérifiez les logs pour voir si des erreurs se produisent.

### Problème: Dépassement de mémoire

**Solution**: 
- Réduisez la fréquence de scraping
- Optimisez les requêtes à la base de données
- Passez au plan payant pour plus de RAM

---

## 🎯 Alternatives à Railway

Si Railway ne convient pas, essayez :

1. **Render.com** - Similaire à Railway, gratuit
2. **Fly.io** - Gratuit avec limites généreuses
3. **Heroku** - Payant maintenant ($7/mois minimum)
4. **DigitalOcean App Platform** - $5/mois
5. **AWS EC2 Free Tier** - Gratuit 12 mois

---

## 📧 Configuration Email Gmail

Pour les alertes email avec Gmail :

1. Activez la **validation en 2 étapes** sur votre compte Google
2. Générez un **mot de passe d'application** :
   - Allez sur https://myaccount.google.com/security
   - Sélectionnez "Mots de passe des applications"
   - Générez un mot de passe pour "Mail"
3. Utilisez ce mot de passe dans `SMTP_PASSWORD`

---

## ✅ Checklist de déploiement

- [ ] Code poussé sur GitHub
- [ ] Projet créé sur Railway
- [ ] Variables d'environnement configurées
- [ ] `ANTHROPIC_API_KEY` ajoutée
- [ ] PostgreSQL configuré (si nécessaire)
- [ ] Selenium remplacé ou configuré
- [ ] Application accessible via l'URL Railway
- [ ] Scraping automatique fonctionne
- [ ] Alertes email testées (si configurées)

---

## 🎉 Félicitations !

Votre application BRVM Analytics est maintenant en ligne et accessible 24/7 !

**URL de votre dashboard**: `https://votre-app.up.railway.app`

---

## 📚 Ressources utiles

- [Documentation Railway](https://docs.railway.app/)
- [Documentation FastAPI](https://fastapi.tiangolo.com/)
- [Documentation Anthropic Claude](https://docs.anthropic.com/)
- [Guide PostgreSQL](https://www.postgresql.org/docs/)

---

**Besoin d'aide ?** Consultez les logs Railway ou la documentation officielle.
