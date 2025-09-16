import React from 'react';
import { Scale, Trash2 } from 'lucide-react';

interface HeaderProps {
  onClearChat: () => void;
  messageCount: number;
}

export function Header({ onClearChat, messageCount }: HeaderProps) {
  return (
    <header className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-4xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              {/* <span className="text-2xl">🇲🇦</span> */}
              <Scale className="h-8 w-8 text-red-600" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">QANOUNEK</h1>
              <p className="text-sm text-gray-600">Votre Assistant Juridique Marocain</p>
            </div>
          </div>
          
          {messageCount > 0 && (
            <button
              onClick={onClearChat}
              className="flex items-center space-x-2 px-3 py-2 text-sm text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors duration-200"
            >
              <Trash2 className="h-4 w-4" />
              <span>Effacer</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}