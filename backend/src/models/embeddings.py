"""
Gestion des modèles d'embeddings
================================
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union
import logging

class EmbeddingModel:
    """Wrapper pour les modèles d'embeddings"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Charger le modèle d'embeddings"""
        self.logger.info(f"Chargement du modèle: {self.config.embedding.model_name}")
        
        try:
            self.model = SentenceTransformer(
                self.config.embedding.model_name,
                device=self.config.embedding.device,
                cache_folder=None  # Ajoutez cette ligne
            )
            print(f"MODÈLE VRAIMENT CHARGÉ: {self.config.embedding.model_name}")
            self.logger.info("Modèle d'embeddings chargé avec succès")
            
        except Exception as e:
            self.logger.error(f"Erreur chargement modèle: {e}")
            raise
    
    def encode(self, texts: Union[str, List[str]], batch_size: int = None) -> np.ndarray:
        """Encoder des textes en embeddings"""
        if isinstance(texts, str):
            texts = [texts]
        
        batch_size = batch_size or self.config.embedding.batch_size
        
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=self.config.embedding.normalize_embeddings,
                show_progress_bar=len(texts) > 100
            )
            
            return embeddings
            
        except Exception as e:
            self.logger.error(f"Erreur encoding: {e}")
            raise
    
    def get_dimension(self) -> int:
        """Obtenir la dimension des embeddings"""
        return self.model.get_sentence_embedding_dimension()