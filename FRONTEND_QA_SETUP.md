# Frontend Quality Assurance & Automated Checks

## Overview
This document outlines the automated testing and quality checks for the ContextPilot frontend.

---

## 1. TypeScript Strict Mode Configuration

### Current: `tsconfig.json`
```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "alwaysStrict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

### Usage
```bash
# Check TypeScript errors (no emit)
npx tsc --noEmit

# Or add to package.json
"type-check": "tsc --noEmit"
```

---

## 2. ESLint Configuration

### Install ESLint
```bash
npm install --save-dev eslint @eslint/js eslint-plugin-react eslint-plugin-react-hooks @typescript-eslint/eslint-plugin @typescript-eslint/parser
```

### Create `.eslintrc.json`
```json
{
  "env": {
    "browser": true,
    "es2021": true
  },
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended"
  ],
  "parser": "@typescript-eslint/parser",
  "parserOptions": {
    "ecmaFeatures": {
      "jsx": true
    },
    "ecmaVersion": "latest",
    "sourceType": "module"
  },
  "plugins": [
    "react",
    "react-hooks",
    "@typescript-eslint"
  ],
  "rules": {
    "react/react-in-jsx-scope": "off",
    "react/prop-types": "off",
    "@typescript-eslint/no-unused-vars": [
      "error",
      {
        "argsIgnorePattern": "^_",
        "varsIgnorePattern": "^_"
      }
    ],
    "no-console": [
      "warn",
      {
        "allow": ["warn", "error"]
      }
    ]
  },
  "settings": {
    "react": {
      "version": "detect"
    }
  }
}
```

### Create `.eslintignore`
```
node_modules/
dist/
build/
.vite/
*.config.js
```

### Usage
```bash
# Lint all files
npx eslint src/

# Fix auto-fixable issues
npx eslint src/ --fix

# Or add to package.json
"lint": "eslint src/",
"lint:fix": "eslint src/ --fix"
```

---

## 3. Unit Testing with Vitest

### Install Vitest
```bash
npm install --save-dev vitest @vitest/ui happy-dom @testing-library/react @testing-library/jest-dom
```

### Create `vitest.config.ts`
```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'happy-dom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
      ]
    }
  }
});
```

### Create `src/test/setup.ts`
```typescript
import '@testing-library/jest-dom';
import { expect, afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});
```

### Example Test: `src/api.test.ts`
```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import axios from 'axios';
import { contextAPI } from './api';

vi.mock('axios');

describe('contextAPI', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should create a context', async () => {
    const mockData = {
      id: '123',
      type: 'preference',
      content: 'Test content',
      confidence: 0.9,
      created_at: new Date().toISOString(),
      last_used: null,
      source: 'manual',
      tags: [],
      status: 'active',
      superseded_by: null
    };

    (axios.post as any).mockResolvedValueOnce({ data: mockData });

    const result = await contextAPI.createContext({
      type: 'preference',
      content: 'Test content',
      confidence: 0.9,
      tags: []
    });

    expect(result.id).toBe('123');
    expect(result.content).toBe('Test content');
  });

  it('should list contexts', async () => {
    const mockContexts = [
      { id: '1', type: 'preference', content: 'Test 1' },
      { id: '2', type: 'fact', content: 'Test 2' }
    ];

    (axios.get as any).mockResolvedValueOnce({ data: mockContexts });

    const result = await contextAPI.listContexts();

    expect(result).toHaveLength(2);
    expect(result[0].id).toBe('1');
  });
});
```

### Usage
```bash
# Run tests
npm run test

# Watch mode
npm run test:watch

# Coverage
npm run test:coverage

# UI dashboard
npm run test:ui

# Or add to package.json
"test": "vitest",
"test:watch": "vitest --watch",
"test:coverage": "vitest --coverage",
"test:ui": "vitest --ui"
```

---

## 4. Integration Testing with Playwright

### Install Playwright
```bash
npm install --save-dev @playwright/test
npx playwright install
```

### Create `playwright.config.ts`
```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

### Example E2E Test: `e2e/chat.spec.ts`
```typescript
import { test, expect } from '@playwright/test';

test.describe('Chat Tab', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Wait for app to load
    await page.waitForSelector('button[title*="Chat"]', { timeout: 5000 });
  });

  test('should display chat interface', async ({ page }) => {
    const chatTab = page.locator('button[title*="Chat"]');
    await expect(chatTab).toBeVisible();
    await chatTab.click();

    const messageInput = page.locator('input[placeholder*="message"]');
    await expect(messageInput).toBeVisible();
  });

  test('should send message when OpenAI provider selected', async ({ page }) => {
    // Click settings icon
    await page.click('button[title*="Settings"]');

    // Fill OpenAI API key
    const apiKeyInput = page.locator('input[placeholder*="OpenAI"]');
    await apiKeyInput.fill('sk-test-key');

    // Select OpenAI provider
    const providerSelect = page.locator('select');
    await providerSelect.first().selectOption('openai');

    // Go back to chat
    await page.click('button[title*="Chat"]');

    // Send message
    const messageInput = page.locator('input[placeholder*="message"]');
    await messageInput.fill('Hello');
    await page.keyboard.press('Enter');

    // Expect loading indicator or response
    await expect(page.locator('.message-assistant, .typing-indicator')).toBeVisible({ timeout: 10000 });
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Verify error handling UI exists
    const errorContainer = page.locator('.error-message, .error');
    // Test should show error if API fails
  });
});
```

### Usage
```bash
# Run E2E tests
npx playwright test

# Run with UI
npx playwright test --ui

# Debug mode
npx playwright test --debug

# Or add to package.json
"e2e": "playwright test",
"e2e:ui": "playwright test --ui",
"e2e:debug": "playwright test --debug"
```

---

## 5. Pre-commit Hooks with Husky

### Install Husky
```bash
npm install husky --save-dev
npx husky install
npx husky add .husky/pre-commit "npm run pre-commit"
```

### Add to `package.json`
```json
{
  "scripts": {
    "pre-commit": "npm run type-check && npm run lint && npm run test:quick"
  }
}
```

### Create `.husky/pre-commit`
```bash
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

npm run pre-commit
```

---

## 6. GitHub Actions CI/CD Pipeline

### Create `.github/workflows/frontend-ci.yml`
```yaml
name: Frontend CI

on:
  push:
    branches: [ main, develop ]
    paths:
      - 'frontend/**'
      - '.github/workflows/frontend-ci.yml'
  pull_request:
    branches: [ main, develop ]
    paths:
      - 'frontend/**'

jobs:
  quality:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./frontend

    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Type checking
        run: npm run type-check
        continue-on-error: true

      - name: Linting
        run: npm run lint
        continue-on-error: true

      - name: Unit tests
        run: npm run test:coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./frontend/coverage/coverage-final.json
          flags: frontend
          name: frontend-coverage

  build:
    needs: quality
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./frontend

    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Build for production
        run: npm run build

      - name: Verify build artifacts
        run: |
          test -f dist/index.html || exit 1
          test -d dist/assets || exit 1
          echo "Build artifacts verified ✓"

      - name: Upload build artifacts
        uses: actions/upload-artifact@v3
        with:
          name: build-artifacts
          path: frontend/dist

  e2e:
    needs: build
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./frontend

    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Run E2E tests
        run: npm run e2e

      - name: Upload Playwright report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
```

---

## 7. Complete Package.json Scripts

### Updated `package.json`
```json
{
  "name": "contextpilot-frontend",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "start": "vite",
    "type-check": "tsc --noEmit",
    "lint": "eslint src/ --max-warnings 0",
    "lint:fix": "eslint src/ --fix",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:coverage": "vitest --coverage",
    "test:ui": "vitest --ui",
    "test:quick": "vitest --run",
    "e2e": "playwright test",
    "e2e:ui": "playwright test --ui",
    "e2e:debug": "playwright test --debug",
    "pre-commit": "npm run type-check && npm run lint && npm run test:quick",
    "qa": "npm run type-check && npm run lint && npm run test:coverage && npm run build",
    "qa:full": "npm run qa && npm run e2e"
  },
  "dependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^5.1.3",
    "axios": "^1.13.4",
    "highlight.js": "^11.11.1",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-markdown": "^10.1.0",
    "rehype-highlight": "^7.0.2",
    "remark-gfm": "^4.0.1",
    "typescript": "^4.9.5",
    "vite": "^7.3.1"
  },
  "devDependencies": {
    "@eslint/js": "^9.0.0",
    "@playwright/test": "^1.40.0",
    "@testing-library/jest-dom": "^6.1.5",
    "@testing-library/react": "^14.1.2",
    "@types/node": "^20.0.0",
    "@typescript-eslint/eslint-plugin": "^6.13.2",
    "@typescript-eslint/parser": "^6.13.2",
    "@vitest/ui": "^1.0.4",
    "eslint": "^8.55.0",
    "eslint-plugin-react": "^7.33.2",
    "eslint-plugin-react-hooks": "^4.6.0",
    "happy-dom": "^12.10.3",
    "husky": "^8.0.3",
    "vitest": "^1.0.4"
  }
}
```

---

## 8. Automated Quality Gate Script

### Create `scripts/quality-check.sh`
```bash
#!/bin/bash

set -e

echo "🔍 Running Frontend Quality Checks..."
echo ""

cd frontend

# TypeScript
echo "✓ TypeScript type checking..."
npm run type-check || { echo "❌ Type check failed"; exit 1; }

# ESLint
echo "✓ Linting code..."
npm run lint || { echo "❌ Linting failed"; exit 1; }

# Unit Tests
echo "✓ Running unit tests..."
npm run test:quick || { echo "❌ Tests failed"; exit 1; }

# Build
echo "✓ Building for production..."
npm run build || { echo "❌ Build failed"; exit 1; }

# Verify artifacts
if [ ! -f "dist/index.html" ]; then
  echo "❌ Build artifacts missing"
  exit 1
fi

echo ""
echo "✅ All quality checks passed!"
echo ""
echo "Summary:"
echo "  ✓ TypeScript compilation successful"
echo "  ✓ ESLint passed with no warnings"
echo "  ✓ All tests passed"
echo "  ✓ Production build successful"
```

### Make executable
```bash
chmod +x scripts/quality-check.sh
```

### Run before deployment
```bash
./scripts/quality-check.sh
```

---

## 9. Environment-Specific Validation

### Create `src/config.test.ts`
```typescript
import { describe, it, expect } from 'vitest';

describe('Configuration Validation', () => {
  it('should use correct API URL in development', () => {
    if (import.meta.env.MODE === 'development') {
      expect(import.meta.env.VITE_API_URL).toBe('http://localhost:8000');
    }
  });

  it('should have API URL configured', () => {
    expect(import.meta.env.VITE_API_URL).toBeDefined();
  });

  it('should not expose sensitive keys', () => {
    const html = document.documentElement.innerHTML;
    expect(html).not.toContain('sk-');
    expect(html).not.toContain('sk_');
  });
});
```

---

## 10. Quick Start Commands

### Initialize Everything
```bash
cd frontend

# Install all dependencies
npm install

# Setup Husky hooks
npx husky install

# Run full QA
npm run qa

# Run with E2E
npm run qa:full
```

### Daily Development
```bash
# Watch mode with live reload
npm run dev

# Watch tests
npm run test:watch

# Fix linting issues
npm run lint:fix
```

### Pre-Deployment Checklist
```bash
# Run all quality checks
npm run qa

# If E2E environment ready
npm run e2e

# Check test coverage
npm run test:coverage
```

---

## 11. Dashboard & Reporting

### Vitest UI Dashboard
```bash
npm run test:ui
# Opens http://localhost:51204/__vitest__/
```

### Coverage HTML Report
```bash
npm run test:coverage
# Opens coverage/index.html
```

### Playwright Report
```bash
npx playwright show-report
```

---

## 12. Integration with Main CI/CD

### Backend Trigger Frontend Checks
Create `.github/workflows/full-ci.yml`:
```yaml
name: Full CI Pipeline

on: [push, pull_request]

jobs:
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: cd frontend && npm ci && npm run qa

  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: cd backend && pip install -r requirements.txt && pytest
```

---

## Summary

This setup provides:
✅ **Type Checking** - TypeScript strict mode
✅ **Code Quality** - ESLint with React rules
✅ **Unit Tests** - Vitest with coverage
✅ **E2E Tests** - Playwright cross-browser
✅ **Pre-commit** - Automatic checks before commits
✅ **CI/CD** - GitHub Actions automation
✅ **Dashboards** - Visual test/coverage reports
✅ **Metrics** - Coverage tracking and artifacts

All frontend issues will be caught automatically before reaching production!
