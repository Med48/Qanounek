"""
Configuration centrale du système RAG - Lois Marocaines
======================================================
"""

import os
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

@dataclass
class PDFConfig:
    """Configuration pour l'extraction PDF"""
    raw_pdfs_dir: str = "data/raw_pdfs"
    extracted_text_dir: str = "data/processed/extracted_text"
    articles_dir: str = "data/processed/articles"
    
    # Codes juridiques supportés
    legal_codes: Dict[str, str] = None
    
    def __post_init__(self):
        if self.legal_codes is None:
            self.legal_codes = {
                "code_penal": "Code Pénal",
                "code_travail": "Code du Travail", 
                "code_commerce": "Code de Commerce",
                "code_procedure_civile": "Code de Procédure Civile",
                "code_route": "Code de la Route"
            }

@dataclass
class ChunkingConfig:
    """Configuration pour le chunking"""
    chunk_size: int = 256
    chunk_overlap: int = 50
    min_chunk_size: int = 100
    max_chunk_size: int = 1500
    
    # Séparateurs pour le chunking intelligent
    separators: List[str] = None
    
    def __post_init__(self):
        if self.separators is None:
            self.separators = [
                "\n\n",      # Paragraphes
                "\n",        # Lignes
                ". ",        # Phrases
                " ",         # Mots
                ""
            ]

@dataclass
class EmbeddingConfig:
    """Configuration pour les embeddings"""
    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    batch_size: int = 32
    device: str = "cpu"  # ou "cuda" si GPU disponible
    normalize_embeddings: bool = True

@dataclass
class VectorStoreConfig:
    """Configuration pour la base vectorielle"""
    database_path: str = "data/vector_db"
    collection_name: str = "lois_marocaines_v2"
    distance_metric: str = "cosine"
    vector_size: int = 384  # Pour all-MiniLM-L12-v2
    
    # Paramètres de recherche
    search_limit: int = 10
    similarity_threshold: float = 0.3

@dataclass
class LLMConfig:
    """Configuration pour le LLM"""
    provider: str = "google"  # google, openai, anthropic
    model_name: str = "gemini-1.5-flash"
    api_key_env: str = "GEMINI_API_KEY"
    
    # Paramètres de génération
    temperature: float = 0.2
    max_tokens: int = 800
    top_p: float = 0.8

@dataclass
class APIConfig:
    """Configuration pour l'API FastAPI"""
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    
    # CORS
    cors_origins: List[str] = None
    
    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["*"]  # À restreindre en production

class Config:
    """Configuration principale du système"""
    
    def __init__(self):
        # Répertoire racine du projet
        self.root_dir = Path(__file__).parent.parent
        
        # Configurations des modules
        self.pdf = PDFConfig()
        self.chunking = ChunkingConfig()
        self.embedding = EmbeddingConfig()
        self.vector_store = VectorStoreConfig()
        self.llm = LLMConfig()
        self.api = APIConfig()
        
        # Variables d'environnement
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.environment = os.getenv("ENVIRONMENT", "development")
        
        # Créer les répertoires nécessaires
        self._create_directories()
        
        # Validation
        self._validate_config()
    
    def _create_directories(self):
        """Créer tous les répertoires nécessaires"""
        directories = [
            self.pdf.raw_pdfs_dir,
            self.pdf.extracted_text_dir,
            self.pdf.articles_dir,
            "data/processed/chunks",
            self.vector_store.database_path,
            "logs"
        ]
        
        for directory in directories:
            Path(self.root_dir / directory).mkdir(parents=True, exist_ok=True)
    
    def _validate_config(self):
        """Valider la configuration"""
        # Vérifier la clé API Gemini
        if not self.gemini_api_key:
            print("⚠️ GEMINI_API_KEY non définie. Créez un fichier .env avec votre clé API.")
        
        # Vérifier que les PDFs existent
        pdf_dir = Path(self.root_dir / self.pdf.raw_pdfs_dir)
        if not any(pdf_dir.glob("*.pdf")):
            print(f"⚠️ Aucun PDF trouvé dans {pdf_dir}")
    
    def get_pdf_path(self, code_name: str) -> Path:
        """Obtenir le chemin d'un PDF spécifique"""
        return Path(self.root_dir / self.pdf.raw_pdfs_dir / f"{code_name}.pdf")
    
    def get_extracted_text_path(self, code_name: str) -> Path:
        """Obtenir le chemin du texte extrait"""
        return Path(self.root_dir / self.pdf.extracted_text_dir / f"{code_name}.txt")
    
    def get_articles_path(self, code_name: str) -> Path:
        """Obtenir le chemin des articles structurés"""
        return Path(self.root_dir / self.pdf.articles_dir / f"{code_name}.json")
    
    def list_available_pdfs(self) -> List[str]:
        """Lister les PDFs disponibles"""
        pdf_dir = Path(self.root_dir / self.pdf.raw_pdfs_dir)
        return [pdf.stem for pdf in pdf_dir.glob("*.pdf")]
    
    def __str__(self) -> str:
        """Représentation string de la configuration"""
        return f"""
Configuration RAG Lois Marocaines:
- Environnement: {self.environment}
- Modèle embeddings: {self.embedding.model_name}
- Base vectorielle: {self.vector_store.database_path}
- LLM: {self.llm.model_name}
- PDFs disponibles: {len(self.list_available_pdfs())}
        """.strip()

# Instance globale de configuration
config = Config()

# Fonctions utilitaires
def get_config() -> Config:
    """Obtenir l'instance de configuration"""
    return config

def is_development() -> bool:
    """Vérifier si on est en mode développement"""
    return config.environment == "development"

def is_production() -> bool:
    """Vérifier si on est en mode production"""
    return config.environment == "production"