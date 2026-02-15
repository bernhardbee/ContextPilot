import { ContextStatus, ContextType, type ContextUnit, type ConversationMessage } from '../types';

export const createMockContext = (overrides: Partial<ContextUnit> = {}): ContextUnit => ({
  id: 'context-1',
  type: ContextType.FACT,
  content: 'Test context content',
  confidence: 0.8,
  created_at: new Date().toISOString(),
  last_used: null,
  source: 'test',
  tags: [],
  status: ContextStatus.ACTIVE,
  superseded_by: null,
  ...overrides,
});

export const createMockMessage = (
  overrides: Partial<ConversationMessage> = {}
): ConversationMessage => ({
  id: 'message-1',
  role: 'user',
  content: 'Test message',
  created_at: new Date().toISOString(),
  ...overrides,
});
