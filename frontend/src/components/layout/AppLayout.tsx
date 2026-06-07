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

  // No auth guard or loading screens required for public access mode

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
