import { fireEvent, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App';
import { render } from './test/render-with-providers';

let consoleErrorSpy: { mockRestore: () => void };

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    listContexts: vi.fn(),
    getStats: vi.fn(),
    getSettings: vi.fn(),
    getProviders: vi.fn(),
    listConversations: vi.fn(),
    createContext: vi.fn(),
    deleteContext: vi.fn(),
    updateSettings: vi.fn(),
    validateProviderConnection: vi.fn(),
    chatWithAI: vi.fn(),
    getConversation: vi.fn(),
  },
}));

vi.mock('./api', () => ({
  contextAPI: mockApi,
}));

const defaultContexts = [
  {
    id: 'ctx-1',
    type: 'fact',
    content: 'Existing context',
    confidence: 0.8,
    created_at: '2026-02-15T10:00:00Z',
    last_used: null,
    source: 'test',
    tags: ['alpha'],
    status: 'active',
    superseded_by: null,
  },
];

const defaultSettings = {
  openai_api_key_set: false,
  openai_base_url: 'https://api.openai.com/v1',
  openai_default_model: 'gpt-4o',
  openai_temperature: 1,
  openai_top_p: 1,
  openai_max_tokens: 4000,
  anthropic_api_key_set: false,
  anthropic_default_model: 'claude-3-5-sonnet-20241022',
  anthropic_temperature: 1,
  anthropic_top_p: 1,
  anthropic_top_k: 40,
  anthropic_max_tokens: 4000,
  ollama_configured: false,
  ollama_base_url: 'http://localhost:11434',
  ollama_default_model: 'llama3.2',
  ollama_temperature: 0.8,
  ollama_top_p: 0.9,
  ollama_num_predict: 4000,
  ollama_num_ctx: 8192,
  ollama_keep_alive: '5m',
  default_ai_provider: 'openai',
  default_ai_model: 'gpt-4o',
  ai_temperature: 1,
  ai_max_tokens: 4000,
};

const defaultProviders = {
  providers: [
    {
      name: 'openai',
      display_name: 'OpenAI',
      description: 'OpenAI models',
      requires_api_key: true,
      supports_local: false,
      homepage_url: 'https://openai.com',
      documentation_url: 'https://platform.openai.com/docs',
      configured: false,
      available_models: ['gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo'],
    },
    {
      name: 'anthropic',
      display_name: 'Anthropic',
      description: 'Anthropic models',
      requires_api_key: true,
      supports_local: false,
      homepage_url: 'https://anthropic.com',
      documentation_url: 'https://docs.anthropic.com',
      configured: false,
      available_models: ['claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022'],
    },
    {
      name: 'ollama',
      display_name: 'Ollama (Local)',
      description: 'Local Ollama models',
      requires_api_key: false,
      supports_local: true,
      homepage_url: 'https://ollama.ai',
      documentation_url: 'https://ollama.ai/library',
      configured: true,
      available_models: ['llama3.2'],
    },
  ],
  default_provider: 'openai',
  default_model: 'gpt-4o',
};

function setupDefaults() {
  mockApi.listContexts.mockResolvedValue(defaultContexts);
  mockApi.getStats.mockResolvedValue({
    total_contexts: 1,
    active_contexts: 1,
    superseded_contexts: 0,
    contexts_by_type: { preference: 0, goal: 0, decision: 0, fact: 1 },
    contexts_with_embeddings: 0,
  });
  mockApi.getSettings.mockResolvedValue(defaultSettings);
  mockApi.getProviders.mockResolvedValue(defaultProviders);
  mockApi.listConversations.mockResolvedValue([]);
  mockApi.createContext.mockResolvedValue({ id: 'ctx-2' });
  mockApi.deleteContext.mockResolvedValue({});
  mockApi.updateSettings.mockResolvedValue({ ok: true });
  mockApi.validateProviderConnection.mockResolvedValue({
    provider: 'openai',
    valid: true,
    message: 'OpenAI connection and API key are valid.',
    checked_model: 'gpt-4o',
  });
  mockApi.chatWithAI.mockResolvedValue({
    conversation_id: 'conv-1',
    task: 'hello',
    response: 'assistant reply',
    provider: 'openai',
    model: 'gpt-4o',
    context_ids: ['ctx-1'],
    prompt_used: 'p',
    timestamp: '2026-02-15T11:00:00Z',
  });
  mockApi.getConversation.mockResolvedValue({
    id: 'conv-1',
    task: 'first task',
    provider: 'openai',
    model: 'gpt-4o',
    created_at: '2026-02-15T11:00:00Z',
    messages: [
      { role: 'system', content: 'sys', created_at: '2026-02-15T11:00:00Z' },
      { role: 'user', content: 'u1', created_at: '2026-02-15T11:00:01Z' },
      { role: 'assistant', content: 'a1', created_at: '2026-02-15T11:00:02Z' },
    ],
  });
}

describe('App integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupDefaults();
    window.localStorage.clear();
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText: vi.fn() },
    });
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it('loads app data on mount and shows welcome view', async () => {
    render(<App />);

    await waitFor(() => {
      expect(mockApi.listContexts).toHaveBeenCalled();
      expect(mockApi.getStats).toHaveBeenCalled();
      expect(mockApi.getSettings).toHaveBeenCalled();
      expect(mockApi.getProviders).toHaveBeenCalled();
      expect(mockApi.listConversations).toHaveBeenCalled();
    });

    expect(await screen.findByText(/ready to chat!/i)).toBeInTheDocument();
  });

  it('collapses the conversations sidebar to button-only mode and expands it again', async () => {
    mockApi.listConversations.mockResolvedValueOnce([
      {
        id: 'conv-1',
        task: 'first task',
        provider: 'openai',
        model: 'gpt-4o',
        created_at: '2026-02-15T11:00:00Z',
        message_count: 2,
      },
    ]);

    const { user, container } = render(<App />);

    expect(await screen.findByText(/first task/i)).toBeInTheDocument();
    expect(await screen.findByRole('log', { name: /interaction log output/i })).toBeInTheDocument();

    await user.click(screen.getByTitle(/hide conversations/i));

    expect(container.querySelector('.left-sidebar-stack')).toHaveClass('collapsed');
    expect(screen.queryByText(/first task/i)).not.toBeInTheDocument();
    expect(screen.queryByRole('log', { name: /interaction log output/i })).not.toBeInTheDocument();
    expect(screen.getByTitle(/show conversations/i)).toBeInTheDocument();

    await user.click(screen.getByTitle(/show conversations/i));

    expect(container.querySelector('.left-sidebar-stack')).toHaveClass('visible');
    expect(await screen.findByText(/first task/i)).toBeInTheDocument();
  });

  it('orders conversations by latest entry time with newest at the top', async () => {
    mockApi.listConversations.mockResolvedValueOnce([
      {
        id: 'conv-older',
        task: 'Older conversation in payload',
        provider: 'openai',
        model: 'gpt-4o',
        created_at: '2026-02-15T08:00:00Z',
        last_message_at: '2026-02-15T09:00:00Z',
        message_count: 2,
      },
      {
        id: 'conv-newer',
        task: 'Newest conversation in payload',
        provider: 'openai',
        model: 'gpt-4o',
        created_at: '2026-02-15T07:00:00Z',
        last_message_at: '2026-02-15T12:00:00Z',
        message_count: 4,
      },
    ]);

    const { container } = render(<App />);

    expect(await screen.findByText(/older conversation in payload/i)).toBeInTheDocument();
    expect(await screen.findByText(/newest conversation in payload/i)).toBeInTheDocument();

    const orderedTasks = Array.from(
      container.querySelectorAll('.conversation-item .conversation-task')
    ).map((node) => node.textContent || '');

    expect(orderedTasks[0]).toContain('Newest conversation in payload');
    expect(orderedTasks[1]).toContain('Older conversation in payload');
  });

  it('moves an updated lower conversation to the top immediately after sending, before reply returns', async () => {
    mockApi.listConversations
      .mockResolvedValueOnce([
        {
          id: 'conv-top',
          task: 'Top conversation before update',
          provider: 'openai',
          model: 'gpt-4o',
          created_at: '2026-02-15T08:00:00Z',
          last_message_at: '2026-02-15T12:00:00Z',
          message_count: 5,
        },
        {
          id: 'conv-bottom',
          task: 'Bottom conversation before update',
          provider: 'openai',
          model: 'gpt-4o',
          created_at: '2026-02-15T08:30:00Z',
          last_message_at: '2026-02-15T09:00:00Z',
          message_count: 2,
        },
      ])
      .mockResolvedValueOnce([
        {
          id: 'conv-top',
          task: 'Top conversation before update',
          provider: 'openai',
          model: 'gpt-4o',
          created_at: '2026-02-15T08:00:00Z',
          last_message_at: '2026-02-15T12:00:00Z',
          message_count: 5,
        },
        {
          id: 'conv-bottom',
          task: 'Bottom conversation before update',
          provider: 'openai',
          model: 'gpt-4o',
          created_at: '2026-02-15T08:30:00Z',
          last_message_at: '2026-02-15T09:00:00Z',
          message_count: 2,
        },
      ]);

    mockApi.getConversation.mockResolvedValueOnce({
      id: 'conv-bottom',
      task: 'Bottom conversation before update',
      provider: 'openai',
      model: 'gpt-4o',
      created_at: '2026-02-15T08:30:00Z',
      messages: [
        { role: 'system', content: 'sys', created_at: '2026-02-15T08:30:00Z' },
        { role: 'user', content: 'older user', created_at: '2026-02-15T08:31:00Z' },
        { role: 'assistant', content: 'older assistant', created_at: '2026-02-15T08:32:00Z' },
      ],
    });

    const chatResponse = {
      conversation_id: 'conv-bottom',
      task: 'promote this conversation',
      response: 'updated response',
      provider: 'openai',
      model: 'gpt-4o',
      context_ids: ['ctx-1'],
      prompt_used: 'p',
      timestamp: '2026-02-15T13:00:00Z',
    };

    let resolveChatRequest!: (value: typeof chatResponse) => void;
    const pendingChatRequest = new Promise<typeof chatResponse>((resolve) => {
      resolveChatRequest = resolve;
    });
    mockApi.chatWithAI.mockReturnValueOnce(pendingChatRequest);

    const { user, container } = render(<App />);

    expect(await screen.findByText(/top conversation before update/i)).toBeInTheDocument();
    expect(await screen.findByText(/bottom conversation before update/i)).toBeInTheDocument();

    await user.click(screen.getByText(/bottom conversation before update/i));
    await user.type(await screen.findByPlaceholderText(/continue the conversation/i), 'promote this conversation');
    await user.click(screen.getByRole('button', { name: /🚀/i }));

    await waitFor(() => {
      expect(mockApi.chatWithAI).toHaveBeenCalledWith(
        expect.objectContaining({ conversation_id: 'conv-bottom' })
      );
    });

    await waitFor(() => {
      const orderedTasks = Array.from(
        container.querySelectorAll('.conversation-item .conversation-task')
      ).map((node) => node.textContent || '');
      expect(orderedTasks[0]).toContain('Bottom conversation before update');
    });

    resolveChatRequest(chatResponse);
    expect(await screen.findByText('updated response')).toBeInTheDocument();
  });

  it('shows context loading error when listContexts fails', async () => {
    mockApi.listContexts.mockRejectedValue(new Error('load fail'));
    render(<App />);

    expect(await screen.findByText(/failed to load contexts/i)).toBeInTheDocument();
  });

  it('can switch to manage tab and validate create form', async () => {
    const { user } = render(<App />);

    await user.click(await screen.findByRole('button', { name: /manage all contexts/i }));
    const addContextHeading = await screen.findByRole('heading', { name: /add context/i });
    expect(addContextHeading).toBeInTheDocument();

    const addContextCard = addContextHeading.closest('.card');
    const addContextForm = addContextCard?.querySelector('form');
    expect(addContextForm).not.toBeNull();
    fireEvent.submit(addContextForm as HTMLFormElement);

    await waitFor(() => {
      expect(mockApi.createContext).not.toHaveBeenCalled();
    });
  });

  it('creates context successfully in manage tab', async () => {
    const { user } = render(<App />);

    await user.click(await screen.findByRole('button', { name: /manage all contexts/i }));
    await user.type(
      screen.getByPlaceholderText(/describe your preference, decision, fact, or goal/i),
      'New context content'
    );

    const addContextHeading = await screen.findByRole('heading', { name: /add context/i });
    const addContextCard = addContextHeading.closest('.card');
    const addContextForm = addContextCard?.querySelector('form');
    expect(addContextForm).not.toBeNull();
    fireEvent.submit(addContextForm as HTMLFormElement);

    await waitFor(() => {
      expect(mockApi.createContext).toHaveBeenCalledWith(
        expect.objectContaining({ content: 'New context content' })
      );
    });
    expect(screen.getAllByText(/context created successfully!/i).length).toBeGreaterThan(0);
  });

  it('deletes context when confirmed and skips when canceled', async () => {
    const { user } = render(<App />);
    await user.click(await screen.findByRole('button', { name: /manage all contexts/i }));

    await user.click(await screen.findByRole('button', { name: /^delete$/i }));
    await waitFor(() => {
      expect(mockApi.deleteContext).toHaveBeenCalledWith('ctx-1');
    });

    (window.confirm as unknown as ReturnType<typeof vi.fn>).mockReturnValueOnce(false);
    await user.click(await screen.findByRole('button', { name: /^delete$/i }));
    expect(mockApi.deleteContext).toHaveBeenCalledTimes(1);
  });

  it('loads template content through template click', async () => {
    const { user } = render(<App />);
    await user.click(await screen.findByRole('button', { name: /manage all contexts/i }));

    await user.click(screen.getByRole('button', { name: /code preference/i }));

    expect(screen.getAllByText(/template loaded!/i).length).toBeGreaterThan(0);
    expect(
      (
        screen.getByPlaceholderText(/describe your preference, decision, fact, or goal/i) as HTMLTextAreaElement
      ).value
    ).toContain('well-documented code');
  });

  it('opens settings modal and saves settings', async () => {
    const { user } = render(<App />);

    await user.click(await screen.findByTitle('Settings'));

    const settingsForm = document.querySelector('.settings-form');
    expect(settingsForm).not.toBeNull();
    fireEvent.submit(settingsForm as HTMLFormElement);

    await waitFor(() => {
      expect(mockApi.updateSettings).toHaveBeenCalled();
    });
    expect(screen.getAllByText(/settings updated successfully!/i).length).toBeGreaterThan(0);
  });

  it('shows settings update error from backend detail', async () => {
    mockApi.updateSettings.mockRejectedValueOnce({
      response: { data: { detail: 'bad settings' } },
    });
    const { user } = render(<App />);

    await user.click(await screen.findByTitle('Settings'));

    const settingsForm = document.querySelector('.settings-form');
    expect(settingsForm).not.toBeNull();
    fireEvent.submit(settingsForm as HTMLFormElement);

    expect(await screen.findByText(/bad settings|failed to update settings/i)).toBeInTheDocument();
  });

  it('validates provider connection from settings modal', async () => {
    const { user } = render(<App />);
    await user.click(await screen.findByTitle('Settings'));
    await user.click(screen.getByRole('tab', { name: /provider settings/i }));

    await user.click(screen.getByRole('button', { name: /test openai connection/i }));

    await waitFor(() => {
      expect(mockApi.validateProviderConnection).toHaveBeenCalledWith('openai', expect.any(String));
    });

    expect((await screen.findAllByText(/openai connection and api key are valid/i)).length).toBeGreaterThan(0);
  });

  it('toggles dark mode from general settings and persists preference', async () => {
    const { user, container } = render(<App />);
    await user.click(await screen.findByTitle('Settings'));
    await user.click(await screen.findByRole('tab', { name: /general settings/i }));

    const darkModeToggle = await screen.findByLabelText(/dark mode:/i);
    expect(darkModeToggle).not.toBeChecked();

    await user.click(darkModeToggle);

    const appRoot = container.querySelector('.app');
    expect(appRoot).toHaveClass('dark-mode');
    expect(window.localStorage.getItem('contextpilot-dark-mode')).toBe('true');
  });

  it('shows anthropic and ollama provider panels in settings modal', async () => {
    mockApi.getSettings.mockResolvedValueOnce({
      ...defaultSettings,
      ollama_configured: true,
    });
    const { user } = render(<App />);

    await user.click(await screen.findByTitle('Settings'));
    await user.click(screen.getByRole('tab', { name: /provider settings/i }));

    await user.click(screen.getByRole('button', { name: 'Anthropic' }));
    expect(await screen.findByText(/anthropic console/i)).toBeInTheDocument();
    expect(screen.getByText('claude-3-5-sonnet-20241022', { selector: '.model-badge' })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /ollama \(local\)/i }));
    expect(await screen.findByText(/download ollama/i)).toBeInTheDocument();
    expect(screen.getByText(/configured/i)).toBeInTheDocument();
  });

  it('switches between provider and general settings tabs', async () => {
    const { user } = render(<App />);
    await user.click(await screen.findByTitle('Settings'));

    expect(await screen.findByRole('tab', { name: /general settings/i })).toHaveAttribute('aria-selected', 'true');
    expect(screen.queryByRole('button', { name: /test openai connection/i })).not.toBeInTheDocument();

    await user.click(screen.getByRole('tab', { name: /provider settings/i }));

    expect(screen.getByRole('tab', { name: /provider settings/i })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('button', { name: /test openai connection/i })).toBeInTheDocument();
  });

  it('updates default model options when default provider changes', async () => {
    const { user, container } = render(<App />);
    await user.click(await screen.findByTitle('Settings'));
    await user.click(await screen.findByRole('tab', { name: /general settings/i }));

    const settingsForm = container.querySelector('.settings-form');
    expect(settingsForm).not.toBeNull();
    const defaultSettingsSection = settingsForm?.querySelector('.form-section');
    const sectionSelects = defaultSettingsSection?.querySelectorAll('select');
    expect(sectionSelects).toHaveLength(2);

    const defaultProviderSelect = sectionSelects?.[0] as HTMLSelectElement;
    const defaultModelSelect = sectionSelects?.[1] as HTMLSelectElement;

    await user.selectOptions(defaultProviderSelect, 'anthropic');
    await waitFor(() => {
      const anthropicValues = Array.from(defaultModelSelect.options).map((option) => option.value);
      expect(anthropicValues).toContain('claude-sonnet-4-5-20250929');
      expect(anthropicValues).toContain('claude-haiku-4-5-20251001');
    });

    await user.selectOptions(defaultProviderSelect, 'openai');
    await waitFor(() => {
      const openaiValues = Array.from(defaultModelSelect.options).map((option) => option.value);
      const openaiLabels = Array.from(defaultModelSelect.options).map((option) => option.text);

      expect(openaiValues).toContain('gpt-3.5-turbo');
      expect(openaiValues).toContain('gpt-4-turbo');
      expect(openaiLabels).toContain('GPT-4 Turbo');
      expect(openaiLabels).toContain('GPT-3.5 Turbo');
    });
  });

  it('submits provider-compatible default model when default provider changes', async () => {
    mockApi.getSettings.mockResolvedValueOnce({
      ...defaultSettings,
      default_ai_provider: 'ollama',
      default_ai_model: 'llama3.2',
    });

    const { user, container } = render(<App />);
    await user.click(await screen.findByTitle('Settings'));
    await user.click(await screen.findByRole('tab', { name: /general settings/i }));

    const settingsForm = container.querySelector('.settings-form');
    expect(settingsForm).not.toBeNull();

    const defaultSettingsSection = settingsForm?.querySelector('.form-section');
    const sectionSelects = defaultSettingsSection?.querySelectorAll('select');
    expect(sectionSelects).toHaveLength(2);

    const defaultProviderSelect = sectionSelects?.[0] as HTMLSelectElement;
    const defaultModelSelect = sectionSelects?.[1] as HTMLSelectElement;

    await user.selectOptions(defaultProviderSelect, 'openai');

    let selectedModel = '';
    await waitFor(() => {
      expect(defaultModelSelect.value).not.toBe('llama3.2');
      selectedModel = defaultModelSelect.value;
    });

    fireEvent.submit(settingsForm as HTMLFormElement);

    await waitFor(() => {
      expect(mockApi.updateSettings).toHaveBeenCalledWith(
        expect.objectContaining({
          default_ai_provider: 'openai',
          default_ai_model: selectedModel,
        })
      );
    });
  });

  it('sends chat and renders assistant response', async () => {
    const { user } = render(<App />);

    const input = await screen.findByPlaceholderText(/ask a question or describe a task/i);
    await user.type(input, 'Hello AI');
    await user.click(screen.getByRole('button', { name: /🚀/i }));

    await waitFor(() => {
      expect(mockApi.chatWithAI).toHaveBeenCalledWith(
        expect.objectContaining({ task: 'Hello AI', max_context_units: 5 })
      );
    });
    expect(await screen.findByText('assistant reply')).toBeInTheDocument();
  });

  it('shows provider/model-aware fallback chat error when backend detail is missing', async () => {
    mockApi.chatWithAI.mockRejectedValueOnce({ response: { status: 500, data: {} } });
    const { user } = render(<App />);

    const input = await screen.findByPlaceholderText(/ask a question or describe a task/i);
    await user.type(input, 'Hello AI');
    await user.click(screen.getByRole('button', { name: /🚀/i }));

    expect((await screen.findAllByText(/failed to generate ai response using provider 'openai' and model 'gpt-4o'/i)).length).toBeGreaterThan(0);
  });

  it('displays backend-attributed model even when requested model differs', async () => {
    mockApi.chatWithAI.mockResolvedValueOnce({
      conversation_id: 'conv-attr',
      task: 'who answered',
      response: 'I am Claude.',
      provider: 'anthropic',
      model: 'claude-sonnet-4-5',
      context_ids: ['ctx-1'],
      prompt_used: 'p',
      timestamp: '2026-02-15T11:05:00Z',
    });

    const { user } = render(<App />);

    const selects = document.querySelectorAll('.chat-settings .setting-select');
    const providerSelect = selects[0] as HTMLSelectElement;
    await user.selectOptions(providerSelect, 'ollama');

    const input = await screen.findByPlaceholderText(/ask a question or describe a task/i);
    await user.type(input, 'who answered');
    await user.click(screen.getByRole('button', { name: /🚀/i }));

    await waitFor(() => {
      expect(mockApi.chatWithAI).toHaveBeenCalledWith(
        expect.objectContaining({ provider: 'ollama' })
      );
    });

    expect(await screen.findByText('I am Claude.')).toBeInTheDocument();
    expect(screen.getByTitle('Generated by claude-sonnet-4-5')).toBeInTheDocument();
  });

  it('uses the last model from selected conversation when available', async () => {
    mockApi.listConversations.mockResolvedValueOnce([
      {
        id: 'conv-existing',
        task: 'existing chat',
        provider: 'openai',
        model: 'gpt-4-turbo',
        created_at: '2026-02-15T11:00:00Z',
        message_count: 2,
      },
    ]);

    mockApi.getConversation.mockResolvedValueOnce({
      id: 'conv-existing',
      task: 'existing chat',
      provider: 'openai',
      model: 'gpt-4-turbo',
      created_at: '2026-02-15T11:00:00Z',
      messages: [
        { role: 'system', content: 'sys', created_at: '2026-02-15T11:00:00Z' },
        { role: 'user', content: 'u1', created_at: '2026-02-15T11:00:01Z' },
        { role: 'assistant', content: 'a1', created_at: '2026-02-15T11:00:02Z' },
      ],
    });

    const { user } = render(<App />);

    await user.click(await screen.findByText(/existing chat/i));

    await waitFor(() => {
      const selects = document.querySelectorAll('.chat-settings .setting-select');
      const providerSelect = selects[0] as HTMLSelectElement;
      const modelSelect = selects[1] as HTMLSelectElement;
      expect(providerSelect.value).toBe('openai');
      expect(modelSelect.value).toBe('gpt-4-turbo');
    });
  });

  it('falls back to provider default model when conversation model is unavailable', async () => {
    mockApi.listConversations.mockResolvedValueOnce([
      {
        id: 'conv-fallback',
        task: 'fallback chat',
        provider: 'anthropic',
        model: 'claude-2-obsolete',
        created_at: '2026-02-15T11:00:00Z',
        message_count: 2,
      },
    ]);

    mockApi.getConversation.mockResolvedValueOnce({
      id: 'conv-fallback',
      task: 'fallback chat',
      provider: 'anthropic',
      model: 'claude-2-obsolete',
      created_at: '2026-02-15T11:00:00Z',
      messages: [
        { role: 'system', content: 'sys', created_at: '2026-02-15T11:00:00Z' },
        { role: 'user', content: 'u1', created_at: '2026-02-15T11:00:01Z' },
        { role: 'assistant', content: 'a1', created_at: '2026-02-15T11:00:02Z' },
      ],
    });

    const { user } = render(<App />);

    await user.click(await screen.findByText(/fallback chat/i));

    await waitFor(() => {
      const selects = document.querySelectorAll('.chat-settings .setting-select');
      const providerSelect = selects[0] as HTMLSelectElement;
      const modelSelect = selects[1] as HTMLSelectElement;
      expect(providerSelect.value).toBe('anthropic');
      expect(modelSelect.value).not.toBe('claude-2-obsolete');
      expect(Array.from(modelSelect.options).map((option) => option.value)).toContain(modelSelect.value);
    });
  });

  it('uses max_context_units=0 for existing conversation until refresh', async () => {
    mockApi.listConversations.mockResolvedValueOnce([
      {
        id: 'conv-1',
        task: 'first task',
        provider: 'openai',
        model: 'gpt-4o',
        created_at: '2026-02-15T11:00:00Z',
        message_count: 2,
      },
    ]);

    const { user } = render(<App />);

    await user.click(await screen.findByText(/first task/i));
    await user.type(await screen.findByPlaceholderText(/continue the conversation/i), 'follow up');
    await user.click(screen.getByRole('button', { name: /🚀/i }));

    await waitFor(() => {
      expect(mockApi.chatWithAI).toHaveBeenCalledWith(
        expect.objectContaining({ task: 'follow up', max_context_units: 0 })
      );
    });

    await user.click(screen.getByRole('button', { name: /refresh contexts/i }));
    await user.type(await screen.findByPlaceholderText(/continue the conversation/i), 'with refresh');
    await user.click(screen.getByRole('button', { name: /🚀/i }));

    await waitFor(() => {
      expect(mockApi.chatWithAI).toHaveBeenLastCalledWith(
        expect.objectContaining({ task: 'with refresh', max_context_units: 5 })
      );
    });
  });

  it('shows conversation load error when getConversation fails', async () => {
    mockApi.listConversations.mockResolvedValueOnce([
      {
        id: 'conv-1',
        task: 'first task',
        provider: 'openai',
        model: 'gpt-4o',
        created_at: '2026-02-15T11:00:00Z',
        message_count: 2,
      },
    ]);
    mockApi.getConversation.mockRejectedValueOnce(new Error('fail to load conv'));
    const { user } = render(<App />);

    await user.click(await screen.findByText(/first task/i));

    await waitFor(() => {
      expect(mockApi.getConversation).toHaveBeenCalledWith('conv-1');
    });
    const log = await screen.findByRole('log', { name: /interaction log output/i });
    expect(log).toHaveTextContent(/failed to load conversation/i);
  });

  it('copies a message to clipboard', async () => {
    const { user } = render(<App />);
    const writeTextSpy = vi
      .spyOn(navigator.clipboard, 'writeText')
      .mockResolvedValue(undefined as unknown as void);

    const input = await screen.findByPlaceholderText(/ask a question or describe a task/i);
    await user.type(input, 'copy target');
    await user.click(screen.getByRole('button', { name: /🚀/i }));

    const copyButtons = await screen.findAllByTitle(/copy message/i);
    await user.click(copyButtons[copyButtons.length - 1]);
    expect(writeTextSpy).toHaveBeenCalled();
    expect(screen.getAllByText(/message copied to clipboard!/i).length).toBeGreaterThan(0);
  });

  it('shows bottom interaction log for user/frontend and frontend/backend events', async () => {
    const { user } = render(<App />);

    const input = await screen.findByPlaceholderText(/ask a question or describe a task/i);
    await user.type(input, 'Log this interaction');
    await user.click(screen.getByRole('button', { name: /🚀/i }));

    const log = await screen.findByRole('log', { name: /interaction log output/i });
    expect(log).toHaveTextContent(/User ↔ Frontend/i);
    expect(log).toHaveTextContent(/Frontend ↔ Backend/i);
    expect(log).toHaveTextContent(/chat message|chat request|chat response/i);

    await user.click(screen.getByRole('button', { name: /clear log/i }));
    expect(log).toHaveTextContent(/no interactions recorded yet/i);
  });
});
