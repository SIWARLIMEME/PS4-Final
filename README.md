# SmartDoc Analyser

Un chatbot capable d'ingérer des documents techniques (PDF, DOCX, PPTX) et de répondre aux questions de manière précise en utilisant Ollama et Mistral.

## Fonctionnalités
- Interface similaire à ChatGPT améliorée avec formatage avancé des réponses
- Traitement de documents PDF, DOCX et PPTX avec découpage intelligent préservant la structure
- Spécialisé pour les contenus techniques (manuels, guides, etc.)
- Analyse exhaustive avec extraction de jusqu'à 30 sections pertinentes du document
- Réponses structurées avec citations précises des sections et mise en valeur des informations clés
- Utilisation d'Ollama et Mistral en local pour la génération de réponses

## Améliorations majeures
- **Découpage intelligent des documents** : Préservation des titres et des sections logiques pour un meilleur contexte
- **Analyse exhaustive configurable** : Possibilité d'analyser jusqu'à 30 sections du document avec un contexte étendu (12000 caractères)
- **Regroupement des sections contiguës** : Maintien de la cohérence des informations extraites
- **Génération de réponses améliorée** : Citations précises, formatage avancé, et structuration des informations
- **Interface utilisateur optimisée** : Mise en valeur visuelle des citations et des éléments importants

## Prérequis
1. Ollama installé localement - [Installation Ollama](https://ollama.com)
2. **IMPORTANT** : Assurez-vous que le service Ollama est démarré avant de lancer l'application
3. Modèle Mistral téléchargé via Ollama:
```bash
ollama pull mistral
```

## Installation

```bash
# Créer un environnement virtuel
python -m venv venv
venv\Scripts\activate  # Sur Windows

# Installer les dépendances
pip install -r requirements.txt

# S'assurer qu'Ollama fonctionne et que le modèle Mistral est disponible
ollama list

# Lancer l'application (port 8080 par défaut)
python app.py

# Pour changer le port d'écoute (exemple : port 9000)
set PORT=9000  # Windows
# ou
export PORT=9000  # Linux/Mac
python app.py
```

## Utilisation
1. Assurez-vous qu'Ollama est en cours d'exécution en arrière-plan (vérifiez l'icône dans la barre des tâches)
2. Accédez à l'application sur http://localhost:8080 (ou le port que vous avez défini)
3. Téléchargez un document technique
4. Posez des questions sur le document
5. Le système analysera de manière exhaustive les 30 sections les plus pertinentes du document pour répondre précisément à votre question

## Performance et temps d'attente
Cette version utilise une méthode d'analyse exhaustive qui peut nécessiter plus de temps :
- Analyse de jusqu'à 30 sections pertinentes du document (contre 8-12 dans la version standard)
- Contexte étendu jusqu'à 12000 caractères pour des réponses plus complètes
- Temps d'attente configuré jusqu'à 5 minutes pour les documents volumineux
- Optimisation des paramètres du modèle pour un équilibre entre qualité et factualité

## Configuration de l'analyse
Si vous souhaitez ajuster les paramètres d'analyse, vous pouvez modifier les valeurs suivantes dans le fichier `app/models/chatbot.py` :
- `limit=30` : Nombre de sections analysées (ligne 9)
- `max_context_size = 12000` : Taille maximale du contexte en caractères (ligne 79)
- `timeout=300` : Temps d'attente maximal en secondes (ligne 133)

## Dépannage
Si vous rencontrez des problèmes :
1. Vérifiez que le service Ollama est démarré et accessible sur http://localhost:11434
2. Vérifiez que le modèle Mistral est bien installé (`ollama list`)
3. Redémarrez le service Ollama
4. Pour des documents très volumineux, soyez patient - l'analyse peut prendre jusqu'à 5 minutes
5. Si les réponses prennent systématiquement trop de temps, vous pouvez réduire le nombre de sections analysées
6. Assurez-vous que votre ordinateur dispose de suffisamment de RAM (au moins 8 Go recommandés)
7. En cas de timeouts fréquents, essayez de fermer d'autres applications consommant des ressources

## Structure du projet
- `/app` - Code principal de l'application
- `/app/static` - Ressources statiques (CSS, JS)
- `/app/templates` - Templates HTML
- `/app/models` - Modèles et logique métier
- `/app/database` - Gestion de la base de données SQLite
- `/uploads` - Stockage temporaire des documents uploadés 
