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
} from './types';

function App() {
  const [contexts, setContexts] = useState<ContextUnit[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

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

      <div className="main-content">
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
      </div>
    </div>
  );
}

export default App;
