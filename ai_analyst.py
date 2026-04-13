"""
Module d'analyse IA utilisant Claude d'Anthropic pour analyser les données BRVM
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv
import json
from datetime import datetime

# Charger les variables d'environnement
load_dotenv()


class ClaudeAnalyst:
    """Classe pour analyser les données BRVM avec Claude AI"""
    
    def __init__(self):
        """Initialise le client Anthropic"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY non trouvée dans le fichier .env")
        
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Claude Analyst initialisé avec le modèle {self.model}")
    
    def analyse_action(self, donnees_action):
        """
        Analyse une action spécifique avec Claude
        
        Args:
            donnees_action (dict): Données de l'action incluant prix, variation, historique
            
        Returns:
            dict: Analyse structurée avec recommandation, risque, explication
        """
        try:
            # Préparer le prompt pour Claude
            prompt = f"""Tu es un analyste financier expert spécialisé dans les marchés boursiers africains, notamment la BRVM (Bourse Régionale des Valeurs Mobilières).

Analyse l'action suivante et fournis une recommandation d'investissement détaillée:

**Données de l'action:**
- Symbole: {donnees_action.get('symbole', 'N/A')}
- Nom: {donnees_action.get('nom', 'N/A')}
- Prix actuel: {donnees_action.get('prix', 0)} FCFA
- Variation: {donnees_action.get('variation', 0)}%
- Volume: {donnees_action.get('volume', 0)}
- Plus haut: {donnees_action.get('plus_haut', 0)} FCFA
- Plus bas: {donnees_action.get('plus_bas', 0)} FCFA

**Historique récent:**
{self._format_historique(donnees_action.get('historique', []))}

Fournis ton analyse au format JSON avec cette structure exacte:
{{
    "recommandation": "ACHETER" ou "VENDRE" ou "NEUTRE",
    "niveau_risque": "FAIBLE" ou "MOYEN" ou "ÉLEVÉ",
    "score_confiance": <nombre entre 0 et 100>,
    "prix_cible": <prix cible estimé en FCFA>,
    "explication": "<explication détaillée de 2-3 phrases>",
    "points_forts": ["point 1", "point 2", "point 3"],
    "points_faibles": ["point 1", "point 2"],
    "horizon_investissement": "COURT_TERME" ou "MOYEN_TERME" ou "LONG_TERME"
}}

Réponds UNIQUEMENT avec le JSON, sans texte supplémentaire."""

            # Appeler Claude
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extraire la réponse
            response_text = message.content[0].text
            
            # Parser le JSON
            try:
                analyse = json.loads(response_text)
            except json.JSONDecodeError:
                # Si la réponse n'est pas du JSON pur, essayer d'extraire le JSON
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    analyse = json.loads(json_match.group())
                else:
                    raise ValueError("Impossible de parser la réponse JSON")
            
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Analyse générée pour {donnees_action.get('symbole', 'N/A')}")
            return analyse
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors de l'analyse: {e}")
            return {
                "recommandation": "NEUTRE",
                "niveau_risque": "MOYEN",
                "score_confiance": 0,
                "prix_cible": donnees_action.get('prix', 0),
                "explication": f"Erreur lors de l'analyse: {str(e)}",
                "points_forts": [],
                "points_faibles": [],
                "horizon_investissement": "MOYEN_TERME"
            }
    
    def analyse_marche(self, toutes_les_actions):
        """
        Analyse globale du marché BRVM
        
        Args:
            toutes_les_actions (list): Liste de toutes les actions avec leurs données
            
        Returns:
            dict: Analyse globale du marché
        """
        try:
            # Calculer des statistiques de marché
            total_actions = len(toutes_les_actions)
            actions_hausse = sum(1 for a in toutes_les_actions if a.get('variation', 0) > 0)
            actions_baisse = sum(1 for a in toutes_les_actions if a.get('variation', 0) < 0)
            variation_moyenne = sum(a.get('variation', 0) for a in toutes_les_actions) / total_actions if total_actions > 0 else 0
            
            # Top 5 hausses et baisses
            top_hausses = sorted(toutes_les_actions, key=lambda x: x.get('variation', 0), reverse=True)[:5]
            top_baisses = sorted(toutes_les_actions, key=lambda x: x.get('variation', 0))[:5]
            
            # Préparer le prompt
            prompt = f"""Tu es un analyste financier expert spécialisé dans les marchés boursiers africains, notamment la BRVM.

Analyse l'état global du marché BRVM avec les données suivantes:

**Statistiques du marché:**
- Nombre total d'actions: {total_actions}
- Actions en hausse: {actions_hausse}
- Actions en baisse: {actions_baisse}
- Variation moyenne: {variation_moyenne:.2f}%

**Top 5 hausses:**
{self._format_top_actions(top_hausses)}

**Top 5 baisses:**
{self._format_top_actions(top_baisses)}

Fournis ton analyse au format JSON avec cette structure exacte:
{{
    "tendance_generale": "HAUSSIERE" ou "BAISSIERE" ou "NEUTRE",
    "sentiment_marche": "OPTIMISTE" ou "PESSIMISTE" ou "PRUDENT",
    "score_sante": <nombre entre 0 et 100>,
    "resume": "<résumé de 2-3 phrases sur l'état du marché>",
    "opportunites": ["opportunité 1", "opportunité 2", "opportunité 3"],
    "risques": ["risque 1", "risque 2"],
    "secteurs_performants": ["secteur 1", "secteur 2"],
    "recommandation_generale": "<recommandation générale pour les investisseurs>"
}}

Réponds UNIQUEMENT avec le JSON, sans texte supplémentaire."""

            # Appeler Claude
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extraire et parser la réponse
            response_text = message.content[0].text
            
            try:
                analyse = json.loads(response_text)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    analyse = json.loads(json_match.group())
                else:
                    raise ValueError("Impossible de parser la réponse JSON")
            
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Analyse de marché générée")
            return analyse
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erreur lors de l'analyse du marché: {e}")
            return {
                "tendance_generale": "NEUTRE",
                "sentiment_marche": "PRUDENT",
                "score_sante": 50,
                "resume": f"Erreur lors de l'analyse: {str(e)}",
                "opportunites": [],
                "risques": [],
                "secteurs_performants": [],
                "recommandation_generale": "Analyse indisponible"
            }
    
    def _format_historique(self, historique):
        """Formate l'historique pour le prompt"""
        if not historique:
            return "Aucun historique disponible"
        
        formatted = []
        for h in historique[:10]:  # Limiter aux 10 derniers
            formatted.append(f"- {h.get('date_heure', 'N/A')}: Prix {h.get('prix', 0)} FCFA, Variation {h.get('variation', 0)}%")
        
        return "\n".join(formatted)
    
    def _format_top_actions(self, actions):
        """Formate la liste des top actions"""
        formatted = []
        for a in actions:
            formatted.append(f"- {a.get('symbole', 'N/A')} ({a.get('nom', 'N/A')}): {a.get('variation', 0):+.2f}%")
        
        return "\n".join(formatted)


if __name__ == "__main__":
    # Test du module
    analyst = ClaudeAnalyst()
    
    # Test avec une action fictive
    test_action = {
        'symbole': 'BOAC',
        'nom': 'BANK OF AFRICA COTE D\'IVOIRE',
        'prix': 5500,
        'variation': 2.5,
        'volume': 1500,
        'plus_haut': 5600,
        'plus_bas': 5400,
        'historique': [
            {'date_heure': '2026-04-12', 'prix': 5370, 'variation': -1.2},
            {'date_heure': '2026-04-11', 'prix': 5435, 'variation': 0.8},
        ]
    }
    
    print("\n" + "="*80)
    print("Test d'analyse d'une action:")
    print("="*80)
    analyse = analyst.analyse_action(test_action)
    print(json.dumps(analyse, indent=2, ensure_ascii=False))
