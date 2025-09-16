#!/usr/bin/env python3
"""
Script de génération des embeddings et création de la base vectorielle
=====================================================================
"""

import sys
import json
import logging
from pathlib import Path
from tqdm import tqdm

sys.path.append(str(Path(__file__).parent.parent / "src"))

from config import get_config
from models.embeddings import EmbeddingModel
from vector_store.qdrant_store import QdrantStore

def load_all_chunks(config):
    """Charger tous les chunks depuis les fichiers JSON"""
    chunks_dir = Path(config.root_dir / "data/processed/chunks")
    all_chunks = []
    
    for json_file in chunks_dir.glob("*_chunks.json"):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        code_chunks = data['chunks']
        print(f"Chargé {len(code_chunks)} chunks de {json_file.stem}")
        all_chunks.extend(code_chunks)
    
    return all_chunks

def main():
    """Fonction principale"""
    print("GÉNÉRATION DES EMBEDDINGS ET CRÉATION DE LA BASE VECTORIELLE")
    print("=" * 70)
    
    logging.basicConfig(level=logging.INFO)
    config = get_config()
    
    # Vérifier les chunks disponibles
    chunks_dir = Path(config.root_dir / "data/processed/chunks")
    chunk_files = list(chunks_dir.glob("*_chunks.json"))
    
    if not chunk_files:
        print(f"ERREUR: Aucun fichier de chunks trouvé dans {chunks_dir}")
        print("Exécutez d'abord le script 03_create_chunks.py")
        return
    
    print(f"Fichiers de chunks: {len(chunk_files)}")
    for file in chunk_files:
        print(f"  - {file.name}")
    
    # Charger tous les chunks
    print("\nChargement des chunks...")
    all_chunks = load_all_chunks(config)
    print(f"Total chunks chargés: {len(all_chunks)}")
    
    if not all_chunks:
        print("Aucun chunk à traiter.")
        return
    
    # Confirmer
    response = input(f"\nGénérer les embeddings pour {len(all_chunks)} chunks? (o/n): ").lower().strip()
    if response not in ['o', 'oui', 'y', 'yes']:
        print("Génération annulée.")
        return
    
    try:
        # FORCER directement le modèle sans passer par EmbeddingModel
        print("\nInitialisation FORCÉE du modèle d'embeddings...")
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", device="cpu")
        print(f"Modèle forcé: {model}")
        
        # Créer un wrapper simple pour remplacer EmbeddingModel
        class SimpleEmbeddingModel:
            def __init__(self, model):
                self.model = model
            def encode(self, texts):
                return self.model.encode(texts)
            def get_dimension(self):
                return self.model.get_sentence_embedding_dimension()
        
        embedding_model = SimpleEmbeddingModel(model)
        vector_dimension = embedding_model.get_dimension()
        print(f"Dimension des vecteurs: {vector_dimension}")
        
        # Initialiser la base vectorielle
        print("\nInitialisation de la base vectorielle...")
        vector_store = QdrantStore(config)
        vector_store.create_collection(vector_dimension)
        
        # Extraire les textes des chunks
        print("\nExtraction des textes...")
        chunk_texts = [chunk['text'] for chunk in all_chunks]
        
        # Générer les embeddings
        print("\nGénération des embeddings...")
        embeddings = embedding_model.encode(chunk_texts)
        print(f"Embeddings générés: {embeddings.shape}")
        
        # Ajouter à la base vectorielle
        print("\nAjout à la base vectorielle...")
        vector_store.add_chunks(all_chunks, embeddings)
        
        # Vérification finale
        print("\nVérification finale...")
        collection_info = vector_store.get_collection_info()
        print(f"Collection créée avec succès:")
        print(f"  - Nom: {collection_info['name']}")
        print(f"  - Points: {collection_info['points_count']}")
        print(f"  - Statut: {collection_info['status']}")
        
        print("\nBase vectorielle créée avec succès!")
        
    except Exception as e:
        print(f"\nERREUR: {e}")
        logging.error(f"Erreur génération embeddings: {e}")

if __name__ == "__main__":
    main()