"""
API FastAPI pour le dashboard BRVM avec intégration Claude AI et scraping automatique
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
from pydantic import BaseModel
import sqlite3
from datetime import datetime
from typing import List, Optional
import os
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager

from ai_analyst import ClaudeAnalyst
from scraper import BRVMScraper
from database import BRVMDatabase
from alerts import AlertManager

# Charger les variables d'environnement
load_dotenv()

# Initialiser le scraper, la base de données et le gestionnaire d'alertes
scraper = BRVMScraper()
db = BRVMDatabase()
alert_manager = AlertManager()
scheduler = BackgroundScheduler()


def scrape_and_save():
    """
    Effectue le scraping et sauvegarde les données dans la base de données
    """
    try:
        print(f"\n{'='*80}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Début du cycle de scraping automatique")
        print(f"{'='*80}")
        
        # Scraper les données
        actions = scraper.scrape()
        
        # Sauvegarder dans la base de données
        if actions:
            count = db.save_data(actions)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✓ Cycle terminé avec succès: {count} actions sauvegardées")
            
            # Vérifier les alertes
            alert_manager.check_alerts(actions)
            
            # Afficher un résumé des données
            print(f"\n{'='*80}")
            print(f"Résumé des données récupérées:")
            print(f"{'='*80}")
            for i, action in enumerate(actions[:5], 1):  # Afficher les 5 premières
                print(f"{i}. {action['symbole']:10s} | Prix: {action['prix']:8.2f} | Var: {action['variation']:+6.2f}% | Vol: {action['volume']:10d}")
            
            if len(actions) > 5:
                print(f"... et {len(actions) - 5} autres actions")
            
        else:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✗ Aucune donnée récupérée lors de ce cycle")
        
        print(f"\n{'='*80}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Prochain scraping dans 15 minutes")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✗ Erreur lors du cycle de scraping: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gère le cycle de vie de l'application FastAPI
    - Startup: Lance le scraping immédiat et programme les scrapings automatiques
    - Shutdown: Arrête le scheduler proprement
    """
    # Startup
    print(f"\n{'='*80}")
    print(f"BRVM Analytics API - Démarrage du système")
    print(f"{'='*80}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Initialisation du scraping automatique...")
    
    # Lancer le premier scraping immédiatement
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Lancement du premier scraping...")
    scrape_and_save()
    
    # Programmer les scrapings toutes les 15 minutes
    scheduler.add_job(
        scrape_and_save,
        'interval',
        minutes=15,
        id='brvm_scraper',
        name='BRVM Scraper Job',
        replace_existing=True
    )
    
    scheduler.start()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✓ Scheduler démarré - Scraping automatique toutes les 15 minutes")
    print(f"{'='*80}\n")
    
    yield
    
    # Shutdown
    print(f"\n{'='*80}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Arrêt du système...")
    scheduler.shutdown()
    db.close()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✓ Scheduler et base de données fermés")
    print(f"{'='*80}\n")


# Initialiser FastAPI avec le gestionnaire de cycle de vie
app = FastAPI(
    title="BRVM Analytics API",
    version="1.0.0",
    lifespan=lifespan
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Monter les fichiers statiques
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates Jinja2
templates = Jinja2Templates(directory="templates")

# Initialiser l'analyste IA
try:
    analyst = ClaudeAnalyst()
except Exception as e:
    print(f"Avertissement: Impossible d'initialiser Claude Analyst: {e}")
    analyst = None


# Modèles Pydantic
class ActionData(BaseModel):
    symbole: str
    nom: str
    prix: float
    variation: float
    volume: int
    plus_haut: float
    plus_bas: float
    date_heure: str


class AnalyseRequest(BaseModel):
    symbole: str
    nom: str
    prix: float
    variation: float
    volume: int
    plus_haut: float
    plus_bas: float


# Fonctions utilitaires
def get_db_connection():
    """Crée une connexion à la base de données SQLite"""
    conn = sqlite3.connect('brvm.db')
    conn.row_factory = sqlite3.Row
    return conn


def get_latest_cours():
    """Récupère les derniers cours pour chaque action"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Récupérer le dernier cours pour chaque symbole
    cursor.execute('''
        SELECT c1.symbole, c1.nom, c1.prix, c1.variation, c1.volume, 
               c1.plus_haut, c1.plus_bas, c1.date_heure
        FROM cours c1
        INNER JOIN (
            SELECT symbole, MAX(date_heure) as max_date
            FROM cours
            GROUP BY symbole
        ) c2 ON c1.symbole = c2.symbole AND c1.date_heure = c2.max_date
        ORDER BY c1.symbole
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_historique_action(symbole: str, limit: int = 30):
    """Récupère l'historique d'une action"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT symbole, nom, prix, variation, volume, plus_haut, plus_bas, date_heure
        FROM cours
        WHERE symbole = ?
        ORDER BY date_heure DESC
        LIMIT ?
    ''', (symbole, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


# Routes API
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Page d'accueil du dashboard"""
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/api/cours", response_model=List[dict])
async def get_cours():
    """
    Retourne tous les derniers cours BRVM depuis SQLite
    """
    try:
        cours = get_latest_cours()
        return cours
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des cours: {str(e)}")


@app.get("/api/cours/{symbole}")
async def get_cours_symbole(symbole: str, limit: int = 30):
    """
    Retourne l'historique d'une action spécifique
    """
    try:
        historique = get_historique_action(symbole, limit)
        
        if not historique:
            raise HTTPException(status_code=404, detail=f"Aucune donnée trouvée pour le symbole {symbole}")
        
        return {
            "symbole": symbole,
            "historique": historique
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération de l'historique: {str(e)}")


@app.post("/api/analyse")
async def analyser_action(data: AnalyseRequest):
    """
    Envoie les données BRVM à Claude API et retourne une analyse d'investissement
    """
    if not analyst:
        raise HTTPException(status_code=503, detail="Service d'analyse IA non disponible. Vérifiez la clé API.")
    
    try:
        # Récupérer l'historique de l'action
        historique = get_historique_action(data.symbole, limit=10)
        
        # Préparer les données pour l'analyse
        donnees_action = {
            'symbole': data.symbole,
            'nom': data.nom,
            'prix': data.prix,
            'variation': data.variation,
            'volume': data.volume,
            'plus_haut': data.plus_haut,
            'plus_bas': data.plus_bas,
            'historique': historique
        }
        
        # Analyser avec Claude
        analyse = analyst.analyse_action(donnees_action)
        
        return {
            "symbole": data.symbole,
            "nom": data.nom,
            "analyse": analyse,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {str(e)}")


@app.get("/api/recommandations")
async def get_recommandations():
    """
    Retourne les recommandations Acheter/Vendre/Neutre pour chaque action
    """
    if not analyst:
        raise HTTPException(status_code=503, detail="Service d'analyse IA non disponible. Vérifiez la clé API.")
    
    try:
        # Récupérer tous les cours
        cours = get_latest_cours()
        
        if not cours:
            return {"recommandations": [], "message": "Aucune donnée disponible"}
        
        recommandations = []
        
        # Analyser chaque action (limiter à 10 pour éviter les coûts API élevés)
        for action in cours[:10]:
            try:
                historique = get_historique_action(action['symbole'], limit=5)
                
                donnees_action = {
                    'symbole': action['symbole'],
                    'nom': action['nom'],
                    'prix': action['prix'],
                    'variation': action['variation'],
                    'volume': action['volume'],
                    'plus_haut': action['plus_haut'],
                    'plus_bas': action['plus_bas'],
                    'historique': historique
                }
                
                analyse = analyst.analyse_action(donnees_action)
                
                recommandations.append({
                    'symbole': action['symbole'],
                    'nom': action['nom'],
                    'prix': action['prix'],
                    'variation': action['variation'],
                    'recommandation': analyse.get('recommandation', 'NEUTRE'),
                    'niveau_risque': analyse.get('niveau_risque', 'MOYEN'),
                    'score_confiance': analyse.get('score_confiance', 0),
                    'explication': analyse.get('explication', '')
                })
                
            except Exception as e:
                print(f"Erreur lors de l'analyse de {action['symbole']}: {e}")
                continue
        
        return {
            "recommandations": recommandations,
            "timestamp": datetime.now().isoformat(),
            "total": len(recommandations)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération des recommandations: {str(e)}")


@app.get("/api/analyse-marche")
async def analyser_marche():
    """
    Retourne une analyse globale du marché BRVM
    """
    if not analyst:
        raise HTTPException(status_code=503, detail="Service d'analyse IA non disponible. Vérifiez la clé API.")
    
    try:
        # Récupérer tous les cours
        cours = get_latest_cours()
        
        if not cours:
            raise HTTPException(status_code=404, detail="Aucune donnée disponible")
        
        # Analyser le marché
        analyse = analyst.analyse_marche(cours)
        
        return {
            "analyse": analyse,
            "nombre_actions": len(cours),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse du marché: {str(e)}")


@app.get("/api/stats")
async def get_statistics():
    """
    Retourne des statistiques sur la base de données
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Nombre total d'enregistrements
        cursor.execute('SELECT COUNT(*) as total FROM cours')
        total_records = cursor.fetchone()['total']
        
        # Nombre de symboles uniques
        cursor.execute('SELECT COUNT(DISTINCT symbole) as total FROM cours')
        unique_symboles = cursor.fetchone()['total']
        
        # Date du premier et dernier enregistrement
        cursor.execute('SELECT MIN(date_heure) as first_date, MAX(date_heure) as last_date FROM cours')
        dates = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_records': total_records,
            'unique_symboles': unique_symboles,
            'first_date': dates['first_date'],
            'last_date': dates['last_date']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des statistiques: {str(e)}")


@app.get("/health")
async def health_check():
    """Vérification de l'état de l'API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ai_service": "available" if analyst else "unavailable"
    }


# Routes pour les alertes
class AlerteRequest(BaseModel):
    symbole: str
    email: str
    prix_cible: float
    direction: str  # 'hausse' ou 'baisse'


@app.post("/api/alertes")
async def creer_alerte(data: AlerteRequest):
    """
    Crée une nouvelle alerte de prix
    """
    try:
        # Valider la direction
        if data.direction not in ['hausse', 'baisse']:
            raise HTTPException(status_code=400, detail="La direction doit être 'hausse' ou 'baisse'")
        
        # Créer l'alerte
        alert_id = alert_manager.create_alert(
            symbole=data.symbole,
            email=data.email,
            prix_cible=data.prix_cible,
            direction=data.direction
        )
        
        return {
            "success": True,
            "alert_id": alert_id,
            "message": f"Alerte créée pour {data.symbole} @ {data.prix_cible} FCFA ({data.direction})"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création de l'alerte: {str(e)}")


@app.get("/api/alertes/{email}")
async def get_alertes_utilisateur(email: str):
    """
    Récupère les alertes d'un utilisateur
    """
    try:
        alertes = alert_manager.get_user_alerts(email)
        return {
            "email": email,
            "alertes": alertes,
            "total": len(alertes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des alertes: {str(e)}")


@app.delete("/api/alertes/{alert_id}")
async def supprimer_alerte(alert_id: int):
    """
    Supprime une alerte
    """
    try:
        alert_manager.delete_alert(alert_id)
        return {
            "success": True,
            "message": f"Alerte {alert_id} supprimée"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression de l'alerte: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))
    
    print(f"\n{'='*80}")
    print(f"Démarrage du serveur BRVM Analytics API")
    print(f"{'='*80}")
    print(f"URL: http://{host}:{port}")
    print(f"Documentation API: http://{host}:{port}/docs")
    print(f"{'='*80}\n")
    
    uvicorn.run(app, host=host, port=port, reload=True)
