"""
Recherche hybride : Vectorielle + BM25 pour le RAG juridique
==========================================================
"""

from typing import List, Dict, Any, Tuple
import logging
import pickle
import os
from pathlib import Path
from rank_bm25 import BM25Okapi
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import numpy as np

# Télécharger les ressources NLTK si nécessaire
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class HybridSearchEngine:
    """Moteur de recherche hybride combinant vectoriel et BM25"""
    
    def __init__(self, config, embedding_model, vector_store):
        self.config = config
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.logger = logging.getLogger(__name__)
        
        # Index BM25
        self.bm25_index = None
        self.documents = []  # Textes pour BM25
        self.metadata_list = []  # Métadonnées correspondantes
        
        # Cache BM25
        self.bm25_cache_path = Path(config.vector_store.database_path) / "bm25_index.pkl"
        
        # Stop words français et arabe
        self.stop_words = set()
        try:
            self.stop_words.update(stopwords.words('french'))
            self.stop_words.update(stopwords.words('arabic'))
        except:
            pass  # Continuer sans stop words si erreur
        
        # Charger ou créer l'index BM25
        self._load_or_create_bm25_index()
    
    def _load_or_create_bm25_index(self):
        """Charge l'index BM25 existant ou le crée"""
        try:
            if self.bm25_cache_path.exists():
                self.logger.info("Chargement de l'index BM25 existant...")
                with open(self.bm25_cache_path, 'rb') as f:
                    cache_data = pickle.load(f)
                    self.bm25_index = cache_data['bm25_index']
                    self.documents = cache_data['documents']
                    self.metadata_list = cache_data['metadata_list']
                self.logger.info(f"Index BM25 chargé : {len(self.documents)} documents")
            else:
                self.logger.info("Création de l'index BM25...")
                self._create_bm25_index()
        except Exception as e:
            self.logger.error(f"Erreur chargement BM25 : {e}")
            self._create_bm25_index()
    
    def _create_bm25_index(self):
        """Crée un nouvel index BM25 à partir de la base vectorielle"""
        try:
            # Récupérer tous les documents de la base vectorielle
            all_results = self.vector_store.search(
                query_vector=np.zeros(self.config.vector_store.vector_size),
                limit=10000  # Récupérer tous les documents
            )
            
            self.documents = []
            self.metadata_list = []
            tokenized_docs = []
            
            for result in all_results:
                # Texte pour BM25
                text = result['text']
                self.documents.append(text)
                self.metadata_list.append(result['metadata'])
                
                # Tokenisation pour BM25
                tokens = self._tokenize_text(text)
                tokenized_docs.append(tokens)
            
            # Créer l'index BM25
            if tokenized_docs:
                self.bm25_index = BM25Okapi(tokenized_docs)
                
                # Sauvegarder l'index
                os.makedirs(self.bm25_cache_path.parent, exist_ok=True)
                with open(self.bm25_cache_path, 'wb') as f:
                    pickle.dump({
                        'bm25_index': self.bm25_index,
                        'documents': self.documents,
                        'metadata_list': self.metadata_list
                    }, f)
                
                self.logger.info(f"Index BM25 créé et sauvegardé : {len(self.documents)} documents")
            else:
                self.logger.warning("Aucun document trouvé pour créer l'index BM25")
                
        except Exception as e:
            self.logger.error(f"Erreur création index BM25 : {e}")
    
    def _tokenize_text(self, text: str) -> List[str]:
        """Tokenise le texte pour BM25"""
        try:
            # Tokenisation
            tokens = word_tokenize(text.lower(), language='french')
            
            # Filtrer les tokens (garder seulement les mots significatifs)
            filtered_tokens = [
                token for token in tokens 
                if token.isalnum() and len(token) > 2 and token not in self.stop_words
            ]
            
            return filtered_tokens
        except Exception as e:
            # Fallback simple si erreur NLTK
            return text.lower().split()
    
    def hybrid_search(self, question: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Recherche hybride combinant vectoriel et BM25"""
        try:
            # 1. Recherche vectorielle
            vector_results = self._vector_search(question, limit * 2)
            
            # 2. Recherche BM25
            bm25_results = self._bm25_search(question, limit * 2)
            
            # 3. Fusion des résultats
            merged_results = self._merge_results(vector_results, bm25_results, limit)
            
            self.logger.info(f"Recherche hybride : {len(merged_results)} résultats")
            return merged_results
            
        except Exception as e:
            self.logger.error(f"Erreur recherche hybride : {e}")
            # Fallback sur recherche vectorielle uniquement
            return self._vector_search(question, limit)
    
    def _vector_search(self, question: str, limit: int) -> List[Dict[str, Any]]:
        """Recherche vectorielle classique"""
        try:
            question_embedding = self.embedding_model.encode(question)
            results = self.vector_store.search(
                query_vector=question_embedding,
                limit=limit
            )
            
            # Ajouter le type de recherche
            for result in results:
                result['search_type'] = 'vector'
                result['vector_score'] = result['score']
            
            return results
        except Exception as e:
            self.logger.error(f"Erreur recherche vectorielle : {e}")
            return []
    
    def _bm25_search(self, question: str, limit: int) -> List[Dict[str, Any]]:
        """Recherche BM25 (mots-clés)"""
        try:
            if not self.bm25_index:
                return []
            
            # Tokeniser la question
            query_tokens = self._tokenize_text(question)
            
            if not query_tokens:
                return []
            
            # Scores BM25
            scores = self.bm25_index.get_scores(query_tokens)
            
            # Trier par score décroissant
            scored_docs = [
                (idx, score) for idx, score in enumerate(scores)
                if score > 0  # Garder seulement les scores positifs
            ]
            scored_docs.sort(key=lambda x: x[1], reverse=True)
            
            # Prendre les meilleurs résultats
            results = []
            for idx, bm25_score in scored_docs[:limit]:
                result = {
                    'text': self.documents[idx],
                    'metadata': self.metadata_list[idx],
                    'score': float(bm25_score),
                    'search_type': 'bm25',
                    'bm25_score': float(bm25_score)
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Erreur recherche BM25 : {e}")
            return []
    
    def _merge_results(self, vector_results: List[Dict], bm25_results: List[Dict], limit: int) -> List[Dict]:
        """Fusionne les résultats vectoriels et BM25"""
        try:
            # Normaliser les scores entre 0 et 1
            vector_normalized = self._normalize_scores(vector_results, 'vector_score')
            bm25_normalized = self._normalize_scores(bm25_results, 'bm25_score')
            
            # Combiner les résultats par document unique
            merged_docs = {}
            
            # Ajouter les résultats vectoriels
            for result in vector_normalized:
                doc_id = self._get_doc_id(result['metadata'])
                merged_docs[doc_id] = {
                    **result,
                    'vector_score_norm': result.get('vector_score_norm', 0),
                    'bm25_score_norm': 0
                }
            
            # Ajouter/fusionner les résultats BM25
            for result in bm25_normalized:
                doc_id = self._get_doc_id(result['metadata'])
                if doc_id in merged_docs:
                    # Document déjà trouvé par recherche vectorielle
                    merged_docs[doc_id]['bm25_score_norm'] = result.get('bm25_score_norm', 0)
                    merged_docs[doc_id]['search_type'] = 'hybrid'
                else:
                    # Nouveau document trouvé seulement par BM25
                    merged_docs[doc_id] = {
                        **result,
                        'vector_score_norm': 0,
                        'bm25_score_norm': result.get('bm25_score_norm', 0)
                    }
            
            # Calculer le score final hybride
            for doc_id, doc in merged_docs.items():
                # Pondération : 60% vectoriel, 40% BM25
                final_score = (0.4 * doc['vector_score_norm'] + 0.6 * doc['bm25_score_norm'])
                doc['score'] = final_score
                doc['hybrid_score'] = final_score
            
            # Trier par score final et limiter
            final_results = list(merged_docs.values())
            final_results.sort(key=lambda x: x['score'], reverse=True)
            
            return final_results[:limit]
            
        except Exception as e:
            self.logger.error(f"Erreur fusion résultats : {e}")
            return vector_results[:limit]
    
    def _normalize_scores(self, results: List[Dict], score_key: str) -> List[Dict]:
        """Normalise les scores entre 0 et 1"""
        if not results:
            return results
        
        scores = [r.get(score_key, 0) for r in results]
        max_score = max(scores) if scores else 1
        min_score = min(scores) if scores else 0
        
        if max_score == min_score:
            # Tous les scores sont identiques
            for result in results:
                result[f'{score_key}_norm'] = 1.0
        else:
            # Normalisation min-max
            for result in results:
                original_score = result.get(score_key, 0)
                normalized = (original_score - min_score) / (max_score - min_score)
                result[f'{score_key}_norm'] = normalized
        
        return results
    
    def _get_doc_id(self, metadata: Dict) -> str:
        """Génère un ID unique pour un document"""
        code = metadata.get('code_source', 'unknown')
        article = metadata.get('article_number', 'unknown')
        chunk_id = metadata.get('chunk_id', '0')
        return f"{code}_{article}_{chunk_id}"
    
    def rebuild_bm25_index(self):
        """Force la reconstruction de l'index BM25"""
        try:
            if self.bm25_cache_path.exists():
                os.remove(self.bm25_cache_path)
            self._create_bm25_index()
            self.logger.info("Index BM25 reconstruit avec succès")
        except Exception as e:
            self.logger.error(f"Erreur reconstruction BM25 : {e}")