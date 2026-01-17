import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, Database, Sparkles, AlertCircle, CheckCircle } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
  timestamp?: Date;
}

const Chat: React.FC = () => {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [sending, setSending] = useState(false);
  const [includeSchema, setIncludeSchema] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [aiStatus, setAiStatus] = useState<'configured' | 'not_configured' | 'checking'>('checking');

  useEffect(() => {
    // Check AI status on mount
    checkAiStatus();
    // Add welcome message
    setMessages([{
      role: 'assistant',
      content: 'Hello! I\'m your AI assistant for the AiX Decision System. I can help you:\n\n• Query and analyze database data\n• Understand SPC metrics and FDC alarms\n• Interpret control charts and process data\n• Provide insights on process optimization\n\nAsk me anything about the system!',
      timestamp: new Date()
    }]);
  }, []);

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const checkAiStatus = async () => {
    try {
      // Try to get schema to check if backend is responsive
      await axios.get(`${API_BASE_URL}/api/v1/chat/schema`);
      setAiStatus('configured');
    } catch (error) {
      setAiStatus('not_configured');
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    const userMessage: Message = {
      role: 'user',
      content: message,
      timestamp: new Date()
    };
    
    setMessage('');
    setMessages(prev => [...prev, userMessage]);
    setSending(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/v1/chat`, {
        message: userMessage.content,
        include_schema: includeSchema
      });
      
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.response,
        sources: response.data.sources,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error: any) {
      console.error('Chat failed:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: error.response?.data?.detail || 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setSending(false);
    }
  };

  const handleQuickQuestion = (question: string) => {
    setMessage(question);
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="p-6 h-full flex flex-col bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <MessageSquare className="w-8 h-8 text-blue-400" />
            <div>
              <h1 className="text-3xl font-bold text-white">AI Agent Chat</h1>
              <p className="text-slate-400">Intelligent assistant powered by DeepSeek AI</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {aiStatus === 'configured' && (
              <div className="flex items-center gap-2 px-3 py-1 bg-green-500/20 border border-green-500/50 rounded-lg">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span className="text-sm text-green-400">AI Ready</span>
              </div>
            )}
            {aiStatus === 'not_configured' && (
              <div className="flex items-center gap-2 px-3 py-1 bg-yellow-500/20 border border-yellow-500/50 rounded-lg">
                <AlertCircle className="w-4 h-4 text-yellow-400" />
                <span className="text-sm text-yellow-400">AI Not Configured</span>
              </div>
            )}
          </div>
        </div>

        {/* Quick Questions */}
        <div className="flex flex-wrap gap-2 mt-4">
          <button
            onClick={() => handleQuickQuestion('What tables are in the database?')}
            className="px-3 py-1 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm text-slate-300 transition-colors"
          >
            <Database className="w-3 h-3 inline mr-1" />
            Show Tables
          </button>
          <button
            onClick={() => handleQuickQuestion('What are the recent SPC violations?')}
            className="px-3 py-1 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm text-slate-300 transition-colors"
          >
            <AlertCircle className="w-3 h-3 inline mr-1" />
            SPC Violations
          </button>
          <button
            onClick={() => handleQuickQuestion('Show me recent alarms')}
            className="px-3 py-1 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm text-slate-300 transition-colors"
          >
            Recent Alarms
          </button>
          <button
            onClick={() => handleQuickQuestion('Explain the database schema')}
            className="px-3 py-1 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm text-slate-300 transition-colors"
          >
            <Sparkles className="w-3 h-3 inline mr-1" />
            Schema Info
          </button>
        </div>
      </div>

      {/* Chat Container */}
      <div className="card flex-1 flex flex-col min-h-0">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto mb-4 space-y-4 p-4">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className="flex flex-col max-w-[75%]">
                <div
                  className={`rounded-lg p-4 ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-700 text-slate-200'
                  }`}
                >
                  <div className="whitespace-pre-wrap break-words">{msg.content}</div>
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-slate-600">
                      <div className="flex flex-wrap gap-2">
                        {msg.sources.map((source, sIdx) => (
                          <span
                            key={sIdx}
                            className="text-xs px-2 py-1 bg-slate-600/50 rounded"
                          >
                            {source}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                {msg.timestamp && (
                  <span className="text-xs text-slate-500 mt-1 px-2">
                    {formatTime(msg.timestamp)}
                  </span>
                )}
              </div>
            </div>
          ))}
          {sending && (
            <div className="flex justify-start">
              <div className="bg-slate-700 rounded-lg p-4 text-slate-400">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                  <span className="ml-2">Thinking...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-slate-700 pt-4">
          <div className="flex items-center gap-2 mb-2">
            <input
              type="checkbox"
              id="includeSchema"
              checked={includeSchema}
              onChange={(e) => setIncludeSchema(e.target.checked)}
              className="w-4 h-4"
            />
            <label htmlFor="includeSchema" className="text-sm text-slate-400">
              Include database schema in context
            </label>
          </div>
          <form onSubmit={handleSend} className="flex gap-2">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Ask about database, SPC metrics, FDC alarms, or process data..."
              className="flex-1 input-field"
              disabled={sending}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend(e);
                }
              }}
            />
            <button
              type="submit"
              disabled={sending || !message.trim()}
              className="btn-primary flex items-center gap-2 disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Chat;
