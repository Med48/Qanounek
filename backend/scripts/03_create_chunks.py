#!/usr/bin/env python3
"""
Script de création des chunks
=============================
"""

import sys
import logging
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))

from config import get_config
from processing.chunker import IntelligentChunker

def main():
    """Fonction principale de chunking"""
    print("CRÉATION DES CHUNKS")
    print("=" * 50)
    
    logging.basicConfig(level=logging.INFO)
    config = get_config()
    
    # Vérifier les articles disponibles
    articles_dir = Path(config.pdf.articles_dir)
    json_files = list(articles_dir.glob("*.json"))
    
    if not json_files:
        print(f"ERREUR: Aucun fichier d'articles trouvé dans {articles_dir}")
        print("Exécutez d'abord le script 02_parse_articles.py")
        return
    
    print(f"Fichiers d'articles: {len(json_files)}")
    for file in json_files:
        print(f"  - {file.name}")
    
    # Créer le chunker
    chunker = IntelligentChunker(config)
    
    # Confirmer
    response = input("\nProcéder au chunking? (o/n): ").lower().strip()
    if response not in ['o', 'oui', 'y', 'yes']:
        print("Chunking annulé.")
        return
    
    print("\nDémarrage du chunking...")
    print("-" * 30)
    
    # Traiter tous les articles
    results = chunker.process_all_articles()
    
    # Résumé
    total_chunks = sum(len(chunks) for chunks in results.values())
    print(f"\nChunking terminé!")
    print(f"Total chunks créés: {total_chunks}")
    
    for code_name, chunks in results.items():
        print(f"  {code_name}: {len(chunks)} chunks")

if __name__ == "__main__":
    main()