/**
 * Main App component for ContextPilot.
 */
import 'highlight.js/styles/github-dark.css';
import React, { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import remarkGfm from 'remark-gfm';
import { contextAPI } from './api';
import './App.css';
import { ContextTemplates } from './ContextTemplates';
import { ContextTools } from './ContextTools';
import modelOptions from './model_options.json';
import {
  ContextType,
  ContextUnit,
  ContextUnitCreate,
  Conversation,
  ConversationMessage,
  Settings,
  SettingsUpdate,
  Stats,
} from './types';

function App() {
  const [contexts, setContexts] = useState<ContextUnit[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'chat' | 'manage'>('chat');
  const [showConversations, setShowConversations] = useState(true);
  const [showContexts, setShowContexts] = useState(true);

  // Form states
  const [newContext, setNewContext] = useState<ContextUnitCreate>({
    type: ContextType.PREFERENCE,
    content: '',
    confidence: 1.0,
    tags: [],
  });
  const [tagInput, setTagInput] = useState('');

  // AI Chat states
  const [aiTask, setAiTask] = useState('');
  const [aiMaxContexts, setAiMaxContexts] = useState(5);
  const [aiProvider, setAiProvider] = useState('openai');
  const [aiModel, setAiModel] = useState('gpt-4o');
  const [aiMaxTokens, setAiMaxTokens] = useState(4000);
  const [aiTemperature, setAiTemperature] = useState(1.0);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [conversationContexts, setConversationContexts] = useState<{[conversationId: string]: string[]}>({});
  const [currentChatMessages, setCurrentChatMessages] = useState<ConversationMessage[]>([]);
  const [refreshContexts, setRefreshContexts] = useState(false);
  const messageListRef = useRef<HTMLDivElement>(null);

  // Search and filter states
  const [filters, setFilters] = useState({
    search: '',
    type: '',
    tags: '',
    status: '',
  });

  // Settings states
  const [settings, setSettings] = useState<Settings | null>(null);
  const [settingsModal, setSettingsModal] = useState(false);
  const [settingsForm, setSettingsForm] = useState<SettingsUpdate>({});

  // Load contexts and stats on mount
  useEffect(() => {
    loadContexts();
    loadStats();
    loadSettings();
    loadConversations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Reload contexts when filters change
  useEffect(() => {
    loadContexts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]);

  // Auto-scroll to latest message
  useEffect(() => {
    if (messageListRef.current) {
      // Use setTimeout to ensure DOM is updated before scrolling
      setTimeout(() => {
        if (messageListRef.current) {
          messageListRef.current.scrollTop = messageListRef.current.scrollHeight;
        }
      }, 100);
    }
  }, [currentChatMessages, loading]);

  const loadContexts = async () => {
    try {
      setLoading(true);
      const apiFilters: any = {};
      if (filters.type) apiFilters.type = filters.type;
      if (filters.tags) apiFilters.tags = filters.tags;
      if (filters.search) apiFilters.search = filters.search;
      if (filters.status) apiFilters.status_filter = filters.status;
      
      const data = await contextAPI.listContexts(false, apiFilters);
      setContexts(data);
      setError(null);
    } catch (err) {
      setError('Failed to load contexts');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const data = await contextAPI.getStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  const loadSettings = async () => {
    try {
      const data = await contextAPI.getSettings();
      setSettings(data);
      // Apply settings to AI chat defaults
      if (data.default_ai_provider) setAiProvider(data.default_ai_provider);
      if (data.default_ai_model) setAiModel(data.default_ai_model);
      if (data.ai_max_tokens) setAiMaxTokens(data.ai_max_tokens);
      if (data.ai_temperature !== undefined) setAiTemperature(data.ai_temperature);
    } catch (err) {
      console.error('Failed to load settings:', err);
    }
  };

  const handleUpdateSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      await contextAPI.updateSettings(settingsForm);
      setSuccess('Settings updated successfully!');
      setSettingsModal(false);
      setSettingsForm({});
      loadSettings(); // Reload settings to get updated status
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update settings');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const openSettingsModal = () => {
    setSettingsForm({
      default_ai_provider: settings?.default_ai_provider,
      default_ai_model: settings?.default_ai_model,
      ai_temperature: settings?.ai_temperature,
      ai_max_tokens: settings?.ai_max_tokens,
    });
    setSettingsModal(true);
  };

  const handleCreateContext = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newContext.content.trim()) {
      setError('Content is required');
      return;
    }

    try {
      setLoading(true);
      await contextAPI.createContext(newContext);
      setSuccess('Context created successfully!');
      setNewContext({
        type: ContextType.PREFERENCE,
        content: '',
        confidence: 1.0,
        tags: [],
      });
      setTagInput('');
      await loadContexts();
      await loadStats();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('Failed to create context');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteContext = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this context?')) {
      return;
    }

    try {
      setLoading(true);
      await contextAPI.deleteContext(id);
      setSuccess('Context deleted successfully!');
      await loadContexts();
      await loadStats();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('Failed to delete context');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !newContext.tags?.includes(tagInput.trim())) {
      setNewContext({
        ...newContext,
        tags: [...(newContext.tags || []), tagInput.trim()],
      });
      setTagInput('');
    }
  };

  const handleRemoveTag = (tag: string) => {
    setNewContext({
      ...newContext,
      tags: newContext.tags?.filter((t) => t !== tag) || [],
    });
  };

  const handleUseTemplate = (template: ContextUnitCreate) => {
    setNewContext(template);
    setSuccess('Template loaded! Modify as needed and click Add Context.');
    setTimeout(() => setSuccess(null), 3000);
  };

  // Legacy prompt generation functions removed - now using direct AI chat
// AI Chat handlers
  const loadConversations = async () => {
    try {
      const data = await contextAPI.listConversations();
      setConversations(data);
    } catch (err) {
      console.error('Failed to load conversations:', err);
    }
  };

  const handleAIChat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!aiTask.trim() || loading) {
      return;
    }

    // Create user message immediately
    const userMessage: ConversationMessage = {
      role: 'user',
      content: aiTask,
      created_at: new Date().toISOString()
    };
    
    // Add user message to chat immediately
    setCurrentChatMessages(prev => [...prev, userMessage]);
    
    // Store task for API call before clearing
    const taskToSend = aiTask;
    
    // Clear input immediately
    setAiTask('');

    try {
      setLoading(true);
      
      // Context sending logic:
      // - New conversation: send contexts normally
      // - Continuing conversation: send 0 contexts (already in conversation history)
      // - Exception: if user explicitly wants to refresh contexts, send them again
      let maxContextsToSend = aiMaxContexts;
      if (selectedConversation?.id && currentChatMessages.length > 0 && !refreshContexts) {
        // Continuing existing conversation - contexts already in history
        maxContextsToSend = 0;
      }
      
      // Reset refresh flag after use
      if (refreshContexts) {
        setRefreshContexts(false);
      }
      
      const result = await contextAPI.chatWithAI({
        task: taskToSend,
        max_context_units: maxContextsToSend,
        provider: aiProvider,
        model: aiModel,
        conversation_id: selectedConversation?.id,
        max_tokens: aiMaxTokens,
        temperature: aiTemperature,
      });
      
      // Track contexts used for this conversation (for display purposes)
      if (result.context_ids && result.context_ids.length > 0) {
        const existingContexts = conversationContexts[result.conversation_id] || [];
        const allContexts = Array.from(new Set([...existingContexts, ...result.context_ids]));
        setConversationContexts(prev => ({
          ...prev,
          [result.conversation_id]: allContexts
        }));
      }
      
      // Add AI response to current chat
      const assistantMessage: ConversationMessage = {
        role: 'assistant',
        content: result.response || '',
        created_at: result.timestamp || new Date().toISOString(),
        model: result.model  // Include model information from API response
      };
      
      setCurrentChatMessages(prev => [...prev, assistantMessage]);
      
      // Update selected conversation if it's a new conversation
      if (!selectedConversation || selectedConversation.id !== result.conversation_id) {
        const newConversation: Conversation = {
          id: result.conversation_id,
          task: taskToSend,
          provider: result.provider,
          model: result.model,
          created_at: result.timestamp,
          messages: [userMessage, assistantMessage]
        };
        setSelectedConversation(newConversation);
      }
      
      setError(null);
      await loadConversations();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to generate AI response. Check that API keys are configured.';
      setError(errorMessage);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleViewConversation = async (id: string) => {
    try {
      setLoading(true);
      const conversation = await contextAPI.getConversation(id);
      setSelectedConversation(conversation);
      // Set current chat messages for display
      if (conversation.messages) {
        const filteredMessages = conversation.messages.filter(msg => msg.role !== 'system');
        setCurrentChatMessages(filteredMessages);
      }
      // Clear any pending response
      setAiTask('');
    } catch (err) {
      setError('Failed to load conversation');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleNewConversation = () => {
    setSelectedConversation(null);
    setCurrentChatMessages([]);
    setAiTask('');
    setRefreshContexts(false);
  };

  const handleCopyMessage = (content: string) => {
    navigator.clipboard.writeText(content);
    setSuccess('Message copied to clipboard!');
    setTimeout(() => setSuccess(null), 2000);
  };

  const renderMessageContent = (message: ConversationMessage) => {
    const { content, role, tokens, finish_reason } = message;
    
    if (!content || content.trim() === '') {
      // Handle empty content cases
      if (finish_reason === 'length') {
        console.log(`Message truncated: ${role} message was cut off (${tokens || 'unknown'} tokens used)`);
        return <span style={{ color: '#999', fontStyle: 'italic' }}>(Response was truncated due to length limit. Used {tokens} tokens.)</span>;
      }
      
      console.log(`Empty content for ${role} message (finish_reason: ${finish_reason || 'none'})`);
      return <span style={{ color: '#999', fontStyle: 'italic' }}>(Empty response)</span>;
    }
    
    // Use ReactMarkdown for full markdown support including code blocks
    return (
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          // Custom image component with error handling
          img: ({ node, ...props }) => (
            <img
              {...props}
              alt={props.alt || 'AI-generated image'}
              style={{
                maxWidth: '100%',
                borderRadius: '8px',
                margin: '8px 0',
                display: 'block'
              }}
              onError={(e) => {
                const target = e.currentTarget;
                const imageUrl = target.src;
                console.error('Image failed to load:', imageUrl);
                target.style.display = 'none';
                const errorDiv = document.createElement('div');
                errorDiv.style.cssText = 'padding: 12px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; margin: 8px 0; color: #856404;';
                errorDiv.innerHTML = `⚠️ <strong>Image unavailable:</strong> <a href="${imageUrl}" target="_blank" style="color: #856404; text-decoration: underline;">${imageUrl}</a>`;
                target.parentNode?.insertBefore(errorDiv, target);
              }}
            />
          ),
          // Style code blocks
          code: ({ node, inline, className, children, ...props }: any) => {
            if (inline) {
              return (
                <code
                  style={{
                    backgroundColor: '#f6f8fa',
                    padding: '2px 6px',
                    borderRadius: '3px',
                    fontSize: '0.9em',
                    fontFamily: 'Monaco, Consolas, monospace'
                  }}
                  {...props}
                >
                  {children}
                </code>
              );
            }
            return (
              <code className={className} {...props}>
                {children}
              </code>
            );
          },
          // Style pre blocks with copy button
          pre: ({ node, children, ...props }) => {
            const codeContent = React.Children.toArray(children)
              .map((child: any) => {
                if (typeof child === 'string') return child;
                if (child?.props?.children) {
                  if (typeof child.props.children === 'string') {
                    return child.props.children;
                  }
                  if (Array.isArray(child.props.children)) {
                    return child.props.children.join('');
                  }
                }
                return '';
              })
              .join('');

            const handleCopyCode = () => {
              navigator.clipboard.writeText(codeContent);
              setSuccess('Code copied to clipboard!');
              setTimeout(() => setSuccess(null), 2000);
            };

            return (
              <div style={{ position: 'relative', marginTop: '8px', marginBottom: '8px' }}>
                <button
                  onClick={handleCopyCode}
                  style={{
                    position: 'absolute',
                    top: '8px',
                    right: '8px',
                    background: '#238636',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    padding: '4px 8px',
                    fontSize: '12px',
                    cursor: 'pointer',
                    opacity: 0.8,
                    zIndex: 1
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
                  onMouseLeave={(e) => e.currentTarget.style.opacity = '0.8'}
                  title="Copy code"
                >
                  📋 Copy
                </button>
                <pre
                  style={{
                    backgroundColor: '#0d1117',
                    padding: '16px',
                    borderRadius: '6px',
                    overflow: 'auto',
                    margin: 0
                  }}
                  {...props}
                >
                  {children}
                </pre>
              </div>
            );
          },
          // Style links
          a: ({ node, children, ...props }) => (
            <a
              {...props}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                color: '#0969da',
                textDecoration: 'none'
              }}
            >
              {children}
            </a>
          )
        }}
      >
        {content}
      </ReactMarkdown>
    );
  };

  
  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div className="title-section">
            <h1>🧭 ContextPilot</h1>
            <span className="by-signature">
              by <img src="b-logo.png" alt="B" className="b-logo" />
            </span>
          </div>
          <button 
            className="settings-button"
            onClick={openSettingsModal}
            title="Settings"
          >
            ⚙️
          </button>
        </div>
      </header>

      {error && <div className="error">{error}</div>}
      {success && <div className="success">{success}</div>}

      <div className="workspace-layout">
        {activeTab === 'chat' && (
          <>
            {/* Left Sidebar: Conversations */}
            <div className={`sidebar sidebar-left ${showConversations ? 'visible' : 'collapsed'}`}>
              <div className="sidebar-header">
                <h3>💬 Conversations</h3>
                <button 
                  className="toggle-button"
                  onClick={() => setShowConversations(!showConversations)}
                  title={showConversations ? "Hide conversations" : "Show conversations"}
                >
                  {showConversations ? '◀' : '▶'}
                </button>
              </div>
              {showConversations && (
                <div className="sidebar-content">
                  {conversations.length === 0 ? (
                    <p className="help-text">No conversations yet</p>
                  ) : (
                    <div className="conversation-list">
                      {conversations.map((conv) => (
                        <div 
                          key={conv.id} 
                          className={`conversation-item ${selectedConversation?.id === conv.id ? 'active' : ''}`}
                          onClick={() => handleViewConversation(conv.id)}
                        >
                          <div className="conversation-preview">
                            <div className="conversation-task">{conv.task.substring(0, 60)}...</div>
                            <div className="conversation-meta">
                              <span className="conversation-model">{conv.model}</span>
                              <span className="conversation-messages">{conv.message_count} msgs</span>
                            </div>
                            <div className="conversation-date">
                              {new Date(conv.created_at).toLocaleDateString()}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Center: Main Chat Area */}
            <div className="main-panel">
              <div className="chat-container">
                <div className="card chat-card">
                  <div className="chat-header">
                    <h2>� {selectedConversation ? 'Conversation' : 'New Chat'}</h2>
                    <div className="chat-controls">
                      <button 
                        className="button button-small"
                        onClick={handleNewConversation}
                        title="Start new conversation"
                      >
                        ➕ New
                      </button>
                      {selectedConversation && (
                        <div className="conversation-info">
                          <span className="conversation-model">{selectedConversation.model}</span>
                          <span className="context-count">
                            {(conversationContexts[selectedConversation.id] || []).length} contexts used
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="chat-messages" ref={messageListRef}>
                    {currentChatMessages.length === 0 ? (
                      <div className="welcome-message">
                        <div className="welcome-icon">🚀</div>
                        <h3>Ready to Chat!</h3>
                        <p>Ask me anything. I'll use your personal contexts to provide relevant responses.</p>
                        <div className="context-preview">
                          <strong>Available contexts:</strong> {contexts.length}
                        </div>
                      </div>
                    ) : (
                      <div className="message-list">
                        {currentChatMessages.map((msg, idx) => {
                          const msgTime = msg.created_at || msg.timestamp || new Date().toISOString();
                          return (
                          <div key={`${msgTime}-${idx}`} className={`message message-${msg.role}`}>
                            <div className="message-avatar">
                              {msg.role === 'user' ? '👤' : '🤖'}
                            </div>
                            <div className="message-bubble">
                              <div className="message-content">
                                {renderMessageContent(msg)}
                              </div>
                              <div className="message-actions">
                                <span className="message-time">
                                  {new Date(msg.created_at || msg.timestamp || '').toLocaleTimeString()}
                                </span>
                                {msg.model && msg.role === 'assistant' && (
                                  <span className="message-model" title={`Generated by ${msg.model}`}>
                                    {msg.model}
                                  </span>
                                )}
                                <button
                                  className="copy-message-btn"
                                  onClick={() => handleCopyMessage(msg.content)}
                                  title="Copy message"
                                >
                                  📋
                                </button>
                              </div>
                            </div>
                          </div>
                          );
                        })}
                        {loading && (
                          <div className="message message-assistant">
                            <div className="message-avatar">🤖</div>
                            <div className="message-bubble typing">
                              <div className="typing-indicator">
                                <span></span>
                                <span></span>
                                <span></span>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="chat-input-area">
                    <form onSubmit={handleAIChat} className="chat-input-form">
                      <div className="input-row">
                        <textarea
                          value={aiTask}
                          onChange={(e) => setAiTask(e.target.value)}
                          placeholder={selectedConversation ? "Continue the conversation..." : "Ask a question or describe a task..."}
                          rows={3}
                          className="chat-input"
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                              e.preventDefault();
                              handleAIChat(e);
                            }
                          }}
                        />
                        <button 
                          type="submit" 
                          className="send-button" 
                          disabled={loading || !aiTask.trim()}
                          title={loading ? 'Thinking...' : 'Send message (Enter)'}
                        >
                          {loading ? '⏳' : '🚀'}
                        </button>
                      </div>
                      
                      <div className="chat-settings">
                        <div className="setting-group">
                          <select
                            value={aiProvider}
                            onChange={(e) => {
                              setAiProvider(e.target.value);
                              const newProviderModels = (modelOptions as any)[e.target.value] || [];
                              if (newProviderModels.length > 0) {
                                setAiModel(newProviderModels[0]);
                              }
                            }}
                            className="setting-select"
                          >
                            <option value="openai">OpenAI</option>
                            <option value="anthropic">Anthropic</option>
                            <option value="ollama">Ollama (Local)</option>
                          </select>
                          
                          <select
                            value={aiModel}
                            onChange={(e) => setAiModel(e.target.value)}
                            className="setting-select"
                          >
                            {((modelOptions as any)[aiProvider] || []).map((model: string) => (
                              <option key={model} value={model}>
                                {model.includes('gpt-4o') ? `${model} (Latest)` :
                                 model.includes('gpt-4-turbo') ? `${model.replace('gpt-4-turbo', 'GPT-4 Turbo')}` :
                                 model.includes('gpt-4') ? `${model.replace('gpt-4', 'GPT-4')}` :
                                 model.includes('gpt-3.5-turbo') ? `${model.replace('gpt-3.5-turbo', 'GPT-3.5 Turbo')}` :
                                 model.includes('claude-3-5-sonnet') ? 'Claude 3.5 Sonnet' :
                                 model.includes('claude-3-5-haiku') ? 'Claude 3.5 Haiku' :
                                 model.includes('claude-3-opus') ? 'Claude 3 Opus' :
                                 model.includes('claude-3-sonnet') ? 'Claude 3 Sonnet' :
                                 model.includes('claude-3-haiku') ? 'Claude 3 Haiku' :
                                 model}
                              </option>
                            ))}
                            {((modelOptions as any)[aiProvider] || []).length === 0 && (
                              <option value="" disabled>No models available</option>
                            )}
                          </select>
                        </div>
                        
                        <div className="setting-group">
                          <label className="setting-label">
                            Max Contexts: 
                            <input
                              type="number"
                              min="1"
                              max="20"
                              value={aiMaxContexts}
                              onChange={(e) => setAiMaxContexts(parseInt(e.target.value))}
                              className="setting-input"
                            />
                          </label>
                          <label className="setting-label">
                            Max Tokens: 
                            <input
                              type="number"
                              min="100"
                              max="16000"
                              step="100"
                              value={aiMaxTokens}
                              onChange={(e) => setAiMaxTokens(parseInt(e.target.value))}
                              className="setting-input"
                              title="Higher values allow longer responses (recommended: 4000+)"
                            />
                          </label>
                          {selectedConversation && currentChatMessages.length > 0 && (
                            <button
                              type="button"
                              className={`refresh-contexts-btn ${refreshContexts ? 'active' : ''}`}
                              onClick={() => setRefreshContexts(!refreshContexts)}
                              title={refreshContexts ? "Contexts will be refreshed" : "Using existing contexts"}
                            >
                              {refreshContexts ? '🔄 Refreshing' : '♻️ Refresh Contexts'}
                            </button>
                          )}
                        </div>
                      </div>
                    </form>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Sidebar: Quick Context View */}
            <div className={`sidebar sidebar-right ${showContexts ? 'visible' : 'collapsed'}`}>
              <div className="sidebar-header">
                <h3>📚 Your Contexts</h3>
                <button 
                  className="toggle-button"
                  onClick={() => setShowContexts(!showContexts)}
                  title={showContexts ? "Hide contexts" : "Show contexts"}
                >
                  {showContexts ? '▶' : '◀'}
                </button>
              </div>
              {showContexts && (
                <div className="sidebar-content">
                  <div className="context-summary">
                    <div className="context-stats">
                      <div className="stat-mini">
                        <span className="stat-value">{contexts.filter(c => c.type === 'preference').length}</span>
                        <span className="stat-label">Preferences</span>
                      </div>
                      <div className="stat-mini">
                        <span className="stat-value">{contexts.filter(c => c.type === 'decision').length}</span>
                        <span className="stat-label">Decisions</span>
                      </div>
                      <div className="stat-mini">
                        <span className="stat-value">{contexts.filter(c => c.type === 'fact').length}</span>
                        <span className="stat-label">Facts</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="quick-context-list">
                    {contexts.slice(0, 10).map((context) => (
                      <div key={context.id} className="quick-context-item">
                        <span className={`context-type-badge ${context.type}`}>
                          {context.type[0].toUpperCase()}
                        </span>
                        <div className="quick-context-content">
                          {context.content.substring(0, 80)}...
                        </div>
                      </div>
                    ))}
                  </div>

                  <button 
                    className="button button-secondary button-full"
                    onClick={() => setActiveTab('manage')}
                  >
                    ➕ Manage All Contexts
                  </button>
                </div>
              )}
            </div>
          </>
        )}

        {activeTab === 'manage' && (
          <div className="manage-content">
            <div className="manage-header">
              <button 
                className="return-button"
                onClick={() => setActiveTab('chat')}
                title="Return to Chats"
              >
                ← Back to Chats
              </button>
            </div>
            {stats && (
              <div className="stats-bar">
                <div className="stat">
                  <div className="stat-value">{stats.active_contexts}</div>
                  <div className="stat-label">Active Contexts</div>
                </div>
                <div className="stat">
                  <div className="stat-value">{stats.contexts_by_type.preference || 0}</div>
                  <div className="stat-label">Preferences</div>
                </div>
                <div className="stat">
                  <div className="stat-value">{stats.contexts_by_type.goal || 0}</div>
                  <div className="stat-label">Goals</div>
                </div>
                <div className="stat">
                  <div className="stat-value">{stats.contexts_by_type.decision || 0}</div>
                  <div className="stat-label">Decisions</div>
                </div>
                <div className="stat">
                  <div className="stat-value">{stats.contexts_by_type.fact || 0}</div>
                  <div className="stat-label">Facts</div>
                </div>
              </div>
            )}

            <div className="manage-columns">
              <div className="manage-column-left">
                <ContextTools
                  onFiltersChange={setFilters}
                  onRefresh={loadContexts}
                />
                
                <ContextTemplates onUseTemplate={handleUseTemplate} />
              </div>
              
              <div className="manage-column-right">
                <div className="card">
                  <h2>Add Context</h2>
          <form onSubmit={handleCreateContext}>
            <div className="form-group">
              <label>Type</label>
              <select
                value={newContext.type}
                onChange={(e) =>
                  setNewContext({ ...newContext, type: e.target.value as ContextType })
                }
              >
                <option value={ContextType.PREFERENCE}>Preference</option>
                <option value={ContextType.DECISION}>Decision</option>
                <option value={ContextType.FACT}>Fact</option>
                <option value={ContextType.GOAL}>Goal</option>
              </select>
            </div>

            <div className="form-group">
              <label>Content</label>
              <textarea
                value={newContext.content}
                onChange={(e) =>
                  setNewContext({ ...newContext, content: e.target.value })
                }
                placeholder="Describe your preference, decision, fact, or goal..."
              />
            </div>

            <div className="form-group">
              <label>Confidence (0.0 - 1.0)</label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.05"
                value={newContext.confidence}
                onChange={(e) =>
                  setNewContext({ ...newContext, confidence: parseFloat(e.target.value) })
                }
              />
            </div>

            <div className="form-group">
              <label>Tags</label>
              <div className="tag-input">
                <input
                  type="text"
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTag())}
                  placeholder="Add a tag and press Enter"
                />
                <button
                  type="button"
                  className="button button-small"
                  onClick={handleAddTag}
                >
                  Add
                </button>
              </div>
              <div className="context-tags">
                {newContext.tags?.map((tag) => (
                  <span key={tag} className="tag" onClick={() => handleRemoveTag(tag)}>
                    {tag} ×
                  </span>
                ))}
              </div>
            </div>

            <button type="submit" className="button" disabled={loading}>
              {loading ? 'Adding...' : 'Add Context'}
            </button>
          </form>
        </div>

        <div className="card">
          <h2>Your Contexts ({contexts.length})</h2>
          <div className="context-list">
            {contexts.length === 0 ? (
              <p>No contexts yet. Add your first context above!</p>
            ) : (
              contexts.map((context) => (
                <div key={context.id} className="context-item">
                  <div className="context-header">
                    <span className={`context-type ${context.type}`}>
                      {context.type}
                    </span>
                    <span className="context-confidence">
                      {(context.confidence * 100).toFixed(0)}% confidence
                    </span>
                  </div>
                  <div className="context-content">{context.content}</div>
                  {context.tags.length > 0 && (
                    <div className="context-tags">
                      {context.tags.map((tag) => (
                        <span key={tag} className="tag">
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                  <div className="context-actions">
                    <button
                      className="button button-small button-danger"
                      onClick={() => handleDeleteContext(context.id)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Settings Modal */}
      {settingsModal && (
        <div className="modal-overlay" onClick={() => setSettingsModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>⚙️ Settings</h2>
              <button 
                className="modal-close"
                onClick={() => setSettingsModal(false)}
              >
                ×
              </button>
            </div>
            
            <form onSubmit={handleUpdateSettings} className="settings-form">
              <div className="form-section">
                <h3>API Keys</h3>
                <div className="form-group">
                  <label>OpenAI API Key:</label>
                  <input
                    type="password"
                    placeholder={settings?.openai_api_key_set ? "••••••••••••••••" : "Enter OpenAI API key"}
                    value={settingsForm.openai_api_key || ''}
                    onChange={(e) => setSettingsForm({ ...settingsForm, openai_api_key: e.target.value })}
                  />
                  {settings?.openai_api_key_set && (
                    <span className="api-key-status">✅ Set</span>
                  )}
                </div>
                
                <div className="form-group">
                  <label>Anthropic API Key:</label>
                  <input
                    type="password"
                    placeholder={settings?.anthropic_api_key_set ? "••••••••••••••••" : "Enter Anthropic API key"}
                    value={settingsForm.anthropic_api_key || ''}
                    onChange={(e) => setSettingsForm({ ...settingsForm, anthropic_api_key: e.target.value })}
                  />
                  {settings?.anthropic_api_key_set && (
                    <span className="api-key-status">✅ Set</span>
                  )}
                </div>
                
                <div className="form-group">
                  <label>Ollama Base URL:</label>
                  <input
                    type="text"
                    placeholder="http://localhost:11434"
                    value={settingsForm.ollama_base_url || settings?.ollama_base_url || ''}
                    onChange={(e) => setSettingsForm({ ...settingsForm, ollama_base_url: e.target.value })}
                  />
                  {settings?.ollama_configured && (
                    <span className="api-key-status">✅ Configured</span>
                  )}
                  <small>Local Ollama server endpoint (default: http://localhost:11434)</small>
                </div>
              </div>
              
              <div className="form-section">
                <h3>AI Settings</h3>
                <div className="form-group">
                  <label>Default Provider:</label>
                  <select
                    value={settingsForm.default_ai_provider || settings?.default_ai_provider || 'openai'}
                    onChange={(e) => setSettingsForm({ ...settingsForm, default_ai_provider: e.target.value })}
                  >
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic</option>
                    <option value="ollama">Ollama (Local)</option>
                  </select>
                </div>
                
                <div className="form-group">
                  <label>Default Model:</label>
                  <select
                    value={settingsForm.default_ai_model || settings?.default_ai_model || (modelOptions.openai[0] || 'gpt-4o')}
                    onChange={(e) => setSettingsForm({ ...settingsForm, default_ai_model: e.target.value })}
                  >
                    {((modelOptions as any)[(settingsForm.default_ai_provider || settings?.default_ai_provider || 'openai')] || []).map((model: string) => (
                      <option key={model} value={model}>
                        {model.includes('gpt-4o') ? `${model} (Latest)` :
                         model.includes('gpt-4-turbo') ? `${model.replace('gpt-4-turbo', 'GPT-4 Turbo')}` :
                         model.includes('gpt-4') ? `${model.replace('gpt-4', 'GPT-4')}` :
                         model.includes('gpt-3.5-turbo') ? `${model.replace('gpt-3.5-turbo', 'GPT-3.5 Turbo')}` :
                         model.includes('claude-3-5-sonnet') ? 'Claude 3.5 Sonnet' :
                         model.includes('claude-3-5-haiku') ? 'Claude 3.5 Haiku' :
                         model.includes('claude-3-opus') ? 'Claude 3 Opus' :
                         model.includes('claude-3-sonnet') ? 'Claude 3 Sonnet' :
                         model.includes('claude-3-haiku') ? 'Claude 3 Haiku' :
                         model}
                      </option>
                    ))}
                    {((modelOptions as any)[(settingsForm.default_ai_provider || settings?.default_ai_provider || 'openai')] || []).length === 0 && (
                      <option value="" disabled>No models available</option>
                    )}
                  </select>
                </div>
                
                <div className="form-group">
                  <label>Temperature:</label>
                  <input
                    type="number"
                    min="0"
                    max="2"
                    step="0.1"
                    value={settingsForm.ai_temperature ?? settings?.ai_temperature ?? 0.7}
                    onChange={(e) => setSettingsForm({ ...settingsForm, ai_temperature: parseFloat(e.target.value) })}
                  />
                </div>
                
                <div className="form-group">
                  <label>Max Tokens:</label>
                  <input
                    type="number"
                    min="1"
                    max="16000"
                    value={settingsForm.ai_max_tokens ?? settings?.ai_max_tokens ?? 4000}
                    onChange={(e) => setSettingsForm({ ...settingsForm, ai_max_tokens: parseInt(e.target.value) })}
                  />
                </div>
              </div>
              
              <div className="modal-actions">
                <button
                  type="button"
                  className="button button-secondary"
                  onClick={() => setSettingsModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="button button-primary"
                  disabled={loading}
                >
                  {loading ? 'Updating...' : 'Save Settings'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
