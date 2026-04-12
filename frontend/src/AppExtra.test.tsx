import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import App from './App';

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

vi.mock('./pages/DemandComparisonPage', () => ({
  DemandComparisonPage: () => <div>Demand comparison route content</div>,
}));

vi.mock('./pages/HistoricalDemandPage', () => ({
  HistoricalDemandPage: () => <div>Historical route content</div>,
}));

vi.mock('./pages/PublicForecastPage', () => ({
  PublicForecastPage: () => <div>Public forecast route content</div>,
}));

vi.mock('./pages/ForecastAccuracyPage', () => ({
  ForecastAccuracyPage: () => <div>Forecast accuracy route content</div>,
}));

vi.mock('./pages/UserGuideHostPage', () => ({
  UserGuideHostPage: () => <div>User guide route content</div>,
}));

function renderApp(initialEntries: string[]) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <App />
    </MemoryRouter>,
  );
}

describe('App extra coverage', () => {
  beforeEach(() => {
    authMocks.fetchCurrentUser.mockRejectedValue(new Error('expired'));
    authMocks.refreshStoredSession.mockRejectedValue(new Error('refresh failed'));
    authMocks.logoutSession.mockResolvedValue(undefined);
  });

  afterEach(() => {
    cleanup();
    window.localStorage.clear();
    vi.clearAllMocks();
  });

  it('clears local state when bootstrap refresh fails', async () => {
    window.localStorage.setItem(
      'forecast-system-auth-session',
      JSON.stringify({
        accessToken: 'stale-token',
        user: { userAccountId: 'user-1', email: 'planner@example.com', roles: ['CityPlanner'] },
      }),
    );

    renderApp(['/app/forecasts']);

    expect(await screen.findByRole('heading', { name: /sign in to view internal forecasts/i })).toBeInTheDocument();
    expect(window.localStorage.getItem('forecast-system-auth-session')).toBeNull();
  });

  it('loads guest, accuracy, and user guide routes', async () => {
    window.localStorage.setItem(
      'forecast-system-auth-session',
      JSON.stringify({
        accessToken: 'token-1',
        user: { userAccountId: 'user-1', email: 'planner@example.com', roles: ['CityPlanner'] },
      }),
    );
    authMocks.fetchCurrentUser.mockResolvedValue({
      userAccountId: 'user-1',
      email: 'planner@example.com',
      roles: ['CityPlanner'],
    });

    const guestView = renderApp(['/guest']);
    expect(await screen.findByText(/public forecast route content/i)).toBeInTheDocument();
    guestView.unmount();

    const accuracyView = renderApp(['/app/forecast-accuracy']);
    expect(await screen.findByText(/forecast accuracy route content/i)).toBeInTheDocument();
    accuracyView.unmount();

    renderApp(['/app/user-guide']);
    expect(await screen.findByText(/user guide route content/i)).toBeInTheDocument();
  });

  it('logs out from the internal layout', async () => {
    const user = userEvent.setup();
    window.localStorage.setItem(
      'forecast-system-auth-session',
      JSON.stringify({
        accessToken: 'token-2',
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

    await user.click(screen.getByRole('button', { name: /log out/i }));

    await waitFor(() => {
      expect(authMocks.logoutSession).toHaveBeenCalledTimes(1);
    });
    expect(await screen.findByRole('heading', { name: /sign in to view internal forecasts/i })).toBeInTheDocument();
  });

  it('shows fallback user badge details when email and roles are empty', async () => {
    window.localStorage.setItem(
      'forecast-system-auth-session',
      JSON.stringify({
        accessToken: 'token-3',
        user: { userAccountId: 'user-3', email: '', roles: [] },
      }),
    );
    authMocks.fetchCurrentUser.mockResolvedValue({
      userAccountId: 'user-3',
      email: '',
      roles: [],
    });

    renderApp(['/app/forecasts']);

    expect(await screen.findByText('Forecast route content')).toBeInTheDocument();
    expect(screen.getByText('?')).toBeInTheDocument();
    expect(screen.getByText('User')).toBeInTheDocument();
  });
});
