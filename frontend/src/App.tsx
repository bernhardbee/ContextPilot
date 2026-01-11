/**
 * Main App component for ContextPilot.
 */
import React, { useEffect, useState } from 'react';
import { contextAPI } from './api';
import './App.css';
import { ContextTemplates } from './ContextTemplates';
import { ContextTools } from './ContextTools';
import {
  AIResponse,
  ContextType,
  ContextUnit,
  ContextUnitCreate,
  Conversation,
  GeneratedPrompt,
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

  // Task and prompt states
  const [task, setTask] = useState('');
  const [maxContexts, setMaxContexts] = useState(5);
  const [generatedPrompt, setGeneratedPrompt] = useState<GeneratedPrompt | null>(null);

  // AI Chat states
  const [aiTask, setAiTask] = useState('');
  const [aiMaxContexts, setAiMaxContexts] = useState(5);
  const [aiProvider, setAiProvider] = useState('openai');
  const [aiModel, setAiModel] = useState('gpt-5');
  const [aiResponse, setAiResponse] = useState<AIResponse | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);

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

  const handleGeneratePrompt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!task.trim()) {
      setError('Task is required');
      return;
    }

    try {
      setLoading(true);
      const result = await contextAPI.generatePrompt({
        task,
        max_context_units: maxContexts,
      });
      setGeneratedPrompt(result);
      setError(null);
    } catch (err) {
      setError('Failed to generate prompt');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyPrompt = () => {
    if (generatedPrompt) {
      navigator.clipboard.writeText(generatedPrompt.generated_prompt);
      setSuccess('Prompt copied to clipboard!');
      setTimeout(() => setSuccess(null), 2000);
    }
  };
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
    if (!aiTask.trim()) {
      setError('Task is required');
      return;
    }

    try {
      setLoading(true);
      setAiResponse(null);
      const result = await contextAPI.chatWithAI({
        task: aiTask,
        max_context_units: aiMaxContexts,
        provider: aiProvider,
        model: aiModel,
        conversation_id: selectedConversation?.id,
      });
      setAiResponse(result);
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
    } catch (err) {
      setError('Failed to load conversation');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyAIResponse = () => {
    if (aiResponse) {
      navigator.clipboard.writeText(aiResponse.response);
      setSuccess('Response copied to clipboard!');
      setTimeout(() => setSuccess(null), 2000);
    }
  };

  
  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div>
            <h1>🧭 ContextPilot</h1>
            <p>AI-powered personal context engine</p>
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

      {error && <div className="error">{error}</div>}
      {success && <div className="success">{success}</div>}

      <div className="tabs">
        <button
          className={`tab ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          🤖 AI Workspace
        </button>
        <button
          className={`tab ${activeTab === 'manage' ? 'active' : ''}`}
          onClick={() => setActiveTab('manage')}
        >
          📝 Manage Contexts
        </button>
      </div>

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
                    <h2>🚀 AI Assistant</h2>
                    <div className="chat-stats">
                      <span className="stat-badge">{contexts.length} contexts available</span>
                    </div>
                  </div>

                  <form onSubmit={handleAIChat} className="chat-form">
                    <div className="form-group">
                      <label>Your Task or Question</label>
                      <textarea
                        value={aiTask}
                        onChange={(e) => setAiTask(e.target.value)}
                        placeholder="Ask a question or describe a task... Your contexts will be automatically included."
                        rows={5}
                      />
                    </div>

                    <div className="form-row">
                      <div className="form-group">
                        <label>Provider</label>
                        <select
                          value={aiProvider}
                          onChange={(e) => {
                            setAiProvider(e.target.value);
                            if (e.target.value === 'openai') {
                              setAiModel('gpt-5');
                            } else {
                              setAiModel('claude-3-5-sonnet-20241022');
                            }
                          }}
                        >
                          <option value="openai">OpenAI</option>
                          <option value="anthropic">Anthropic</option>
                        </select>
                      </div>

                      <div className="form-group">
                        <label>Model</label>
                        <select
                          value={aiModel}
                          onChange={(e) => setAiModel(e.target.value)}
                        >
                          {aiProvider === 'openai' ? (
                            <>
                              <option value="gpt-5">GPT-5</option>
                              <option value="gpt-4o">GPT-4o</option>
                              <option value="gpt-4o-mini">GPT-4o Mini</option>
                              <option value="gpt-4-turbo">GPT-4 Turbo</option>
                              <option value="gpt-4">GPT-4</option>
                            </>
                          ) : (
                            <>
                              <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet</option>
                              <option value="claude-3-5-haiku-20241022">Claude 3.5 Haiku</option>
                              <option value="claude-3-opus-20240229">Claude 3 Opus</option>
                              <option value="claude-3-haiku-20240307">Claude 3 Haiku</option>
                            </>
                          )}
                        </select>
                      </div>

                      <div className="form-group">
                        <label>Max Contexts</label>
                        <input
                          type="number"
                          min="1"
                          max="20"
                          value={aiMaxContexts}
                          onChange={(e) => setAiMaxContexts(parseInt(e.target.value))}
                        />
                      </div>
                    </div>

                    <button type="submit" className="button button-ai" disabled={loading}>
                      {loading ? 'Thinking...' : '🚀 Ask AI'}
                    </button>
                  </form>

                  {aiResponse && (
                    <div className="ai-response">
                      <div className="response-header">
                        <h3>AI Response</h3>
                        <button className="button button-small copy-button" onClick={handleCopyAIResponse}>
                          📋 Copy
                        </button>
                      </div>
                      <div className="response-meta">
                        <span className="meta-item">
                          {aiResponse.provider} / {aiResponse.model}
                        </span>
                        <span className="meta-item">
                          {aiResponse.context_ids.length} contexts used
                        </span>
                      </div>
                      <div className="response-content">{aiResponse.response}</div>

                      <details className="prompt-details">
                        <summary>View Full Prompt Sent to AI</summary>
                        <pre className="prompt-code">{aiResponse.prompt_used}</pre>
                      </details>
                    </div>
                  )}

                  {selectedConversation && (
                    <div className="conversation-details">
                      <div className="conversation-header">
                        <h3>Conversation Details</h3>
                        <button 
                          className="button button-small"
                          onClick={() => setSelectedConversation(null)}
                        >
                          ✕ Close
                        </button>
                      </div>
                      <div className="conversation-messages">
                        {selectedConversation.messages?.map((msg, idx) => (
                          <div key={idx} className={`message message-${msg.role}`}>
                            <div className="message-role">{msg.role}</div>
                            <div className="message-content">{msg.content}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
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
            <ContextTools
              onFiltersChange={setFilters}
              onRefresh={loadContexts}
            />
            
            <ContextTemplates onUseTemplate={handleUseTemplate} />
            
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
                  </select>
                </div>
                
                <div className="form-group">
                  <label>Default Model:</label>
                  <select
                    value={settingsForm.default_ai_model || settings?.default_ai_model || 'gpt-5'}
                    onChange={(e) => setSettingsForm({ ...settingsForm, default_ai_model: e.target.value })}
                  >
                    {(settingsForm.default_ai_provider || settings?.default_ai_provider) === 'anthropic' ? (
                      <>
                        <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet</option>
                        <option value="claude-3-5-haiku-20241022">Claude 3.5 Haiku</option>
                        <option value="claude-3-opus-20240229">Claude 3 Opus</option>
                        <option value="claude-3-haiku-20240307">Claude 3 Haiku</option>
                      </>
                    ) : (
                      <>
                        <option value="gpt-5">GPT-5</option>
                        <option value="gpt-4o">GPT-4o</option>
                        <option value="gpt-4o-mini">GPT-4o Mini</option>
                        <option value="gpt-4-turbo">GPT-4 Turbo</option>
                        <option value="gpt-4">GPT-4</option>
                      </>
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
                    max="4000"
                    value={settingsForm.ai_max_tokens ?? settings?.ai_max_tokens ?? 2000}
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
