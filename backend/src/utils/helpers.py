"""
Fonctions utilitaires pour le système RAG
=========================================
"""

import re
from typing import List, Dict, Any
from pathlib import Path
import json

def clean_legal_text(text: str) -> str:
    """Nettoyer un texte juridique"""
    # Normaliser les espaces
    text = re.sub(r'\s+', ' ', text)
    
    # Supprimer les caractères de contrôle
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    # Corriger la ponctuation
    text = re.sub(r'\s+([,.;:])', r'\1', text)
    text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', text)
    
    return text.strip()

def extract_article_numbers(text: str) -> List[str]:
    """Extraire les numéros d'articles d'un texte"""
    pattern = r'[Aa]rticle\s+(\d+)'
    matches = re.findall(pattern, text)
    return list(set(matches))  # Dédupliquer

def validate_chunk_quality(chunk_text: str) -> float:
    """Évaluer la qualité d'un chunk (0-1)"""
    score = 1.0
    
    # Longueur appropriée
    if len(chunk_text) < 50:
        score -= 0.3
    
    # Ratio de caractères alphabétiques
    alpha_ratio = sum(c.isalpha() for c in chunk_text) / len(chunk_text)
    if alpha_ratio < 0.6:
        score -= 0.2
    
    # Présence de mots juridiques typiques
    legal_words = ['article', 'loi', 'code', 'droit', 'juridique']
    if any(word in chunk_text.lower() for word in legal_words):
        score += 0.1
    
    return max(0.0, min(1.0, score))

def save_processing_log(stage: str, results: Dict[str, Any], log_dir: str = "logs"):
    """Sauvegarder un log de traitement"""
    log_path = Path(log_dir) / f"{stage}_log.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)