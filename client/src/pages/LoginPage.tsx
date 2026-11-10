import { ArrowRight, FileText } from 'lucide-react';
import { useState, type FormEvent } from 'react';
import { Navigate, useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import Alert from '../components/ui/Alert';
import Avatar from '../components/ui/Avatar';
import { useAuth } from '../hooks/useAuth';
import { APP_NAME, DEMO_ACCOUNTS, DEMO_PASSWORD } from '../utils/constants';
import { getErrorMessage } from '../utils/errors';

export default function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [params] = useSearchParams();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(
    params.get('expired') ? 'Your session expired. Please sign in again.' : null,
  );
  const [submitting, setSubmitting] = useState<string | null>(null);

  const redirectTo = (location.state as { from?: string } | null)?.from ?? '/';
  if (user) return <Navigate to={redirectTo} replace />;

  async function signIn(emailValue: string, passwordValue: string, source: string) {
    setError(null);
    setSubmitting(source);
    try {
      await login(emailValue.trim(), passwordValue);
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setError(getErrorMessage(err, 'Could not sign in.'));
      setSubmitting(null);
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!email.trim() || !password) {
      setError('Enter your email and password.');
      return;
    }
    void signIn(email, password, 'form');
  }

  return (
    <div className="flex min-h-full items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="mb-8 flex flex-col items-center text-center">
          <span className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600 text-white shadow-sm">
            <FileText className="h-6 w-6" aria-hidden />
          </span>
          <h1 className="text-2xl font-semibold tracking-tight">Sign in to {APP_NAME}</h1>
          <p className="mt-1 text-sm text-slate-500">Write, format and share documents with your team.</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          {error && (
            <div className="mb-4">
              <Alert onDismiss={() => setError(null)}>{error}</Alert>
            </div>
          )}

          <h2 className="text-sm font-medium text-slate-700">Continue as a demo user</h2>
          <ul className="mt-3 space-y-2">
            {DEMO_ACCOUNTS.map((acct) => (
              <li key={acct.email}>
                <button
                  type="button"
                  disabled={submitting !== null}
                  onClick={() => void signIn(acct.email, DEMO_PASSWORD, acct.email)}
                  className="group flex w-full items-center gap-3 rounded-lg border border-slate-200 px-3 py-2.5 text-left transition hover:border-blue-300 hover:bg-blue-50/50 disabled:opacity-60"
                >
                  <Avatar name={acct.name} />
                  <span className="flex-1">
                    <span className="block text-sm font-medium text-slate-900">{acct.name}</span>
                    <span className="block text-xs text-slate-500">{acct.email}</span>
                  </span>
                  <span className="text-xs text-slate-400 group-hover:text-blue-600">
                    {submitting === acct.email ? 'Signing in…' : <ArrowRight className="h-4 w-4" />}
                  </span>
                </button>
              </li>
            ))}
          </ul>

          <div className="my-5 flex items-center gap-3 text-xs uppercase tracking-wide text-slate-400">
            <span className="h-px flex-1 bg-slate-200" /> or <span className="h-px flex-1 bg-slate-200" />
          </div>

          <form onSubmit={onSubmit} className="space-y-3" noValidate>
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-700">
                Email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-xs focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-700">
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-xs focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none"
              />
            </div>
            <button
              type="submit"
              disabled={submitting !== null}
              className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 disabled:opacity-60"
            >
              {submitting === 'form' ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
        </div>

        <p className="mt-4 text-center text-xs text-slate-500">
          Demo environment: every account uses the password <code className="rounded bg-slate-100 px-1">{DEMO_PASSWORD}</code>.
        </p>
      </div>
    </div>
  );
}
