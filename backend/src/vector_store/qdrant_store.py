"""
Interface pour la base vectorielle Qdrant
=========================================
"""

import qdrant_client
from qdrant_client.models import Distance, VectorParams, PointStruct
import numpy as np
from typing import List, Dict, Any, Optional
import uuid
import logging

class QdrantStore:
    """Interface pour Qdrant"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.collection_name = config.vector_store.collection_name
        self._setup_client()
    
    def _setup_client(self):
        """Configurer le client Qdrant"""
        try:
            self.client = qdrant_client.QdrantClient(
                path=self.config.vector_store.database_path
            )
            self.logger.info(f"Client Qdrant initialisé: {self.config.vector_store.database_path}")
            
        except Exception as e:
            self.logger.error(f"Erreur initialisation Qdrant: {e}")
            raise
    
    def create_collection(self, vector_size: int):
        """Créer une collection"""
        try:
            # Supprimer la collection existante si elle existe
            try:
                self.client.delete_collection(self.collection_name)
                self.logger.info(f"Collection {self.collection_name} supprimée")
            except:
                pass
            
            # Créer nouvelle collection
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            
            self.logger.info(f"Collection {self.collection_name} créée (dimension: {vector_size})")
            
        except Exception as e:
            self.logger.error(f"Erreur création collection: {e}")
            raise
    
    def add_chunks(self, chunks: List[Dict], embeddings: np.ndarray):
        """Ajouter des chunks avec leurs embeddings"""
        try:
            points = []
            
            for i, chunk in enumerate(chunks):
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embeddings[i].tolist(),
                    payload={
                        'text': chunk['text'],
                        'metadata': chunk['metadata'],
                        'chunk_id': chunk['id']
                    }
                )
                points.append(point)
            
            # Insérer par batch
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
                
                self.logger.info(f"Batch {i//batch_size + 1}: {len(batch)} chunks ajoutés")
            
            self.logger.info(f"Total {len(chunks)} chunks ajoutés à la collection")
            
        except Exception as e:
            self.logger.error(f"Erreur ajout chunks: {e}")
            raise
    
    def search(self, query_vector: np.ndarray, limit: int = 5) -> List[Dict]:
        """Rechercher des chunks similaires"""
        try:
            # Vérifier les dimensions
            if hasattr(query_vector, 'shape'):
                if len(query_vector.shape) > 1:
                    query_vector = query_vector.flatten()
            
            # Convertir en liste si nécessaire
            if isinstance(query_vector, np.ndarray):
                query_list = query_vector.tolist()
            else:
                query_list = query_vector
            
            self.logger.info(f"Recherche avec vecteur de dimension: {len(query_list)}")
            
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_list,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'text': result.payload['text'],
                    'metadata': result.payload['metadata'],
                    'chunk_id': result.payload['chunk_id'],
                    'score': result.score
                })
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Erreur recherche: {e}")
            # Log plus détaillé pour debug
            self.logger.error(f"Type query_vector: {type(query_vector)}")
            if hasattr(query_vector, 'shape'):
                self.logger.error(f"Shape query_vector: {query_vector.shape}")
            return []
    
    def get_collection_info(self) -> Dict:
        """Obtenir les informations sur la collection"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                'name': self.collection_name,
                'points_count': info.points_count,
                'vectors_count': info.vectors_count,
                'status': info.status
            }
        except Exception as e:
            self.logger.error(f"Erreur info collection: {e}")
            return {}