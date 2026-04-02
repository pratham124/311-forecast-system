import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  fetchCurrentUser,
  loginUser,
  logoutSession,
  refreshSession,
  refreshStoredSession,
  registerUser,
} from '../auth';

const STORAGE_KEY = 'forecast-system-auth-session';

const fetchMock = vi.fn();

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock);
  window.localStorage.clear();
});

afterEach(() => {
  vi.unstubAllGlobals();
  fetchMock.mockReset();
  window.localStorage.clear();
});

function okJson(body: unknown) {
  return new Response(JSON.stringify(body), { status: 200 });
}

function errJson(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status });
}

const authResponse = { accessToken: 'tok', user: { id: '1', email: 'a@b.com', roles: [] } };

describe('loginUser', () => {
  it('returns response on success', async () => {
    fetchMock.mockResolvedValue(okJson(authResponse));
    const result = await loginUser('a@b.com', 'password');
    expect(result).toEqual(authResponse);
  });

  it('throws with detail string on failure', async () => {
    fetchMock.mockResolvedValue(errJson(401, { detail: 'Invalid credentials' }));
    await expect(loginUser('a@b.com', 'bad')).rejects.toThrow('Invalid credentials');
  });

  it('throws with joined validation messages on array detail', async () => {
    fetchMock.mockResolvedValue(errJson(422, {
      detail: [
        { loc: ['body', 'password'], msg: 'too short', type: 'string_too_short' },
      ],
    }));
    await expect(loginUser('a@b.com', 'x')).rejects.toThrow('Password must be at least 8 characters.');
  });

  it('throws fallback when array detail messages are all null', async () => {
    fetchMock.mockResolvedValue(errJson(422, {
      detail: [{ loc: ['body', 'unknown_field'] }],
    }));
    await expect(loginUser('a@b.com', 'x')).rejects.toThrow('Please check your details and try again.');
  });

  it('throws status code error when response body is not JSON', async () => {
    fetchMock.mockResolvedValue(new Response('not json', { status: 500 }));
    await expect(loginUser('a@b.com', 'x')).rejects.toThrow('Auth request failed with status 500');
  });

  it('throws with password:msg when field is password with msg (non-too_short)', async () => {
    fetchMock.mockResolvedValue(errJson(422, {
      detail: [{ loc: ['body', 'password'], msg: 'too common', type: 'value_error' }],
    }));
    await expect(loginUser('a@b.com', 'x')).rejects.toThrow('Password: too common');
  });

  it('throws with email:msg when field is email', async () => {
    fetchMock.mockResolvedValue(errJson(422, {
      detail: [{ loc: ['body', 'email'], msg: 'not valid' }],
    }));
    await expect(loginUser('a@b.com', 'x')).rejects.toThrow('Email: not valid');
  });

  it('capitalizes generic field msg', async () => {
    fetchMock.mockResolvedValue(errJson(422, {
      detail: [{ loc: ['body', 'other'], msg: 'value is wrong' }],
    }));
    await expect(loginUser('a@b.com', 'x')).rejects.toThrow('Value is wrong');
  });

  it('throws status fallback when detail is missing entirely', async () => {
    fetchMock.mockResolvedValue(errJson(500, {}));
    await expect(loginUser('a@b.com', 'x')).rejects.toThrow('Auth request failed with status 500');
  });
});

describe('registerUser', () => {
  it('returns response on success', async () => {
    fetchMock.mockResolvedValue(okJson(authResponse));
    const result = await registerUser('a@b.com', 'password123');
    expect(result).toEqual(authResponse);
  });

  it('throws on failure', async () => {
    fetchMock.mockResolvedValue(errJson(409, { detail: 'Email already registered' }));
    await expect(registerUser('a@b.com', 'password123')).rejects.toThrow('Email already registered');
  });
});

describe('refreshSession', () => {
  it('returns response on success', async () => {
    fetchMock.mockResolvedValue(okJson(authResponse));
    const result = await refreshSession();
    expect(result).toEqual(authResponse);
  });

  it('throws on failure', async () => {
    fetchMock.mockResolvedValue(errJson(401, { detail: 'Session expired' }));
    await expect(refreshSession()).rejects.toThrow('Session expired');
  });
});

describe('logoutSession', () => {
  it('resolves without value on success', async () => {
    fetchMock.mockResolvedValue(new Response('', { status: 200 }));
    await expect(logoutSession()).resolves.toBeUndefined();
  });

  it('throws on failure', async () => {
    fetchMock.mockResolvedValue(errJson(401, { detail: 'Not authenticated' }));
    await expect(logoutSession()).rejects.toThrow('Not authenticated');
  });
});

describe('fetchCurrentUser', () => {
  it('returns user on success', async () => {
    const user = { id: '1', email: 'a@b.com', roles: ['CityPlanner'] };
    fetchMock.mockResolvedValue(okJson(user));
    const result = await fetchCurrentUser('my-token');
    expect(result).toEqual(user);
  });

  it('throws on failure', async () => {
    fetchMock.mockResolvedValue(errJson(401, { detail: 'Unauthorized' }));
    await expect(fetchCurrentUser('bad-token')).rejects.toThrow('Unauthorized');
  });
});

describe('refreshStoredSession', () => {
  it('throws when no session stored', async () => {
    await expect(refreshStoredSession()).rejects.toThrow('No local access session available');
  });

  it('saves refreshed session and returns it', async () => {
    const stored = { accessToken: 'old-tok', user: { id: '1', email: 'a@b.com', roles: [] } };
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));

    const refreshed = { accessToken: 'new-tok', user: { id: '1', email: 'a@b.com', roles: [] } };
    fetchMock.mockResolvedValue(okJson(refreshed));

    const result = await refreshStoredSession();
    expect(result.accessToken).toBe('new-tok');
    const saved = JSON.parse(window.localStorage.getItem(STORAGE_KEY)!);
    expect(saved.accessToken).toBe('new-tok');
  });

  it('clears session and re-throws when refresh fails', async () => {
    const stored = { accessToken: 'old-tok', user: { id: '1', email: 'a@b.com', roles: [] } };
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));

    fetchMock.mockResolvedValue(errJson(401, { detail: 'Expired' }));
    await expect(refreshStoredSession()).rejects.toThrow('Expired');
    expect(window.localStorage.getItem(STORAGE_KEY)).toBeNull();
  });
});
