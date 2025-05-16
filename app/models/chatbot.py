import json
from sentence_transformers import SentenceTransformer
import requests
import time
from app.database.db import search_similar_chunks, get_db, get_full_document
import re
from langdetect import detect  

def is_english(text):
    try:
        return detect(text) == 'en'
    except:
        return False
class Chatbot:
    from langdetect import detect



    def __init__(self):
        # Modèle d'embedding pour les requêtes
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Configuration Ollama
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = "mistral"  # Le modèle Mistral installé localement via Ollama
        
        # Vérifier si Ollama est disponible
        self.ollama_available = self._check_ollama_available()
        if not self.ollama_available:
            print("⚠️ ATTENTION: Ollama n'est pas disponible. Vérifiez que le service est démarré sur http://localhost:11434")
        else:
            print("✅ Ollama est disponible et prêt à être utilisé.")
        
        # Historique des conversations par défaut
        self.default_history = [
            {"role": "system", "content": "Tu es un assistant technique spécialisé qui répond aux questions basées sur des documents techniques."},
        ]
    
    def _check_ollama_available(self):
        """Vérifie si le service Ollama est disponible"""
        try:
            response = requests.get("http://localhost:11434/api/version", timeout=2)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_response(self, user_message, document_id=None):
        """Génère une réponse basée sur la requête de l'utilisateur et le document entier"""
        if not document_id:
            return "Veuillez sélectionner un document pour poser une question."
        
        # Récupérer le document complet
        document = get_full_document(document_id)
        
        if not document:
            return "Document introuvable. Veuillez sélectionner un document valide."
        
        document_content = document['content_text']
        document_title = document['title']
        
        # Forcer l'utilisation de la recherche sémantique pour tous les documents
        # afin d'éviter les problèmes de timeout avec les documents complets
        print(f"Document: {document_title} ({len(document_content)} caractères)")
        return self._get_response_with_semantic_search(user_message, document_id)
        
        # Le code ci-dessous est commenté car nous utilisons toujours la recherche sémantique
        # pour une meilleure performance
        """
        # Si le contenu est trop long, nous utiliserons quand même la recherche sémantique
        if len(document_content) > 10000:
            print(f"Document très long ({len(document_content)} caractères), utilisation de la recherche sémantique...")
            return self._get_response_with_semantic_search(user_message, document_id)
        
        # Si Ollama n'est pas disponible, retourner un message d'erreur explicite
        if not self.ollama_available and not self._check_ollama_available():
            error_msg = "Erreur: Ollama n'est pas disponible. Veuillez vérifier que le service Ollama est démarré et accessible sur http://localhost:11434."
            self._save_conversation(user_message, error_msg, document_id)
            return error_msg
        
        # Vérifier à nouveau si Ollama est disponible (peut-être qu'il a été démarré entre-temps)
        self.ollama_available = True
        
        # Construire un prompt amélioré pour le modèle avec le document entier
        prompt = f\"""Tu es un assistant technique précis et concis spécialisé dans l'analyse de documents.

Voici l'intégralité du document technique "{document_title}":

{document_content}

Question: {user_message}

Instructions:
1. Réponds de manière précise et directe en te basant UNIQUEMENT sur les informations fournies dans le document.
2. Si le document ne contient pas l'information demandée, indique-le clairement.
3. Organise ta réponse de façon structurée et facile à comprendre.
4. Cite des passages pertinents du document pour appuyer ta réponse quand c'est possible.
5. Évite toute spéculation ou information non présente dans le document.

Réponse:\"""
        
        # Appel à l'API Ollama locale avec des paramètres améliorés
        try:
            print(f"Envoi de la requête à Ollama ({self.model_name}) avec document complet...")
            start_time = time.time()
            
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.5,  # Température plus basse pour des réponses plus cohérentes
                        "top_p": 0.85,
                        "top_k": 40,  # Contrôle supplémentaire sur la diversité des tokens
                        "num_predict": 300,  # Augmenter pour des réponses plus complètes
                        "stop": ["Question:", "Instructions:"]  # Arrêter la génération si ces tokens apparaissent
                    }
                },
                timeout=60  # Timeout plus long pour les documents complets
            )
            
            elapsed_time = time.time() - start_time
            print(f"Réponse reçue en {elapsed_time:.2f} secondes")
            
            response.raise_for_status()
            response_data = response.json()
            generated_text = response_data.get("response", "")
            
            # Nettoyer la réponse
            if "Réponse:" in generated_text:
                generated_text = generated_text.split("Réponse:")[1].strip()
            
            # Post-traitement pour améliorer la présentation
            generated_text = self._format_response(generated_text)
            
            self._save_conversation(user_message, generated_text, document_id)
            return generated_text
            
        except requests.exceptions.ConnectionError:
            self.ollama_available = False
            error_msg = "Erreur de connexion: Impossible de se connecter à Ollama. Vérifiez que le service est démarré."
            self._save_conversation(user_message, error_msg, document_id)
            return error_msg
        except requests.exceptions.Timeout:
            error_msg = "Délai d'attente dépassé: La génération de la réponse prend trop de temps. Le document est peut-être trop volumineux, essayez de redémarrer Ollama."
            self._save_conversation(user_message, error_msg, document_id)
            return error_msg
        except Exception as e:
            print(f"Erreur lors de l'appel à Ollama: {str(e)}")
            error_msg = f"Désolé, une erreur s'est produite lors de la génération de la réponse: {str(e)}"
            self._save_conversation(user_message, error_msg, document_id)
            return error_msg
        """
    
    def _get_response_with_semantic_search(self, user_message, document_id):
        """Méthode optimisée utilisant la recherche sémantique avancée pour les documents"""
        # Générer l'embedding de la requête
        query_embedding = self.embedding_model.encode(user_message, convert_to_tensor=True)
        
        # Rechercher les chunks pertinents - augmenté pour une analyse plus exhaustive
        relevant_chunks = search_similar_chunks(json.dumps(query_embedding.tolist()), limit=30)  # Augmenté de 12 à 30
        
        # Filtrer par document_id
        relevant_chunks = [chunk for chunk in relevant_chunks if chunk['document_id'] == document_id]
        
        # Obtenir le document complet pour le contexte
        document = get_full_document(document_id)
        document_title = document['title'] if document else "Document"
        
        # Trier les chunks par indice pour maintenir l'ordre du document original
        try:
            relevant_chunks.sort(key=lambda x: int(x.get('chunk_index', 0)))
        except:
            # Si les indices ne sont pas disponibles ou pas numériques, ne rien faire
            pass
        
        # Construire le contexte pour le modèle de manière optimisée
        context_parts = []
        
        # Ajouter des méta-informations sur le document
        context_parts.append(f"DOCUMENT: {document_title}")
        
        # Identifier et regrouper les sections contiguës pour maintenir le contexte
        current_section = []
        current_index = -10  # Valeur initiale qui ne correspondra à aucun index

        for chunk in relevant_chunks:
            chunk_index = int(chunk.get('chunk_index', 0))
            
            # Si c'est un nouveau groupe (non contigu avec le précédent)
            if chunk_index > current_index + 1 and current_section:
                # Ajouter la section précédente au contexte
                section_text = "\n".join([c['content'].strip() for c in current_section])
                if section_text.strip():
                    context_parts.append(f"SECTION {current_section[0].get('chunk_index', '?')}-{current_section[-1].get('chunk_index', '?')}:\n{section_text}")
                # Démarrer une nouvelle section
                current_section = [chunk]
            else:
                # Continuer la section actuelle
                current_section.append(chunk)
            
            current_index = chunk_index
        
        # Ajouter la dernière section
        if current_section:
            section_text = "\n".join([c['content'].strip() for c in current_section])
            if section_text.strip():
                context_parts.append(f"SECTION {current_section[0].get('chunk_index', '?')}-{current_section[-1].get('chunk_index', '?')}:\n{section_text}")
        
        # Si aucune section n'a été ajoutée, utiliser les chunks individuels
        if len(context_parts) <= 1:  # Seulement le titre du document
            for idx, chunk in enumerate(relevant_chunks, 1):
                context_parts.append(f"EXTRAIT {idx}:\n{chunk['content'].strip()}")
        
        # Joindre les parties du contexte
        context = "\n\n".join(context_parts)
        
        # Limiter la taille du contexte - augmenté pour une analyse plus complète
        max_context_size = 12000  # Augmenté de 6000 à 12000 pour une analyse plus exhaustive
        if len(context) > max_context_size:
            # Préserver les premières lignes qui contiennent le titre du document
            title_section = context_parts[0] + "\n\n"
            remaining_budget = max_context_size - len(title_section)
            
            # Essayer de conserver des sections complètes jusqu'à la limite
            sections_to_include = []
            current_length = 0
            
            for part in context_parts[1:]:  # Skip the title
                if current_length + len(part) <= remaining_budget:
                    sections_to_include.append(part)
                    current_length += len(part) + 2  # +2 pour le séparateur "\n\n"
                else:
                    # Si on ne peut pas ajouter la section entière et qu'on n'a encore rien ajouté,
                    # on prend autant de la première section que possible
                    if not sections_to_include and part:
                        truncated_part = part[:remaining_budget]
                        sections_to_include.append(truncated_part + "...")
                    break
            
            if sections_to_include:
                context = title_section + "\n\n".join(sections_to_include)
            else:
                # Fallback: prendre autant du contexte que possible
                context = context[:max_context_size] + "..."
        
        # Si Ollama n'est pas disponible, retourner un message d'erreur explicite
        if not self.ollama_available and not self._check_ollama_available():
            error_msg = "Erreur: Ollama n'est pas disponible. Veuillez vérifier que le service Ollama est démarré et accessible sur http://localhost:11434."
            self._save_conversation(user_message, error_msg, document_id)
            return error_msg
        
        # Vérifier à nouveau si Ollama est disponible (peut-être qu'il a été démarré entre-temps)
        self.ollama_available = True
        
        # Construire un prompt antihallucinatoire strict pour le modèle
                # Construire le prompt dynamiquement en fonction de la langue détectée
        if is_english(user_message):
            prompt = f"""You are a highly specialized technical assistant who analyzes industrial documents and helps answer engineering questions.

I have extracted the 30 most relevant sections from the document "{document_title}" to answer this question.

Instructions:
1. Use only the content from the excerpts provided below.
2. If the answer is only partially available, say so clearly and helpfully.
3. Do not invent any information that is not present.
4. Cite sections (e.g., "SECTION 3-4") for every piece of information.
5. If the document lacks relevant info, suggest related data instead.

Excerpts:
{context}

Question: {user_message}

Answer:"""
        else:
            prompt = f"""Tu es un assistant d'analyse de documents techniques hautement spécialisé qui aide à interpréter les informations disponibles.

J'ai analysé le document "{document_title}" et extrait les 30 sections les plus pertinentes pour répondre à cette question.

Instructions :
1. Utilise uniquement les informations présentes dans les extraits ci-dessous.
2. Si les extraits contiennent des informations partiellement pertinentes, indique-le clairement.
3. N'invente aucune information absente.
4. Cite les sections (ex : "SECTION 3-4") pour chaque élément.
5. Si rien n'est pertinent, indique-le de manière constructive.

Extraits :
{context}

Question : {user_message}

Réponse :"""


        
        # Paramètres du modèle ajustés pour minimiser les hallucinations
        try:
            print(f"Envoi de la requête à Ollama ({self.model_name}) avec analyse exhaustive du document...")
            start_time = time.time()
            
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,        # Température très basse pour limiter la créativité
                        "top_p": 0.50,             # Très restrictif pour limiter les variations
                        "top_k": 20,               # Restreint davantage les choix de tokens possibles
                        "num_predict": 500,        # Augmenté de 300 à 500 pour des réponses plus complètes
                        "stop": ["Question:", "Instructions:"]
                    }
                },
                timeout=300  # Augmenté de 120 à 300 secondes (5 minutes) pour l'analyse exhaustive
            )
            
            elapsed_time = time.time() - start_time
            print(f"Réponse reçue en {elapsed_time:.2f} secondes")
            
            response.raise_for_status()
            response_data = response.json()
            generated_text = response_data.get("response", "")
            
            # Nettoyer la réponse
            if "Réponse:" in generated_text:
                generated_text = generated_text.split("Réponse:")[1].strip()
            
            # Vérification finale pour les hallucinations - si la réponse est trop longue par rapport au contexte
            if len(generated_text) > len(context) * 0.7 and len(context) > 1000:
                # La réponse est suspicieusement longue par rapport au contexte
                warning_prefix = "ATTENTION: La réponse générée semble contenir des informations au-delà du document. Voici seulement les faits vérifiés:\n\n"
                # Réduire la réponse et ajouter un avertissement
                generated_text = warning_prefix + self._truncate_response(generated_text)
            
            # Post-traitement avancé pour améliorer la présentation
            generated_text = self._enhanced_response_format(generated_text)
            
            self._save_conversation(user_message, generated_text, document_id)
            return generated_text
            
        except requests.exceptions.Timeout:
            # Cas spécifique: timeout de la requête
            error_msg = "Délai d'attente dépassé: La génération de la réponse prend trop de temps. Essayez de poser une question plus spécifique, de redémarrer Ollama ou d'utiliser un modèle plus rapide."
            self._save_conversation(user_message, error_msg, document_id)
            return error_msg
        except Exception as e:
            print(f"Erreur lors de l'appel à Ollama avec analyse avancée: {str(e)}")
            error_msg = f"Désolé, une erreur s'est produite lors de la génération de la réponse: {str(e)}"
            self._save_conversation(user_message, error_msg, document_id)
            return error_msg
    
    def _truncate_response(self, text):
        """Tronque et filtre la réponse pour éliminer les potentielles hallucinations"""
        # Diviser en paragraphes
        paragraphs = text.split('\n\n')
        
        # Ne garder que les paragraphes qui contiennent des références aux sections
        verified_paragraphs = []
        for para in paragraphs:
            # Si le paragraphe mentionne une section ou un extrait, il est probablement fiable
            if re.search(r'(SECTION|EXTRAIT|section|extrait)\s+\d+', para):
                verified_paragraphs.append(para)
            # Si c'est le premier paragraphe et qu'il ne contient pas de référence
            elif len(verified_paragraphs) == 0 and len(para) < 150:
                verified_paragraphs.append(para)
        
        # S'il n'y a pas de paragraphes vérifiés, renvoyer un message par défaut
        if not verified_paragraphs:
            return "Le document ne semble pas contenir suffisamment d'informations pour répondre à cette question avec certitude."
        
        return '\n\n'.join(verified_paragraphs)
    
    def _enhanced_response_format(self, text):
        """Format amélioré pour les réponses"""
        if not text:
            return ""
            
        # Supprimer les espaces multiples
        text = ' '.join(text.split())
        
        # Améliorer la présentation des paragraphes
        # Préserver les sauts de ligne intentionnels tout en ajoutant des séparations pour les phrases
        paragraphs = []
        for paragraph in text.split('\n'):
            if paragraph.strip():
                # Séparer les phrases longues pour une meilleure lisibilité
                paragraph = paragraph.replace(". ", ".\n").strip()
                # Recombiner les phrases trop courtes (moins de 60 caractères)
                lines = paragraph.split('\n')
                combined_lines = []
                current_line = ""
                
                for line in lines:
                    if len(current_line) + len(line) < 100:
                        current_line = (current_line + " " + line).strip()
                    else:
                        if current_line:
                            combined_lines.append(current_line)
                        current_line = line
                
                if current_line:
                    combined_lines.append(current_line)
                
                # Rejoindre les lignes combinées
                paragraph = '\n'.join(combined_lines)
                paragraphs.append(paragraph)
        
        # Joindre les paragraphes avec des sauts de ligne doubles
        text = '\n\n'.join(paragraphs)
        
        # Mettre en surbrillance les références aux sections
        text = re.sub(r'SECTION (\d+-\d+)', r'SECTION \1', text, flags=re.IGNORECASE)
        text = re.sub(r'EXTRAIT (\d+)', r'EXTRAIT \1', text, flags=re.IGNORECASE)
        
        # Améliorer la mise en forme des listes
        # Détecter les lignes qui commencent par des tirets ou des nombres suivis d'un point
        text = re.sub(r'(?m)^(-|\d+\.) ', r'\n\1 ', text)
        
        return text
    
    def _format_response(self, text):
        """Formate la réponse pour améliorer la présentation"""
        # Supprimer les espaces multiples
        text = ' '.join(text.split())
        
        # Gérer les sauts de ligne
        text = text.replace(". ", ".\n\n").replace("! ", "!\n\n").replace("? ", "?\n\n")
        
        # Recréer des paragraphes propres
        paragraphs = text.split("\n\n")
        clean_paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        # Reconstituer avec au plus deux sauts de ligne
        text = "\n\n".join(clean_paragraphs)
        
        # Supprimer les retours à la ligne excédentaires
        text = text.replace("\n\n\n", "\n\n")
        
        return text
    
    def _save_conversation(self, user_message, bot_response, document_id=None):
        """Sauvegarde la conversation dans la base de données"""
        db = get_db()
        cursor = db.cursor()
        
        # Récupérer ou créer une conversation
        if document_id:
            cursor.execute(
                'SELECT id FROM conversations WHERE document_id = ? ORDER BY timestamp DESC LIMIT 1',
                (document_id,)
            )
        else:
            cursor.execute(
                'SELECT id FROM conversations WHERE document_id IS NULL ORDER BY timestamp DESC LIMIT 1'
            )
        
        result = cursor.fetchone()
        
        if result:
            conversation_id = result['id']
        else:
            # Créer une nouvelle conversation
            cursor.execute(
                'INSERT INTO conversations (document_id) VALUES (?)',
                (document_id,)
            )
            conversation_id = cursor.lastrowid
        
        # Enregistrer le message de l'utilisateur
        cursor.execute(
            'INSERT INTO messages (conversation_id, is_user, content) VALUES (?, ?, ?)',
            (conversation_id, True, user_message)
        )
        
        # Enregistrer la réponse du bot
        cursor.execute(
            'INSERT INTO messages (conversation_id, is_user, content) VALUES (?, ?, ?)',
            (conversation_id, False, bot_response)
        )
        
        db.commit() 
