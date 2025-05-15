-- Schéma de la base de données pour TechDocBot

-- Suppression des tables si elles existent déjà
DROP TABLE IF EXISTS chunks;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS conversations;
DROP TABLE IF EXISTS messages;

-- Table des documents
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    file_path TEXT NOT NULL,
    content_text TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table des chunks de texte (sections de document)
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding TEXT NOT NULL, -- Stockage des embeddings sous format texte (JSON)
    FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
);

-- Table des conversations
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT DEFAULT 'Nouvelle conversation',
    document_id INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE SET NULL
);

-- Table des messages
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    is_user BOOLEAN NOT NULL, -- TRUE pour les messages de l'utilisateur, FALSE pour les réponses du bot
    content TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
);

-- Index pour optimiser les recherches
CREATE INDEX idx_document_id ON chunks (document_id);
CREATE INDEX idx_conversation_id ON messages (conversation_id); 