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
