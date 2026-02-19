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
  ProviderInfo,
  ProvidersResponse,
  Settings,
  SettingsUpdate,
  Stats,
} from './types';

type InteractionChannel = 'User ↔ Frontend' | 'Frontend ↔ Backend';

interface InteractionLogEntry {
  id: string;
  timestamp: string;
  channel: InteractionChannel;
  message: string;
}

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
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [settingsModal, setSettingsModal] = useState(false);
  const [settingsForm, setSettingsForm] = useState<SettingsUpdate>({});
  const [settingsTab, setSettingsTab] = useState<string>('openai');
  const [settingsSectionTab, setSettingsSectionTab] = useState<'provider' | 'general'>('general');
  const [interactionLogs, setInteractionLogs] = useState<InteractionLogEntry[]>([]);
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    try {
      return window.localStorage.getItem('contextpilot-dark-mode') === 'true';
    } catch {
      return false;
    }
  });

  const appendInteractionLog = (channel: InteractionChannel, message: string) => {
    const entry: InteractionLogEntry = {
      id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      timestamp: new Date().toISOString(),
      channel,
      message,
    };

    setInteractionLogs((previousLogs) => {
      const nextLogs = [...previousLogs, entry];
      return nextLogs.slice(-200);
    });
  };

  useEffect(() => {
    if (error) {
      appendInteractionLog('User ↔ Frontend', `Status error: ${error}`);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [error]);

  useEffect(() => {
    if (success) {
      appendInteractionLog('User ↔ Frontend', `Status success: ${success}`);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [success]);

  useEffect(() => {
    try {
      window.localStorage.setItem('contextpilot-dark-mode', String(darkMode));
    } catch {
      // no-op: storage can be unavailable in restricted environments
    }

    document.body.classList.toggle('dark-mode', darkMode);
    return () => {
      document.body.classList.remove('dark-mode');
    };
  }, [darkMode]);

  // Load contexts and stats on mount
  useEffect(() => {
    loadContexts();
    loadStats();
    loadSettings();
    loadProviders();
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
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const apiFilters: any = {};
      if (filters.type) apiFilters.type = filters.type;
      if (filters.tags) apiFilters.tags = filters.tags;
      if (filters.search) apiFilters.search = filters.search;
      if (filters.status) apiFilters.status_filter = filters.status;
      
      const data = await contextAPI.listContexts(false, apiFilters);
      setContexts(data);
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
      const { provider, model } = resolveConversationChatSelection(selectedConversation, data);
      setAiProvider(provider);
      if (model) {
        setAiModel(model);
      }
      if (data.ai_max_tokens) setAiMaxTokens(data.ai_max_tokens);
      if (data.ai_temperature !== undefined) setAiTemperature(data.ai_temperature);
    } catch (err) {
      console.error('Failed to load settings:', err);
    }
  };

  const getProviderModelOptions = (providerName: string): string[] => {
    const models = (modelOptions as Record<string, string[]>)[providerName];
    return Array.isArray(models) ? models : [];
  };

  const getConfiguredDefaultModelForProvider = (
    providerName: string,
    settingsSnapshot: Settings | null = settings
  ): string => {
    const availableModels = getProviderModelOptions(providerName);
    if (availableModels.length === 0) {
      return '';
    }

    const providerSpecificDefault =
      providerName === 'openai'
        ? settingsSnapshot?.openai_default_model
        : providerName === 'anthropic'
          ? settingsSnapshot?.anthropic_default_model
          : providerName === 'ollama'
            ? settingsSnapshot?.ollama_default_model
            : undefined;

    if (providerSpecificDefault && availableModels.includes(providerSpecificDefault)) {
      return providerSpecificDefault;
    }

    if (
      settingsSnapshot?.default_ai_provider === providerName &&
      settingsSnapshot.default_ai_model &&
      availableModels.includes(settingsSnapshot.default_ai_model)
    ) {
      return settingsSnapshot.default_ai_model;
    }

    return availableModels[0];
  };

  const resolveConversationChatSelection = (
    conversation: Conversation | null,
    settingsSnapshot: Settings | null = settings
  ): { provider: string; model: string } => {
    const fallbackProvider = settingsSnapshot?.default_ai_provider || 'openai';

    if (!conversation) {
      return {
        provider: fallbackProvider,
        model: getConfiguredDefaultModelForProvider(fallbackProvider, settingsSnapshot),
      };
    }

    const conversationProvider = conversation.provider || fallbackProvider;
    const availableModels = getProviderModelOptions(conversationProvider);

    if (conversation.model && availableModels.includes(conversation.model)) {
      return {
        provider: conversationProvider,
        model: conversation.model,
      };
    }

    return {
      provider: conversationProvider,
      model: getConfiguredDefaultModelForProvider(conversationProvider, settingsSnapshot),
    };
  };

  const loadProviders = async () => {
    try {
      const data: ProvidersResponse = await contextAPI.getProviders();
      setProviders(data.providers);
      // Set initial settings tab to the default provider
      if (data.default_provider) {
        setSettingsTab(data.default_provider);
      }
    } catch (err) {
      console.error('Failed to load providers:', err);
    }
  };

  const handleUpdateSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    appendInteractionLog('User ↔ Frontend', 'User submitted settings update.');
    try {
      setLoading(true);
      
      // Build settings update - only include fields that were actually changed/filled
      const updateData: SettingsUpdate = {};
      
      // Only send API keys if they have values (non-empty strings)
      if (settingsForm.openai_api_key?.trim()) {
        updateData.openai_api_key = settingsForm.openai_api_key.trim();
      }
      if (settingsForm.openai_base_url?.trim()) {
        updateData.openai_base_url = settingsForm.openai_base_url.trim();
      }
      if (settingsForm.openai_default_model?.trim()) {
        updateData.openai_default_model = settingsForm.openai_default_model.trim();
      }
      if (settingsForm.anthropic_api_key?.trim()) {
        updateData.anthropic_api_key = settingsForm.anthropic_api_key.trim();
      }
      if (settingsForm.anthropic_default_model?.trim()) {
        updateData.anthropic_default_model = settingsForm.anthropic_default_model.trim();
      }
      if (settingsForm.ollama_base_url?.trim()) {
        updateData.ollama_base_url = settingsForm.ollama_base_url.trim();
      }
      if (settingsForm.ollama_default_model?.trim()) {
        updateData.ollama_default_model = settingsForm.ollama_default_model.trim();
      }
      if (settingsForm.ollama_keep_alive?.trim()) {
        updateData.ollama_keep_alive = settingsForm.ollama_keep_alive.trim();
      }
      
      // Always include AI settings if they exist
      if (settingsForm.default_ai_provider !== undefined) {
        updateData.default_ai_provider = settingsForm.default_ai_provider;
      }
      if (settingsForm.default_ai_model !== undefined) {
        updateData.default_ai_model = settingsForm.default_ai_model;
      }
      if (settingsForm.ai_temperature !== undefined) {
        updateData.ai_temperature = settingsForm.ai_temperature;
      }
      if (settingsForm.ai_max_tokens !== undefined) {
        updateData.ai_max_tokens = settingsForm.ai_max_tokens;
      }
      if (settingsForm.openai_temperature !== undefined) {
        updateData.openai_temperature = settingsForm.openai_temperature;
      }
      if (settingsForm.openai_top_p !== undefined) {
        updateData.openai_top_p = settingsForm.openai_top_p;
      }
      if (settingsForm.openai_max_tokens !== undefined) {
        updateData.openai_max_tokens = settingsForm.openai_max_tokens;
      }
      if (settingsForm.anthropic_temperature !== undefined) {
        updateData.anthropic_temperature = settingsForm.anthropic_temperature;
      }
      if (settingsForm.anthropic_top_p !== undefined) {
        updateData.anthropic_top_p = settingsForm.anthropic_top_p;
      }
      if (settingsForm.anthropic_top_k !== undefined) {
        updateData.anthropic_top_k = settingsForm.anthropic_top_k;
      }
      if (settingsForm.anthropic_max_tokens !== undefined) {
        updateData.anthropic_max_tokens = settingsForm.anthropic_max_tokens;
      }
      if (settingsForm.ollama_temperature !== undefined) {
        updateData.ollama_temperature = settingsForm.ollama_temperature;
      }
      if (settingsForm.ollama_top_p !== undefined) {
        updateData.ollama_top_p = settingsForm.ollama_top_p;
      }
      if (settingsForm.ollama_num_predict !== undefined) {
        updateData.ollama_num_predict = settingsForm.ollama_num_predict;
      }
      if (settingsForm.ollama_num_ctx !== undefined) {
        updateData.ollama_num_ctx = settingsForm.ollama_num_ctx;
      }
      
      appendInteractionLog('Frontend ↔ Backend', 'Sending settings update request to backend.');
      await contextAPI.updateSettings(updateData);
      appendInteractionLog('Frontend ↔ Backend', 'Settings update completed successfully.');
      setSuccess('Settings updated successfully!');
      setSettingsModal(false);
      setSettingsForm({});
      loadSettings(); // Reload settings to get updated status
      loadProviders(); // Reload providers to update configuration status
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      appendInteractionLog('Frontend ↔ Backend', `Settings update failed: ${err?.response?.data?.message || err?.response?.data?.detail || 'unknown error'}`);
      setError(err.response?.data?.message || err.response?.data?.detail || 'Failed to update settings');
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
      openai_base_url: settings?.openai_base_url,
      openai_default_model: settings?.openai_default_model,
      openai_temperature: settings?.openai_temperature ?? undefined,
      openai_top_p: settings?.openai_top_p ?? undefined,
      openai_max_tokens: settings?.openai_max_tokens ?? undefined,
      anthropic_default_model: settings?.anthropic_default_model,
      anthropic_temperature: settings?.anthropic_temperature ?? undefined,
      anthropic_top_p: settings?.anthropic_top_p ?? undefined,
      anthropic_top_k: settings?.anthropic_top_k ?? undefined,
      anthropic_max_tokens: settings?.anthropic_max_tokens ?? undefined,
      ollama_base_url: settings?.ollama_base_url,
      ollama_default_model: settings?.ollama_default_model,
      ollama_temperature: settings?.ollama_temperature ?? undefined,
      ollama_top_p: settings?.ollama_top_p ?? undefined,
      ollama_num_predict: settings?.ollama_num_predict ?? undefined,
      ollama_num_ctx: settings?.ollama_num_ctx ?? undefined,
      ollama_keep_alive: settings?.ollama_keep_alive,
    });
    setSettingsSectionTab('general');
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

    appendInteractionLog('User ↔ Frontend', `User sent chat message (${aiTask.trim().length} chars).`);

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
      
      appendInteractionLog('Frontend ↔ Backend', `Sending chat request to backend (provider: ${aiProvider}, model: ${aiModel}).`);
      const result = await contextAPI.chatWithAI({
        task: taskToSend,
        max_context_units: maxContextsToSend,
        provider: aiProvider,
        model: aiModel,
        conversation_id: selectedConversation?.id,
        max_tokens: aiMaxTokens,
        temperature: aiTemperature,
      });
      appendInteractionLog('Frontend ↔ Backend', `Received chat response from backend (provider: ${result.provider}, model: ${result.model}).`);
      setAiProvider(result.provider);
      setAiModel(result.model);
      
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
      } else {
        setSelectedConversation((previousConversation) => (
          previousConversation
            ? {
                ...previousConversation,
                provider: result.provider,
                model: result.model,
              }
            : previousConversation
        ));
      }
      
      setError(null);
      await loadConversations();
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      appendInteractionLog('Frontend ↔ Backend', `Chat request failed: ${err?.response?.data?.message || err?.response?.data?.detail || err?.message || 'unknown error'}`);
      const backendDetail = err?.response?.data?.message || err?.response?.data?.detail;
      const statusCode = err?.response?.status;

      let errorMessage = backendDetail;
      if (!errorMessage && (statusCode === 401 || statusCode === 403)) {
        errorMessage = `${aiProvider.toUpperCase()} authentication failed for model '${aiModel}'. Please verify the API key in Settings.`;
      }
      if (!errorMessage) {
        errorMessage = `Failed to generate AI response using provider '${aiProvider}' and model '${aiModel}'. Please verify provider connection and credentials in Settings.`;
      }

      setError(errorMessage);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getValidationModel = (providerName: string): string | undefined => {
    if (providerName === 'openai') {
      return settingsForm.openai_default_model || settings?.openai_default_model || settingsForm.default_ai_model || settings?.default_ai_model;
    }
    if (providerName === 'anthropic') {
      return settingsForm.anthropic_default_model || settings?.anthropic_default_model || settingsForm.default_ai_model || settings?.default_ai_model;
    }
    if (providerName === 'ollama') {
      return settingsForm.ollama_default_model || settings?.ollama_default_model || settingsForm.default_ai_model || settings?.default_ai_model;
    }
    return settingsForm.default_ai_model || settings?.default_ai_model;
  };

  const handleValidateProviderConnection = async () => {
    appendInteractionLog('User ↔ Frontend', `User requested provider validation for '${settingsTab}'.`);
    try {
      setLoading(true);
      const modelToCheck = getValidationModel(settingsTab);
      appendInteractionLog('Frontend ↔ Backend', `Sending provider validation request (${settingsTab}${modelToCheck ? `, model: ${modelToCheck}` : ''}).`);
      const result = await contextAPI.validateProviderConnection(settingsTab, modelToCheck);
      appendInteractionLog('Frontend ↔ Backend', `Provider validation result for '${settingsTab}': ${result.valid ? 'valid' : 'invalid'}.`);

      if (result.valid) {
        setSuccess(result.message);
        setError(null);
      } else {
        setError(result.message);
      }
    } catch (err: any) {
      appendInteractionLog('Frontend ↔ Backend', `Provider validation failed for '${settingsTab}': ${err?.response?.data?.message || err?.response?.data?.detail || 'unknown error'}`);
      const message = err?.response?.data?.message || err?.response?.data?.detail || `Failed to validate provider '${settingsTab}'.`;
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleViewConversation = async (id: string) => {
    appendInteractionLog('User ↔ Frontend', `User opened conversation '${id}'.`);
    try {
      setLoading(true);
      appendInteractionLog('Frontend ↔ Backend', `Requesting conversation '${id}' from backend.`);
      const conversation = await contextAPI.getConversation(id);
      appendInteractionLog('Frontend ↔ Backend', `Loaded conversation '${id}' from backend.`);
      setSelectedConversation(conversation);
      const { provider, model } = resolveConversationChatSelection(conversation);
      setAiProvider(provider);
      if (model) {
        setAiModel(model);
      }
      // Set current chat messages for display
      if (conversation.messages) {
        const filteredMessages = conversation.messages.filter(msg => msg.role !== 'system');
        setCurrentChatMessages(filteredMessages);
      }
      // Clear any pending response
      setAiTask('');
    } catch (err) {
      appendInteractionLog('Frontend ↔ Backend', `Failed to load conversation '${id}' from backend.`);
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
    const { provider, model } = resolveConversationChatSelection(null);
    setAiProvider(provider);
    if (model) {
      setAiModel(model);
    }
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
        // eslint-disable-next-line no-console
        // eslint-disable-next-line no-console
        console.log(`Message truncated: ${role} message was cut off (${tokens || 'unknown'} tokens used)`);
        return <span style={{ color: '#999', fontStyle: 'italic' }}>(Response was truncated due to length limit. Used {tokens} tokens.)</span>;
      }

      // eslint-disable-next-line no-console
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
          img: ({ ...props }) => (
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
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          code: ({ inline, className, children, ...props }: any) => {
            if (inline) {
              return (
                <code
                  style={{
                    backgroundColor: darkMode ? '#1f2937' : '#f6f8fa',
                    padding: '2px 6px',
                    borderRadius: '3px',
                    fontSize: '0.9em',
                    color: darkMode ? '#e5e7eb' : '#24292f',
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
          pre: ({ children, ...props }) => {
            const codeContent = React.Children.toArray(children)
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
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
          a: ({ children, ...props }) => (
            <a
              {...props}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                color: darkMode ? '#58a6ff' : '#0969da',
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
    <div className={`app ${darkMode ? 'dark-mode' : ''}`}>
      <header className="header">
        <div className="header-content">
          <div className="title-section">
            <h1>🧭 ContextPilot</h1>
            <span className="by-signature">
              by <img src="b-logo.png" alt="B" className="b-logo" />
            </span>
          </div>
          <div className="header-actions">
            {(error || success) && (
              <div className={`header-status ${error ? 'error' : 'success'}`} title={error || success || ''}>
                {error || success}
              </div>
            )}
            <button 
              className="settings-button"
              onClick={openSettingsModal}
              title="Settings"
            >
              ⚙️
            </button>
          </div>
        </div>
      </header>

      <div className="workspace-layout">
        {activeTab === 'chat' && (
          <>
            <div className={`left-sidebar-stack ${showConversations ? 'visible' : 'collapsed'}`}>
              {/* Left Sidebar: Conversations */}
              <div className={`sidebar sidebar-left sidebar-left-panel ${showConversations ? 'visible' : 'collapsed'}`}>
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
                  <div className="sidebar-content conversation-pane">
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
                              </div>
                              <div className="conversation-meta-bottom">
                                <span className="conversation-date">{new Date(conv.created_at).toLocaleDateString()}</span>
                                <span className="conversation-message-count">{conv.message_count} msgs</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {showConversations && (
                <div className="interaction-log-panel sidebar-log-panel interaction-log-panel-left">
                  <div className="interaction-log-header sidebar-log-header">
                    <h3>Interaction Log</h3>
                    <button
                      type="button"
                      className="button button-small button-secondary"
                      onClick={() => setInteractionLogs([])}
                      disabled={interactionLogs.length === 0}
                    >
                      Clear Log
                    </button>
                  </div>
                  <div className="interaction-log-list sidebar-log-list" role="log" aria-label="interaction log output">
                    {interactionLogs.length === 0 ? (
                      <div className="interaction-log-empty">No interactions recorded yet.</div>
                    ) : (
                      [...interactionLogs].reverse().map((entry) => (
                        <div key={entry.id} className="interaction-log-entry">
                          <span className="interaction-log-time">{new Date(entry.timestamp).toLocaleTimeString()}</span>
                          <span className="interaction-log-channel">{entry.channel}</span>
                          <span className="interaction-log-message">{entry.message}</span>
                        </div>
                      ))
                    )}
                  </div>
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
                        <p>Ask me anything. I&apos;ll use your personal contexts to provide relevant responses.</p>
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
                              const nextProvider = e.target.value;
                              setAiProvider(nextProvider);
                              const providerDefaultModel = getConfiguredDefaultModelForProvider(nextProvider);
                              if (providerDefaultModel) {
                                setAiModel(providerDefaultModel);
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
                            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
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
                            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
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
                <button 
                  className="toggle-button"
                  onClick={() => setShowContexts(!showContexts)}
                  title={showContexts ? "Hide contexts" : "Show contexts"}
                >
                  {showContexts ? '▶' : '◀'}
                </button>
                <h3>📚 Your Contexts</h3>
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
          <div className="modal modal-large" onClick={(e) => e.stopPropagation()}>
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
              <div className="settings-main-tabs" role="tablist" aria-label="settings sections">
                <button
                  type="button"
                  role="tab"
                  aria-selected={settingsSectionTab === 'general'}
                  className={`settings-main-tab ${settingsSectionTab === 'general' ? 'active' : ''}`}
                  onClick={() => setSettingsSectionTab('general')}
                >
                  General Settings
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={settingsSectionTab === 'provider'}
                  className={`settings-main-tab ${settingsSectionTab === 'provider' ? 'active' : ''}`}
                  onClick={() => setSettingsSectionTab('provider')}
                >
                  Provider Settings
                </button>
              </div>

              {settingsSectionTab === 'provider' && (
                <div className="settings-content-panel settings-column-provider">
                  {/* Provider Tabs */}
                  <div className="provider-tabs">
                    {providers.map((provider) => (
                      <button
                        key={provider.name}
                        type="button"
                        className={`provider-tab ${settingsTab === provider.name ? 'active' : ''}`}
                        onClick={() => setSettingsTab(provider.name)}
                      >
                        {provider.display_name}
                        {provider.configured && <span className="tab-indicator">●</span>}
                      </button>
                    ))}
                  </div>

                  {/* Provider Settings Content */}
                  <div className="provider-settings-content">
                    {providers.map((provider) => (
                      <div 
                        key={provider.name}
                        className={`provider-panel ${settingsTab === provider.name ? 'active' : ''}`}
                      >
                        <div className="provider-header">
                          <h3>{provider.display_name}</h3>
                          <p className="provider-description">{provider.description}</p>
                          {provider.homepage_url && (
                            <a 
                              href={provider.homepage_url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="provider-link"
                            >
                              🔗 {provider.homepage_url}
                            </a>
                          )}
                        </div>

                    {/* OpenAI Settings */}
                    {provider.name === 'openai' && (
                      <>
                        <div className="form-group">
                          <label>API Key:</label>
                          <input
                            type="password"
                            placeholder={settings?.openai_api_key_set ? "••••••••••••••••" : "Enter OpenAI API key"}
                            value={settingsForm.openai_api_key || ''}
                            onChange={(e) => setSettingsForm({ ...settingsForm, openai_api_key: e.target.value })}
                          />
                          {settings?.openai_api_key_set && (
                            <span className="api-key-status">✅ Set</span>
                          )}
                          <small>Get your API key from <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer">OpenAI Platform</a></small>
                        </div>

                        <div className="form-group">
                          <label>Base URL (optional):</label>
                          <input
                            type="text"
                            placeholder="https://api.openai.com/v1"
                            value={settingsForm.openai_base_url || settings?.openai_base_url || ''}
                            onChange={(e) => setSettingsForm({ ...settingsForm, openai_base_url: e.target.value })}
                          />
                          <small>Override for compatible gateways (leave blank for default)</small>
                        </div>

                        <div className="form-group">
                          <label>Default Model Override:</label>
                          <select
                            value={settingsForm.openai_default_model || settings?.openai_default_model || ''}
                            onChange={(e) => setSettingsForm({ ...settingsForm, openai_default_model: e.target.value })}
                          >
                            <option value="">Use global default</option>
                            {provider.available_models.map((model) => (
                              <option key={model} value={model}>{model}</option>
                            ))}
                          </select>
                        </div>

                        <div className="form-group">
                          <label>Temperature Override:</label>
                          <input
                            type="number"
                            min="0"
                            max="2"
                            step="0.1"
                            value={settingsForm.openai_temperature ?? settings?.openai_temperature ?? ''}
                            onChange={(e) => setSettingsForm({
                              ...settingsForm,
                              openai_temperature: e.target.value === '' ? undefined : parseFloat(e.target.value)
                            })}
                          />
                        </div>

                        <div className="form-group">
                          <label>Top P Override:</label>
                          <input
                            type="number"
                            min="0"
                            max="1"
                            step="0.05"
                            value={settingsForm.openai_top_p ?? settings?.openai_top_p ?? ''}
                            onChange={(e) => setSettingsForm({
                              ...settingsForm,
                              openai_top_p: e.target.value === '' ? undefined : parseFloat(e.target.value)
                            })}
                          />
                        </div>

                        <div className="form-group">
                          <label>Max Completion Tokens Override:</label>
                          <input
                            type="number"
                            min="1"
                            max="16000"
                            value={settingsForm.openai_max_tokens ?? settings?.openai_max_tokens ?? ''}
                            onChange={(e) => setSettingsForm({
                              ...settingsForm,
                              openai_max_tokens: e.target.value === '' ? undefined : parseInt(e.target.value)
                            })}
                          />
                          <small>Uses max_completion_tokens for o-series models</small>
                        </div>
                        
                        <div className="form-group">
                          <label>Available Models:</label>
                          <div className="model-list">
                            {provider.available_models.map((model) => (
                              <span key={model} className="model-badge">{model}</span>
                            ))}
                          </div>
                        </div>
                      </>
                    )}

                    {/* Anthropic Settings */}
                    {provider.name === 'anthropic' && (
                      <>
                        <div className="form-group">
                          <label>API Key:</label>
                          <input
                            type="password"
                            placeholder={settings?.anthropic_api_key_set ? "••••••••••••••••" : "Enter Anthropic API key"}
                            value={settingsForm.anthropic_api_key || ''}
                            onChange={(e) => setSettingsForm({ ...settingsForm, anthropic_api_key: e.target.value })}
                          />
                          {settings?.anthropic_api_key_set && (
                            <span className="api-key-status">✅ Set</span>
                          )}
                          <small>Get your API key from <a href="https://console.anthropic.com/settings/keys" target="_blank" rel="noopener noreferrer">Anthropic Console</a></small>
                        </div>

                        <div className="form-group">
                          <label>Default Model Override:</label>
                          <select
                            value={settingsForm.anthropic_default_model || settings?.anthropic_default_model || ''}
                            onChange={(e) => setSettingsForm({ ...settingsForm, anthropic_default_model: e.target.value })}
                          >
                            <option value="">Use global default</option>
                            {provider.available_models.map((model) => (
                              <option key={model} value={model}>{model}</option>
                            ))}
                          </select>
                        </div>

                        <div className="form-group">
                          <label>Temperature Override:</label>
                          <input
                            type="number"
                            min="0"
                            max="2"
                            step="0.1"
                            value={settingsForm.anthropic_temperature ?? settings?.anthropic_temperature ?? ''}
                            onChange={(e) => setSettingsForm({
                              ...settingsForm,
                              anthropic_temperature: e.target.value === '' ? undefined : parseFloat(e.target.value)
                            })}
                          />
                        </div>

                        <div className="form-group">
                          <label>Top P Override:</label>
                          <input
                            type="number"
                            min="0"
                            max="1"
                            step="0.05"
                            value={settingsForm.anthropic_top_p ?? settings?.anthropic_top_p ?? ''}
                            onChange={(e) => setSettingsForm({
                              ...settingsForm,
                              anthropic_top_p: e.target.value === '' ? undefined : parseFloat(e.target.value)
                            })}
                          />
                        </div>

                        <div className="form-group">
                          <label>Top K Override:</label>
                          <input
                            type="number"
                            min="0"
                            step="1"
                            value={settingsForm.anthropic_top_k ?? settings?.anthropic_top_k ?? ''}
                            onChange={(e) => setSettingsForm({
                              ...settingsForm,
                              anthropic_top_k: e.target.value === '' ? undefined : parseInt(e.target.value)
                            })}
                          />
                        </div>

                        <div className="form-group">
                          <label>Max Tokens Override:</label>
                          <input
                            type="number"
                            min="1"
                            max="16000"
                            value={settingsForm.anthropic_max_tokens ?? settings?.anthropic_max_tokens ?? ''}
                            onChange={(e) => setSettingsForm({
                              ...settingsForm,
                              anthropic_max_tokens: e.target.value === '' ? undefined : parseInt(e.target.value)
                            })}
                          />
                        </div>
                        
                        <div className="form-group">
                          <label>Available Models:</label>
                          <div className="model-list">
                            {provider.available_models.map((model) => (
                              <span key={model} className="model-badge">{model}</span>
                            ))}
                          </div>
                        </div>
                      </>
                    )}

                    {/* Ollama Settings */}
                    {provider.name === 'ollama' && (
                      <>
                        <div className="form-group">
                          <label>Base URL:</label>
                          <input
                            type="text"
                            placeholder="http://localhost:11434"
                            value={settingsForm.ollama_base_url || settings?.ollama_base_url || ''}
                            onChange={(e) => setSettingsForm({ ...settingsForm, ollama_base_url: e.target.value })}
                          />
                          {settings?.ollama_configured && (
                            <span className="api-key-status">✅ Configured</span>
                          )}
                          <small>Local Ollama server endpoint. <a href="https://ollama.ai/download" target="_blank" rel="noopener noreferrer">Download Ollama</a></small>
                        </div>

                        <div className="form-group">
                          <label>Default Model Override:</label>
                          <input
                            type="text"
                            placeholder="llama3.2"
                            value={settingsForm.ollama_default_model || settings?.ollama_default_model || ''}
                            onChange={(e) => setSettingsForm({ ...settingsForm, ollama_default_model: e.target.value })}
                          />
                          <small>Leave blank to use global default model</small>
                        </div>

                        <div className="form-group">
                          <label>Temperature Override:</label>
                          <input
                            type="number"
                            min="0"
                            max="2"
                            step="0.1"
                            value={settingsForm.ollama_temperature ?? settings?.ollama_temperature ?? ''}
                            onChange={(e) => setSettingsForm({
                              ...settingsForm,
                              ollama_temperature: e.target.value === '' ? undefined : parseFloat(e.target.value)
                            })}
                          />
                        </div>

                        <div className="form-group">
                          <label>Top P Override:</label>
                          <input
                            type="number"
                            min="0"
                            max="1"
                            step="0.05"
                            value={settingsForm.ollama_top_p ?? settings?.ollama_top_p ?? ''}
                            onChange={(e) => setSettingsForm({
                              ...settingsForm,
                              ollama_top_p: e.target.value === '' ? undefined : parseFloat(e.target.value)
                            })}
                          />
                        </div>

                        <div className="form-group">
                          <label>Num Predict Override:</label>
                          <input
                            type="number"
                            min="1"
                            value={settingsForm.ollama_num_predict ?? settings?.ollama_num_predict ?? ''}
                            onChange={(e) => setSettingsForm({
                              ...settingsForm,
                              ollama_num_predict: e.target.value === '' ? undefined : parseInt(e.target.value)
                            })}
                          />
                        </div>

                        <div className="form-group">
                          <label>Context Size Override:</label>
                          <input
                            type="number"
                            min="1"
                            value={settingsForm.ollama_num_ctx ?? settings?.ollama_num_ctx ?? ''}
                            onChange={(e) => setSettingsForm({
                              ...settingsForm,
                              ollama_num_ctx: e.target.value === '' ? undefined : parseInt(e.target.value)
                            })}
                          />
                        </div>

                        <div className="form-group">
                          <label>Keep Alive Override:</label>
                          <input
                            type="text"
                            placeholder="5m"
                            value={settingsForm.ollama_keep_alive || settings?.ollama_keep_alive || ''}
                            onChange={(e) => setSettingsForm({ ...settingsForm, ollama_keep_alive: e.target.value })}
                          />
                          <small>Controls how long models stay loaded (e.g., 5m, 1h, 0)</small>
                        </div>
                        
                        <div className="form-group">
                          <label>Common Models:</label>
                          <div className="model-list">
                            {provider.available_models.map((model) => (
                              <span key={model} className="model-badge">{model}</span>
                            ))}
                          </div>
                          <small>Models will be automatically downloaded when first used</small>
                        </div>
                      </>
                    )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {settingsSectionTab === 'general' && (
                <div className="settings-content-panel settings-column-general">
                  <div className="form-section general-settings-section">
                    <h3>General Settings</h3>
                    <div className="form-group">
                      <label>Default Provider:</label>
                      <select
                        value={settingsForm.default_ai_provider || settings?.default_ai_provider || 'openai'}
                        onChange={(e) => {
                          const nextProvider = e.target.value;
                          // eslint-disable-next-line @typescript-eslint/no-explicit-any
                          const providerModels = (modelOptions as any)[nextProvider] || [];
                          const nextModel = providerModels.length > 0 ? providerModels[0] : '';

                          setSettingsForm({
                            ...settingsForm,
                            default_ai_provider: nextProvider,
                            default_ai_model: nextModel,
                          });
                        }}
                      >
                        {providers.map((provider) => (
                          <option key={provider.name} value={provider.name}>
                            {provider.display_name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="form-group">
                      <label>Default Model:</label>
                      <select
                        value={settingsForm.default_ai_model || settings?.default_ai_model || (modelOptions.openai[0] || 'gpt-4o')}
                        onChange={(e) => setSettingsForm({ ...settingsForm, default_ai_model: e.target.value })}
                      >
                        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
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
                      <small>Controls randomness (0 = focused, 2 = creative)</small>
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
                      <small>Maximum length of AI response</small>
                    </div>

                    <div className="form-group">
                      <label className="dark-mode-toggle" htmlFor="dark-mode-toggle-input">
                        <input
                          id="dark-mode-toggle-input"
                          type="checkbox"
                          checked={darkMode}
                          onChange={(e) => {
                            const nextDarkMode = e.target.checked;
                            setDarkMode(nextDarkMode);
                            appendInteractionLog('User ↔ Frontend', `Dark mode ${nextDarkMode ? 'enabled' : 'disabled'}.`);
                          }}
                        />
                        <span className="dark-mode-toggle-text">Dark mode: {darkMode ? 'On' : 'Off'}</span>
                      </label>
                      <small>Applies to the full interface immediately.</small>
                    </div>
                  </div>
                </div>
              )}
              
              <div className="modal-actions">
                {settingsSectionTab === 'provider' && (
                  <button
                    type="button"
                    className="button button-secondary"
                    onClick={handleValidateProviderConnection}
                    disabled={loading}
                  >
                    {loading ? 'Checking...' : `Test ${settingsTab} Connection`}
                  </button>
                )}
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
