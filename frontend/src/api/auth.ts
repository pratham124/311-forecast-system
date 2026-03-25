import { env } from '../config/env';
import { clearAuthSession, getStoredAuthSession, saveAuthSession } from '../lib/authSession';
import type { AuthResponse, AuthenticatedUser, AuthSession } from '../types/auth';

type ValidationDetail = {
  loc?: Array<string | number>;
  msg?: string;
  type?: string;
};

type ErrorBody = {
  detail?: string | ValidationDetail[];
};

function formatValidationMessage(detail: ValidationDetail): string | null {
  const field = typeof detail.loc?.[detail.loc.length - 1] === 'string' ? String(detail.loc?.[detail.loc.length - 1]) : null;

  if (field === 'password' && detail.type === 'string_too_short') {
    return 'Password must be at least 8 characters.';
  }
  if (field === 'password' && detail.msg) {
    return `Password: ${detail.msg}`;
  }
  if (field === 'email' && detail.msg) {
    return `Email: ${detail.msg}`;
  }
  if (detail.msg) {
    return detail.msg.charAt(0).toUpperCase() + detail.msg.slice(1);
  }
  return null;
}

async function parseError(response: Response): Promise<Error> {
  try {
    const body = (await response.json()) as ErrorBody;
    if (typeof body.detail === 'string') {
      return new Error(body.detail);
    }
    if (Array.isArray(body.detail) && body.detail.length > 0) {
      const messages = body.detail.map(formatValidationMessage).filter((message): message is string => Boolean(message));
      if (messages.length > 0) {
        return new Error(messages.join(' '));
      }
      return new Error('Please check your details and try again.');
    }
    return new Error(`Auth request failed with status ${response.status}`);
  } catch {
    return new Error(`Auth request failed with status ${response.status}`);
  }
}

export async function loginUser(email: string, password: string): Promise<AuthResponse> {
  const response = await fetch(`${env.apiBaseUrl}/api/v1/auth/login`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) throw await parseError(response);
  return response.json() as Promise<AuthResponse>;
}

export async function registerUser(email: string, password: string): Promise<AuthResponse> {
  const response = await fetch(`${env.apiBaseUrl}/api/v1/auth/register`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) throw await parseError(response);
  return response.json() as Promise<AuthResponse>;
}

export async function refreshSession(): Promise<AuthResponse> {
  const response = await fetch(`${env.apiBaseUrl}/api/v1/auth/refresh`, {
    method: 'POST',
    credentials: 'include',
  });
  if (!response.ok) throw await parseError(response);
  return response.json() as Promise<AuthResponse>;
}

export async function logoutSession(): Promise<void> {
  const response = await fetch(`${env.apiBaseUrl}/api/v1/auth/logout`, {
    method: 'POST',
    credentials: 'include',
  });
  if (!response.ok) throw await parseError(response);
}

export async function fetchCurrentUser(accessToken: string): Promise<AuthenticatedUser> {
  const response = await fetch(`${env.apiBaseUrl}/api/v1/auth/me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!response.ok) throw await parseError(response);
  return response.json() as Promise<AuthenticatedUser>;
}

export async function refreshStoredSession(): Promise<AuthSession> {
  const stored = getStoredAuthSession();
  if (!stored) {
    throw new Error('No local access session available');
  }
  try {
    const refreshed = await refreshSession();
    const nextSession = {
      accessToken: refreshed.accessToken,
      user: refreshed.user,
    } satisfies AuthSession;
    saveAuthSession(nextSession);
    return nextSession;
  } catch (error) {
    clearAuthSession();
    throw error;
  }
}
