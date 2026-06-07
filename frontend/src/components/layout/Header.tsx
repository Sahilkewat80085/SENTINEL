'use client';

import React, { useEffect, useState } from 'react';
import { useFilterStore } from '@/stores/filterStore';
import { useDashboardStore } from '@/stores/dashboardStore';
import { apiService } from '@/lib/api';
import { Menu, RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function Header() {
  const { toggleSidebar, sidebarOpen } = useDashboardStore();
  const { 
    selectedRepoId, 
    repositories, 
    period, 
    setSelectedRepoId, 
    setPeriod, 
    fetchRepositories 
  } = useFilterStore();

  const [syncLoading, setSyncLoading] = useState(false);
  const [syncStatus, setSyncStatus] = useState<string | null>(null);

  useEffect(() => {
    fetchRepositories();
  }, [fetchRepositories]);

  const handleSync = async () => {
    if (!selectedRepoId) return;
    setSyncLoading(true);
    setSyncStatus('syncing');
    try {
      await apiService.repositories.sync(selectedRepoId);
      // Wait for it, simple delay for demo
      setTimeout(async () => {
        setSyncStatus('success');
        setSyncLoading(false);
        // Refresh the page or trigger state update
        if (typeof window !== 'undefined') {
          window.location.reload();
        }
      }, 3000);
    } catch (err) {
      setSyncStatus('error');
      setSyncLoading(false);
    }
  };

  return (
    <header className="sticky top-0 z-10 flex h-16 w-full items-center justify-between px-6 border-b border-card-border bg-background/85 backdrop-blur-md">
      {/* Left side: Toggle button and page details */}
      <div className="flex items-center gap-4">
        {!sidebarOpen && (
          <button 
            onClick={toggleSidebar}
            className="rounded-lg p-1.5 text-gray-400 hover:bg-card-border hover:text-white"
          >
            <Menu className="h-5 w-5" />
          </button>
        )}
        <div className="hidden md:flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="text-xs font-semibold text-gray-400 tracking-wider uppercase">Live Readiness Monitor</span>
        </div>
      </div>

      {/* Right side: Global Filters (Repo Select, Period Select, Sync Trigger) */}
      <div className="flex items-center gap-4">
        {/* Repo Selector */}
        <div className="flex items-center gap-2">
          <label htmlFor="repo-select" className="hidden sm:inline text-xs font-medium text-gray-400">
            Repository:
          </label>
          <select
            id="repo-select"
            value={selectedRepoId || ''}
            onChange={(e) => setSelectedRepoId(e.target.value || null)}
            className="rounded-lg border border-card-border bg-card px-3 py-1.5 text-sm font-medium text-white focus:border-blue-500 focus:outline-none"
          >
            {repositories.map((repo) => (
              <option key={repo.id} value={repo.id} className="bg-card">
                {repo.name}
              </option>
            ))}
            {repositories.length === 0 && (
              <option value="" disabled className="bg-card">No repositories</option>
            )}
          </select>
        </div>

        {/* Timeframe Selector */}
        <div className="flex items-center gap-2">
          <label htmlFor="period-select" className="hidden sm:inline text-xs font-medium text-gray-400">
            Period:
          </label>
          <select
            id="period-select"
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="rounded-lg border border-card-border bg-card px-3 py-1.5 text-sm font-medium text-white focus:border-blue-500 focus:outline-none"
          >
            <option value="7d" className="bg-card">Last 7 Days</option>
            <option value="30d" className="bg-card">Last 30 Days</option>
            <option value="90d" className="bg-card">Last 90 Days</option>
            <option value="all" className="bg-card">All Time</option>
          </select>
        </div>

        {/* Sync Trigger button */}
        <button
          onClick={handleSync}
          disabled={syncLoading || !selectedRepoId}
          className={cn(
            "flex items-center gap-2 rounded-lg bg-blue-600 px-3.5 py-1.5 text-sm font-semibold text-white shadow-md hover:bg-blue-700 disabled:opacity-50 transition-all duration-150 glow-primary",
            syncLoading && "animate-pulse"
          )}
        >
          <RefreshCw className={cn("h-4 w-4", syncLoading && "animate-spin")} />
          <span className="hidden sm:inline">
            {syncLoading ? 'Syncing...' : 'Sync Now'}
          </span>
        </button>

        {/* Sync Result Indicators */}
        {syncStatus === 'success' && (
          <span title="Sync successful">
            <CheckCircle2 className="h-5 w-5 text-emerald-500" />
          </span>
        )}
        {syncStatus === 'error' && (
          <span title="Sync failed">
            <AlertCircle className="h-5 w-5 text-rose-500" />
          </span>
        )}
      </div>
    </header>
  );
}
