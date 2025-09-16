"""
Extraction robuste de texte depuis les PDFs
==========================================
"""

import fitz  # PyMuPDF
import re
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass
import logging

@dataclass
class ExtractionResult:
    """Résultat de l'extraction d'un PDF"""
    code_name: str
    total_pages: int
    extracted_text: str
    text_length: int
    success: bool
    error_message: Optional[str] = None

class PDFExtractor:
    """Extracteur de texte PDF robuste et optimisé"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def extract_text_from_pdf(self, pdf_path: Path, code_name: str) -> ExtractionResult:
        """
        Extraire le texte d'un PDF avec gestion d'erreurs robuste
        """
        self.logger.info(f"Extraction PDF: {pdf_path.name}")
        
        try:
            # Vérifier que le fichier existe
            if not pdf_path.exists():
                return ExtractionResult(
                    code_name=code_name,
                    total_pages=0,
                    extracted_text="",
                    text_length=0,
                    success=False,
                    error_message=f"Fichier non trouvé: {pdf_path}"
                )
            
            # Ouvrir le PDF
            doc = fitz.open(str(pdf_path))
            
            if doc.is_encrypted:
                self.logger.warning(f"PDF chiffré détecté: {pdf_path.name}")
                # Essayer de déchiffrer avec mot de passe vide
                if not doc.authenticate(""):
                    doc.close()
                    return ExtractionResult(
                        code_name=code_name,
                        total_pages=0,
                        extracted_text="",
                        text_length=0,
                        success=False,
                        error_message="PDF protégé par mot de passe"
                    )
            
            extracted_text = ""
            total_pages = doc.page_count
            
            self.logger.info(f"Traitement de {total_pages} pages...")
            
            for page_num in range(total_pages):
                try:
                    page = doc[page_num]
                    
                    # Extraire le texte de la page
                    page_text = page.get_text()
                    
                    # Nettoyage basique du texte
                    cleaned_text = self._clean_page_text(page_text, page_num + 1)
                    
                    if cleaned_text.strip():  # Ignorer les pages vides
                        extracted_text += f"\n\n--- PAGE {page_num + 1} ---\n{cleaned_text}"
                    
                    # Log de progression tous les 50 pages
                    if (page_num + 1) % 50 == 0:
                        self.logger.info(f"  Progression: {page_num + 1}/{total_pages} pages")
                
                except Exception as e:
                    self.logger.warning(f"Erreur page {page_num + 1}: {e}")
                    continue
            
            doc.close()
            
            # Post-traitement du texte complet
            final_text = self._post_process_text(extracted_text, code_name)
            
            result = ExtractionResult(
                code_name=code_name,
                total_pages=total_pages,
                extracted_text=final_text,
                text_length=len(final_text),
                success=True
            )
            
            self.logger.info(f"Extraction réussie: {len(final_text)} caractères")
            return result
            
        except Exception as e:
            self.logger.error(f"Erreur extraction {pdf_path.name}: {e}")
            return ExtractionResult(
                code_name=code_name,
                total_pages=0,
                extracted_text="",
                text_length=0,
                success=False,
                error_message=str(e)
            )
    
    def _clean_page_text(self, text: str, page_num: int) -> str:
        """Nettoyer le texte d'une page"""
        if not text:
            return ""
        
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text)
        
        # Supprimer les caractères de contrôle
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Supprimer les numéros de page en début/fin si détectés
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*Page\s+\d+\s*$', '', text, flags=re.MULTILINE)
        
        # Supprimer les lignes très courtes (probablement des artefacts)
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Garder les lignes avec du contenu substantiel
            if len(line) > 3 and not re.match(r'^\d+$', line):
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def _post_process_text(self, text: str, code_name: str) -> str:
        """Post-traitement du texte complet"""
        
        # Supprimer les marqueurs de page
        text = re.sub(r'\n--- PAGE \d+ ---\n', '\n\n', text)
        
        # Normaliser les espaces multiples
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        # Corrections spécifiques selon le code
        if code_name == "code_route":
            # Le code de la route peut avoir des numérotations spéciales
            text = self._fix_road_code_formatting(text)
        elif code_name == "code_penal":
            # Corrections spécifiques au code pénal
            text = self._fix_penal_code_formatting(text)
        
        # Nettoyage final
        text = text.strip()
        
        return text
    
    def _fix_road_code_formatting(self, text: str) -> str:
        """Corrections spécifiques au code de la route"""
        # Corriger les numérotations cassées
        text = re.sub(r'(\d+)\s*\)\s*([A-Z])', r'\1) \2', text)
        
        # Corriger les articles mal formatés
        text = re.sub(r'Article\s*(\d+)\s*[-–]\s*', r'Article \1 - ', text)
        
        return text
    
    def _fix_penal_code_formatting(self, text: str) -> str:
        """Corrections spécifiques au code pénal"""
        # Corriger les références d'articles
        text = re.sub(r'articles?\s*(\d+)', r'article \1', text, flags=re.IGNORECASE)
        
        return text
    
    def extract_all_pdfs(self) -> Dict[str, ExtractionResult]:
        """Extraire tous les PDFs disponibles"""
        results = {}
        available_pdfs = self.config.list_available_pdfs()
        
        if not available_pdfs:
            self.logger.warning("Aucun PDF trouvé dans le répertoire raw_pdfs")
            return results
        
        self.logger.info(f"Extraction de {len(available_pdfs)} PDFs...")
        
        for code_name in available_pdfs:
            pdf_path = self.config.get_pdf_path(code_name)
            result = self.extract_text_from_pdf(pdf_path, code_name)
            results[code_name] = result
            
            # Sauvegarder le texte extrait
            if result.success:
                output_path = self.config.get_extracted_text_path(code_name)
                self._save_extracted_text(result.extracted_text, output_path)
        
        return results
    
    def _save_extracted_text(self, text: str, output_path: Path):
        """Sauvegarder le texte extrait"""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            self.logger.info(f"Texte sauvegardé: {output_path}")
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde {output_path}: {e}")
    
    def get_extraction_summary(self, results: Dict[str, ExtractionResult]) -> str:
        """Générer un résumé des extractions"""
        summary = "RÉSUMÉ EXTRACTION PDF\n"
        summary += "=" * 50 + "\n\n"
        
        total_success = sum(1 for r in results.values() if r.success)
        total_pages = sum(r.total_pages for r in results.values())
        total_chars = sum(r.text_length for r in results.values())
        
        summary += f"PDFs traités: {len(results)}\n"
        summary += f"Extractions réussies: {total_success}\n"
        summary += f"Pages totales: {total_pages}\n"
        summary += f"Caractères extraits: {total_chars:,}\n\n"
        
        summary += "DÉTAIL PAR CODE:\n"
        summary += "-" * 30 + "\n"
        
        for code_name, result in results.items():
            status = "✅" if result.success else "❌"
            summary += f"{status} {result.code_name:<20}: "
            summary += f"{result.total_pages:>3} pages, {result.text_length:>8,} chars\n"
            
            if not result.success:
                summary += f"    Erreur: {result.error_message}\n"
        
        return summary