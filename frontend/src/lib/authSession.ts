import type { AuthSession } from '../types/auth';

const STORAGE_KEY = 'forecast-system-auth-session';

export function getStoredAuthSession(): AuthSession | null {
  if (typeof window === 'undefined') return null;
  const rawValue = window.localStorage.getItem(STORAGE_KEY);
  if (!rawValue) return null;
  try {
    return JSON.parse(rawValue) as AuthSession;
  } catch {
    window.localStorage.removeItem(STORAGE_KEY);
    return null;
  }
}

export function saveAuthSession(session: AuthSession): void {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}

export function clearAuthSession(): void {
  if (typeof window === 'undefined') return;
  window.localStorage.removeItem(STORAGE_KEY);
}

export function getAccessToken(): string | null {
  return getStoredAuthSession()?.accessToken ?? null;
}
