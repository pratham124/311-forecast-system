import '@testing-library/jest-dom/vitest';
import * as React from 'react';
import { afterEach, vi } from 'vitest';

vi.mock('recharts', async () => {
  const actual = await vi.importActual<typeof import('recharts')>('recharts');

  return {
    ...actual,
    ResponsiveContainer: ({
      children,
      minWidth = 320,
      minHeight = 320,
    }: {
      children: React.ReactNode | ((size: { width: number; height: number }) => React.ReactNode);
      minWidth?: number;
      minHeight?: number;
    }) =>
      React.createElement(
        'div',
        {
          style: { width: Number(minWidth) || 320, height: Number(minHeight) || 320 },
        },
        typeof children === 'function' ? children({ width: Number(minWidth) || 320, height: Number(minHeight) || 320 }) : children,
      ),
  };
});

// Node 20+ can expose a broken experimental localStorage that Vitest/jsdom inherit;
// replace with an in-memory store so authSession and pages using storage work in tests.
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => (key in store ? store[key] : null),
    setItem: (key: string, value: string) => {
      store[key] = String(value);
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
    key: (index: number) => Object.keys(store)[index] ?? null,
    get length() {
      return Object.keys(store).length;
    },
  };
})();

Object.defineProperty(globalThis, 'localStorage', {
  value: localStorageMock,
  writable: true,
  configurable: true,
});

class ResizeObserverMock {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}

Object.defineProperty(globalThis, 'ResizeObserver', {
  value: ResizeObserverMock,
  writable: true,
  configurable: true,
});

const originalConsoleError = console.error.bind(console);
const originalConsoleWarn = console.warn.bind(console);

function shouldSuppressTestNoise(args: unknown[]): boolean {
  const message = args.map((arg) => String(arg)).join(' ');

  return (
    message.includes('The width(-1) and height(-1) of chart should be greater than 0') ||
    message.includes('comparison crashed') ||
    message.includes('Renderer crashed') ||
    message.includes('chart crashed') ||
    message.includes('Error: Uncaught [Error: comparison crashed]') ||
    message.includes('Error: Uncaught [Error: Renderer crashed]') ||
    message.includes('Error: Uncaught [Error: chart crashed]') ||
    message.includes('The above error occurred in the <ForecastAccuracyComparison> component') ||
    message.includes('The above error occurred in the <UserGuideBody> component') ||
    message.includes('The above error occurred in the <Crash> component')
  );
}

vi.spyOn(console, 'error').mockImplementation((...args: Parameters<typeof console.error>) => {
  if (shouldSuppressTestNoise(args)) {
    return;
  }
  originalConsoleError(...args);
});

vi.spyOn(console, 'warn').mockImplementation((...args: Parameters<typeof console.warn>) => {
  if (shouldSuppressTestNoise(args)) {
    return;
  }
  originalConsoleWarn(...args);
});

afterEach(() => {
  vi.useRealTimers();
});
