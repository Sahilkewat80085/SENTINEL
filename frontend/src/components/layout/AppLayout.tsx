'use client';

import React, { useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useDashboardStore } from '@/stores/dashboardStore';
import Sidebar from './Sidebar';
import Header from './Header';
import { cn } from '@/lib/utils';
import { Shield } from 'lucide-react';

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { 
    sidebarOpen, 
    checkAuth, 
    isAuthenticated, 
    isAuthLoading, 
    user 
  } = useDashboardStore();

  const isLoginPage = pathname === '/login';

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Auth Guard redirect
  useEffect(() => {
    if (!isAuthLoading && !isAuthenticated && !isLoginPage) {
      router.push(`/login?redirect=${encodeURIComponent(pathname)}`);
    }
  }, [isAuthenticated, isAuthLoading, isLoginPage, pathname, router]);

  // Render loading state
  if (isAuthLoading && !isLoginPage) {
    return (
      <div className="flex h-screen w-screen flex-col items-center justify-center bg-[#090d16] text-white">
        <div className="relative flex h-16 w-16 items-center justify-center rounded-xl bg-blue-600 shadow-xl glow-primary animate-bounce mb-4">
          <Shield className="h-9 w-9 text-white" />
        </div>
        <p className="text-sm font-semibold tracking-widest text-gray-400 uppercase animate-pulse">
          Sentinel Shield Initializing...
        </p>
      </div>
    );
  }

  // Login page layout (no Sidebar / Header)
  if (isLoginPage) {
    return <div className="min-h-screen w-full bg-[#090d16]">{children}</div>;
  }

  // Standard platform layout shell
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background">
      <Sidebar />
      <div 
        className={cn(
          "flex flex-col flex-1 min-w-0 transition-all duration-300",
          sidebarOpen ? "pl-64" : "pl-16"
        )}
      >
        <Header />
        <div className="flex-1 overflow-y-auto flex flex-col">
          {children}
        </div>
      </div>
    </div>
  );
}
