// types/chat.ts - Version complète et à jour
export interface Article {
  article_number: string;
  code_source: string;
  content: string;
  relevance_score: number;
}

export interface Message {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
  language?: string;
  articles?: Article[];
  apiResponse?: ChatResponse; // Pour stocker la réponse complète de l'API
}

export interface ChatResponse {
  answer: string;
  articles_used: Article[];
  relevant_articles: string[];    // ✅ NOUVEAU : Numéros d'articles référencés
  language_detected: string;
  sources_used: number;           // ✅ NOUVEAU : Nombre de sources utilisées
  simple_explanation?: string;    // Optionnel : explication simplifiée
  query_time: number;            // Temps de traitement en secondes
  timestamp: string;             // Timestamp ISO de la réponse
}

export interface ChatRequest {
  question: string;
  language: 'fr' | 'ar' | 'auto';
  simple_explanation?: boolean;   // ✅ Rendu optionnel (plus utilisé dans la v2)
  max_articles?: number;
}

export type Language = 'fr' | 'ar' | 'auto';

// ✅ NOUVEAU : Interface pour l'état du chat
export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error?: string;
  language: Language;
}

// ✅ NOUVEAU : Interface pour les statistiques de l'API
export interface ApiStats {
  total_chunks: number;
  collection_name: string;
  embedding_model: string;
  supported_languages: string[];
  codes_available: string[];
  version: string;
  features: string[];
}

// ✅ NOUVEAU : Interface pour le health check
export interface HealthStatus {
  api: string;
  chromadb: string;
  embedding_model: string;
  gemini: string;
  timestamp: string;
  error?: string;
}