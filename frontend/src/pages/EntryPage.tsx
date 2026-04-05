import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';

type AuthMode = 'login' | 'register';

type EntryPageProps = {
  onAuthenticate: (mode: AuthMode, email: string, password: string) => Promise<void>;
  onGuestView: () => void;
  onModeChange?: () => void;
  isSubmitting: boolean;
  errorMessage: string | null;
};

export function EntryPage({ onAuthenticate, onGuestView, onModeChange, isSubmitting, errorMessage }: EntryPageProps) {
  const [mode, setMode] = useState<AuthMode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const submitLabel = mode === 'login' ? 'Sign in' : 'Register';

  const handleModeChange = (nextMode: AuthMode) => {
    setMode(nextMode);
    setEmail('');
    setPassword('');
    onModeChange?.();
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await onAuthenticate(mode, email, password);
  };

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.96),_rgba(230,242,250,0.92)_38%,_rgba(203,225,241,0.8)_100%)] px-4 py-10 sm:px-6 lg:px-8">
      <div className="mx-auto grid min-h-[calc(100vh-5rem)] w-full max-w-6xl items-center gap-8 lg:grid-cols-[1.15fr_0.85fr]">
        <section className="space-y-6">
          <p className="text-xs uppercase tracking-[0.24em] text-accent">311 Forecast System</p>
          <h1 className="max-w-3xl text-5xl font-semibold leading-[0.92] text-ink sm:text-6xl">
            Sign in to view internal forecasts, or continue to the public forecast.
          </h1>
          <p className="max-w-2xl text-base leading-7 text-muted sm:text-lg">
            Use your approved email to sign in. If your email has already been approved, you can create your account here.
          </p>
        </section>

        <Card className="rounded-[30px] border-white/70 bg-white/90 shadow-[0_24px_80px_rgba(0,80,135,0.16)] backdrop-blur">
          <CardHeader className="space-y-3 pb-3">
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => handleModeChange('login')}
                className={`rounded-full px-4 py-2 text-sm font-semibold transition ${mode === 'login' ? 'bg-ink text-white' : 'bg-[#dce9f2] text-ink'}`}
              >
                Sign in
              </button>
              <button
                type="button"
                onClick={() => handleModeChange('register')}
                className={`rounded-full px-4 py-2 text-sm font-semibold transition ${mode === 'register' ? 'bg-ink text-white' : 'bg-[#dce9f2] text-ink'}`}
              >
                Register
              </button>
            </div>
            <CardTitle className="text-3xl text-ink">{mode === 'login' ? 'Welcome back' : 'Create your account'}</CardTitle>
            <CardDescription className="text-base leading-7 text-muted">
              {mode === 'login'
                ? 'Sign in with your email and password to open the internal forecast dashboard.'
                : 'Create your account with an approved email address to access the internal dashboard.'}
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 pt-3">
            <form className="grid gap-4" onSubmit={handleSubmit}>
              <label className="grid gap-2 text-sm font-medium text-ink">
                Email
                <input
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  className="min-h-11 rounded-2xl border border-slate-300 px-4 text-sm outline-none transition focus:border-accent"
                  placeholder="you@example.com"
                  autoComplete="email"
                />
              </label>
              <label className="grid gap-2 text-sm font-medium text-ink">
                Password
                <input
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  className="min-h-11 rounded-2xl border border-slate-300 px-4 text-sm outline-none transition focus:border-accent"
                  placeholder="Minimum 8 characters"
                  autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                />
              </label>
              {errorMessage ? <p className="text-sm font-medium text-red-700">{errorMessage}</p> : null}
              <button
                type="submit"
                disabled={isSubmitting}
                className="inline-flex min-h-12 items-center justify-center rounded-2xl bg-ink px-5 text-sm font-semibold text-white transition hover:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isSubmitting ? 'Please wait...' : submitLabel}
              </button>
            </form>
            <button
              type="button"
              onClick={onGuestView}
              className="inline-flex min-h-12 items-center justify-center rounded-2xl border border-slate-300 bg-white px-5 text-sm font-semibold text-ink transition hover:border-accent hover:text-accent"
            >
              View public forecast
            </button>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
