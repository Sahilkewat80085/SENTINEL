'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useDashboardStore } from '@/stores/dashboardStore';
import { Shield, Lock, User, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';

export default function Login() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, isAuthenticated, authError, isAuthLoading } = useDashboardStore();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const redirectUrl = searchParams.get('redirect') || '/';

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      router.push(redirectUrl);
    }
  }, [isAuthenticated, router, redirectUrl]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) return;
    const success = await login(username, password);
    if (success) {
      router.push(redirectUrl);
    }
  };

  return (
    <div className="flex h-screen w-screen items-center justify-center p-4 bg-[#090d16]">
      <div className="w-full max-w-md">
        {/* Logo Icon Header */}
        <div className="flex flex-col items-center mb-6">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-600 shadow-lg glow-primary mb-3">
            <Shield className="h-6.5 w-6.5 text-white" />
          </div>
          <h2 className="text-2xl font-extrabold tracking-widest text-white font-sans">
            SENTINEL
          </h2>
          <p className="text-xs text-gray-500 font-semibold uppercase mt-1">
            Git Governance Platform
          </p>
        </div>

        {/* Login Form Card */}
        <Card className="glow-primary border-card-border/60">
          <CardHeader>
            <CardTitle>Sign In</CardTitle>
            <CardDescription>Enter credentials to access the release readiness dashboard</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4.5">
              {/* Username field */}
              <div className="flex flex-col gap-1.5">
                <label htmlFor="username" className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Username
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-500">
                    <User className="h-4 w-4" />
                  </span>
                  <input
                    id="username"
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="Enter username..."
                    disabled={isAuthLoading}
                    className="w-full rounded-lg border border-card-border bg-slate-900/50 py-2 pl-10 pr-4 text-sm text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none transition-colors"
                  />
                </div>
              </div>

              {/* Password field */}
              <div className="flex flex-col gap-1.5">
                <label htmlFor="password" className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Password
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-500">
                    <Lock className="h-4 w-4" />
                  </span>
                  <input
                    id="password"
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    disabled={isAuthLoading}
                    className="w-full rounded-lg border border-card-border bg-slate-900/50 py-2 pl-10 pr-4 text-sm text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none transition-colors"
                  />
                </div>
              </div>

              {/* Error messages */}
              {authError && (
                <div className="flex items-start gap-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 p-3.5 text-xs font-medium text-rose-400">
                  <AlertCircle className="h-4.5 w-4.5 flex-shrink-0" />
                  <span>{authError}</span>
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isAuthLoading || !username || !password}
                className="w-full rounded-lg bg-blue-600 py-2.5 text-sm font-bold text-white shadow-md hover:bg-blue-700 disabled:opacity-50 transition-colors glow-primary"
              >
                {isAuthLoading ? 'Authenticating...' : 'Sign In'}
              </button>
            </form>
          </CardContent>
        </Card>

        {/* Demo login tips */}
        <div className="mt-4 text-center">
          <p className="text-xs text-gray-500">
            Demo credentials: <span className="font-semibold text-gray-400">admin</span> / <span className="font-semibold text-gray-400">admin</span>
          </p>
        </div>
      </div>
    </div>
  );
}
