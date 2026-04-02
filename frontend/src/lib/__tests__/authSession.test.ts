import { afterEach, describe, expect, it } from 'vitest';
import { clearAuthSession, getAccessToken, getStoredAuthSession, saveAuthSession } from '../authSession';

const STORAGE_KEY = 'forecast-system-auth-session';

afterEach(() => {
  window.localStorage.clear();
});

describe('getStoredAuthSession', () => {
  it('returns null when nothing is stored', () => {
    expect(getStoredAuthSession()).toBeNull();
  });

  it('returns the parsed session when stored', () => {
    const session = { accessToken: 'tok', user: { userAccountId: '1', email: 'a@b.com', roles: [] } };
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    expect(getStoredAuthSession()).toEqual(session);
  });

  it('removes corrupted data and returns null', () => {
    window.localStorage.setItem(STORAGE_KEY, 'not-valid-json{{{');
    expect(getStoredAuthSession()).toBeNull();
    expect(window.localStorage.getItem(STORAGE_KEY)).toBeNull();
  });
});

describe('saveAuthSession', () => {
  it('serializes session into localStorage', () => {
    const session = { accessToken: 'tok2', user: { userAccountId: '2', email: 'b@c.com', roles: ['CityPlanner'] } };
    saveAuthSession(session);
    expect(JSON.parse(window.localStorage.getItem(STORAGE_KEY)!)).toEqual(session);
  });
});

describe('clearAuthSession', () => {
  it('removes the session from localStorage', () => {
    window.localStorage.setItem(STORAGE_KEY, '{}');
    clearAuthSession();
    expect(window.localStorage.getItem(STORAGE_KEY)).toBeNull();
  });
});

describe('getAccessToken', () => {
  it('returns null when no session', () => {
    expect(getAccessToken()).toBeNull();
  });

  it('returns the access token from stored session', () => {
    const session = { accessToken: 'my-token', user: { userAccountId: '3', email: 'c@d.com', roles: [] } };
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    expect(getAccessToken()).toBe('my-token');
  });
});

describe('authSession – window undefined branches (SSR guard)', () => {
  it('getStoredAuthSession returns null when window is undefined (line 6)', () => {
    const originalWindow = globalThis.window;
    // @ts-expect-error intentionally setting window to undefined for SSR simulation
    delete globalThis.window;
    try {
      expect(getStoredAuthSession()).toBeNull();
    } finally {
      globalThis.window = originalWindow;
    }
  });

  it('saveAuthSession returns early when window is undefined (line 18)', () => {
    const originalWindow = globalThis.window;
    // @ts-expect-error intentionally setting window to undefined for SSR simulation
    delete globalThis.window;
    try {
      // Should not throw; just returns early
      expect(() =>
        saveAuthSession({ accessToken: 'x', user: { userAccountId: '1', email: 'a@b.com', roles: [] } }),
      ).not.toThrow();
    } finally {
      globalThis.window = originalWindow;
    }
  });

  it('clearAuthSession returns early when window is undefined (line 23)', () => {
    const originalWindow = globalThis.window;
    // @ts-expect-error intentionally setting window to undefined for SSR simulation
    delete globalThis.window;
    try {
      expect(() => clearAuthSession()).not.toThrow();
    } finally {
      globalThis.window = originalWindow;
    }
  });
});
