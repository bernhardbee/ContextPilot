import { beforeEach, describe, expect, it, vi } from 'vitest';

const mockPost = vi.fn();
const mockGet = vi.fn();
const mockPut = vi.fn();
const mockDelete = vi.fn();

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      post: mockPost,
      get: mockGet,
      put: mockPut,
      delete: mockDelete,
    })),
  },
}));

describe('contextAPI', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('createContext posts to /contexts', async () => {
    const payload = { id: '1' };
    mockPost.mockResolvedValue({ data: payload });
    const { contextAPI } = await import('./api');

    const result = await contextAPI.createContext({ type: 'fact' as never, content: 'x' });

    expect(mockPost).toHaveBeenCalledWith('/contexts', { type: 'fact', content: 'x' });
    expect(result).toEqual(payload);
  });

  it('listContexts sends include_superseded and filters', async () => {
    mockGet.mockResolvedValue({ data: [{ id: '1' }] });
    const { contextAPI } = await import('./api');

    const result = await contextAPI.listContexts(true, { type: 'fact', search: 'abc' });

    expect(mockGet).toHaveBeenCalledWith('/contexts', {
      params: { include_superseded: true, type: 'fact', search: 'abc' },
    });
    expect(result).toEqual([{ id: '1' }]);
  });

  it('getContext fetches by id', async () => {
    mockGet.mockResolvedValue({ data: { id: 'ctx-1' } });
    const { contextAPI } = await import('./api');

    const result = await contextAPI.getContext('ctx-1');

    expect(mockGet).toHaveBeenCalledWith('/contexts/ctx-1');
    expect(result.id).toBe('ctx-1');
  });

  it('updateContext puts by id', async () => {
    mockPut.mockResolvedValue({ data: { id: 'ctx-1', content: 'updated' } });
    const { contextAPI } = await import('./api');

    const result = await contextAPI.updateContext('ctx-1', { content: 'updated' });

    expect(mockPut).toHaveBeenCalledWith('/contexts/ctx-1', { content: 'updated' });
    expect(result.content).toBe('updated');
  });

  it('deleteContext deletes by id', async () => {
    mockDelete.mockResolvedValue({});
    const { contextAPI } = await import('./api');

    await contextAPI.deleteContext('ctx-1');

    expect(mockDelete).toHaveBeenCalledWith('/contexts/ctx-1');
  });

  it('exportContexts fetches blob with json default', async () => {
    const blob = new Blob(['{}']);
    mockGet.mockResolvedValue({ data: blob });
    const { contextAPI } = await import('./api');

    const result = await contextAPI.exportContexts();

    expect(mockGet).toHaveBeenCalledWith('/contexts/export', {
      params: { format: 'json' },
      responseType: 'blob',
    });
    expect(result).toBe(blob);
  });

  it('importContexts sends multipart form data', async () => {
    mockPost.mockResolvedValue({ data: { imported: 1, skipped: 0, errors: [], total_errors: 0 } });
    const { contextAPI } = await import('./api');
    const file = new File(['{}'], 'contexts.json', { type: 'application/json' });

    const result = await contextAPI.importContexts(file, true);

    expect(mockPost).toHaveBeenCalledWith(
      '/contexts/import',
      expect.any(FormData),
      {
        params: { replace_existing: true },
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );
    expect(result.imported).toBe(1);
  });

  it('generatePrompt posts to prompt endpoint', async () => {
    mockPost.mockResolvedValue({ data: { generated_prompt: 'abc' } });
    const { contextAPI } = await import('./api');

    const result = await contextAPI.generatePrompt({ task: 'do thing' });

    expect(mockPost).toHaveBeenCalledWith('/generate-prompt', { task: 'do thing' });
    expect(result.generated_prompt).toBe('abc');
  });

  it('generatePromptCompact posts to compact endpoint', async () => {
    mockPost.mockResolvedValue({ data: { generated_prompt: 'compact' } });
    const { contextAPI } = await import('./api');

    const result = await contextAPI.generatePromptCompact({ task: 'compact' });

    expect(mockPost).toHaveBeenCalledWith('/generate-prompt/compact', { task: 'compact' });
    expect(result.generated_prompt).toBe('compact');
  });

  it('getStats fetches /stats', async () => {
    mockGet.mockResolvedValue({ data: { active_contexts: 1 } });
    const { contextAPI } = await import('./api');

    const result = await contextAPI.getStats();

    expect(mockGet).toHaveBeenCalledWith('/stats');
    expect(result.active_contexts).toBe(1);
  });

  it('healthCheck fetches /health', async () => {
    mockGet.mockResolvedValue({ data: { status: 'ok' } });
    const { contextAPI } = await import('./api');

    const result = await contextAPI.healthCheck();

    expect(mockGet).toHaveBeenCalledWith('/health');
    expect(result.status).toBe('ok');
  });

  it('chatWithAI posts to /ai/chat', async () => {
    mockPost.mockResolvedValue({ data: { response: 'hello', conversation_id: '1' } });
    const { contextAPI } = await import('./api');

    const result = await contextAPI.chatWithAI({ task: 'hi' });

    expect(mockPost).toHaveBeenCalledWith('/ai/chat', { task: 'hi' });
    expect(result.response).toBe('hello');
  });

  it('listConversations maps nested response', async () => {
    mockGet.mockResolvedValue({ data: { conversations: [{ id: 'c1' }], limit: 10, offset: 0, count: 1 } });
    const { contextAPI } = await import('./api');

    const result = await contextAPI.listConversations();

    expect(mockGet).toHaveBeenCalledWith('/ai/conversations');
    expect(result).toEqual([{ id: 'c1' }]);
  });

  it('getConversation fetches by id', async () => {
    mockGet.mockResolvedValue({ data: { id: 'conv-1' } });
    const { contextAPI } = await import('./api');

    const result = await contextAPI.getConversation('conv-1');

    expect(mockGet).toHaveBeenCalledWith('/ai/conversations/conv-1');
    expect(result.id).toBe('conv-1');
  });

  it('getSettings fetches settings', async () => {
    mockGet.mockResolvedValue({ data: { default_ai_provider: 'openai' } });
    const { contextAPI } = await import('./api');

    const result = await contextAPI.getSettings();

    expect(mockGet).toHaveBeenCalledWith('/settings');
    expect(result.default_ai_provider).toBe('openai');
  });

  it('updateSettings posts settings payload', async () => {
    mockPost.mockResolvedValue({ data: { ok: true } });
    const { contextAPI } = await import('./api');

    const result = await contextAPI.updateSettings({ default_ai_provider: 'anthropic' });

    expect(mockPost).toHaveBeenCalledWith('/settings', { default_ai_provider: 'anthropic' });
    expect(result.ok).toBe(true);
  });

  it('getProviders fetches provider metadata', async () => {
    mockGet.mockResolvedValue({ data: { providers: [], default_provider: 'openai', default_model: 'gpt-4o' } });
    const { contextAPI } = await import('./api');

    const result = await contextAPI.getProviders();

    expect(mockGet).toHaveBeenCalledWith('/providers');
    expect(result.default_provider).toBe('openai');
  });

  it('validateProviderConnection posts validation request with model', async () => {
    mockPost.mockResolvedValue({ data: { provider: 'openai', valid: true, message: 'ok', checked_model: 'gpt-5.2' } });
    const { contextAPI } = await import('./api');

    const result = await contextAPI.validateProviderConnection('openai', 'gpt-5.2');

    expect(mockPost).toHaveBeenCalledWith('/providers/openai/validate', null, {
      params: { model: 'gpt-5.2' },
    });
    expect(result.valid).toBe(true);
  });
});
