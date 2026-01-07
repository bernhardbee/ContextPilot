/**
 * API client for ContextPilot backend.
 */
import axios from 'axios';
import {
  ContextUnit,
  ContextUnitCreate,
  ContextUnitUpdate,
  GeneratedPrompt,
  TaskRequest,
  Stats,
} from './types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const contextAPI = {
  // Context CRUD operations
  createContext: async (data: ContextUnitCreate): Promise<ContextUnit> => {
    const response = await api.post<ContextUnit>('/contexts', data);
    return response.data;
  },

  listContexts: async (includSuperseded: boolean = false): Promise<ContextUnit[]> => {
    const response = await api.get<ContextUnit[]>('/contexts', {
      params: { include_superseded: includSuperseded },
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
};
