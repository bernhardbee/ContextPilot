/**
 * Main App component for ContextPilot.
 */
import React, { useState, useEffect } from 'react';
import './App.css';
import { contextAPI } from './api';
import {
  ContextUnit,
  ContextUnitCreate,
  ContextType,
  GeneratedPrompt,
  Stats,
  AIResponse,
  Conversation,
} from './types';

function App() {
  const [contexts, setContexts] = useState<ContextUnit[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'contexts' | 'prompt' | 'ai'>('contexts');

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
  const [aiModel, setAiModel] = useState('gpt-4-turbo-preview');
  const [aiResponse, setAiResponse] = useState<AIResponse | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);

  // Load contexts and stats on mount
  useEffect(() => {
    loadContexts();
    loadStats();
  }, []);

  const loadContexts = async () => {
    try {
      setLoading(true);
      const data = await contextAPI.listContexts();
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
        <h1>🧭 ContextPilot</h1>
        <p>AI-powered personal context engine</p>
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
          className={`tab ${activeTab === 'contexts' ? 'active' : ''}`}
          onClick={() => setActiveTab('contexts')}
        >
          📝 Manage Contexts
        </button>
        <button
          className={`tab ${activeTab === 'prompt' ? 'active' : ''}`}
          onClick={() => setActiveTab('prompt')}
        >
          ✨ Generate Prompt
        </button>
        <button
          className={`tab ${activeTab === 'ai' ? 'active' : ''}`}
          onClick={() => setActiveTab('ai')}
        >
          🤖 AI Chat
        </button>
      </div>

      <div className="main-content">
        {activeTab === 'contexts' && (
          <>
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
          <form onSubmit={handleGeneratePrompt}>
            <div className="form-group">
              <label>Task</label>
              <textarea
                value={task}
                onChange={(e) => setTask(e.target.value)}
                placeholder="Describe what you want to do..."
              />
            </div>

            <div className="form-group">
              <label>Max Context Units</label>
              <input
                type="number"
                min="1"
                max="20"
                value={maxContexts}
                onChange={(e) => setMaxContexts(parseInt(e.target.value))}
              />
            </div>

            <button type="submit" className="button button-secondary" disabled={loading}>
              {loading ? 'Generating...' : 'Generate Prompt'}
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
          </>
        )}

        {activeTab === 'prompt' && (
          <>
            <div className="card">
              <h2>Generate Prompt</h2>
              <form onSubmit={handleGeneratePrompt}>
                <div className="form-group">
                  <label>Task</label>
                  <textarea
                    value={task}
                    onChange={(e) => setTask(e.target.value)}
                    placeholder="Describe what you want to do..."
                  />
                </div>

                <div className="form-group">
                  <label>Max Context Units</label>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={maxContexts}
                    onChange={(e) => setMaxContexts(parseInt(e.target.value))}
                  />
                </div>

                <button type="submit" className="button button-secondary" disabled={loading}>
                  {loading ? 'Generating...' : 'Generate Prompt'}
                </button>
              </form>
            </div>

            {generatedPrompt && (
              <div className="card prompt-output">
                <h2>Generated Prompt</h2>
                <div className="prompt-display">{generatedPrompt.generated_prompt}</div>
                <button className="button copy-button" onClick={handleCopyPrompt}>
                  Copy to Clipboard
                </button>

                <div className="relevant-contexts">
                  <h3>Relevant Contexts Used ({generatedPrompt.relevant_context.length})</h3>
                  {generatedPrompt.relevant_context.map((ranked, idx) => (
                    <div key={idx} className="relevant-context-item">
                      <div className="context-header">
                        <span className={`context-type ${ranked.context_unit.type}`}>
                          {ranked.context_unit.type}
                        </span>
                        <span className="relevance-score">
                          Relevance: {(ranked.relevance_score * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="context-content">{ranked.context_unit.content}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {activeTab === 'ai' && (
          <>
            <div className="card">
              <h2>🤖 AI Chat with Context</h2>
              <p className="help-text">
                Ask a question and the AI will respond using your relevant contexts.
              </p>
              <form onSubmit={handleAIChat}>
                <div className="form-group">
                  <label>Question / Task</label>
                  <textarea
                    value={aiTask}
                    onChange={(e) => setAiTask(e.target.value)}
                    placeholder="Ask a question or describe a task..."
                    rows={4}
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
                          setAiModel('gpt-4-turbo-preview');
                        } else {
                          setAiModel('claude-3-opus-20240229');
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
                          <option value="gpt-4-turbo-preview">GPT-4 Turbo</option>
                          <option value="gpt-4">GPT-4</option>
                          <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                        </>
                      ) : (
                        <>
                          <option value="claude-3-opus-20240229">Claude 3 Opus</option>
                          <option value="claude-3-sonnet-20240229">Claude 3 Sonnet</option>
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
            </div>

            {aiResponse && (
              <div className="card ai-response">
                <h2>AI Response</h2>
                <div className="response-meta">
                  <span className="meta-item">
                    Provider: <strong>{aiResponse.provider}</strong>
                  </span>
                  <span className="meta-item">
                    Model: <strong>{aiResponse.model}</strong>
                  </span>
                  <span className="meta-item">
                    Contexts Used: <strong>{aiResponse.context_ids.length}</strong>
                  </span>
                </div>
                <div className="response-content">{aiResponse.response}</div>
                <button className="button copy-button" onClick={handleCopyAIResponse}>
                  Copy Response
                </button>

                <details className="prompt-details">
                  <summary>View Full Prompt Sent to AI</summary>
                  <pre className="prompt-code">{aiResponse.prompt_used}</pre>
                </details>
              </div>
            )}

            <div className="card">
              <h2>Conversation History ({conversations.length})</h2>
              {conversations.length === 0 ? (
                <p className="help-text">No conversations yet. Start chatting above!</p>
              ) : (
                <div className="conversation-list">
                  {conversations.map((conv) => (
                    <div key={conv.id} className="conversation-item">
                      <div className="conversation-header">
                        <span className="conversation-task">{conv.task}</span>
                        <span className="conversation-meta">
                          {conv.provider} · {conv.model}
                        </span>
                      </div>
                      <div className="conversation-footer">
                        <span className="conversation-date">
                          {new Date(conv.created_at).toLocaleString()}
                        </span>
                        <button
                          className="button button-small"
                          onClick={() => handleViewConversation(conv.id)}
                        >
                          View
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {selectedConversation && (
              <div className="card conversation-detail">
                <h2>Conversation Details</h2>
                <button
                  className="button button-small"
                  onClick={() => setSelectedConversation(null)}
                >
                  Close
                </button>
                <div className="conversation-messages">
                  {selectedConversation.messages?.map((msg, idx) => (
                    <div key={idx} className={`message message-${msg.role}`}>
                      <div className="message-role">{msg.role}</div>
                      <div className="message-content">{msg.content}</div>
                      {msg.tokens && (
                        <div className="message-meta">
                          Tokens: {msg.tokens} · {msg.finish_reason}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {generatedPrompt && activeTab === 'prompt' && (
          <></>
        )}
      </div>
    </div>
  );
}

export default App;
