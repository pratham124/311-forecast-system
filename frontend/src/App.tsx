import { lazy, Suspense, useEffect, useState } from 'react';
import { NavLink, Navigate, Outlet, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { fetchCurrentUser, loginUser, logoutSession, refreshStoredSession, registerUser } from './api/auth';
import { clearAuthSession, getStoredAuthSession, saveAuthSession } from './lib/authSession';
import type { AuthSession } from './types/auth';

type AuthMode = 'login' | 'register';

const EntryPage = lazy(async () => {
  const module = await import('./pages/EntryPage');
  return { default: module.EntryPage };
});
const EvaluationPage = lazy(async () => {
  const module = await import('./pages/EvaluationPage');
  return { default: module.EvaluationPage };
});
const ForecastVisualizationPage = lazy(async () => {
  const module = await import('./pages/ForecastVisualizationPage');
  return { default: module.ForecastVisualizationPage };
});
const DemandComparisonPage = lazy(async () => {
  const module = await import('./pages/DemandComparisonPage');
  return { default: module.DemandComparisonPage };
});
const HistoricalDemandPage = lazy(async () => {
  const module = await import('./pages/HistoricalDemandPage');
  return { default: module.HistoricalDemandPage };
});
const IngestionPage = lazy(async () => {
  const module = await import('./pages/IngestionPage');
  return { default: module.IngestionPage };
});
const GuestPlaceholderPage = lazy(async () => {
  const module = await import('./pages/GuestPlaceholderPage');
  return { default: module.GuestPlaceholderPage };
});

function RouteFallback() {
  return <main className="flex min-h-[40vh] items-center justify-center text-sm font-medium text-muted">Loading page...</main>;
}

function canReadInternalOperations(roles: string[]): boolean {
  return roles.some((role) => role === 'CityPlanner' || role === 'OperationalManager');
}

function InternalLayout({ session, onLogout }: { session: AuthSession; onLogout: () => Promise<void> }) {
  const showEvaluationPage = canReadInternalOperations(session.user.roles);
  const showIngestionPage = canReadInternalOperations(session.user.roles);

  return (
    <div className="min-h-screen bg-[#f3f4f5]">
      <header className="border-b border-slate-200 bg-white/95 px-4 py-3 backdrop-blur sm:px-6 lg:px-8">
        <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-accent">Signed in</p>
              <p className="text-sm text-ink">{session.user.email} · {session.user.roles.join(', ')}</p>
            </div>
            <nav className="flex items-center gap-2 pl-2" aria-label="internal navigation">
              <NavLink
                to="/app/forecasts"
                className={({ isActive }) => `inline-flex min-h-10 items-center justify-center rounded-2xl px-4 text-sm font-semibold transition ${isActive ? 'bg-accent text-white' : 'border border-slate-300 bg-white text-ink hover:border-accent hover:text-accent'}`}
              >
                Forecasts
              </NavLink>
              <NavLink
                to="/app/demand-comparisons"
                className={({ isActive }) => `inline-flex min-h-10 items-center justify-center rounded-2xl px-4 text-sm font-semibold transition ${isActive ? 'bg-accent text-white' : 'border border-slate-300 bg-white text-ink hover:border-accent hover:text-accent'}`}
              >
                Comparisons
              </NavLink>
              <NavLink
                to="/app/historical-demand"
                className={({ isActive }) => `inline-flex min-h-10 items-center justify-center rounded-2xl px-4 text-sm font-semibold transition ${isActive ? 'bg-accent text-white' : 'border border-slate-300 bg-white text-ink hover:border-accent hover:text-accent'}`}
              >
                Historical
              </NavLink>
              {showEvaluationPage ? (
                <NavLink
                  to="/app/evaluations"
                  className={({ isActive }) => `inline-flex min-h-10 items-center justify-center rounded-2xl px-4 text-sm font-semibold transition ${isActive ? 'bg-accent text-white' : 'border border-slate-300 bg-white text-ink hover:border-accent hover:text-accent'}`}
                >
                  Evaluations
                </NavLink>
              ) : null}
              {showIngestionPage ? (
                <NavLink
                  to="/app/ingestion"
                  className={({ isActive }) => `inline-flex min-h-10 items-center justify-center rounded-2xl px-4 text-sm font-semibold transition ${isActive ? 'bg-accent text-white' : 'border border-slate-300 bg-white text-ink hover:border-accent hover:text-accent'}`}
                >
                  Ingestion
                </NavLink>
              ) : null}
            </nav>
          </div>
          <button
            type="button"
            onClick={() => {
              void onLogout();
            }}
            className="inline-flex min-h-10 items-center justify-center rounded-2xl border border-slate-300 bg-white px-4 text-sm font-semibold text-ink transition hover:border-accent hover:text-accent"
          >
            Log out
          </button>
        </div>
      </header>
      <Outlet />
    </div>
  );
}

function AppShell() {
  const [session, setSession] = useState<AuthSession | null>(() => getStoredAuthSession());
  const [isBootstrappingSession, setIsBootstrappingSession] = useState(Boolean(getStoredAuthSession()));
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (session && location.pathname === '/') {
      navigate('/app/forecasts', { replace: true });
    }
  }, [location.pathname, navigate, session]);

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
      })
      .catch(async () => {
        if (cancelled) return;
        try {
          const nextSession = await refreshStoredSession();
          if (cancelled) return;
          setSession(nextSession);
        } catch {
          if (cancelled) return;
          clearAuthSession();
          setSession(null);
          navigate('/', { replace: true });
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
  }, [navigate]);

  const handleAuthenticate = async (mode: AuthMode, email: string, password: string) => {
    setIsSubmitting(true);
    setAuthError(null);
    try {
      const response = mode === 'login' ? await loginUser(email, password) : await registerUser(email, password);
      const nextSession = { accessToken: response.accessToken, user: response.user };
      saveAuthSession(nextSession);
      setSession(nextSession);
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
    navigate('/', { replace: true });
  };

  if (isBootstrappingSession) {
    return <main className="flex min-h-screen items-center justify-center text-sm font-medium text-muted">Checking your session...</main>;
  }

  const showEvaluationPage = session ? canReadInternalOperations(session.user.roles) : false;
  const showIngestionPage = session ? canReadInternalOperations(session.user.roles) : false;

  return (
    <Suspense fallback={<RouteFallback />}>
      <Routes>
        <Route
          path="/"
          element={session ? <Navigate to="/app/forecasts" replace /> : <EntryPage onAuthenticate={handleAuthenticate} onGuestView={() => navigate('/guest')} onModeChange={() => setAuthError(null)} isSubmitting={isSubmitting} errorMessage={authError} />}
        />
        <Route path="/guest" element={<GuestPlaceholderPage onBack={() => navigate('/')} />} />
        <Route path="/app" element={session ? <InternalLayout session={session} onLogout={handleLogout} /> : <Navigate to="/" replace />}>
          <Route index element={<Navigate to="forecasts" replace />} />
          <Route path="forecasts" element={<ForecastVisualizationPage />} />
          <Route path="demand-comparisons" element={<DemandComparisonPage />} />
          <Route path="historical-demand" element={<HistoricalDemandPage />} />
          <Route
            path="evaluations"
            element={showEvaluationPage ? <EvaluationPage roles={session!.user.roles} /> : <Navigate to="/app/forecasts" replace />}
          />
          <Route
            path="ingestion"
            element={showIngestionPage ? <IngestionPage roles={session!.user.roles} /> : <Navigate to="/app/forecasts" replace />}
          />
        </Route>
        <Route path="*" element={<Navigate to={session ? '/app/forecasts' : '/'} replace />} />
      </Routes>
    </Suspense>
  );
}

export default function App() {
  return <AppShell />;
}
