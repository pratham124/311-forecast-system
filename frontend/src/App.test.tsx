import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
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
  ForecastVisualizationPage: () => <div>Internal forecast dashboard</div>,
}));

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
    render(<App />);
    expect(await screen.findByRole('heading', { name: /sign in to view internal forecasts/i })).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: /^sign in$/i })).toHaveLength(2);
    expect(screen.getByRole('button', { name: /view as guest/i })).toBeInTheDocument();
  });

  it('signs in and opens the internal dashboard', async () => {
    const user = userEvent.setup();
    authMocks.loginUser.mockResolvedValue({
      accessToken: 'token-1',
      tokenType: 'bearer',
      user: { userAccountId: 'user-1', email: 'planner@example.com', roles: ['CityPlanner'] },
    });

    render(<App />);
    await screen.findByRole('heading', { name: /sign in to view internal forecasts/i });
    await user.type(screen.getByPlaceholderText(/you@example.com/i), 'planner@example.com');
    await user.type(screen.getByPlaceholderText(/minimum 8 characters/i), 'super-secret-password');
    await user.click(screen.getAllByRole('button', { name: /^sign in$/i })[1]);

    await waitFor(() => {
      expect(authMocks.loginUser).toHaveBeenCalledWith('planner@example.com', 'super-secret-password');
    });
    expect(screen.getByText(/internal forecast dashboard/i)).toBeInTheDocument();
    expect(screen.getByText(/planner@example.com/i)).toBeInTheDocument();
  });

  it('shows a user-friendly validation error for short passwords', async () => {
    const user = userEvent.setup();
    authMocks.loginUser.mockRejectedValue(new Error('Password must be at least 8 characters.'));

    render(<App />);
    await screen.findByRole('heading', { name: /sign in to view internal forecasts/i });
    await user.type(screen.getByPlaceholderText(/you@example.com/i), 'planner@example.com');
    await user.type(screen.getByPlaceholderText(/minimum 8 characters/i), 'short');
    await user.click(screen.getAllByRole('button', { name: /^sign in$/i })[1]);

    expect(await screen.findByText(/password must be at least 8 characters\./i)).toBeInTheDocument();
  });

  it('clears the form when switching between sign in and register', async () => {
    const user = userEvent.setup();

    render(<App />);
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

    render(<App />);
    await screen.findByRole('heading', { name: /sign in to view internal forecasts/i });
    await user.click(screen.getByRole('button', { name: /^register$/i }));
    await user.type(screen.getByPlaceholderText(/you@example.com/i), 'manager@example.com');
    await user.type(screen.getByPlaceholderText(/minimum 8 characters/i), 'super-secret-password');
    await user.click(screen.getAllByRole('button', { name: /^register$/i })[1]);

    await waitFor(() => {
      expect(authMocks.registerUser).toHaveBeenCalledWith('manager@example.com', 'super-secret-password');
    });
    expect(screen.getByText(/manager@example.com/i)).toBeInTheDocument();
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

    render(<App />);

    await waitFor(() => {
      expect(authMocks.refreshStoredSession).toHaveBeenCalled();
    });
    expect(screen.getByText(/internal forecast dashboard/i)).toBeInTheDocument();
  });

  it('opens the empty guest placeholder and can return', async () => {
    const user = userEvent.setup();
    render(<App />);
    await screen.findByRole('heading', { name: /sign in to view internal forecasts/i });

    await user.click(screen.getByRole('button', { name: /view as guest/i }));
    expect(screen.getByLabelText(/guest placeholder page/i)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /back/i }));
    expect(screen.getByRole('button', { name: /view as guest/i })).toBeInTheDocument();
  });
});
