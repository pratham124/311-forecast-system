import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
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

vi.mock('./pages/FeedbackSubmissionPage', () => ({
  FeedbackSubmissionPage: ({ isAuthenticated }: { isAuthenticated: boolean }) => (
    <div>Feedback submission route content {isAuthenticated ? 'authenticated' : 'anonymous'}</div>
  ),
}));

vi.mock('./pages/FeedbackReviewPage', () => ({
  FeedbackReviewPage: ({ roles }: { roles: string[] }) => <div>Feedback review route content for {roles.join(', ')}</div>,
}));

vi.mock('./pages/AlertReviewPage', () => ({
  AlertReviewPage: ({ roles }: { roles: string[] }) => <div>Alert review route content for {roles.join(', ')}</div>,
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

beforeEach(() => {
  authMocks.fetchCurrentUser.mockRejectedValue(new Error('No session'));
  authMocks.refreshStoredSession.mockRejectedValue(new Error('No refresh session'));
  authMocks.logoutSession.mockResolvedValue(undefined);
});

afterEach(() => {
  cleanup();
  window.localStorage.clear();
  vi.clearAllMocks();
});

describe('App feedback routes', () => {
  it('opens the feedback submission route from the entry page for anonymous users', async () => {
    const user = userEvent.setup();

    renderApp(['/']);
    await screen.findByRole('heading', { name: /sign in to view internal forecasts/i });
    await user.click(screen.getByRole('button', { name: /report an issue/i }));

    expect(await screen.findByText(/feedback submission route content anonymous/i)).toBeInTheDocument();
  });

  it('renders authenticated feedback routes', async () => {
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

    renderApp(['/feedback']);

    expect(await screen.findByText(/feedback submission route content authenticated/i)).toBeInTheDocument();
  });

  it('renders the feedback inbox route for authenticated reviewers', async () => {
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

    renderApp(['/app/feedback-review']);

    expect(await screen.findByText(/feedback review route content for CityPlanner/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /feedback inbox/i })).toBeInTheDocument();
  });

  it('renders the user guide route for authenticated users', async () => {
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

    renderApp(['/app/user-guide']);

    expect(await screen.findByText(/user guide route content/i)).toBeInTheDocument();
  });

  it('renders the alert review route for authorized users', async () => {
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

    renderApp(['/app/alerts']);

    expect(await screen.findByText(/alert review route content for CityPlanner/i)).toBeInTheDocument();
  });
});
