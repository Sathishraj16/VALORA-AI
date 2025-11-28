'use client';

import { useState, useEffect, useRef } from 'react';
import { MessageSquare, Send, RefreshCw, Trash2, Bot, User, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { useSimulationStore, useChatStore, type ChatMessage } from '@/lib/store';
import { crewApi } from '@/lib/api';

export default function CrewChatPage() {
  const { currentSimulation, macroState } = useSimulationStore();
  const { messages, isLoading, conversationId, addMessage, setLoading, setConversationId, clearChat } = useChatStore();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || !currentSimulation || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };

    addMessage(userMessage);
    setInput('');
    setLoading(true);

    try {
      const response = await crewApi.chat(
        currentSimulation.simulation_id,
        input.trim(),
        conversationId || undefined
      );

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date().toISOString(),
      };

      addMessage(assistantMessage);
      
      if (response.data.conversation_id && !conversationId) {
        setConversationId(response.data.conversation_id);
      }
    } catch (error) {
      toast.error('Failed to get response from AI');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const quickPrompts = [
    "What's the current state of the economy?",
    "What policy should I implement to reduce unemployment?",
    "Explain the relationship between inflation and interest rates",
    "What are the risks in the current scenario?",
    "Generate a forecast for the next 20 ticks",
  ];

  if (!currentSimulation) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <MessageSquare className="w-12 h-12 text-dark-500 mb-4" />
        <h2 className="text-xl font-semibold text-white mb-2">No Simulation Selected</h2>
        <p className="text-dark-400">Create or select a simulation to chat with the AI assistant.</p>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-primary-400" />
            AI Economic Advisor
          </h1>
          <p className="text-dark-400">Powered by CrewAI multi-agent system</p>
        </div>
        <button
          onClick={() => {
            clearChat();
            toast.success('Chat cleared');
          }}
          className="btn-secondary flex items-center gap-2"
        >
          <Trash2 className="w-4 h-4" />
          Clear Chat
        </button>
      </div>

      {/* Chat Container */}
      <div className="flex-1 glass-card flex flex-col overflow-hidden">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center py-12">
              <Bot className="w-16 h-16 text-primary-400 mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">
                Welcome to VALORA AI Assistant
              </h3>
              <p className="text-dark-400 max-w-md mb-8">
                I can help you analyze your economic simulation, recommend policies, 
                forecast trends, and explain complex economic concepts.
              </p>
              
              {/* Quick Prompts */}
              <div className="flex flex-wrap justify-center gap-2 max-w-2xl">
                {quickPrompts.map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setInput(prompt);
                    }}
                    className="px-4 py-2 rounded-full bg-dark-700/50 border border-dark-600 text-sm text-dark-300 hover:text-white hover:border-primary-500/50 transition-all"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={cn(
                    'flex gap-3',
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  )}
                >
                  {message.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-lg bg-primary-600/20 flex items-center justify-center flex-shrink-0">
                      <Bot className="w-5 h-5 text-primary-400" />
                    </div>
                  )}
                  
                  <div
                    className={cn(
                      'max-w-[70%] rounded-2xl px-4 py-3',
                      message.role === 'user'
                        ? 'bg-primary-600 text-white'
                        : 'bg-dark-700/50 text-dark-100'
                    )}
                  >
                    <p className="whitespace-pre-wrap">{message.content}</p>
                    <div
                      className={cn(
                        'text-xs mt-1',
                        message.role === 'user' ? 'text-primary-200' : 'text-dark-500'
                      )}
                    >
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                  
                  {message.role === 'user' && (
                    <div className="w-8 h-8 rounded-lg bg-accent-600/20 flex items-center justify-center flex-shrink-0">
                      <User className="w-5 h-5 text-accent-400" />
                    </div>
                  )}
                </div>
              ))}
              
              {isLoading && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-lg bg-primary-600/20 flex items-center justify-center">
                    <Bot className="w-5 h-5 text-primary-400" />
                  </div>
                  <div className="bg-dark-700/50 rounded-2xl px-4 py-3">
                    <div className="flex items-center gap-2">
                      <RefreshCw className="w-4 h-4 text-primary-400 animate-spin" />
                      <span className="text-dark-400">Thinking...</span>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input */}
        <div className="border-t border-dark-700 p-4">
          <div className="flex gap-3">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about the economy, policies, forecasts..."
              className="input-field flex-1 resize-none"
              rows={1}
              disabled={isLoading}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="btn-primary px-4"
            >
              {isLoading ? (
                <RefreshCw className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
          
          {/* Context Info */}
          <div className="flex items-center gap-4 mt-2 text-xs text-dark-500">
            <span>Simulation: {currentSimulation.name}</span>
            <span>Tick: {macroState?.tick || 0}</span>
            <span>GDP: {macroState?.gdp?.toLocaleString() || 'N/A'}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
