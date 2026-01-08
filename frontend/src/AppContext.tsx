/**
 * Global state management using React Context API.
 */
import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import { ContextUnit, Stats, GeneratedPrompt, AIResponse, Conversation } from './types';

// State interface
interface AppState {
  contexts: ContextUnit[];
  stats: Stats | null;
  generatedPrompt: GeneratedPrompt | null;
  aiResponse: AIResponse | null;
  conversations: Conversation[];
  selectedConversation: Conversation | null;
  loading: boolean;
  error: string | null;
  success: string | null;
}

// Action types
type AppAction =
  | { type: 'SET_CONTEXTS'; payload: ContextUnit[] }
  | { type: 'ADD_CONTEXT'; payload: ContextUnit }
  | { type: 'UPDATE_CONTEXT'; payload: ContextUnit }
  | { type: 'DELETE_CONTEXT'; payload: string }
  | { type: 'SET_STATS'; payload: Stats }
  | { type: 'SET_GENERATED_PROMPT'; payload: GeneratedPrompt | null }
  | { type: 'SET_AI_RESPONSE'; payload: AIResponse | null }
  | { type: 'SET_CONVERSATIONS'; payload: Conversation[] }
  | { type: 'SET_SELECTED_CONVERSATION'; payload: Conversation | null }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_SUCCESS'; payload: string | null }
  | { type: 'CLEAR_MESSAGES' };

// Initial state
const initialState: AppState = {
  contexts: [],
  stats: null,
  generatedPrompt: null,
  aiResponse: null,
  conversations: [],
  selectedConversation: null,
  loading: false,
  error: null,
  success: null,
};

// Reducer
function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_CONTEXTS':
      return { ...state, contexts: action.payload };
    
    case 'ADD_CONTEXT':
      return { ...state, contexts: [...state.contexts, action.payload] };
    
    case 'UPDATE_CONTEXT':
      return {
        ...state,
        contexts: state.contexts.map(c =>
          c.id === action.payload.id ? action.payload : c
        ),
      };
    
    case 'DELETE_CONTEXT':
      return {
        ...state,
        contexts: state.contexts.filter(c => c.id !== action.payload),
      };
    
    case 'SET_STATS':
      return { ...state, stats: action.payload };
    
    case 'SET_GENERATED_PROMPT':
      return { ...state, generatedPrompt: action.payload };
    
    case 'SET_AI_RESPONSE':
      return { ...state, aiResponse: action.payload };
    
    case 'SET_CONVERSATIONS':
      return { ...state, conversations: action.payload };
    
    case 'SET_SELECTED_CONVERSATION':
      return { ...state, selectedConversation: action.payload };
    
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    
    case 'SET_ERROR':
      return { ...state, error: action.payload, success: null };
    
    case 'SET_SUCCESS':
      return { ...state, success: action.payload, error: null };
    
    case 'CLEAR_MESSAGES':
      return { ...state, error: null, success: null };
    
    default:
      return state;
  }
}

// Context
interface AppContextValue {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
}

const AppContext = createContext<AppContextValue | undefined>(undefined);

// Provider component
interface AppProviderProps {
  children: ReactNode;
}

export function AppProvider({ children }: AppProviderProps) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
}

// Custom hook to use the context
export function useAppContext() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
}

// Action creators (helper functions)
export const actions = {
  setContexts: (contexts: ContextUnit[]): AppAction => ({
    type: 'SET_CONTEXTS',
    payload: contexts,
  }),
  
  addContext: (context: ContextUnit): AppAction => ({
    type: 'ADD_CONTEXT',
    payload: context,
  }),
  
  updateContext: (context: ContextUnit): AppAction => ({
    type: 'UPDATE_CONTEXT',
    payload: context,
  }),
  
  deleteContext: (id: string): AppAction => ({
    type: 'DELETE_CONTEXT',
    payload: id,
  }),
  
  setStats: (stats: Stats): AppAction => ({
    type: 'SET_STATS',
    payload: stats,
  }),
  
  setGeneratedPrompt: (prompt: GeneratedPrompt | null): AppAction => ({
    type: 'SET_GENERATED_PROMPT',
    payload: prompt,
  }),
  
  setAiResponse: (response: AIResponse | null): AppAction => ({
    type: 'SET_AI_RESPONSE',
    payload: response,
  }),
  
  setConversations: (conversations: Conversation[]): AppAction => ({
    type: 'SET_CONVERSATIONS',
    payload: conversations,
  }),
  
  setSelectedConversation: (conversation: Conversation | null): AppAction => ({
    type: 'SET_SELECTED_CONVERSATION',
    payload: conversation,
  }),
  
  setLoading: (loading: boolean): AppAction => ({
    type: 'SET_LOADING',
    payload: loading,
  }),
  
  setError: (error: string | null): AppAction => ({
    type: 'SET_ERROR',
    payload: error,
  }),
  
  setSuccess: (success: string | null): AppAction => ({
    type: 'SET_SUCCESS',
    payload: success,
  }),
  
  clearMessages: (): AppAction => ({
    type: 'CLEAR_MESSAGES',
  }),
};
