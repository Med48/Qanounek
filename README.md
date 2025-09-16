# Qanounek - Système RAG de Consultation Juridique Marocaine

## Description
Qanounek est un système de questions-réponses intelligent basé sur l'architecture RAG (Retrieval-Augmented Generation) pour consulter les lois marocaines. Le système permet aux citoyens de poser des questions en langage naturel (français/arabe) et d'obtenir des réponses précises avec citations d'articles juridiques.

## Fonctionnalités principales
- **Consultation multilingue** : Questions en français et arabe
- **Reformulation intelligente** : Transformation automatique des questions en langage naturel vers des termes juridiques
- **Recherche hybride** : Combinaison de recherche vectorielle et par mots-clés (BM25)
- **Citations précises** : Références exactes aux articles de loi avec sources
- **Interface utilisateur** : Interface web intuitive pour les non-juristes

## Codes juridiques couverts
- Code du Travail
- Code Pénal
- Code de Commerce
- Code de la Route
- Code de Procédure Civile

### Stack technologique
- **Backend** : FastAPI (Python)
- **Base vectorielle** : Qdrant
- **Embeddings** : SentenceTransformers (`paraphrase-multilingual-MiniLM-L12-v2`)
- **LLM** : Google Gemini 1.5 Flash
- **Recherche hybride** : Vectorielle + BM25

### Workflow
1. **Préprocessing** : Extraction et chunking des textes juridiques
2. **Vectorisation** : Génération d'embeddings multilingues
3. **Indexation** : Stockage dans Qdrant + index BM25
4. **Recherche** : Reformulation + recherche hybride
5. **Génération** : Réponse contextuelle avec Gemini

## Contact
Mohammed RHOUATI - mohamedrhouati0@gmail.com