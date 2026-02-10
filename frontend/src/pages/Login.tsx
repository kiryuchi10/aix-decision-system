import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Zap } from 'lucide-react';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, demoLogin } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Zap className="w-10 h-10 text-yellow-400" />
            <h1 className="text-3xl font-bold text-white">AiX System</h1>
          </div>
          <p className="text-slate-400">Sign in to your account</p>
        </div>

        <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-xl p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg space-y-2">
                <p>{error}</p>
                {error.includes('Cannot reach server') && (
                  <ul className="text-sm text-slate-400 list-disc list-inside space-y-1">
                    <li>Start backend: <code className="bg-black/30 px-1 rounded">cd backend</code> then <code className="bg-black/30 px-1 rounded">uvicorn app.main:app --reload</code></li>
                    <li>Use proxy: in frontend <code className="bg-black/30 px-1 rounded">.env</code> remove <code className="bg-black/30 px-1 rounded">VITE_API_BASE_URL</code> (or set it empty), then restart <code className="bg-black/30 px-1 rounded">npm run dev</code></li>
                  </ul>
                )}
                {!error.includes('Cannot reach server') && (
                  <p className="text-sm text-slate-400">
                    No account? Use <strong>Demo Login</strong> below or <Link to="/signup" className="text-cyan-400 hover:underline">Sign up</Link>.
                  </p>
                )}
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full input-field"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-2">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full input-field"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <div className="mt-4">
            <button
              type="button"
              onClick={async () => {
                setError('');
                setLoading(true);
                try {
                  await demoLogin();
                  navigate('/');
                } catch (err: any) {
                  setError(err.message || 'Demo login failed');
                } finally {
                  setLoading(false);
                }
              }}
              disabled={loading}
              className="w-full btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Loading...' : '🚀 Demo Login (Skip Authentication)'}
            </button>
          </div>

          <div className="mt-6 text-center">
            <p className="text-slate-400">
              Don't have an account?{' '}
              <Link to="/signup" className="text-blue-400 hover:text-blue-300">
                Sign up
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
