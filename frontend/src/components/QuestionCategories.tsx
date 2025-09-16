import React from 'react';
import { Briefcase, Heart, Car, AlertTriangle } from 'lucide-react';

interface QuestionCategoriesProps {
  onQuestionSelect: (question: string) => void;
  disabled: boolean;
}

const categories = [
  {
    icon: Briefcase,
    title: 'Travail',
    color: 'bg-green-600 hover:bg-green-700',
    questions: [
      'Qu est-ce que le contrat de travail selon la loi marocaine?',
      'Combien d heures puis-je travailler par semaine au Maroc?',
      'Quelles sont les conditions de validité d un contrat de travail?',
    ],
  },
  {
    icon: Heart,
    title: 'Famille',
    color: 'bg-red-600 hover:bg-red-700',
    questions: [
      'Comment procéder à un divorce au Maroc?',
      'Quels sont les droits de garde des enfants?',
      'Comment établir une pension alimentaire?',
    ],
  },
  {
    icon: Car,
    title: 'Route',
    color: 'bg-green-600 hover:bg-green-700',
    questions: [
      'Quelles sont les sanctions pour excès de vitesse?',
      'Comment contester une contravention routière?',
      'Que faire en cas d\'accident de la route?',
    ],
  },
  {
    icon: AlertTriangle,
    title: 'Pénal',
    color: 'bg-red-600 hover:bg-red-700',
    questions: [
      'Quels sont mes droits lors d\'une arrestation?',
      'Comment porter plainte au Maroc?',
      'Que faire en cas de vol ou d\'agression?',
    ],
  },
];

export function QuestionCategories({ onQuestionSelect, disabled }: QuestionCategoriesProps) {
  return (
    <div className="p-4 bg-white border-t border-gray-200">
      <h3 className="text-sm font-medium text-gray-700 mb-3 text-center">
        Questions fréquentes par catégorie
      </h3>
      
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
        {categories.map((category) => {
          const Icon = category.icon;
          return (
            <div key={category.title} className="space-y-2">
              <div className={`${category.color} text-white p-2 rounded-lg text-center`}>
                <Icon className="h-5 w-5 mx-auto mb-1" />
                <span className="text-xs font-medium">{category.title}</span>
              </div>
              
              <div className="space-y-1">
                {category.questions.map((question, index) => (
                  <button
                    key={index}
                    onClick={() => onQuestionSelect(question)}
                    disabled={disabled}
                    className="w-full text-xs text-left text-gray-600 hover:text-gray-900 hover:bg-gray-50 p-2 rounded transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed border border-gray-200 hover:border-gray-300"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}