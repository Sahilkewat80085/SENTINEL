'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useDashboardStore } from '@/stores/dashboardStore';
import { cn } from '@/lib/utils';
import { 
  LayoutDashboard, 
  Ticket, 
  FolderGit2, 
  Grid3x3, 
  Binary, 
  ShieldAlert, 
  TrendingUp, 
  FileDown, 
  Settings, 
  ChevronLeft, 
  ChevronRight,
  LogOut,
  User as UserIcon,
  Shield,
  GitCommit
} from 'lucide-react';

interface SidebarItem {
  name: string;
  href: string;
  icon: React.ComponentType<any>;
}

const sidebarItems: SidebarItem[] = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Jira Explorer', href: '/jiras', icon: Ticket },
  { name: 'Folder Overview', href: '/folders', icon: FolderGit2 },
  { name: 'Coverage Matrix', href: '/coverage', icon: Grid3x3 },
  { name: 'Commit Log', href: '/commits', icon: GitCommit },
  { name: 'Content Drift', href: '/content', icon: Binary },
  { name: 'Governance Issues', href: '/violations', icon: ShieldAlert },
  { name: 'Historical Trends', href: '/trends', icon: TrendingUp },
  { name: 'Report Builder', href: '/reports', icon: FileDown },
  { name: 'Configuration', href: '/settings', icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { sidebarOpen, toggleSidebar, user, logout } = useDashboardStore();

  const isLinkActive = (href: string) => {
    if (href === '/') {
      return pathname === '/';
    }
    return pathname.startsWith(href);
  };

  return (
    <aside 
      className={cn(
        "fixed inset-y-0 left-0 z-20 flex flex-col border-r border-card-border bg-sidebar transition-all duration-300",
        sidebarOpen ? "w-64" : "w-16"
      )}
    >
      {/* Header / Logo */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-card-border bg-background/50">
        <Link href="/" className="flex items-center gap-2 overflow-hidden">
          <div className="flex h-8 w-8 items-center justify-between rounded-lg bg-blue-600 p-1.5 text-white shadow-md glow-primary">
            <Shield className="h-5 w-5" />
          </div>
          {sidebarOpen && (
            <span className="font-sans text-lg font-bold tracking-wider text-white">
              SENTINEL
            </span>
          )}
        </Link>
        {sidebarOpen && (
          <button 
            onClick={toggleSidebar}
            className="rounded-lg p-1.5 text-gray-400 hover:bg-card-border hover:text-white"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 space-y-1 px-2 py-4 overflow-y-auto">
        {sidebarItems.map((item) => {
          const active = isLinkActive(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "group flex items-center rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150",
                active 
                  ? "bg-blue-600 text-white shadow-sm glow-primary" 
                  : "text-gray-400 hover:bg-card hover:text-white"
              )}
            >
              <Icon 
                className={cn(
                  "h-5 w-5 flex-shrink-0 transition-all duration-150",
                  sidebarOpen ? "mr-3" : "mr-0",
                  active ? "text-white" : "text-gray-400 group-hover:text-white"
                )} 
              />
              {sidebarOpen && <span>{item.name}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Collapse button when sidebar is collapsed */}
      {!sidebarOpen && (
        <div className="flex justify-center py-2 border-t border-card-border">
          <button 
            onClick={toggleSidebar}
            className="rounded-lg p-2 text-gray-400 hover:bg-card-border hover:text-white"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* User Footer Profile */}
      <div className="border-t border-card-border bg-background/50 p-4">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-slate-800 text-gray-300">
            <UserIcon className="h-4 w-4" />
          </div>
          {sidebarOpen && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-white truncate">
                System Administrator
              </p>
              <p className="text-xs text-gray-400 capitalize truncate">
                Public Dashboard Mode
              </p>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
