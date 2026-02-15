import { render, screen, waitFor } from '@testing-library/react';
import React, { useEffect } from 'react';
import { describe, expect, it, vi } from 'vitest';
import { AppProvider, actions, useAppContext } from './AppContext';
import { createMockContext, createMockMessage } from './test/factories';

function StateView() {
  const { state } = useAppContext();
  return <pre data-testid="state">{JSON.stringify(state)}</pre>;
}

function DispatchOnMount({ action }: { action: ReturnType<(typeof actions)[keyof typeof actions]> }) {
  const { dispatch } = useAppContext();

  useEffect(() => {
    dispatch(action);
  }, [dispatch, action]);

  return <StateView />;
}

function renderWithProvider(ui: React.ReactElement) {
  return render(<AppProvider>{ui}</AppProvider>);
}

function parseState() {
  const raw = screen.getByTestId('state').textContent || '{}';
  return JSON.parse(raw);
}

describe('AppContext', () => {
  it('provides initial state values', () => {
    renderWithProvider(<StateView />);
    const state = parseState();

    expect(state.contexts).toEqual([]);
    expect(state.stats).toBeNull();
    expect(state.generatedPrompt).toBeNull();
    expect(state.aiResponse).toBeNull();
    expect(state.conversations).toEqual([]);
    expect(state.selectedConversation).toBeNull();
    expect(state.loading).toBe(false);
    expect(state.error).toBeNull();
    expect(state.success).toBeNull();
  });

  it('throws when useAppContext is used outside provider', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => render(<StateView />)).toThrow('useAppContext must be used within an AppProvider');

    spy.mockRestore();
  });

  it('sets contexts', async () => {
    const contexts = [createMockContext({ id: '1' }), createMockContext({ id: '2' })];
    renderWithProvider(<DispatchOnMount action={actions.setContexts(contexts)} />);

    await waitFor(() => {
      expect(parseState().contexts).toHaveLength(2);
    });
  });

  it('adds context', async () => {
    const context = createMockContext({ id: 'new' });
    renderWithProvider(<DispatchOnMount action={actions.addContext(context)} />);

    await waitFor(() => {
      expect(parseState().contexts[0].id).toBe('new');
    });
  });

  it('updates context by id', async () => {
    function Harness() {
      const { dispatch } = useAppContext();
      useEffect(() => {
        dispatch(actions.setContexts([createMockContext({ id: '1', content: 'old' })]));
        dispatch(actions.updateContext(createMockContext({ id: '1', content: 'updated' })));
      }, [dispatch]);
      return <StateView />;
    }

    renderWithProvider(<Harness />);

    await waitFor(() => {
      expect(parseState().contexts[0].content).toBe('updated');
    });
  });

  it('does not update non-matching context ids', async () => {
    function Harness() {
      const { dispatch } = useAppContext();
      useEffect(() => {
        dispatch(actions.setContexts([createMockContext({ id: '1', content: 'one' })]));
        dispatch(actions.updateContext(createMockContext({ id: '2', content: 'two' })));
      }, [dispatch]);
      return <StateView />;
    }

    renderWithProvider(<Harness />);

    await waitFor(() => {
      expect(parseState().contexts[0].content).toBe('one');
    });
  });

  it('deletes context by id', async () => {
    function Harness() {
      const { dispatch } = useAppContext();
      useEffect(() => {
        dispatch(actions.setContexts([createMockContext({ id: '1' }), createMockContext({ id: '2' })]));
        dispatch(actions.deleteContext('1'));
      }, [dispatch]);
      return <StateView />;
    }

    renderWithProvider(<Harness />);

    await waitFor(() => {
      const state = parseState();
      expect(state.contexts).toHaveLength(1);
      expect(state.contexts[0].id).toBe('2');
    });
  });

  it('sets stats', async () => {
    renderWithProvider(
      <DispatchOnMount
        action={actions.setStats({
          total_contexts: 10,
          active_contexts: 8,
          superseded_contexts: 2,
          contexts_by_type: { preference: 2, goal: 3, decision: 1, fact: 4 },
          contexts_with_embeddings: 6,
        })}
      />
    );

    await waitFor(() => {
      expect(parseState().stats.total_contexts).toBe(10);
    });
  });

  it('sets generated prompt', async () => {
    renderWithProvider(
      <DispatchOnMount
        action={actions.setGeneratedPrompt({
          original_task: 'task',
          relevant_context: [],
          generated_prompt: 'prompt',
          timestamp: '2026-01-01',
        })}
      />
    );

    await waitFor(() => {
      expect(parseState().generatedPrompt.generated_prompt).toBe('prompt');
    });
  });

  it('clears generated prompt with null', async () => {
    renderWithProvider(<DispatchOnMount action={actions.setGeneratedPrompt(null)} />);
    await waitFor(() => {
      expect(parseState().generatedPrompt).toBeNull();
    });
  });

  it('sets ai response', async () => {
    renderWithProvider(
      <DispatchOnMount
        action={actions.setAiResponse({
          conversation_id: 'c1',
          task: 'hello',
          response: 'world',
          provider: 'openai',
          model: 'gpt-4o',
          context_ids: ['1'],
          prompt_used: 'p',
          timestamp: '2026-01-01',
        })}
      />
    );

    await waitFor(() => {
      expect(parseState().aiResponse.response).toBe('world');
    });
  });

  it('clears ai response with null', async () => {
    renderWithProvider(<DispatchOnMount action={actions.setAiResponse(null)} />);
    await waitFor(() => {
      expect(parseState().aiResponse).toBeNull();
    });
  });

  it('sets conversations', async () => {
    renderWithProvider(
      <DispatchOnMount
        action={actions.setConversations([
          { id: '1', task: 't1', provider: 'openai', model: 'gpt-4o', created_at: '2026-01-01' },
          { id: '2', task: 't2', provider: 'openai', model: 'gpt-4o', created_at: '2026-01-02' },
        ])}
      />
    );

    await waitFor(() => {
      expect(parseState().conversations).toHaveLength(2);
    });
  });

  it('sets selected conversation', async () => {
    renderWithProvider(
      <DispatchOnMount
        action={actions.setSelectedConversation({
          id: 'selected',
          task: 'task',
          provider: 'openai',
          model: 'gpt-4o',
          created_at: '2026-01-01',
        })}
      />
    );

    await waitFor(() => {
      expect(parseState().selectedConversation.id).toBe('selected');
    });
  });

  it('clears selected conversation with null', async () => {
    renderWithProvider(<DispatchOnMount action={actions.setSelectedConversation(null)} />);
    await waitFor(() => {
      expect(parseState().selectedConversation).toBeNull();
    });
  });

  it('sets loading', async () => {
    renderWithProvider(<DispatchOnMount action={actions.setLoading(true)} />);
    await waitFor(() => {
      expect(parseState().loading).toBe(true);
    });
  });

  it('setError clears success message', async () => {
    function Harness() {
      const { dispatch } = useAppContext();
      useEffect(() => {
        dispatch(actions.setSuccess('ok'));
        dispatch(actions.setError('bad'));
      }, [dispatch]);
      return <StateView />;
    }

    renderWithProvider(<Harness />);
    await waitFor(() => {
      const state = parseState();
      expect(state.error).toBe('bad');
      expect(state.success).toBeNull();
    });
  });

  it('setSuccess clears error message', async () => {
    function Harness() {
      const { dispatch } = useAppContext();
      useEffect(() => {
        dispatch(actions.setError('bad'));
        dispatch(actions.setSuccess('ok'));
      }, [dispatch]);
      return <StateView />;
    }

    renderWithProvider(<Harness />);
    await waitFor(() => {
      const state = parseState();
      expect(state.success).toBe('ok');
      expect(state.error).toBeNull();
    });
  });

  it('clearMessages clears both error and success', async () => {
    function Harness() {
      const { dispatch } = useAppContext();
      useEffect(() => {
        dispatch(actions.setError('bad'));
        dispatch(actions.setSuccess('ok'));
        dispatch(actions.clearMessages());
      }, [dispatch]);
      return <StateView />;
    }

    renderWithProvider(<Harness />);
    await waitFor(() => {
      const state = parseState();
      expect(state.error).toBeNull();
      expect(state.success).toBeNull();
    });
  });

  it('action creator setContexts returns expected action', () => {
    const payload = [createMockContext({ id: 'x' })];
    expect(actions.setContexts(payload)).toEqual({ type: 'SET_CONTEXTS', payload });
  });

  it('action creator addContext returns expected action', () => {
    const payload = createMockContext({ id: 'x' });
    expect(actions.addContext(payload)).toEqual({ type: 'ADD_CONTEXT', payload });
  });

  it('action creator updateContext returns expected action', () => {
    const payload = createMockContext({ id: 'x' });
    expect(actions.updateContext(payload)).toEqual({ type: 'UPDATE_CONTEXT', payload });
  });

  it('action creator deleteContext returns expected action', () => {
    expect(actions.deleteContext('abc')).toEqual({ type: 'DELETE_CONTEXT', payload: 'abc' });
  });

  it('action creator setStats returns expected action', () => {
    const stats = {
      total_contexts: 1,
      active_contexts: 1,
      superseded_contexts: 0,
      contexts_by_type: {},
      contexts_with_embeddings: 0,
    };
    expect(actions.setStats(stats)).toEqual({ type: 'SET_STATS', payload: stats });
  });

  it('action creator setGeneratedPrompt returns expected action', () => {
    const prompt = {
      original_task: 't',
      relevant_context: [],
      generated_prompt: 'p',
      timestamp: '2026',
    };
    expect(actions.setGeneratedPrompt(prompt)).toEqual({ type: 'SET_GENERATED_PROMPT', payload: prompt });
  });

  it('action creator setAiResponse returns expected action', () => {
    const response = {
      conversation_id: '1',
      task: 't',
      response: 'r',
      provider: 'openai',
      model: 'gpt-4o',
      context_ids: [],
      prompt_used: 'p',
      timestamp: '2026',
    };
    expect(actions.setAiResponse(response)).toEqual({ type: 'SET_AI_RESPONSE', payload: response });
  });

  it('action creator setConversations returns expected action', () => {
    const conversations = [{ id: '1', task: 't', provider: 'openai', model: 'gpt-4o', created_at: '2026' }];
    expect(actions.setConversations(conversations)).toEqual({ type: 'SET_CONVERSATIONS', payload: conversations });
  });

  it('action creator setSelectedConversation returns expected action', () => {
    const conversation = { id: '1', task: 't', provider: 'openai', model: 'gpt-4o', created_at: '2026' };
    expect(actions.setSelectedConversation(conversation)).toEqual({
      type: 'SET_SELECTED_CONVERSATION',
      payload: conversation,
    });
  });

  it('action creator setLoading returns expected action', () => {
    expect(actions.setLoading(true)).toEqual({ type: 'SET_LOADING', payload: true });
  });

  it('action creator setError returns expected action', () => {
    expect(actions.setError('err')).toEqual({ type: 'SET_ERROR', payload: 'err' });
  });

  it('action creator setSuccess returns expected action', () => {
    expect(actions.setSuccess('ok')).toEqual({ type: 'SET_SUCCESS', payload: 'ok' });
  });

  it('action creator clearMessages returns expected action', () => {
    expect(actions.clearMessages()).toEqual({ type: 'CLEAR_MESSAGES' });
  });

  it('can hold conversation message objects in selected conversation', async () => {
    const messages = [createMockMessage({ content: 'hello' })];

    renderWithProvider(
      <DispatchOnMount
        action={actions.setSelectedConversation({
          id: 'with-msgs',
          task: 'chat',
          provider: 'openai',
          model: 'gpt-4o',
          created_at: '2026-01-01',
          messages,
        })}
      />
    );

    await waitFor(() => {
      expect(parseState().selectedConversation.messages[0].content).toBe('hello');
    });
  });
});
