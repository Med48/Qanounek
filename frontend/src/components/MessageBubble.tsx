import React, { useState } from 'react';
import { Message } from '../types/chat';
import { FileText, MessageSquare, Scale, BookOpen, ChevronDown, ChevronUp } from 'lucide-react';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.type === 'user';
  const isRTL = message.language === 'ar';
  const [showArticleDetails, setShowArticleDetails] = useState(false);

  // Fonction pour extraire la réponse principale et les références
  const parseResponse = (content: string) => {
    const parts = content.split(/(?:Articles? de référence|المواد المرجعية):/);
    const mainAnswer = parts[0].trim();
    const articleRefs = parts[1]?.trim();
    return { mainAnswer, articleRefs };
  };

  const { mainAnswer, articleRefs } = !isUser ? parseResponse(message.content) : { mainAnswer: message.content, articleRefs: null };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
      <div
        className={`max-w-xs md:max-w-md lg:max-w-2xl ${
          isUser
            ? 'bg-red-600 text-white px-4 py-3 rounded-2xl shadow-sm'
            : 'space-y-4'
        } ${isRTL ? 'text-right' : 'text-left'}`}
        dir={isRTL ? 'rtl' : 'ltr'}
      >
        {isUser ? (
          // Message utilisateur (inchangé)
          <>
            <p className="text-sm md:text-base leading-relaxed whitespace-pre-wrap">
              {message.content}
            </p>
            <p className="text-xs mt-2 opacity-70 text-red-100">
              {message.timestamp.toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit'
              })}
            </p>
          </>
        ) : (
          // Message assistant (nouvelle mise en page)
          <>
            {/* Réponse principale */}
            <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-r-lg">
              <div className="flex items-start space-x-3">
                <MessageSquare className="text-blue-600 mt-1 flex-shrink-0" size={20} />
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-blue-900 mb-2">
                    {isRTL ? "الإجابة" : "Réponse"}
                  </h3>
                  <div className="text-gray-800 leading-relaxed whitespace-pre-line">
                    {mainAnswer}
                  </div>
                </div>
              </div>
            </div>

            {/* Références d'articles */}
            {(articleRefs || (message.apiResponse?.relevant_articles && message.apiResponse.relevant_articles.length > 0)) && (
              <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-lg">
                <div className="flex items-start space-x-3">
                  <Scale className="text-amber-600 mt-1 flex-shrink-0" size={20} />
                  <div className="flex-1">
                    <h4 className="font-semibold text-amber-900 mb-2">
                      {isRTL ? "المواد القانونية المرجعية" : "Articles juridiques de référence"}
                    </h4>
                    <div className="text-amber-800">
                      {articleRefs || (message.apiResponse?.relevant_articles?.join(", ") || "")}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Info sur les sources */}
            {message.apiResponse?.sources_used && (
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 text-sm text-gray-600">
                  <BookOpen size={16} />
                  <span>
                    {isRTL 
                      ? `تم الاستناد إلى ${message.apiResponse.sources_used} مصادر قانونية`
                      : `Basé sur ${message.apiResponse.sources_used} sources juridiques`
                    }
                  </span>
                </div>
                
                {/* Temps de réponse */}
                {message.apiResponse?.query_time && (
                  <div className="text-xs text-gray-400">
                    ⏱️ {message.apiResponse.query_time.toFixed(2)}s
                  </div>
                )}
              </div>
            )}

            {/* Détails des articles (optionnel, collapsible) */}
            {message.articles && message.articles.length > 0 && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg">
                <button
                  onClick={() => setShowArticleDetails(!showArticleDetails)}
                  className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center space-x-2 text-sm text-gray-700">
                    <FileText size={16} />
                    <span>
                      {isRTL 
                        ? `عرض تفاصيل المصادر (${message.articles.length})`
                        : `Voir les détails des sources (${message.articles.length})`
                      }
                    </span>
                  </div>
                  {showArticleDetails ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>
                
                {showArticleDetails && (
                  <div className="px-4 pb-4 space-y-3 border-t border-gray-200">
                    {message.articles.map((article, index) => (
                      <div key={index} className="bg-white p-3 rounded-lg border border-gray-100">
                        <div className="flex items-center justify-between mb-2">
                          <div className="font-medium text-gray-700">
                            📄 Article {article.article_number}
                          </div>
                          {article.relevance_score !== undefined && (
                            <div className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full">
                              {(article.relevance_score * 100).toFixed(0)}% pertinent
                            </div>
                          )}
                        </div>
                        <div className="text-sm text-blue-600 mb-2">
                          📚 {article.code_source.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </div>
                        <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded border-l-2 border-blue-200">
                          {article.content}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Note disclaimer */}
            <div className="text-xs text-gray-500 bg-gray-50 p-3 rounded-lg border-l-2 border-gray-300">
              {isRTL 
                ? "⚠️ هذه معلومات إرشادية. للحصول على استشارة قانونية دقيقة، يُنصح بالتواصل مع محامٍ مختص."
                : "⚠️ Ces informations sont fournies à titre indicatif. Pour un conseil juridique précis, consultez un avocat spécialisé."
              }
            </div>

            {/* Timestamp */}
            <p className="text-xs text-gray-400 text-right">
              {message.timestamp.toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit'
              })}
            </p>
          </>
        )}
      </div>
    </div>
  );
}