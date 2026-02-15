import { vi } from 'vitest';

export const mockApiClient = {
  createContext: vi.fn(),
  getContexts: vi.fn(),
  updateContext: vi.fn(),
  deleteContext: vi.fn(),
  chat: vi.fn(),
  search: vi.fn(),
};

export const createAxiosMock = () => ({
  post: vi.fn(),
  get: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
});

export const setupApiMocks = () => {
  vi.mock('axios', () => ({
    default: {
      create: vi.fn(() => createAxiosMock()),
    },
  }));
};
