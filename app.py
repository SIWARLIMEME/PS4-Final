import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
from app.database.db import init_db, get_db
from app.models.document_processor import DocumentProcessor
from app.models.chatbot import Chatbot
import numpy as np
import json
import re

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'pptx'}

app = Flask(
    __name__,
    template_folder='app/templates',  # Spécifie le chemin des templates
    static_folder='app/static'        # Spécifie le chemin des fichiers statiques
)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# Initialisation
document_processor = DocumentProcessor()
chatbot = Chatbot()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Page principale du chatbot"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Route pour télécharger un document"""
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier trouvé'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Aucun fichier sélectionné'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Traiter le document et extraire le texte
        doc_id = document_processor.process_document(filepath, filename)
        
        return jsonify({
            'success': True,
            'document_id': doc_id,
            'message': f'Document {filename} traité avec succès'
        })
    
    return jsonify({'error': 'Type de fichier non autorisé'}), 400

@app.route('/chat', methods=['POST'])
def chat():
    """Route pour échanger avec le chatbot"""
    data = request.json
    if not data or 'message' not in data:
        return jsonify({'error': 'Message requis'}), 400
    
    user_message = data['message']
    document_id = data.get('document_id', None)
    
    response = chatbot.get_response(user_message, document_id)
    
    return jsonify({
        'response': response
    })

@app.route('/documents', methods=['GET'])
def list_documents():
    """Liste tous les documents traités"""
    db = get_db()
    documents = db.execute('SELECT id, title, timestamp FROM documents ORDER BY timestamp DESC').fetchall()
    return jsonify({
        'documents': [dict(doc) for doc in documents]
    })

if __name__ == '__main__':
    # S'assurer que le dossier d'upload existe
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Initialiser la base de données
    init_db()
    
    # Port d'écoute personnalisable (8080 par défaut)
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port) 