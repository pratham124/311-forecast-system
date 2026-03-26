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
    expect(screen.getByText(/forecast route content/i)).toBeInTheDocument();
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
});
