"""
Interface pour les modèles LLM avec génération optimisée
=======================================================
"""

import google.generativeai as genai
import os
from typing import List, Dict, Any
import logging

class LLMInterface:
    """Interface unifiée pour les LLM avec réponses optimisées"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.model = None
        self._setup_model()
    
    def _setup_model(self):
        """Configurer le modèle LLM"""
        if self.config.llm.provider == "google":
            self._setup_gemini()
        else:
            raise ValueError(f"Provider non supporté: {self.config.llm.provider}")
    
    def _setup_gemini(self):
        """Configurer Gemini"""
        api_key = os.getenv(self.config.llm.api_key_env)
        
        if not api_key:
            self.logger.error(f"Clé API manquante: {self.config.llm.api_key_env}")
            raise ValueError("Clé API Gemini requise")
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(self.config.llm.model_name)
            self.logger.info(f"Gemini configuré: {self.config.llm.model_name}")
            
        except Exception as e:
            self.logger.error(f"Erreur configuration Gemini: {e}")
            raise
    
    def generate_optimized_response(self, original_question: str, legal_context: List[Dict]) -> str:
        """Générer une réponse optimisée, courte et directe"""
        
        # Construire le contexte
        context = self._build_context(legal_context)
        
        # Créer le prompt optimisé
        prompt = self._create_optimized_prompt(original_question, context, legal_context)
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Plus déterministe
                    max_output_tokens=400,  # Plus court
                    top_p=0.8
                )
            )
            
            return response.text.strip()
            
        except Exception as e:
            self.logger.error(f"Erreur génération optimisée: {e}")
            return "Désolé, une erreur s'est produite lors de la génération de la réponse."
    
    def _create_optimized_prompt(self, question: str, context: str, legal_context: List[Dict]) -> str:
        """Créer un prompt optimisé pour des réponses courtes et précises"""
        
        # Extraire les sources pour la citation finale
        sources_info = []
        for item in legal_context[:3]:  # Max 3 sources
            metadata = item.get('metadata', {})
            article_num = metadata.get('article_number', 'N/A')
            code_source = metadata.get('code_source', 'N/A')
            
            # Formatage du nom du code
            code_display = {
                'code_travail': 'Code du Travail',
                'code_penal': 'Code Pénal', 
                'code_commerce': 'Code de Commerce',
                'code_route': 'Code de la Route',
                'code_procedure_civile': 'Code de Procédure Civile'
            }.get(code_source, code_source)
            
            sources_info.append(f"Article {article_num} - {code_display}")
        
        return f"""Tu es un assistant juridique expert en droit marocain qui donne des réponses PRÉCISES et COMPLÈTES.

QUESTION UTILISATEUR:
{question}

TEXTES JURIDIQUES DISPONIBLES:
{context}

INSTRUCTIONS CRITIQUES:
1. LIS ATTENTIVEMENT ET ENTIÈREMENT chaque texte juridique fourni
2. CHERCHE SPÉCIFIQUEMENT toutes les informations pertinentes à la question
3. Si la question porte sur les "heures de travail", cherche TOUTES les mentions de durées (journalières, hebdomadaires, annuelles)
4. MENTIONNE EXPLICITEMENT toutes les durées trouvées (ex: "44 heures par semaine" ET "2288 heures par an")
5. FAIS LES CALCULS nécessaires et EXPLIQUE-LES (ex: 2288 heures/an ÷ 52 semaines = 44h/semaine)
6. DISTINGUE les différents secteurs (agriculture vs non-agriculture) si mentionnés
7. Réponds en 2-3 phrases CLAIRES et DIRECTES
8. COMMENCE directement par la réponse (pas d'introduction)
9. Utilise un langage SIMPLE accessible au grand public
10. À la fin, ajoute: "Sources: {', '.join(sources_info)}"

EXEMPLES DE RÉPONSES ATTENDUES:
- "Au Maroc, vous pouvez travailler 44 heures par semaine maximum dans les activités non agricoles (2288 heures par an ÷ 52 = 44h/semaine). Pour l'agriculture, c'est 48 heures par semaine (2496 heures par an). Sources: Article 184 - Code du Travail"
- "La peine pour vol simple est de 1 à 5 ans d'emprisonnement et une amende de 120 à 1000 dirhams. Sources: Article 505 - Code Pénal"

ATTENTION SPÉCIALE:
- Si tu vois "2288 heures par année ou 44 heures par semaine", MENTIONNE LES DEUX
- Si tu vois des distinctions sectorielles, EXPLIQUE-LES CLAIREMENT
- Ne dis JAMAIS "les textes ne précisent pas" si l'information existe dans le contexte

RÉPONSE:"""
    
    def generate_response(self, prompt: str, context_chunks: List[Dict]) -> str:
        """Méthode de compatibilité - utilise la génération optimisée"""
        return self.generate_optimized_response(prompt, context_chunks)
    
    def _build_context(self, chunks: List[Dict]) -> str:
        """Construire le contexte à partir des chunks"""
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            metadata = chunk.get('metadata', {})
            text = chunk.get('text', '')
            
            article_num = metadata.get('article_number', 'N/A')
            code_source = metadata.get('code_source', 'N/A')
            
            context_parts.append(
                f"Article {article_num} ({code_source}):\n{text}\n"
            )
        
        return "\n".join(context_parts)
    
    def _create_legal_prompt(self, question: str, context: str) -> str:
        """Prompt de base (maintenu pour compatibilité)"""
        return f"""Tu es un assistant juridique spécialisé dans le droit marocain. 
Ta mission est de fournir des réponses claires et précises en français, basées uniquement sur les textes juridiques fournis.

QUESTION DE L'UTILISATEUR:
{question}

TEXTES JURIDIQUES PERTINENTS:
{context}

INSTRUCTIONS:
1. Réponds uniquement en français, même si la question est dans une autre langue
2. Base ta réponse exclusivement sur les textes juridiques fournis
3. Utilise un langage clair et accessible au grand public
4. Évite le jargon juridique complexe
5. Si les textes ne permettent pas de répondre, dis-le clairement
6. Cite les numéros d'articles utilisés à la fin de ta réponse
7. Structure ta réponse de manière logique et complète
8. Si tu dois faire un calcul simple, fais-le

RÉPONSE:"""