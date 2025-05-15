import sqlite3
import os
from flask import g
import numpy as np
import json

DATABASE = 'app/database/techdocbot.db'

def get_db():
    """Récupère une connexion à la base de données"""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def close_db(exception):
    """Ferme la connexion à la base de données"""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Initialise la base de données avec les tables nécessaires"""
    # S'assurer que le dossier existe
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    
    db = sqlite3.connect(DATABASE)
    with open('app/database/schema.sql', 'r') as f:
        db.executescript(f.read())
    db.close()

def add_document(title, path, content_text):
    """Ajoute un document à la base de données"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        'INSERT INTO documents (title, file_path, content_text) VALUES (?, ?, ?)',
        (title, path, content_text)
    )
    db.commit()
    return cursor.lastrowid

def add_chunks(document_id, chunks, embeddings):
    """Ajoute des chunks de texte et leurs embeddings à la base de données"""
    db = get_db()
    cursor = db.cursor()
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        cursor.execute(
            'INSERT INTO chunks (document_id, chunk_index, content, embedding) VALUES (?, ?, ?, ?)',
            (document_id, i, chunk, embedding)
        )
    db.commit()

def get_full_document(document_id):
    """Récupère un document complet à partir de son ID"""
    db = get_db()
    cursor = db.execute(
        'SELECT id, title, file_path, content_text FROM documents WHERE id = ?',
        (document_id,)
    )
    document = cursor.fetchone()
    
    if document:
        return dict(document)
    return None

def search_similar_chunks(query_embedding, limit=5):
    """Recherche les chunks les plus similaires à la requête"""
    query_embedding_array = json.loads(query_embedding)
    db = get_db()
    
    # Récupérer tous les chunks avec leurs embeddings
    cursor = db.execute(
        '''
        SELECT c.id, c.content, c.document_id, d.title, c.embedding
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        '''
    )
    
    chunks = cursor.fetchall()
    similarities = []
    
    # Calculer la similarité cosinus pour chaque chunk
    for chunk in chunks:
        chunk_embedding = json.loads(chunk['embedding'])
        # Calculer la similarité cosinus
        dot_product = np.dot(query_embedding_array, chunk_embedding)
        norm_query = np.linalg.norm(query_embedding_array)
        norm_chunk = np.linalg.norm(chunk_embedding)
        
        if norm_query * norm_chunk == 0:
            similarity = 0
        else:
            similarity = dot_product / (norm_query * norm_chunk)
        
        similarities.append((chunk, similarity))
    
    # Trier par similarité décroissante
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    # Retourner les chunks les plus similaires
    return [dict(s[0]) for s in similarities[:limit]] 