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
  model?: string;  // Track which AI model generated this message
}

export interface Conversation {
  id: string;
  task: string;
  provider: string;
  model: string;
  created_at: string;
  updated_at?: string;
  last_message_at?: string;
  last_entry_at?: string;
  message_count?: number;
  messages?: ConversationMessage[];
}

export interface Settings {
  openai_api_key_set: boolean;
  openai_base_url: string;
  openai_default_model: string;
  openai_temperature: number | null;
  openai_top_p: number | null;
  openai_max_tokens: number | null;
  anthropic_api_key_set: boolean;
  anthropic_default_model: string;
  anthropic_temperature: number | null;
  anthropic_top_p: number | null;
  anthropic_top_k: number | null;
  anthropic_max_tokens: number | null;
  ollama_configured: boolean;
  ollama_base_url: string;
  ollama_default_model: string;
  ollama_temperature: number | null;
  ollama_top_p: number | null;
  ollama_num_predict: number | null;
  ollama_num_ctx: number | null;
  ollama_keep_alive: string;
  default_ai_provider: string;
  default_ai_model: string;
  ai_temperature: number;
  ai_max_tokens: number;
}

export interface SettingsUpdate {
  openai_api_key?: string;
  openai_base_url?: string;
  openai_default_model?: string;
  openai_temperature?: number;
  openai_top_p?: number;
  openai_max_tokens?: number;
  anthropic_api_key?: string;
  anthropic_default_model?: string;
  anthropic_temperature?: number;
  anthropic_top_p?: number;
  anthropic_top_k?: number;
  anthropic_max_tokens?: number;
  ollama_base_url?: string;
  ollama_default_model?: string;
  ollama_temperature?: number;
  ollama_top_p?: number;
  ollama_num_predict?: number;
  ollama_num_ctx?: number;
  ollama_keep_alive?: string;
  default_ai_provider?: string;
  default_ai_model?: string;
  ai_temperature?: number;
  ai_max_tokens?: number;
}

export interface ProviderInfo {
  name: string;
  display_name: string;
  description: string;
  requires_api_key: boolean;
  supports_local: boolean;
  homepage_url: string;
  documentation_url: string;
  configured: boolean;
  api_key_set?: boolean;
  base_url?: string;
  available_models: string[];
}

export interface ProvidersResponse {
  providers: ProviderInfo[];
  default_provider: string;
  default_model: string;
}

export interface ProviderValidationResponse {
  provider: string;
  valid: boolean;
  message: string;
  checked_model?: string;
}
