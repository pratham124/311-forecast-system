import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import App from './App';

const STORAGE_KEY = 'forecast-system-auth-session';

const authMocks = vi.hoisted(() => ({
  loginUser: vi.fn(),
  registerUser: vi.fn(),
  fetchCurrentUser: vi.fn(),
  refreshStoredSession: vi.fn(),
  logoutSession: vi.fn(),
}));

vi.mock('./api/auth', () => ({
  loginUser: authMocks.loginUser,
  registerUser: authMocks.registerUser,
  fetchCurrentUser: authMocks.fetchCurrentUser,
  refreshStoredSession: authMocks.refreshStoredSession,
  logoutSession: authMocks.logoutSession,
}));

vi.mock('./pages/ForecastVisualizationPage', () => ({
  ForecastVisualizationPage: () => <div>Forecast route content</div>,
}));

vi.mock('./pages/EvaluationPage', () => ({
  EvaluationPage: ({ roles }: { roles: string[] }) => <div>Evaluation route content for {roles.join(', ')}</div>,
}));

vi.mock('./pages/IngestionPage', () => ({
  IngestionPage: ({ roles }: { roles: string[] }) => <div>Ingestion route content for {roles.join(', ')}</div>,
}));

vi.mock('./pages/DemandComparisonPage', () => ({
  DemandComparisonPage: () => <div>Demand comparison route content</div>,
}));

vi.mock('./pages/HistoricalDemandPage', () => ({
  HistoricalDemandPage: () => <div>Historical demand route content</div>,
}));

function renderApp(initialEntries: string[] = ['/']) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <App />
    </MemoryRouter>,
  );
}

afterEach(() => {
  cleanup();
  window.localStorage.clear();
  vi.clearAllMocks();
});

beforeEach(() => {
  authMocks.fetchCurrentUser.mockRejectedValue(new Error('No session'));
  authMocks.refreshStoredSession.mockRejectedValue(new Error('No refresh session'));
  authMocks.logoutSession.mockResolvedValue(undefined);
});

describe('App', () => {
  it('shows the auth shell by default', async () => {
    renderApp();
    expect(await screen.findByRole('heading', { name: /sign in to view internal forecasts/i })).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: /^sign in$/i })).toHaveLength(2);
    expect(screen.getByRole('button', { name: /view as guest/i })).toBeInTheDocument();
  });

  it('signs in and opens the internal dashboard route', async () => {
    const user = userEvent.setup();
    authMocks.loginUser.mockResolvedValue({
      accessToken: 'token-1',
      tokenType: 'bearer',
      user: { userAccountId: 'user-1', email: 'planner@example.com', roles: ['CityPlanner'] },
    });

    renderApp();
    await screen.findByRole('heading', { name: /sign in to view internal forecasts/i });
    await user.type(screen.getByPlaceholderText(/you@example.com/i), 'planner@example.com');
    await user.type(screen.getByPlaceholderText(/minimum 8 characters/i), 'super-secret-password');
    await user.click(screen.getAllByRole('button', { name: /^sign in$/i })[1]);

    await waitFor(() => {
      expect(authMocks.loginUser).toHaveBeenCalledWith('planner@example.com', 'super-secret-password');
    });
  });

  it('shows a user-friendly validation error for short passwords', async () => {
    const user = userEvent.setup();
    authMocks.loginUser.mockRejectedValue(new Error('Password must be at least 8 characters.'));

    renderApp();
    await screen.findByRole('heading', { name: /sign in to view internal forecasts/i });
    await user.type(screen.getByPlaceholderText(/you@example.com/i), 'planner@example.com');
    await user.type(screen.getByPlaceholderText(/minimum 8 characters/i), 'short');
    await user.click(screen.getAllByRole('button', { name: /^sign in$/i })[1]);

    expect(await screen.findByText(/password must be at least 8 characters\./i)).toBeInTheDocument();
  });

  it('shows generic authentication failure when auth throws a non-Error value', async () => {
    const user = userEvent.setup();
    authMocks.loginUser.mockRejectedValue('unexpected');

    renderApp();
    await screen.findByRole('heading', { name: /sign in to view internal forecasts/i });
    await user.type(screen.getByPlaceholderText(/you@example.com/i), 'planner@example.com');
    await user.type(screen.getByPlaceholderText(/minimum 8 characters/i), 'super-secret-password');
    await user.click(screen.getAllByRole('button', { name: /^sign in$/i })[1]);

    expect(await screen.findByText(/authentication failed/i)).toBeInTheDocument();
  });

  it('clears auth errors when switching between sign in and register', async () => {
    const user = userEvent.setup();
    authMocks.loginUser.mockRejectedValue(new Error('Password must be at least 8 characters.'));

    renderApp();
    await screen.findByRole('heading', { name: /sign in to view internal forecasts/i });
    await user.type(screen.getByPlaceholderText(/you@example.com/i), 'planner@example.com');
    await user.type(screen.getByPlaceholderText(/minimum 8 characters/i), 'short');
    await user.click(screen.getAllByRole('button', { name: /^sign in$/i })[1]);

    expect(await screen.findByText(/password must be at least 8 characters\./i)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /^register$/i }));

    expect(screen.queryByText(/password must be at least 8 characters\./i)).not.toBeInTheDocument();
  });

  it('clears the form when switching between sign in and register', async () => {
    const user = userEvent.setup();

    renderApp();
    await screen.findByRole('heading', { name: /sign in to view internal forecasts/i });

    const emailInput = screen.getByPlaceholderText(/you@example.com/i) as HTMLInputElement;
    const passwordInput = screen.getByPlaceholderText(/minimum 8 characters/i) as HTMLInputElement;

    await user.type(emailInput, 'planner@example.com');
    await user.type(passwordInput, 'super-secret-password');
    await user.click(screen.getByRole('button', { name: /^register$/i }));

    expect(emailInput.value).toBe('');
    expect(passwordInput.value).toBe('');

    await user.type(emailInput, 'manager@example.com');
    await user.type(passwordInput, 'another-secret-password');
    await user.click(screen.getAllByRole('button', { name: /^sign in$/i })[0]);

    expect(emailInput.value).toBe('');
    expect(passwordInput.value).toBe('');
  });

  it('registers an approved user and opens the internal dashboard', async () => {
    const user = userEvent.setup();
    authMocks.registerUser.mockResolvedValue({
      accessToken: 'token-2',
      tokenType: 'bearer',
      user: { userAccountId: 'user-2', email: 'manager@example.com', roles: ['OperationalManager'] },
    });

    renderApp();
    await screen.findByRole('heading', { name: /sign in to view internal forecasts/i });
    await user.click(screen.getByRole('button', { name: /^register$/i }));
    await user.type(screen.getByPlaceholderText(/you@example.com/i), 'manager@example.com');
    await user.type(screen.getByPlaceholderText(/minimum 8 characters/i), 'super-secret-password');
    await user.click(screen.getAllByRole('button', { name: /^register$/i })[1]);

    await waitFor(() => {
      expect(authMocks.registerUser).toHaveBeenCalledWith('manager@example.com', 'super-secret-password');
    });
  });

  it('restores the session through refresh when the access token is stale', async () => {
    window.localStorage.setItem(
      'forecast-system-auth-session',
      JSON.stringify({
        accessToken: 'expired-access',
        user: { userAccountId: 'user-3', email: 'planner@example.com', roles: ['CityPlanner'] },
      }),
    );
    authMocks.refreshStoredSession.mockResolvedValue({
      accessToken: 'fresh-access',
      user: { userAccountId: 'user-3', email: 'planner@example.com', roles: ['CityPlanner'] },
    });

    renderApp(['/app/forecasts']);

    await waitFor(() => {
      expect(authMocks.refreshStoredSession).toHaveBeenCalled();
    });
    expect(await screen.findByText(/forecast route content/i)).toBeInTheDocument();
  });

  it('ignores bootstrap user resolution after unmount', async () => {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        accessToken: 'stale-access',
        user: { userAccountId: 'user-cancel', email: 'planner@example.com', roles: ['CityPlanner'] },
      }),
    );

    let resolveUser: ((value: { userAccountId: string; email: string; roles: string[] }) => void) | undefined;
    authMocks.fetchCurrentUser.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveUser = resolve;
        }),
    );

    const view = renderApp(['/app/forecasts']);
    view.unmount();

    resolveUser?.({ userAccountId: 'user-cancel', email: 'planner@example.com', roles: ['CityPlanner'] });
    await waitFor(() => {
      expect(authMocks.fetchCurrentUser).toHaveBeenCalledTimes(1);
    });
    expect(authMocks.refreshStoredSession).not.toHaveBeenCalled();
  });

  it('ignores bootstrap user rejection after unmount', async () => {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        accessToken: 'stale-access',
        user: { userAccountId: 'user-cancel-reject', email: 'planner@example.com', roles: ['CityPlanner'] },
      }),
    );

    let rejectUser: ((reason?: unknown) => void) | undefined;
    authMocks.fetchCurrentUser.mockImplementation(
      () =>
        new Promise((_resolve, reject) => {
          rejectUser = reject;
        }),
    );

    const view = renderApp(['/app/forecasts']);
    view.unmount();

    rejectUser?.(new Error('expired'));
    await waitFor(() => {
      expect(authMocks.fetchCurrentUser).toHaveBeenCalledTimes(1);
    });
    expect(authMocks.refreshStoredSession).not.toHaveBeenCalled();
  });

  it('ignores refresh resolution after unmount during bootstrap fallback', async () => {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        accessToken: 'stale-access',
        user: { userAccountId: 'user-refresh', email: 'planner@example.com', roles: ['CityPlanner'] },
      }),
    );

    let resolveRefresh: ((value: {
      accessToken: string;
      user: { userAccountId: string; email: string; roles: string[] };
    }) => void) | undefined;
    authMocks.fetchCurrentUser.mockRejectedValue(new Error('expired'));
    authMocks.refreshStoredSession.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveRefresh = resolve;
        }),
    );

    const view = renderApp(['/app/forecasts']);
    await waitFor(() => {
      expect(authMocks.refreshStoredSession).toHaveBeenCalledTimes(1);
    });

    view.unmount();
    resolveRefresh?.({
      accessToken: 'fresh-access',
      user: { userAccountId: 'user-refresh', email: 'planner@example.com', roles: ['CityPlanner'] },
    });

    await waitFor(() => {
      expect(authMocks.refreshStoredSession).toHaveBeenCalledTimes(1);
    });
    const stored = window.localStorage.getItem(STORAGE_KEY);
    expect(stored).toContain('stale-access');
  });

  it('ignores refresh failure after unmount during bootstrap fallback', async () => {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        accessToken: 'stale-access',
        user: { userAccountId: 'user-refresh-fail', email: 'planner@example.com', roles: ['CityPlanner'] },
      }),
    );

    let rejectRefresh: ((reason?: unknown) => void) | undefined;
    authMocks.fetchCurrentUser.mockRejectedValue(new Error('expired'));
    authMocks.refreshStoredSession.mockImplementation(
      () =>
        new Promise((_resolve, reject) => {
          rejectRefresh = reject;
        }),
    );

    const view = renderApp(['/app/forecasts']);
    await waitFor(() => {
      expect(authMocks.refreshStoredSession).toHaveBeenCalledTimes(1);
    });

    view.unmount();
    rejectRefresh?.(new Error('offline'));

    await waitFor(() => {
      expect(authMocks.refreshStoredSession).toHaveBeenCalledTimes(1);
    });
    expect(window.localStorage.getItem(STORAGE_KEY)).toContain('stale-access');
  });

  it('lets a planner navigate to the evaluation route', async () => {
    const user = userEvent.setup();
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        accessToken: 'fresh-access',
        user: { userAccountId: 'user-1', email: 'planner@example.com', roles: ['CityPlanner'] },
      }),
    );
    authMocks.fetchCurrentUser.mockResolvedValue({
      userAccountId: 'user-1',
      email: 'planner@example.com',
      roles: ['CityPlanner'],
    });

    renderApp(['/app/forecasts']);

    await screen.findByText(/forecast route content/i);
    await user.click(screen.getByRole('link', { name: /evaluations/i }));
    expect(await screen.findByText(/evaluation route content for CityPlanner/i)).toBeInTheDocument();
  });

  it('opens demand-comparisons route for an authenticated session', async () => {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        accessToken: 'fresh-access',
        user: { userAccountId: 'user-1', email: 'planner@example.com', roles: ['CityPlanner'] },
      }),
    );
    authMocks.fetchCurrentUser.mockResolvedValue({
      userAccountId: 'user-1',
      email: 'planner@example.com',
      roles: ['CityPlanner'],
    });

    renderApp(['/app/demand-comparisons']);
    expect(await screen.findByText(/demand comparison route content/i)).toBeInTheDocument();
  });

  it('opens historical-demand route for an authenticated session', async () => {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        accessToken: 'fresh-access',
        user: { userAccountId: 'user-1', email: 'planner@example.com', roles: ['CityPlanner'] },
      }),
    );
    authMocks.fetchCurrentUser.mockResolvedValue({
      userAccountId: 'user-1',
      email: 'planner@example.com',
      roles: ['CityPlanner'],
    });

    renderApp(['/app/historical-demand']);
    expect(await screen.findByText(/historical demand route content/i)).toBeInTheDocument();
  });

  it('hides internal operation links for non-reader roles and redirects protected routes', async () => {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        accessToken: 'fresh-access',
        user: { userAccountId: 'user-9', email: 'viewer@example.com', roles: ['Viewer'] },
      }),
    );
    authMocks.fetchCurrentUser.mockResolvedValue({
      userAccountId: 'user-9',
      email: 'viewer@example.com',
      roles: ['Viewer'],
    });

    renderApp(['/app/forecasts']);
    await screen.findByText(/forecast route content/i);
    expect(screen.queryByRole('link', { name: /evaluations/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /ingestion/i })).not.toBeInTheDocument();

    cleanup();
    renderApp(['/app/evaluations']);
    expect(await screen.findByText(/forecast route content/i)).toBeInTheDocument();
  });


  it('lets an operational manager navigate to the ingestion route', async () => {
    const user = userEvent.setup();
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        accessToken: 'fresh-access',
        user: { userAccountId: 'user-2', email: 'manager@example.com', roles: ['OperationalManager'] },
      }),
    );
    authMocks.fetchCurrentUser.mockResolvedValue({
      userAccountId: 'user-2',
      email: 'manager@example.com',
      roles: ['OperationalManager'],
    });

    renderApp(['/app/forecasts']);

    await screen.findByText(/forecast route content/i);
    await user.click(screen.getByRole('link', { name: /ingestion/i }));
    expect(await screen.findByText(/ingestion route content for OperationalManager/i)).toBeInTheDocument();
  });

  it('opens the guest route and can return', async () => {
    const user = userEvent.setup();
    renderApp();
    await screen.findByRole('heading', { name: /sign in to view internal forecasts/i });

    await user.click(screen.getByRole('button', { name: /view as guest/i }));
    expect(await screen.findByLabelText(/guest placeholder page/i)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /back/i }));
    expect(await screen.findByRole('button', { name: /view as guest/i })).toBeInTheDocument();
  });

  it('redirects unauthorized app routes back to entry', async () => {
    renderApp(['/app/evaluations']);
    expect(await screen.findByRole('heading', { name: /sign in to view internal forecasts/i })).toBeInTheDocument();
  });

  it('logs out when the Log out button is clicked (covers lines 99-100 and 179-188)', async () => {
    const user = userEvent.setup();
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        accessToken: 'fresh-access',
        user: { userAccountId: 'user-1', email: 'planner@example.com', roles: ['CityPlanner'] },
      }),
    );
    authMocks.fetchCurrentUser.mockResolvedValue({
      userAccountId: 'user-1',
      email: 'planner@example.com',
      roles: ['CityPlanner'],
    });
    authMocks.logoutSession.mockResolvedValue(undefined);

    renderApp(['/app/forecasts']);
    await screen.findByText(/forecast route content/i);

    await user.click(screen.getByRole('button', { name: /log out/i }));

    expect(await screen.findByRole('heading', { name: /sign in to view internal forecasts/i })).toBeInTheDocument();
    expect(authMocks.logoutSession).toHaveBeenCalled();
  });

  it('handles logout even when logoutSession throws (catch branch in handleLogout)', async () => {
    const user = userEvent.setup();
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        accessToken: 'fresh-access',
        user: { userAccountId: 'user-1', email: 'planner@example.com', roles: ['CityPlanner'] },
      }),
    );
    authMocks.fetchCurrentUser.mockResolvedValue({
      userAccountId: 'user-1',
      email: 'planner@example.com',
      roles: ['CityPlanner'],
    });
    authMocks.logoutSession.mockRejectedValue(new Error('Network error'));

    renderApp(['/app/forecasts']);
    await screen.findByText(/forecast route content/i);

    await user.click(screen.getByRole('button', { name: /log out/i }));

    // Even if logoutSession throws, the user is still logged out locally
    expect(await screen.findByRole('heading', { name: /sign in to view internal forecasts/i })).toBeInTheDocument();
  });
});
