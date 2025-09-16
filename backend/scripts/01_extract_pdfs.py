#!/usr/bin/env python3
"""
Script d'extraction des PDFs
============================
Extrait le texte de tous les PDFs des codes juridiques
"""

import sys
import logging
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from config import get_config
from processing.pdf_extractor import PDFExtractor

def setup_logging():
    """Configuration du logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/extraction.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """Fonction principale d'extraction"""
    print("EXTRACTION DES PDFS - LOIS MAROCAINES")
    print("=" * 50)
    
    # Configuration et logging
    setup_logging()
    config = get_config()
    
    print(f"Configuration: {config}")
    print()
    
    # Vérifier les PDFs disponibles
    available_pdfs = config.list_available_pdfs()
    if not available_pdfs:
        print("ERREUR: Aucun PDF trouvé dans data/raw_pdfs/")
        print("Assurez-vous d'avoir placé vos PDFs avec les noms:")
        for code_name in config.pdf.legal_codes.keys():
            print(f"  - {code_name}.pdf")
        return
    
    print(f"PDFs détectés: {len(available_pdfs)}")
    for pdf in available_pdfs:
        print(f"  - {pdf}.pdf")
    print()
    
    # Créer l'extracteur
    extractor = PDFExtractor(config)
    
    # Confirmer l'extraction
    response = input("Procéder à l'extraction? (o/n): ").lower().strip()
    if response not in ['o', 'oui', 'y', 'yes']:
        print("Extraction annulée.")
        return
    
    print("\nDémarrage de l'extraction...")
    print("-" * 30)
    
    # Extraire tous les PDFs
    results = extractor.extract_all_pdfs()
    
    # Afficher le résumé
    print("\n" + extractor.get_extraction_summary(results))
    
    # Vérifier les erreurs
    failed_extractions = [name for name, result in results.items() if not result.success]
    if failed_extractions:
        print(f"\nERREURS D'EXTRACTION ({len(failed_extractions)}):")
        for name in failed_extractions:
            print(f"  - {name}: {results[name].error_message}")
    
    print("\nExtraction terminée!")
    print(f"Fichiers texte sauvegardés dans: {config.pdf.extracted_text_dir}")

if __name__ == "__main__":
    main()