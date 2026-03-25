import { Suspense, lazy, useEffect, useState } from 'react';
import { fetchCurrentUser, loginUser, logoutSession, refreshStoredSession, registerUser } from './api/auth';
import { clearAuthSession, getStoredAuthSession, saveAuthSession } from './lib/authSession';
import { EntryPage } from './pages/EntryPage';
import { GuestPlaceholderPage } from './pages/GuestPlaceholderPage';
import type { AuthSession } from './types/auth';

const ForecastVisualizationPage = lazy(async () => {
  const module = await import('./pages/ForecastVisualizationPage');
  return { default: module.ForecastVisualizationPage };
});

type AppView = 'entry' | 'internal' | 'guest';
type AuthMode = 'login' | 'register';

export default function App() {
  const [session, setSession] = useState<AuthSession | null>(() => getStoredAuthSession());
  const [view, setView] = useState<AppView>(() => (getStoredAuthSession() ? 'internal' : 'entry'));
  const [isBootstrappingSession, setIsBootstrappingSession] = useState(Boolean(getStoredAuthSession()));
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  useEffect(() => {
    const stored = getStoredAuthSession();
    if (!stored) {
      setIsBootstrappingSession(false);
      return;
    }
    let cancelled = false;
    fetchCurrentUser(stored.accessToken)
      .then((user) => {
        if (cancelled) return;
        const nextSession = { accessToken: stored.accessToken, user };
        saveAuthSession(nextSession);
        setSession(nextSession);
        setView('internal');
      })
      .catch(async () => {
        if (cancelled) return;
        try {
          const nextSession = await refreshStoredSession();
          if (cancelled) return;
          setSession(nextSession);
          setView('internal');
        } catch {
          if (cancelled) return;
          clearAuthSession();
          setSession(null);
          setView('entry');
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsBootstrappingSession(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleAuthenticate = async (mode: AuthMode, email: string, password: string) => {
    setIsSubmitting(true);
    setAuthError(null);
    try {
      const response = mode === 'login' ? await loginUser(email, password) : await registerUser(email, password);
      const nextSession = { accessToken: response.accessToken, user: response.user };
      saveAuthSession(nextSession);
      setSession(nextSession);
      setView('internal');
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : 'Authentication failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logoutSession();
    } catch {
      // Preserve local logout even if the server-side revoke call fails.
    }
    clearAuthSession();
    setSession(null);
    setAuthError(null);
    setView('entry');
  };

  if (isBootstrappingSession) {
    return <main className="flex min-h-screen items-center justify-center text-sm font-medium text-muted">Checking your session...</main>;
  }

  if (view === 'internal' && session) {
    return (
      <div className="min-h-screen bg-[#f3f4f5]">
        <header className="border-b border-slate-200 bg-white/95 px-4 py-3 backdrop-blur sm:px-6 lg:px-8">
          <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-accent">Signed in</p>
              <p className="text-sm text-ink">{session.user.email} · {session.user.roles.join(', ')}</p>
            </div>
            <button
              type="button"
              onClick={() => {
                void handleLogout();
              }}
              className="inline-flex min-h-10 items-center justify-center rounded-2xl border border-slate-300 bg-white px-4 text-sm font-semibold text-ink transition hover:border-accent hover:text-accent"
            >
              Log out
            </button>
          </div>
        </header>
        <Suspense fallback={<main className="flex min-h-[40vh] items-center justify-center text-sm font-medium text-muted">Loading your dashboard...</main>}>
          <ForecastVisualizationPage />
        </Suspense>
      </div>
    );
  }

  if (view === 'guest') {
    return <GuestPlaceholderPage onBack={() => setView('entry')} />;
  }

  return <EntryPage onAuthenticate={handleAuthenticate} onGuestView={() => setView('guest')} isSubmitting={isSubmitting} errorMessage={authError} />;
}
