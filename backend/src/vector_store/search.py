"""
Moteur de recherche RAG avec recherche hybride et regroupement des chunks
=====================================================================
"""

import logging
import os
from typing import Any, Dict, List
import google.generativeai as genai

# Télécharger les ressources NLTK si nécessaire
try:
    import nltk
    nltk.data.find('tokenizers/punkt')
except LookupError:
    import nltk
    nltk.download('punkt')

try:
    import nltk
    nltk.data.find('corpora/stopwords')
except LookupError:
    import nltk
    nltk.download('stopwords')

class RAGSearchEngine:
    """Moteur de recherche RAG avec reformulation intelligente et recherche hybride"""
    
    def __init__(self, config, embedding_model, vector_store, llm):
        self.config = config
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.llm = llm
        self.logger = logging.getLogger(__name__)
        
        # Modèle pour reformulation (utilise le même que le LLM principal)
        self.model = llm.model
        
        # NOUVEAU : Moteur de recherche hybride
        from .hybrid_search import HybridSearchEngine
        self.hybrid_engine = HybridSearchEngine(config, embedding_model, vector_store)
    
    def search_and_answer(self, question: str, max_results: int = 5) -> Dict[str, Any]:
        """Recherche hybride optimisée avec reformulation générale"""
        try:
            self.logger.info(f"🔍 Question: {question}")
            
            # 1. Reformulation intelligente de la question
            enriched_question = self._reformulate_to_legal_terms(question)
            
            # 2. Recherche avec la question enrichie
            question_embedding = self.embedding_model.encode(enriched_question)
            search_results = self.vector_store.search(
                query_vector=question_embedding,
                limit=20
            )
            
            # Ajouter le type de recherche
            for result in search_results:
                result['search_type'] = 'vector'
            
            if not search_results:
                return {
                    'answer': "Aucune information trouvée dans les textes juridiques.",
                    'sources': [],
                    'confidence': 0.0,
                    'search_results_count': 0
                }
            
            # 3. Regrouper les chunks par article
            grouped_results = self._group_chunks_by_article(search_results)
            
            # Prendre les meilleurs articles complets
            best_articles = list(grouped_results.values())[:max_results]
            flattened_results = []
            
            for article_chunks in best_articles:
                flattened_results.extend(article_chunks)
            
            # Debug : Afficher les chunks de l'article 184 s'il est présent
            self.logger.info("=== DEBUG CHUNKS ARTICLE 184 ===")
            for chunk in flattened_results[:10]:
                metadata = chunk['metadata']
                if '184' in str(metadata.get('article_number', '')):
                    self.logger.info(f"Article 184 chunk (score: {chunk['score']:.3f}): {chunk['text'][:100]}...")
            
            # 4. Générer réponse avec le contexte complet
            answer = self.llm.generate_optimized_response(
                original_question=question,  # Question originale de l'utilisateur
                legal_context=flattened_results[:10]  # Maximum 10 chunks
            )
            
            # Sources et confiance
            sources = self._extract_sources(flattened_results[:max_results])
            confidence = self._calculate_confidence(flattened_results)
            
            # Log des résultats pour debug
            self.logger.info(f"📊 Types de recherche utilisés:")
            for result in flattened_results[:5]:
                search_type = result.get('search_type', 'unknown')
                score = result.get('score', 0)
                article = result['metadata'].get('article_number', 'N/A')
                self.logger.info(f"   - {search_type}: Article {article} (score: {score:.3f})")
            
            return {
                'answer': answer,
                'sources': sources,
                'confidence': confidence,
                'search_results_count': len(search_results),
                'search_types': [r.get('search_type', 'unknown') for r in flattened_results[:5]]
            }
            
        except Exception as e:
            self.logger.error(f"Erreur recherche hybride: {e}")
            return {
                'answer': "Une erreur s'est produite lors de la recherche.",
                'sources': [],
                'confidence': 0.0,
                'search_results_count': 0
            }
    
    def _reformulate_to_legal_terms(self, question: str) -> str:
        """Reformulation intelligente générale pour toutes questions juridiques"""
        
        try:
            reformulation_prompt = f"""Tu es un expert en droit marocain. Reformule cette question de citoyen en utilisant les termes juridiques appropriés pour une recherche dans une base de données juridique.

QUESTION ORIGINALE: {question}

INSTRUCTIONS:
1. Identifie le domaine juridique (travail, pénal, commerce, route, procédure civile)
2. Remplace les termes courants par leurs équivalents juridiques
3. Ajoute les termes techniques pertinents
4. Garde la question compréhensible

EXEMPLES DE TRANSFORMATIONS:
- "combien d'heures puis-je travailler" → "durée normale travail hebdomadaire salariés activités non agricoles"
- "créer une entreprise" → "constitution société immatriculation registre commerce"
- "accident de voiture" → "accident circulation responsabilité dommages"
- "vol dans magasin" → "vol simple soustraction frauduleuse sanction"
- "licencier un employé" → "licenciement rupture contrat travail préavis"
- "divorce au Maroc" → "dissolution mariage procédure divorce"
- "permis de conduire étranger" → "permis conduire étranger reconnaissance"
- "amende excès vitesse" → "sanction infraction vitesse contravention"
- "plainte contre quelqu'un" → "action justice procédure plainte"
- "héritage après décès" → "succession héritage partage biens"

REFORMULATION (enrichie avec termes juridiques):"""

            response = self.model.generate_content(
                reformulation_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=150,
                    top_p=0.8
                )
            )
            
            enriched_question = response.text.strip()
            
            if enriched_question and len(enriched_question.split()) >= 3:
                self.logger.info(f"Question enrichie: {enriched_question}")
                return enriched_question
            else:
                return question
                
        except Exception as e:
            self.logger.error(f"Erreur reformulation: {e}")
            return question
    
    def _group_chunks_by_article(self, results: List[Dict]) -> Dict[str, List[Dict]]:
        """Regroupe les chunks par article et les trie par score"""
        grouped = {}
        
        for result in results:
            metadata = result['metadata']
            article_key = f"{metadata.get('code_source')}_{metadata.get('article_number')}"
            
            if article_key not in grouped:
                grouped[article_key] = []
            
            grouped[article_key].append(result)
        
        # Calculer le score moyen par article et trier les chunks
        article_scores = {}
        for article_key, chunks in grouped.items():
            # Trier les chunks par score décroissant
            chunks.sort(key=lambda x: x['score'], reverse=True)
            
            # Calculer le score moyen de l'article (pondéré par le meilleur chunk)
            best_score = chunks[0]['score']
            avg_score = sum(chunk['score'] for chunk in chunks) / len(chunks)
            article_scores[article_key] = best_score * 0.7 + avg_score * 0.3
        
        # Trier les articles par score décroissant
        sorted_article_keys = sorted(article_scores.keys(), 
                                   key=lambda k: article_scores[k], 
                                   reverse=True)
        
        # Retourner les chunks groupés par article, triés par pertinence
        return {key: grouped[key] for key in sorted_article_keys}
    
    def _extract_sources(self, results: List[Dict]) -> List[Dict]:
        """Extraire les informations des sources avec formatage amélioré"""
        sources = []
        seen_articles = set()  # Éviter les doublons d'articles
        
        for result in results:
            metadata = result['metadata']
            article_key = f"{metadata.get('code_source')}_{metadata.get('article_number')}"
            
            # Éviter les doublons d'articles
            if article_key in seen_articles:
                continue
            seen_articles.add(article_key)
            
            # Formatage du nom du code
            code_source = metadata.get('code_source', 'N/A')
            code_display = {
                'code_travail': 'Code du Travail',
                'code_penal': 'Code Pénal', 
                'code_commerce': 'Code de Commerce',
                'code_route': 'Code de la Route',
                'code_procedure_civile': 'Code de Procédure Civile'
            }.get(code_source, code_source)
            
            sources.append({
                'article_number': metadata.get('article_number', 'N/A'),
                'code_source': code_display,  # Nom formaté
                'relevance_score': round(result['score'], 3),
                'text_preview': result['text'][:150] + "..." if len(result['text']) > 150 else result['text'],
                'search_type': result.get('search_type', 'unknown')
            })
        
        return sources
    
    def _calculate_confidence(self, results: List[Dict]) -> float:
        """Calculer la confiance de la réponse"""
        if not results:
            return 0.0
        
        # Moyenne des scores de pertinence (prendre seulement les meilleurs chunks)
        top_results = results[:5]  # Top 5 chunks
        avg_score = sum(r['score'] for r in top_results) / len(top_results)
        
        # Ajuster selon le nombre de sources
        source_factor = min(len(results) / 3, 1.0)  # Optimal avec 3+ sources
        
        # Bonus pour recherche hybride
        hybrid_bonus = 1.1 if any(r.get('search_type') == 'hybrid' for r in results) else 1.0
        
        confidence = avg_score * source_factor * hybrid_bonus
        return round(min(confidence, 1.0), 3)  # Limiter à 1.0 max