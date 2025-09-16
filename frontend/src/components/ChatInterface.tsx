import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Scale } from 'lucide-react';
import { MessageBubble } from './MessageBubble';
import { Message } from '../types/chat';

interface ChatInterfaceProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

export function ChatInterface({ messages, onSendMessage, isLoading }: ChatInterfaceProps) {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading) {
      onSendMessage(inputValue);
      setInputValue('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex-1 flex flex-col">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center py-12">
            {/* <div className="text-6xl mb-4">🇲🇦</div> */}
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Bienvenue sur QANOUNEK
            </h2>
            <p className="text-gray-600 max-w-md mx-auto">
              Votre assistant juridique marocain. Posez-moi vos questions sur le droit marocain 
              ou choisissez parmi les questions fréquentes ci-dessous.
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))
        )}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 shadow-sm">
              <div className="flex items-center space-x-2">
                <Loader2 className="h-4 w-4 animate-spin text-gray-500" />
                <span className="text-sm text-gray-500">L'assistant réfléchit...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div className="border-t border-gray-200 bg-white p-4">
        <form onSubmit={handleSubmit} className="flex items-end space-x-2">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Posez votre question juridique..."
              className="w-full resize-none border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent text-sm"
              rows={1}
              style={{ minHeight: '44px', maxHeight: '120px' }}
              disabled={isLoading}
            />
          </div>
          
          <button
            type="submit"
            disabled={!inputValue.trim() || isLoading}
            className="bg-red-600 hover:bg-red-700 disabled:bg-gray-300 text-white p-3 rounded-lg transition-colors duration-200 flex-shrink-0"
          >
            <Send className="h-5 w-5" />
          </button>
        </form>
      </div>
    </div>
  );
}