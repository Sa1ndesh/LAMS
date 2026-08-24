import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Lock, Mail } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { useAuthContext } from '../context/AuthContext';

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login, loading } = useAuthContext();
  const [email, setEmail] = useState('admin.national@lams.gov.in');
  const [password, setPassword] = useState('LamsAdmin@2026');
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');
    if (!email || !password) {
      setErrorMessage('Please enter official email credentials.');
      return;
    }

    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Invalid credentials. Please check your email and password.';
      // Friendly fallback if backend server is not currently running
      if (msg.includes('Failed to fetch') || msg.includes('request failed')) {
        setErrorMessage('Backend API offline. Logging in with demo development credentials.');
        setTimeout(() => {
          navigate('/dashboard');
        }, 1000);
      } else {
        setErrorMessage(msg);
      }
    }
  };

  return (
    <div className="min-h-screen bg-lams-primary flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Background Grid Pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1261A315_1px,transparent_1px),linear-gradient(to_bottom,#1261A315_1px,transparent_1px)] bg-[size:4rem_4rem]"></div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10 text-center px-4">
        <div className="mx-auto h-16 w-16 rounded-2xl bg-lams-secondary flex items-center justify-center text-white shadow-xl mb-4 border border-sky-400/30">
          <Shield className="h-9 w-9 text-white" />
        </div>
        <span className="text-xs font-semibold uppercase tracking-widest text-sky-300">
          Government of India
        </span>
        <h2 className="mt-1 text-2xl font-extrabold text-white tracking-tight">
          National Land Acquisition Portal
        </h2>
        <p className="mt-2 text-xs text-slate-300">
          Role-Based Management System for Infrastructure Projects
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md relative z-10 px-4">
        <div className="bg-lams-surface py-8 px-6 shadow-2xl rounded-2xl border border-slate-200">
          <form className="space-y-5" onSubmit={handleSubmit}>
            {errorMessage && (
              <div className="p-3 bg-amber-50 border border-amber-200 text-amber-800 text-xs rounded-lg font-medium">
                {errorMessage}
              </div>
            )}

            <Input
              label="Official Email Address"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              icon={<Mail className="h-4 w-4" />}
            />

            <Input
              label="Password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              icon={<Lock className="h-4 w-4" />}
            />

            <div className="flex items-center justify-between text-xs">
              <label className="flex items-center text-lams-muted">
                <input type="checkbox" defaultChecked className="rounded border-gray-300 text-lams-secondary focus:ring-lams-secondary mr-2" />
                Remember credentials
              </label>
              <button
                type="button"
                onClick={() => alert('Demo Credentials: admin.national@lams.gov.in / LamsAdmin@2026')}
                className="text-lams-secondary hover:underline font-medium"
              >
                Seed Admin Hint?
              </button>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              className="w-full"
              isLoading={loading}
            >
              Sign In to Portal
            </Button>
          </form>

          <div className="mt-6 pt-4 border-t border-lams-border text-center text-xs text-lams-muted">
            Ministry of Land Resources • Government of India
          </div>
        </div>
      </div>
    </div>
  );
};
