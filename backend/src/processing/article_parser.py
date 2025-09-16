"""
Parser d'articles juridiques
============================
Parse et structure les articles juridiques depuis le texte extrait
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

@dataclass
class Article:
    """Représentation d'un article juridique"""
    number: str
    content: str
    code_source: str
    word_count: int
    char_count: int
    extraction_confidence: float = 1.0
    
    def to_dict(self) -> Dict:
        """Convertir en dictionnaire"""
        return asdict(self)

@dataclass
class ParsingResult:
    """Résultat du parsing d'un code juridique"""
    code_name: str
    articles: List[Article]
    total_articles: int
    total_words: int
    parsing_success: bool
    issues: List[str]

class ArticleParser:
    """Parser robuste pour extraire les articles juridiques"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Patterns de détection par code
        self.patterns = {
            'default': r'Article\s+(\d+)(?:\s*[-–—.]\s*)?(.+?)(?=Article\s+\d+|$)',
            'code_penal': r'Article\s+(\d+)(?:\s*[-–—.]\s*)?(.+?)(?=Article\s+\d+|$)',
            'code_travail': r'Article\s+(\d+)(?:\s*[-–—.]\s*)?(.+?)(?=Article\s+\d+|$)',
            'code_commerce': r'Article\s+(\d+)(?:\s*[-–—.]\s*)?(.+?)(?=Article\s+\d+|$)',
            'code_route': r'Article\s+(\d+)(?:\s*[-–—.]\s*)?(.+?)(?=Article\s+\d+|$)',
            'code_procedure_civile': r'Article\s+(\d+)(?:\s*[-–—.]\s*)?(.+?)(?=Article\s+\d+|$)'
        }
    
    def parse_text_to_articles(self, text: str, code_name: str) -> ParsingResult:
        """Parser le texte en articles structurés"""
        self.logger.info(f"Parsing des articles pour {code_name}")
        
        issues = []
        articles = []
        
        # Prétraitement du texte
        preprocessed_text = self._preprocess_text(text, code_name)
        
        # Choisir le pattern approprié
        pattern = self.patterns.get(code_name, self.patterns['default'])
        
        # Extraction avec regex
        raw_matches = re.findall(pattern, preprocessed_text, re.DOTALL | re.IGNORECASE)
        
        self.logger.info(f"Matches bruts trouvés: {len(raw_matches)}")
        
        if not raw_matches:
            issues.append("Aucun article détecté avec le pattern standard")
            # Essayer des patterns alternatifs
            raw_matches = self._try_alternative_patterns(preprocessed_text, code_name)
        
        # Traiter chaque match
        for article_num, content in raw_matches:
            article = self._process_article(article_num, content, code_name)
            if article:
                articles.append(article)
            else:
                issues.append(f"Article {article_num} ignoré (contenu insuffisant)")
        
        # Validation et nettoyage
        articles = self._validate_and_clean_articles(articles, code_name)
        
        # Statistiques
        total_words = sum(article.word_count for article in articles)
        
        result = ParsingResult(
            code_name=code_name,
            articles=articles,
            total_articles=len(articles),
            total_words=total_words,
            parsing_success=len(articles) > 0,
            issues=issues
        )
        
        self.logger.info(f"Parsing terminé: {len(articles)} articles extraits")
        
        return result
    
    def _preprocess_text(self, text: str, code_name: str) -> str:
        """Prétraitement du texte avant parsing"""
        
        # Normaliser les espaces et sauts de ligne
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Corriger les patterns d'articles cassés
        text = re.sub(r'Article\s*(\d+)\s*[-–—]\s*', r'Article \1 - ', text)
        text = re.sub(r'Article\s+(\d+)\s*[.]\s*', r'Article \1. ', text)
        
        # Corrections spécifiques par code
        if code_name == "code_route":
            text = self._preprocess_code_route(text)
        elif code_name == "code_penal":
            text = self._preprocess_code_penal(text)
        elif code_name == "code_commerce":
            text = self._preprocess_code_commerce(text)
        
        return text
    
    def _preprocess_code_route(self, text: str) -> str:
        """Prétraitement spécifique au code de la route"""
        # Corriger les numérotations spéciales
        text = re.sub(r'(\d+)\s*°\s*', r'\1° ', text)
        return text
    
    def _preprocess_code_penal(self, text: str) -> str:
        """Prétraitement spécifique au code pénal"""
        # Corriger les références croisées
        text = re.sub(r'articles?\s+(\d+)', r'article \1', text, flags=re.IGNORECASE)
        return text
    
    def _preprocess_code_commerce(self, text: str) -> str:
        """Prétraitement spécifique au code de commerce"""
        # Corriger les numérotations commerciales
        text = re.sub(r'art\.\s*(\d+)', r'Article \1', text, flags=re.IGNORECASE)
        return text
    
    def _try_alternative_patterns(self, text: str, code_name: str) -> List[Tuple[str, str]]:
        """Essayer des patterns alternatifs si le pattern principal échoue"""
        
        alternative_patterns = [
            r'Art\.\s*(\d+)(?:\s*[-–—.]\s*)?(.+?)(?=Art\.\s*\d+|$)',
            r'(\d+)\s*[-–—.]\s*(.+?)(?=\d+\s*[-–—.]|$)',
            r'Article\s+premier\s*[-–—.]?\s*(.+?)(?=Article\s+2|$)',  # Article premier
        ]
        
        for pattern in alternative_patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            if matches:
                self.logger.info(f"Pattern alternatif réussi: {len(matches)} matches")
                return matches
        
        return []
    
    def _process_article(self, article_num: str, content: str, code_name: str) -> Optional[Article]:
        """Traiter un article individuel"""
        
        # Nettoyer le contenu
        content = content.strip()
        content = re.sub(r'\s+', ' ', content)
        
        # Filtrer les contenus trop courts ou suspects
        if len(content) < 20:
            return None
        
        # Supprimer les artefacts communs
        content = self._clean_article_content(content)
        
        # Calculer les métriques
        word_count = len(content.split())
        char_count = len(content)
        
        # Calculer la confiance d'extraction
        confidence = self._calculate_extraction_confidence(content, article_num)
        
        # Filtrer les articles de faible confiance
        if confidence < 0.3:
            return None
        
        return Article(
            number=article_num,
            content=content,
            code_source=code_name,
            word_count=word_count,
            char_count=char_count,
            extraction_confidence=confidence
        )
    
    def _clean_article_content(self, content: str) -> str:
        """Nettoyer le contenu d'un article"""
        
        # Supprimer les références de pages
        content = re.sub(r'page\s+\d+', '', content, flags=re.IGNORECASE)
        content = re.sub(r'^\s*\d+\s*$', '', content, flags=re.MULTILINE)
        
        # Supprimer les lignes très courtes
        lines = content.split('\n')
        cleaned_lines = [line.strip() for line in lines if len(line.strip()) > 3]
        content = ' '.join(cleaned_lines)
        
        # Normaliser la ponctuation
        content = re.sub(r'\s+([,.;:])', r'\1', content)
        content = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', content)
        
        return content.strip()
    
    def _calculate_extraction_confidence(self, content: str, article_num: str) -> float:
        """Calculer la confiance d'extraction d'un article"""
        confidence = 1.0
        
        # Pénaliser les contenus très courts
        if len(content) < 50:
            confidence -= 0.3
        
        # Pénaliser les contenus avec trop de caractères non-alphabétiques
        alpha_ratio = sum(c.isalpha() for c in content) / len(content)
        if alpha_ratio < 0.6:
            confidence -= 0.2
        
        # Bonus pour les structures typiques d'articles juridiques
        if re.search(r'\b(est|sont|peut|doit|sera|seront)\b', content, re.IGNORECASE):
            confidence += 0.1
        
        # Pénaliser les contenus suspects (tableaux, listes, etc.)
        if content.count('\t') > 5 or content.count('|') > 3:
            confidence -= 0.3
        
        return max(0.0, min(1.0, confidence))
    
    def _validate_and_clean_articles(self, articles: List[Article], code_name: str) -> List[Article]:
        """Valider et nettoyer la liste des articles"""
        
        # Trier par numéro d'article
        def sort_key(article):
            try:
                return int(article.number)
            except ValueError:
                return 99999  # Mettre les articles non-numériques à la fin
        
        articles.sort(key=sort_key)
        
        # Supprimer les doublons
        seen_numbers = set()
        unique_articles = []
        
        for article in articles:
            if article.number not in seen_numbers:
                unique_articles.append(article)
                seen_numbers.add(article.number)
            else:
                self.logger.warning(f"Article {article.number} dupliqué - ignoré")
        
        # Vérifier la continuité des numéros
        self._check_article_continuity(unique_articles, code_name)
        
        return unique_articles
    
    def _check_article_continuity(self, articles: List[Article], code_name: str):
        """Vérifier la continuité des numéros d'articles"""
        
        numeric_articles = []
        for article in articles:
            try:
                numeric_articles.append(int(article.number))
            except ValueError:
                continue
        
        if len(numeric_articles) < 2:
            return
        
        numeric_articles.sort()
        gaps = []
        
        for i in range(1, len(numeric_articles)):
            if numeric_articles[i] - numeric_articles[i-1] > 1:
                start = numeric_articles[i-1] + 1
                end = numeric_articles[i] - 1
                if end - start < 10:  # Ne signaler que les petits gaps
                    gaps.append(f"{start}-{end}")
        
        if gaps:
            self.logger.warning(f"Gaps détectés dans {code_name}: {', '.join(gaps)}")
    
    def save_articles(self, result: ParsingResult, output_path: Path):
        """Sauvegarder les articles parsés"""
        
        try:
            # Préparer les données pour JSON
            data = {
                'metadata': {
                    'code_name': result.code_name,
                    'total_articles': result.total_articles,
                    'total_words': result.total_words,
                    'parsing_success': result.parsing_success,
                    'issues': result.issues,
                    'extraction_date': str(Path().absolute())
                },
                'articles': [article.to_dict() for article in result.articles]
            }
            
            # Créer le répertoire si nécessaire
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Sauvegarder
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Articles sauvegardés: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde {output_path}: {e}")
    
    def parse_all_extracted_texts(self) -> Dict[str, ParsingResult]:
        """Parser tous les textes extraits disponibles"""
        
        results = {}
        extracted_dir = Path(self.config.pdf.extracted_text_dir)
        
        for text_file in extracted_dir.glob("*.txt"):
            code_name = text_file.stem
            
            self.logger.info(f"Parsing {code_name}...")
            
            try:
                # Lire le texte
                with open(text_file, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                # Parser
                result = self.parse_text_to_articles(text, code_name)
                results[code_name] = result
                
                # Sauvegarder
                output_path = self.config.get_articles_path(code_name)
                self.save_articles(result, output_path)
                
            except Exception as e:
                self.logger.error(f"Erreur parsing {code_name}: {e}")
                results[code_name] = ParsingResult(
                    code_name=code_name,
                    articles=[],
                    total_articles=0,
                    total_words=0,
                    parsing_success=False,
                    issues=[str(e)]
                )
        
        return results