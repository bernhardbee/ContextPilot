/**
 * API client for ContextPilot backend.
 */
import axios from 'axios';
import {
    AIRequest,
    AIResponse,
    ContextUnit,
    ContextUnitCreate,
    ContextUnitUpdate,
    Conversation,
    GeneratedPrompt,
    Settings,
    SettingsUpdate,
    Stats,
    TaskRequest,
} from './types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 600000, // 10 minutes timeout for Ollama model downloads
});

export const contextAPI = {
  // Context CRUD operations
  createContext: async (data: ContextUnitCreate): Promise<ContextUnit> => {
    const response = await api.post<ContextUnit>('/contexts', data);
    return response.data;
  },

  listContexts: async (
    includeSuperseded: boolean = false,
    filters?: {
      type?: string;
      tags?: string;
      search?: string;
      status_filter?: string;
      limit?: number;
    }
  ): Promise<ContextUnit[]> => {
    const response = await api.get<ContextUnit[]>('/contexts', {
      params: {
        include_superseded: includeSuperseded,
        ...filters,
      },
    });
    return response.data;
  },

  getContext: async (id: string): Promise<ContextUnit> => {
    const response = await api.get<ContextUnit>(`/contexts/${id}`);
    return response.data;
  },

  updateContext: async (id: string, data: ContextUnitUpdate): Promise<ContextUnit> => {
    const response = await api.put<ContextUnit>(`/contexts/${id}`, data);
    return response.data;
  },

  deleteContext: async (id: string): Promise<void> => {
    await api.delete(`/contexts/${id}`);
  },

  // Import/Export operations
  exportContexts: async (format: 'json' | 'csv' = 'json'): Promise<Blob> => {
    const response = await api.get('/contexts/export', {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  },

  importContexts: async (file: File, replaceExisting: boolean = false): Promise<{
    imported: number;
    skipped: number;
    errors: string[];
    total_errors: number;
  }> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/contexts/import', formData, {
      params: { replace_existing: replaceExisting },
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Prompt generation
  generatePrompt: async (data: TaskRequest): Promise<GeneratedPrompt> => {
    const response = await api.post<GeneratedPrompt>('/generate-prompt', data);
    return response.data;
  },

  generatePromptCompact: async (data: TaskRequest): Promise<GeneratedPrompt> => {
    const response = await api.post<GeneratedPrompt>('/generate-prompt/compact', data);
    return response.data;
  },

  // Statistics
  getStats: async (): Promise<Stats> => {
    const response = await api.get<Stats>('/stats');
    return response.data;
  },

  // Health check
  healthCheck: async (): Promise<{ status: string }> => {
    const response = await api.get('/health');
    return response.data;
  },

  // AI Integration
  chatWithAI: async (data: AIRequest): Promise<AIResponse> => {
    console.log('API Request:', data);
    const response = await api.post<AIResponse>('/ai/chat', data);
    console.log('API Raw Response:', response);
    console.log('API Response Data:', response.data);
    return response.data;
  },

  listConversations: async (): Promise<Conversation[]> => {
    const response = await api.get<{conversations: Conversation[], limit: number, offset: number, count: number}>('/ai/conversations');
    return response.data.conversations;
  },

  getConversation: async (id: string): Promise<Conversation> => {
    const response = await api.get<Conversation>(`/ai/conversations/${id}`);
    return response.data;
  },

  // Settings management
  getSettings: async (): Promise<Settings> => {
    const response = await api.get<Settings>('/settings');
    return response.data;
  },

  updateSettings: async (settings: SettingsUpdate): Promise<any> => {
    const response = await api.post('/settings', settings);
    return response.data;
  },
};
