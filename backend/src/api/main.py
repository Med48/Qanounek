"""
API FastAPI pour le système RAG
===============================
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path
import sys

# Ajouter src au path
sys.path.append(str(Path(__file__).parent.parent))

from config import get_config
from models.embeddings import EmbeddingModel
from models.llm import LLMInterface
from vector_store.qdrant_store import QdrantStore
from vector_store.search import RAGSearchEngine

# Modèles Pydantic
class QuestionRequest(BaseModel):
    question: str
    max_results: Optional[int] = 5

class Source(BaseModel):
    article_number: str
    code_source: str
    relevance_score: float
    text_preview: str

class AnswerResponse(BaseModel):
    answer: str
    sources: List[Source]
    confidence: float
    search_results_count: int

# Configuration
config = get_config()

# Initialisation de l'app
app = FastAPI(
    title="RAG Lois Marocaines",
    description="API pour questions-réponses sur les lois marocaines",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables globales pour les modèles
embedding_model = None
vector_store = None
llm = None
search_engine = None

@app.on_event("startup")
async def startup_event():
    """Initialiser les modèles au démarrage"""
    global embedding_model, vector_store, llm, search_engine
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Initialisation des modèles...")
        
        # UTILISER LE MÊME MODÈLE QUE LE SCRIPT
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", device="cpu")
        print(f"MODÈLE API FORCÉ: {model}")
        
        # Wrapper simple
        class SimpleEmbeddingModel:
            def __init__(self, model):
                self.model = model
            def encode(self, texts):
                return self.model.encode(texts)
            def get_dimension(self):
                return self.model.get_sentence_embedding_dimension()
        
        embedding_model = SimpleEmbeddingModel(model)
        
        # Base vectorielle
        vector_store = QdrantStore(config)
        
        # LLM
        llm = LLMInterface(config)
        
        # Moteur de recherche
        search_engine = RAGSearchEngine(config, embedding_model, vector_store, llm)
        
        logger.info("Tous les modèles initialisés avec succès")
        
    except Exception as e:
        logger.error(f"Erreur initialisation: {e}")
        raise

@app.get("/")
async def root():
    """Point d'entrée de l'API"""
    return {
        "message": "API RAG Lois Marocaines",
        "version": "2.0.0",
        "status": "operational",
        "endpoints": {
            "ask": "/ask",
            "health": "/health",
            "info": "/info"
        }
    }

@app.get("/health")
async def health_check():
    """Vérification de santé"""
    try:
        # Vérifier la base vectorielle
        collection_info = vector_store.get_collection_info()
        
        return {
            "api": "healthy",
            "embedding_model": "loaded" if embedding_model else "not_loaded",
            "vector_store": "connected" if vector_store else "not_connected",
            "llm": "configured" if llm else "not_configured",
            "collection_info": collection_info
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/info")
async def get_info():
    """Informations sur le système"""
    try:
        collection_info = vector_store.get_collection_info()
        
        return {
            "system": "RAG Lois Marocaines",
            "version": "2.0.0",
            "embedding_model": config.embedding.model_name,
            "llm_model": config.llm.model_name,
            "vector_dimension": embedding_model.get_dimension(),
            "collection_stats": collection_info,
            "supported_codes": list(config.pdf.legal_codes.values())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """Poser une question sur les lois marocaines"""
    if not search_engine:
        raise HTTPException(status_code=503, detail="Système non initialisé")
    
    try:
        # DEBUG : Test direct avec le nouveau modèle forcé
        print(f"=== DEBUG API DIRECT ===")
        print(f"Question reçue: {request.question}")
        
        # FORCER l'utilisation du nouveau modèle directement
        from sentence_transformers import SentenceTransformer
        temp_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", device="cpu")
        question_embedding = temp_model.encode(request.question)
        
        print(f"UTILISE NOUVEAU MODELE: {temp_model}")
        print(f"Question embedding shape: {question_embedding.shape}")
        collection_info = vector_store.get_collection_info()
        print(f"Collection info: {collection_info}")
        
        direct_results = vector_store.search(query_vector=question_embedding, limit=10)
        
        print("Résultats recherche directe:")
        for i, result in enumerate(direct_results[:5]):
            metadata = result['metadata']
            print(f"  {i+1}. Article {metadata.get('article_number')} - Score: {result['score']:.3f}")
            if '184' in str(metadata.get('article_number', '')):
                print(f"     ARTICLE 184 TROUVÉ ! Contenu: {result['text'][:100]}...")
        
        # Rechercher et générer la réponse normale
        result = search_engine.search_and_answer(
            question=request.question,
            max_results=request.max_results
        )
        
        return AnswerResponse(
            answer=result['answer'],
            sources=[Source(**source) for source in result['sources']],
            confidence=result['confidence'],
            search_results_count=result['search_results_count']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config.api.host,
        port=config.api.port,
        reload=config.api.reload
    )