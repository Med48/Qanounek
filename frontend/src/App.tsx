import React from 'react';
import { Header } from './components/Header';
import { ChatInterface } from './components/ChatInterface';
import { QuestionCategories } from './components/QuestionCategories';
import { LanguageSelector } from './components/LanguageSelector';
import { useChat } from './hooks/useChat';

function App() {
  const {
    messages,
    isLoading,
    language,
    setLanguage,
    simpleExplanation,
    setSimpleExplanation,
    sendMessage,
    clearMessages,
  } = useChat();

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header onClearChat={clearMessages} messageCount={messages.length} />
      
      <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full">
        <ChatInterface
          messages={messages}
          onSendMessage={sendMessage}
          isLoading={isLoading}
        />
        
        <QuestionCategories
          onQuestionSelect={sendMessage}
          disabled={isLoading}
        />
        
        <LanguageSelector
          language={language}
          onLanguageChange={setLanguage}
          simpleExplanation={simpleExplanation}
          onSimpleExplanationChange={setSimpleExplanation}
        />
      </div>
    </div>
  );
}

export default App;