/**
 * Type definitions for ContextPilot API.
 */

export enum ContextType {
  PREFERENCE = 'preference',
  DECISION = 'decision',
  FACT = 'fact',
  GOAL = 'goal',
}

export enum ContextStatus {
  ACTIVE = 'active',
  SUPERSEDED = 'superseded',
}

export interface ContextUnit {
  id: string;
  type: ContextType;
  content: string;
  confidence: number;
  created_at: string;
  last_used: string | null;
  source: string;
  tags: string[];
  status: ContextStatus;
  superseded_by: string | null;
}

export interface ContextUnitCreate {
  type: ContextType;
  content: string;
  confidence?: number;
  tags?: string[];
  source?: string;
}

export interface ContextUnitUpdate {
  type?: ContextType;
  content?: string;
  confidence?: number;
  tags?: string[];
  status?: ContextStatus;
}

export interface RankedContextUnit {
  context_unit: ContextUnit;
  relevance_score: number;
}

export interface GeneratedPrompt {
  original_task: string;
  relevant_context: RankedContextUnit[];
  generated_prompt: string;
  timestamp: string;
}

export interface TaskRequest {
  task: string;
  max_context_units?: number;
}

export interface Stats {
  total_contexts: number;
  active_contexts: number;
  superseded_contexts: number;
  contexts_by_type: Record<string, number>;
  contexts_with_embeddings: number;
}

// AI Integration types
export interface AIRequest {
  task: string;
  max_context_units?: number;
  provider?: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  use_compact?: boolean;
  conversation_id?: string;
}

export interface AIResponse {
  conversation_id: string;
  task: string;
  response: string;
  provider: string;
  model: string;
  context_ids: string[];
  prompt_used: string;
  timestamp: string;
}

export interface ConversationMessage {
  id?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at?: string;  // ISO timestamp from backend
  timestamp?: string;   // Backwards compatibility
  tokens?: number;
  finish_reason?: string;
}

export interface Conversation {
  id: string;
  task: string;
  provider: string;
  model: string;
  created_at: string;
  message_count?: number;
  messages?: ConversationMessage[];
}

export interface Settings {
  openai_api_key_set: boolean;
  anthropic_api_key_set: boolean;
  default_ai_provider: string;
  default_ai_model: string;
  ai_temperature: number;
  ai_max_tokens: number;
}

export interface SettingsUpdate {
  openai_api_key?: string;
  anthropic_api_key?: string;
  default_ai_provider?: string;
  default_ai_model?: string;
  ai_temperature?: number;
  ai_max_tokens?: number;
}
