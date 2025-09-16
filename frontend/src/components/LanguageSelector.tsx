import React from 'react';
import { Language } from '../types/chat';
import { Globe, BookOpen } from 'lucide-react';

interface LanguageSelectorProps {
  language: Language;
  onLanguageChange: (language: Language) => void;
  simpleExplanation: boolean;
  onSimpleExplanationChange: (simple: boolean) => void;
}

export function LanguageSelector({
  language,
  onLanguageChange,
  simpleExplanation,
  onSimpleExplanationChange,
}: LanguageSelectorProps) {
  return (
    <div className="flex flex-wrap items-center justify-center gap-3 p-4 bg-gray-50 border-t border-gray-200">
      {/* Language Selector */}
      <div className="flex items-center space-x-2">
        <Globe className="h-4 w-4 text-gray-500" />
        <label className="text-sm text-gray-700">Langue:</label>
        <select
          value={language}
          onChange={(e) => onLanguageChange(e.target.value as Language)}
          className="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
        >
          <option value="auto">Auto</option>
          <option value="fr">Français</option>
          <option value="ar">العربية</option>
        </select>
      </div>

      {/* Simple Explanation Toggle */}
      <div className="flex items-center space-x-2">
        <BookOpen className="h-4 w-4 text-gray-500" />
        <label className="text-sm text-gray-700">
          <input
            type="checkbox"
            checked={simpleExplanation}
            onChange={(e) => onSimpleExplanationChange(e.target.checked)}
            className="mr-2 rounded focus:ring-2 focus:ring-red-500"
          />
          Explication simple
        </label>
      </div>
    </div>
  );
}