document.addEventListener('DOMContentLoaded', function() {
    // Éléments du DOM
    const fileUpload = document.getElementById('file-upload');
    const documentsListEl = document.getElementById('documents-list');
    const conversationsListEl = document.getElementById('conversations-list');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');
    const welcomeScreen = document.getElementById('welcome-screen');
    const currentDocumentEl = document.getElementById('current-document');
    const loadingModal = document.getElementById('loading-modal');
    const loadingMessage = document.getElementById('loading-message');
    const newChatBtn = document.getElementById('new-chat-btn');
    
    // Variables d'état
    let currentDocumentId = null;
    let currentConversationId = null;
    let isProcessing = false;
    
    // Configuration du redimensionnement automatique du textarea
    chatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
    
    // Initialisation: Charger la liste des documents
    loadDocuments();
    
    // Gestionnaires d'événements
    fileUpload.addEventListener('change', handleFileUpload);
    sendBtn.addEventListener('click', sendMessage);
    newChatBtn.addEventListener('click', startNewChat);
    
    // Permettre l'envoi du message avec Entrée (Shift+Entrée pour nouvelle ligne)
    chatInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Fonctions
    function loadDocuments() {
        fetch('/documents')
            .then(response => response.json())
            .then(data => {
                renderDocumentsList(data.documents);
            })
            .catch(error => {
                console.error('Erreur lors du chargement des documents:', error);
            });
    }
    
    function renderDocumentsList(documents) {
        documentsListEl.innerHTML = '';
        
        if (documents.length === 0) {
            documentsListEl.innerHTML = '<div class="empty-list">Aucun document importé</div>';
            return;
        }
        
        documents.forEach(doc => {
            const docEl = document.createElement('div');
            docEl.className = 'document-item';
            docEl.innerHTML = `
                <div class="document-title">${doc.title}</div>
                <div class="document-date">${formatDate(doc.timestamp)}</div>
            `;
            
            if (currentDocumentId === doc.id) {
                docEl.classList.add('active');
            }
            
            docEl.addEventListener('click', () => {
                selectDocument(doc.id, doc.title);
            });
            
            documentsListEl.appendChild(docEl);
        });
    }
    
    function selectDocument(documentId, documentTitle) {
        currentDocumentId = documentId;
        
        // Mettre à jour l'interface
        document.querySelectorAll('.document-item').forEach(el => {
            el.classList.remove('active');
        });
        
        document.querySelectorAll('.document-item').forEach(el => {
            if (el.querySelector('.document-title').textContent === documentTitle) {
                el.classList.add('active');
            }
        });
        
        currentDocumentEl.textContent = documentTitle;
        
        // Masquer l'écran de bienvenue et préparer l'interface de chat
        welcomeScreen.style.display = 'none';
        chatMessages.innerHTML = '';
        
        // Créer une nouvelle conversation pour ce document
        startNewChat();
    }
    
    function startNewChat() {
        // Réinitialisation de l'interface de chat
        chatMessages.innerHTML = '';
        currentConversationId = null;
        
        // Si un document est sélectionné, mettre à jour l'interface
        if (currentDocumentId) {
            welcomeScreen.style.display = 'none';
        } else {
            welcomeScreen.style.display = 'block';
        }
    }
    
    function handleFileUpload() {
        const file = fileUpload.files[0];
        if (!file) return;
        
        // Afficher le modal de chargement
        loadingMessage.textContent = `Traitement du document ${file.name}...`;
        loadingModal.classList.add('active');
        
        const formData = new FormData();
        formData.append('file', file);
        
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Recharger la liste des documents
                loadDocuments();
                
                // Sélectionner automatiquement le document uploadé
                selectDocument(data.document_id, file.name);
                
                // Afficher un message de succès
                showSuccessMessage(`Le document ${file.name} a été traité avec succès.`);
            } else {
                showErrorMessage(data.error || 'Une erreur est survenue lors du traitement du document.');
            }
        })
        .catch(error => {
            console.error('Erreur lors de l\'upload du document:', error);
            showErrorMessage('Une erreur est survenue lors de l\'upload du document.');
        })
        .finally(() => {
            // Masquer le modal de chargement
            loadingModal.classList.remove('active');
            // Réinitialiser l'input file
            fileUpload.value = '';
        });
    }
    
    function sendMessage() {
        const message = chatInput.value.trim();
        if (!message || isProcessing) return;
        
        // Désactiver le champ de texte pendant le traitement
        isProcessing = true;
        chatInput.disabled = true;
        
        // Afficher le message de l'utilisateur
        appendMessage(message, true);
        
        // Effacer l'input et réinitialiser sa taille
        chatInput.value = '';
        chatInput.style.height = 'auto';
        
        // Afficher l'indicateur de chargement pour la réponse
        const botResponseEl = appendMessage('Analyse exhaustive du document en cours... (jusqu\'à 30 sections analysées)', false);
        
        // Timeout pour la requête - ajusté pour le temps d'attente plus long
        const timeoutId = setTimeout(() => {
            if (isProcessing) {
                botResponseEl.querySelector('.message-content').textContent = 
                    'Analyse approfondie en cours. L\'analyse de nombreuses sections peut prendre jusqu\'à 5 minutes pour des documents volumineux...'
                
                // Deuxième message après 90 secondes
                setTimeout(() => {
                    if (isProcessing) {
                        botResponseEl.querySelector('.message-content').textContent = 
                            'L\'analyse se poursuit... Veuillez patienter pendant que le modèle traite une grande quantité de contenu.';
                        
                        // Troisième message après 3 minutes supplémentaires
                        setTimeout(() => {
                            if (isProcessing) {
                                botResponseEl.querySelector('.message-content').textContent = 
                                    'La génération de la réponse prend plus de temps que prévu. Si cela persiste au-delà de 5 minutes, essayez de redémarrer Ollama ou de réduire le nombre d\'extraits analysés.';
                            }
                        }, 180000); // 3 minutes
                    }
                }, 90000); // 90 secondes
            }
        }, 45000); // 45 secondes
        
        // Envoyer la requête au serveur
        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                document_id: currentDocumentId
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            // Annuler le timeout
            clearTimeout(timeoutId);
            
            // Vérifier si la réponse est vide
            if (!data.response || data.response.trim() === '') {
                botResponseEl.querySelector('.message-content').textContent = 
                    'Le serveur a retourné une réponse vide. Vérifiez les logs du serveur pour plus d\'informations.';
            } else if (data.response === '...') {
                botResponseEl.querySelector('.message-content').textContent = 
                    'Erreur: La réponse du modèle n\'a pas pu être générée correctement. Vérifiez qu\'Ollama fonctionne et que le modèle Mistral est disponible.';
            } else {
                // Mettre à jour la réponse du bot
                botResponseEl.querySelector('.message-content').textContent = data.response;
            }
        })
        .catch(error => {
            // Annuler le timeout
            clearTimeout(timeoutId);
            
            console.error('Erreur lors de l\'envoi du message:', error);
            botResponseEl.querySelector('.message-content').textContent = 
                `Erreur: ${error.message}. Vérifiez que le serveur fonctionne correctement et qu'Ollama est disponible.`;
        })
        .finally(() => {
            // Réactiver le champ de texte
            isProcessing = false;
            chatInput.disabled = false;
            chatInput.focus();
        });
    }
    
    function appendMessage(content, isUser) {
        const messageEl = document.createElement('div');
        messageEl.className = isUser ? 'message user' : 'message bot';
        
        // Préserver les sauts de ligne et ajouter un formatage basique
        if (!isUser) {
            // Formater le contenu pour la réponse du bot
            content = formatBotResponse(content);
        }
        
        messageEl.innerHTML = `
            <div class="message-content">${content}</div>
        `;
        
        chatMessages.appendChild(messageEl);
        
        // Faire défiler vers le bas
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return messageEl;
    }
    
    function formatBotResponse(text) {
        if (!text) return '';
        
        // Échapper les caractères HTML pour éviter les injections
        text = escapeHtml(text);
        
        // Gérer les avertissements concernant les hallucinations
        if (text.startsWith("ATTENTION:")) {
            const warningEnd = text.indexOf("\n\n");
            if (warningEnd !== -1) {
                const warningText = text.substring(0, warningEnd);
                const restOfText = text.substring(warningEnd + 2);
                text = `<div class="warning-prefix">${warningText}</div>${restOfText}`;
            }
        }
        
        // Mettre en évidence quand le document ne contient pas l'information
        text = text.replace(/Le document ne contient pas cette information\./g, 
            '<span class="no-info">Le document ne contient pas cette information.</span>');
        text = text.replace(/Le document ne semble pas contenir suffisamment d'informations/g, 
            '<span class="no-info">Le document ne semble pas contenir suffisamment d\'informations</span>');
        
        // Convertir les sauts de ligne en balises <br>
        text = text.replace(/\n/g, '<br>');
        
        // Formatage amélioré
        
        // Mise en valeur des références aux sections du document
        text = text.replace(/DOCUMENT:\s+([^<]+)/gi, '<span class="document-reference">DOCUMENT: $1</span>');
        text = text.replace(/SECTION\s+(\d+-\d+)/gi, '<span class="section-reference">SECTION $1</span>');
        text = text.replace(/EXTRAIT\s+(\d+)/gi, '<span class="section-reference">EXTRAIT $1</span>');
        text = text.replace(/selon\s+(la\s+)?(section|extrait)\s+([0-9-]+)/gi, 'selon <span class="section-reference">$2 $3</span>');
        text = text.replace(/d['']après\s+(la\s+)?(section|extrait)\s+([0-9-]+)/gi, 'd\'après <span class="section-reference">$2 $3</span>');
        
        // Formatage basique (gras, italique, listes)
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');  // **bold**
        text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');              // *italic*
        
        // Support pour les listes à puces et numériques
        text = text.replace(/(?:<br>|^)\s*[-•]\s+(.*?)(?=<br>|$)/g, '<br><span class="bullet-item">•</span> $1');
        text = text.replace(/(?:<br>|^)\s*(\d+)[).]\s+(.*?)(?=<br>|$)/g, '<br><span class="numbered-item">$1.</span> $2');
        
        // Mise en évidence des termes importants entre guillemets
        text = text.replace(/"([^"]+)"/g, '<span class="quoted-text">"$1"</span>');
        
        // Mise en évidence des définitions (format terme : définition)
        text = text.replace(/(?:<br>|^)([A-Za-z\s]{2,30})\s*:\s*([^<]+)/g, '<br><span class="definition-term">$1</span> : $2');
        
        return text;
    }
    
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
    
    function showSuccessMessage(message) {
        // Message temporaire qui disparaît après quelques secondes
        const messageEl = document.createElement('div');
        messageEl.className = 'system-message success';
        messageEl.textContent = message;
        
        chatMessages.appendChild(messageEl);
        
        // Faire défiler vers le bas
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Disparaître après 5 secondes
        setTimeout(() => {
            messageEl.style.opacity = '0';
            setTimeout(() => {
                messageEl.remove();
            }, 500);
        }, 5000);
    }
    
    function showErrorMessage(message) {
        // Message d'erreur sous forme de message "bot"
        const messageEl = document.createElement('div');
        messageEl.className = 'message bot error';
        messageEl.innerHTML = `
            <div class="message-content">❌ ${message}</div>
        `;
        
        chatMessages.appendChild(messageEl);
        
        // Faire défiler vers le bas
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}); 