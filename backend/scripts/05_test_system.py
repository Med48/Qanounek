#!/usr/bin/env python3
"""
Script de test du système RAG complet
====================================
"""

import sys
import logging
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))

from config import get_config
from models.embeddings import EmbeddingModel
from models.llm import LLMInterface
from vector_store.qdrant_store import QdrantStore
from vector_store.search import RAGSearchEngine

def test_questions():
    """Questions de test pour différents codes juridiques"""
    return [
        {
            "question": "Qu'est-ce que le contrat de travail selon la loi marocaine?",
            "expected_code": "code_travail"
        },
        {
            "question": "Quelles sont les sanctions pour vol au Maroc?",
            "expected_code": "code_penal"
        },
        {
            "question": "Comment créer une société au Maroc?",
            "expected_code": "code_commerce"
        },
        {
            "question": "Quelle est la procédure pour porter plainte?",
            "expected_code": "code_procedure_civile"
        },
        {
            "question": "Quelles sont les règles de circulation routière?",
            "expected_code": "code_route"
        }
    ]

def main():
    """Test complet du système"""
    print("TEST DU SYSTÈME RAG COMPLET")
    print("=" * 50)
    
    logging.basicConfig(level=logging.INFO)
    config = get_config()
    
    try:
        # Initialiser tous les composants
        print("Initialisation des composants...")
        
        embedding_model = EmbeddingModel(config)
        print("✅ Modèle d'embeddings initialisé")
        
        vector_store = QdrantStore(config)
        print("✅ Base vectorielle connectée")
        
        llm = LLMInterface(config)
        print("✅ LLM configuré")
        
        search_engine = RAGSearchEngine(config, embedding_model, vector_store, llm)
        print("✅ Moteur de recherche initialisé")
        
        # Vérifier la base vectorielle
        collection_info = vector_store.get_collection_info()
        print(f"\nInfo collection: {collection_info['points_count']} chunks disponibles")
        
        if collection_info['points_count'] == 0:
            print("ERREUR: Aucun chunk dans la base vectorielle")
            print("Exécutez d'abord le script 04_create_embeddings.py")
            return
        
        # Tests des questions
        print(f"\nTest avec {len(test_questions())} questions...")
        print("-" * 40)
        
        for i, test in enumerate(test_questions(), 1):
            print(f"\n{i}. {test['question']}")
            print(f"   Code attendu: {test['expected_code']}")
            
            try:
                result = search_engine.search_and_answer(test['question'])
                
                print(f"   Confiance: {result['confidence']:.2f}")
                print(f"   Sources trouvées: {result['search_results_count']}")
                print(f"   Réponse: {result['answer'][:100]}...")
                
                # Vérifier si le bon code est trouvé
                found_codes = set()
                for source in result['sources']:
                    found_codes.add(source['code_source'])
                
                if test['expected_code'] in found_codes:
                    print("   ✅ Code correct trouvé")
                else:
                    print(f"   ❌ Code attendu non trouvé. Trouvés: {found_codes}")
                
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
        
        print(f"\nTest terminé!")
        
    except Exception as e:
        print(f"ERREUR: {e}")
        logging.error(f"Erreur test système: {e}")

if __name__ == "__main__":
    main()