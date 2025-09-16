"""
Chunking intelligent des articles juridiques
============================================
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from langchain.text_splitter import RecursiveCharacterTextSplitter
import logging

@dataclass
class Chunk:
    """Représentation d'un chunk"""
    id: str
    text: str
    metadata: Dict[str, Any]
    token_count: int
    
    def to_dict(self) -> Dict:
        return asdict(self)

class IntelligentChunker:
    """Chunker intelligent pour articles juridiques"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Splitter configuré
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunking.chunk_size,
            chunk_overlap=self.config.chunking.chunk_overlap,
            length_function=len,
            separators=self.config.chunking.separators
        )
    
    def chunk_articles(self, articles_data: Dict) -> List[Chunk]:
        """Chunker les articles d'un code juridique"""
        code_name = articles_data['metadata']['code_name']
        articles = articles_data['articles']
        
        self.logger.info(f"Chunking {len(articles)} articles de {code_name}")
        
        chunks = []
        chunk_counter = 0
        
        for article in articles:
            article_chunks = self._chunk_single_article(article, code_name, chunk_counter)
            chunks.extend(article_chunks)
            chunk_counter += len(article_chunks)
        
        self.logger.info(f"Créé {len(chunks)} chunks pour {code_name}")
        return chunks
    
    def _chunk_single_article(self, article: Dict, code_name: str, start_id: int) -> List[Chunk]:
        """Chunker un article individuel"""
        content = article['content']
        article_number = article['number']
        
        # Articles courts : un seul chunk
        if len(content) <= self.config.chunking.chunk_size:
            chunk = Chunk(
                id=f"{code_name}_art{article_number}_chunk1",
                text=content,
                metadata={
                    'article_number': article_number,
                    'code_source': code_name,
                    'chunk_index': 0,
                    'total_chunks': 1,
                    'is_complete_article': True
                },
                token_count=len(content.split())
            )
            return [chunk]
        
        # Articles longs : découpage intelligent
        text_chunks = self.text_splitter.split_text(content)
        chunks = []
        
        for i, chunk_text in enumerate(text_chunks):
            chunk = Chunk(
                id=f"{code_name}_art{article_number}_chunk{i+1}",
                text=chunk_text,
                metadata={
                    'article_number': article_number,
                    'code_source': code_name,
                    'chunk_index': i,
                    'total_chunks': len(text_chunks),
                    'is_complete_article': False
                },
                token_count=len(chunk_text.split())
            )
            chunks.append(chunk)
        
        return chunks
    
    def process_all_articles(self) -> Dict[str, List[Chunk]]:
        """Traiter tous les articles disponibles"""
        results = {}
        articles_dir = Path(self.config.pdf.articles_dir)
        
        for json_file in articles_dir.glob("*.json"):
            code_name = json_file.stem
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    articles_data = json.load(f)
                
                chunks = self.chunk_articles(articles_data)
                results[code_name] = chunks
                
                # Sauvegarder les chunks
                self._save_chunks(chunks, code_name)
                
            except Exception as e:
                self.logger.error(f"Erreur chunking {code_name}: {e}")
                results[code_name] = []
        
        return results
    
    def _save_chunks(self, chunks: List[Chunk], code_name: str):
        """Sauvegarder les chunks"""
        output_path = Path(self.config.root_dir / "data/processed/chunks" / f"{code_name}_chunks.json")
        
        try:
            data = {
                'metadata': {
                    'code_name': code_name,
                    'total_chunks': len(chunks),
                    'chunking_config': {
                        'chunk_size': self.config.chunking.chunk_size,
                        'chunk_overlap': self.config.chunking.chunk_overlap
                    }
                },
                'chunks': [chunk.to_dict() for chunk in chunks]
            }
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Chunks sauvegardés: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde chunks {code_name}: {e}")