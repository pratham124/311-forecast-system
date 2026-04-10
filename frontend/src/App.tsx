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
const AlertReviewPage = lazy(async () => {
  const module = await import('./pages/AlertReviewPage');
  return { default: module.AlertReviewPage };
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
const ForecastAccuracyPage = lazy(async () => {
  const module = await import('./pages/ForecastAccuracyPage');
  return { default: module.ForecastAccuracyPage };
});
const IngestionPage = lazy(async () => {
  const module = await import('./pages/IngestionPage');
  return { default: module.IngestionPage };
});
const PublicForecastPage = lazy(async () => {
  const module = await import('./pages/PublicForecastPage');
  return { default: module.PublicForecastPage };
});
const UserGuideHostPage = lazy(async () => {
  const module = await import('./pages/UserGuideHostPage');
  return { default: module.UserGuideHostPage };
});

function RouteFallback() {
  return <main className="flex min-h-[40vh] items-center justify-center text-sm font-medium text-muted">Loading page...</main>;
}

function canReadInternalOperations(roles: string[]): boolean {
  return roles.some((role) => role === 'CityPlanner' || role === 'OperationalManager');
}

function NavItem({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `relative inline-flex items-center gap-1.5 rounded-lg px-3 py-2.5 text-[13px] font-semibold outline-none transition-colors duration-200 ${
          isActive
            ? 'text-accent after:absolute after:bottom-0 after:left-1 after:right-1 after:h-[2.5px] after:rounded-full after:bg-accent'
            : 'text-slate-500 hover:text-ink'
        }`
      }
    >
      {children}
    </NavLink>
  );
}

function InternalLayout({ session, onLogout }: { session: AuthSession; onLogout: () => Promise<void> }) {
  const showEvaluationPage = canReadInternalOperations(session.user.roles);
  const showIngestionPage = canReadInternalOperations(session.user.roles);
  const userInitial = (session.user.email[0] ?? '?').toUpperCase();
  const displayRole = session.user.roles[0]
    ?.replace(/([a-z])([A-Z])/g, '$1 $2') ?? 'User';

  return (
    <div className="min-h-screen bg-[#f3f4f5]">
      <header className="border-b border-slate-200/80 bg-white/90 backdrop-blur-lg">
        {/* Top bar — brand + user */}
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-2.5 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-accent text-xs font-black tracking-tight text-white shadow-sm">
              311
            </div>
            <span className="text-[15px] font-bold tracking-tight text-ink">
              Forecast<span className="font-normal text-slate-400">&nbsp;System</span>
            </span>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden items-center gap-2.5 sm:flex">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent/10 text-xs font-bold text-accent">
                {userInitial}
              </div>
              <div className="text-right">
                <p className="m-0 text-[13px] font-medium leading-tight text-ink">{session.user.email}</p>
                <p className="m-0 text-[11px] leading-tight text-slate-400">{displayRole}</p>
              </div>
            </div>
            <div className="h-5 w-px bg-slate-200 hidden sm:block" />
            <button
              type="button"
              onClick={() => {
                void onLogout();
              }}
              className="inline-flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-[13px] font-medium text-slate-500 outline-none transition-colors duration-200 hover:bg-slate-100 hover:text-ink"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
              </svg>
              Log out
            </button>
          </div>
        </div>

        {/* Navigation bar */}
        <div className="mx-auto w-full max-w-6xl px-4 sm:px-6 lg:px-8">
          <nav className="-mb-px flex items-center gap-0.5 overflow-x-auto" aria-label="internal navigation">
            <NavItem to="/app/forecasts">Forecasts</NavItem>
            <NavItem to="/app/demand-comparisons">Comparisons</NavItem>
            <NavItem to="/app/forecast-accuracy">Accuracy</NavItem>
            <NavItem to="/app/historical-demand">Historical</NavItem>
            {showEvaluationPage ? <NavItem to="/app/alerts">Alerts</NavItem> : null}
            {showEvaluationPage ? <NavItem to="/app/evaluations">Evaluations</NavItem> : null}
            {showIngestionPage ? <NavItem to="/app/ingestion">Ingestion</NavItem> : null}
            <NavItem to="/app/user-guide">
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z" />
              </svg>
              Help
            </NavItem>
          </nav>
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
        <Route path="/guest" element={<PublicForecastPage />} />
        <Route path="/app" element={session ? <InternalLayout session={session} onLogout={handleLogout} /> : <Navigate to="/" replace />}>
          <Route index element={<Navigate to="forecasts" replace />} />
          <Route path="forecasts" element={<ForecastVisualizationPage />} />
          <Route path="demand-comparisons" element={<DemandComparisonPage />} />
          <Route path="forecast-accuracy" element={<ForecastAccuracyPage />} />
          <Route path="historical-demand" element={<HistoricalDemandPage />} />
          <Route
            path="alerts"
            element={showEvaluationPage ? <AlertReviewPage roles={session!.user.roles} /> : <Navigate to="/app/forecasts" replace />}
          />
          <Route
            path="evaluations"
            element={showEvaluationPage ? <EvaluationPage roles={session!.user.roles} /> : <Navigate to="/app/forecasts" replace />}
          />
          <Route
            path="ingestion"
            element={showIngestionPage ? <IngestionPage roles={session!.user.roles} /> : <Navigate to="/app/forecasts" replace />}
          />
          <Route path="user-guide" element={<UserGuideHostPage />} />
        </Route>
        <Route path="*" element={<Navigate to={session ? '/app/forecasts' : '/'} replace />} />
      </Routes>
    </Suspense>
  );
}

export default function App() {
  return <AppShell />;
}
