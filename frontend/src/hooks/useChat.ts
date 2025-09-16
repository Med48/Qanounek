import { useState, useCallback } from 'react';
import { Message, Language } from '../types/chat';
import { askQuestion } from '../utils/api';

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [language, setLanguage] = useState<Language>('auto');
  const [simpleExplanation, setSimpleExplanation] = useState(false);

  const sendMessage = useCallback(async (question: string) => {
    if (!question.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: question,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await askQuestion({
        question,
        language,
        simple_explanation: simpleExplanation,
      });

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: response.answer,
        timestamp: new Date(),
        language: response.language_detected,
        articles: response.articles_used,
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: 'Désolé, une erreur s\'est produite. Veuillez réessayer.',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [language, simpleExplanation]);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    isLoading,
    language,
    setLanguage,
    simpleExplanation,
    setSimpleExplanation,
    sendMessage,
    clearMessages,
  };
}