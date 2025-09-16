#!/usr/bin/env python3
"""
Script de parsing des articles juridiques
=========================================
Parse les textes extraits en articles structurés
"""

import sys
import logging
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from config import get_config
from processing.article_parser import ArticleParser

def setup_logging():
    """Configuration du logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/parsing.log'),
            logging.StreamHandler()
        ]
    )

def display_parsing_summary(results):
    """Afficher un résumé du parsing"""
    print("\nRÉSUMÉ DU PARSING")
    print("=" * 50)
    
    total_articles = sum(r.total_articles for r in results.values() if r.parsing_success)
    total_words = sum(r.total_words for r in results.values() if r.parsing_success)
    successful_codes = sum(1 for r in results.values() if r.parsing_success)
    
    print(f"Codes traités: {len(results)}")
    print(f"Parsing réussis: {successful_codes}")
    print(f"Articles extraits: {total_articles}")
    print(f"Mots totaux: {total_words:,}")
    print()
    
    print("DÉTAIL PAR CODE:")
    print("-" * 30)
    
    for code_name, result in sorted(results.items()):
        status = "✅" if result.parsing_success else "❌"
        print(f"{status} {code_name:<20}: {result.total_articles:>4} articles, {result.total_words:>8,} mots")
        
        if result.issues:
            print(f"    Issues: {len(result.issues)}")
            for issue in result.issues[:3]:  # Afficher max 3 issues
                print(f"      - {issue}")
            if len(result.issues) > 3:
                print(f"      ... et {len(result.issues) - 3} autres")
        print()

def main():
    """Fonction principale de parsing"""
    print("PARSING DES ARTICLES JURIDIQUES")
    print("=" * 50)
    
    # Configuration et logging
    setup_logging()
    config = get_config()
    
    # Vérifier que l'extraction a été faite
    extracted_dir = Path(config.pdf.extracted_text_dir)
    text_files = list(extracted_dir.glob("*.txt"))
    
    if not text_files:
        print(f"ERREUR: Aucun fichier texte trouvé dans {extracted_dir}")
        print("Exécutez d'abord le script 01_extract_pdfs.py")
        return
    
    print(f"Fichiers texte trouvés: {len(text_files)}")
    for text_file in text_files:
        print(f"  - {text_file.name}")
    print()
    
    # Créer le parser
    parser = ArticleParser(config)
    
    # Confirmer le parsing
    response = input("Procéder au parsing des articles? (o/n): ").lower().strip()
    if response not in ['o', 'oui', 'y', 'yes']:
        print("Parsing annulé.")
        return
    
    print("\nDémarrage du parsing...")
    print("-" * 30)
    
    # Parser tous les textes
    results = parser.parse_all_extracted_texts()
    
    # Afficher le résumé
    display_parsing_summary(results)
    
    # Vérifier les erreurs
    failed_parsing = [name for name, result in results.items() if not result.parsing_success]
    if failed_parsing:
        print(f"ÉCHECS DE PARSING ({len(failed_parsing)}):")
        for name in failed_parsing:
            print(f"  - {name}: {', '.join(results[name].issues)}")
    
    print("\nParsing terminé!")
    print(f"Articles structurés sauvegardés dans: {config.pdf.articles_dir}")

if __name__ == "__main__":
    main()