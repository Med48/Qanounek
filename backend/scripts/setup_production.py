#!/usr/bin/env python3
"""
Script de mise en production complète
====================================
Exécute tous les scripts dans l'ordre correct
"""

import sys
import subprocess
import logging
from pathlib import Path
import time

def run_script(script_path: str, description: str) -> bool:
    """Exécuter un script et retourner le succès"""
    print(f"\n{'='*60}")
    print(f"ÉTAPE: {description}")
    print(f"Script: {script_path}")
    print('='*60)
    
    try:
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=False, 
                              text=True, 
                              cwd=Path(__file__).parent.parent)
        
        if result.returncode == 0:
            print(f"✅ {description} - SUCCÈS")
            return True
        else:
            print(f"❌ {description} - ÉCHEC (code: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ {description} - ERREUR: {e}")
        return False

def main():
    """Processus de mise en production complète"""
    print("MISE EN PRODUCTION DU SYSTÈME RAG - LOIS MAROCAINES")
    print("="*70)
    
    start_time = time.time()
    
    # Vérifier les prérequis
    print("\nVérification des prérequis...")
    
    # Vérifier les PDFs
    pdf_dir = Path("data/raw_pdfs")
    if not pdf_dir.exists() or not list(pdf_dir.glob("*.pdf")):
        print("❌ ERREUR: Placez vos PDFs dans data/raw_pdfs/")
        print("Fichiers requis:")
        print("  - code_penal.pdf")
        print("  - code_travail.pdf")
        print("  - code_commerce.pdf")
        print("  - code_procedure_civile.pdf")
        print("  - code_route.pdf")
        return
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    print(f"✅ {len(pdf_files)} PDFs trouvés")
    
    # Vérifier le fichier .env
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ ERREUR: Créez le fichier .env avec votre clé GEMINI_API_KEY")
        return
    
    print("✅ Fichier .env présent")
    
    # Confirmer le démarrage
    response = input(f"\nDémarrer la mise en production complète? (o/n): ").lower().strip()
    if response not in ['o', 'oui', 'y', 'yes']:
        print("Mise en production annulée.")
        return
    
    # Séquence des scripts
    scripts = [
        ("scripts/01_extract_pdfs.py", "Extraction des PDFs"),
        ("scripts/02_parse_articles.py", "Parsing des articles"),
        ("scripts/03_create_chunks.py", "Création des chunks"),
        ("scripts/04_create_embeddings.py", "Génération des embeddings"),
        ("scripts/05_test_system.py", "Test du système")
    ]
    
    # Exécuter tous les scripts
    success_count = 0
    for script_path, description in scripts:
        success = run_script(script_path, description)
        if success:
            success_count += 1
        else:
            print(f"\n❌ ARRÊT: Échec à l'étape '{description}'")
            break
        
        # Pause entre les étapes
        time.sleep(2)
    
    # Résumé final
    total_time = time.time() - start_time
    
    print(f"\n{'='*70}")
    print("RÉSUMÉ DE LA MISE EN PRODUCTION")
    print('='*70)
    print(f"Étapes complétées: {success_count}/{len(scripts)}")
    print(f"Temps total: {total_time/60:.1f} minutes")
    
    if success_count == len(scripts):
        print("\n🎉 MISE EN PRODUCTION RÉUSSIE!")
        print("\nVotre système RAG est opérationnel.")
        print("\nPour démarrer l'API:")
        print("  python src/api/main.py")
        print("\nOu:")
        print("  uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload")
        
    else:
        print(f"\n❌ MISE EN PRODUCTION INCOMPLÈTE")
        print("Corrigez les erreurs et relancez le script.")

if __name__ == "__main__":
    main()