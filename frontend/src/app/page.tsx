'use client';

import React, { useEffect, useState } from 'react';
import PageContainer from '@/components/layout/PageContainer';
import KPICard from '@/components/dashboard/KPICard';
import CoverageChart from '@/components/dashboard/CoverageChart';
import FolderHeatmap from '@/components/dashboard/FolderHeatmap';
import GovernanceGauge from '@/components/dashboard/GovernanceGauge';
import RecentViolations from '@/components/dashboard/RecentViolations';
import ActivityFeed from '@/components/dashboard/ActivityFeed';
import { useFilterStore } from '@/stores/filterStore';
import { apiService } from '@/lib/api';
import { DashboardSummary, TrendPoint, FolderHealthResult } from '@/lib/types';
import { Ticket, Grid3x3, Clock, ShieldAlert, FileText, CheckCircle2 } from 'lucide-react';
import { formatPercent } from '@/lib/utils';
import Skeleton from '@/components/ui/Skeleton';

export default function Home() {
  const { selectedRepoId, period } = useFilterStore();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [trendData, setTrendData] = useState<TrendPoint[]>([]);
  const [folderHealth, setFolderHealth] = useState<FolderHealthResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchData = React.useCallback(async () => {
    if (!selectedRepoId) return;
    setIsLoading(true);
    try {
      const [summaryRes, trendRes, folderRes] = await Promise.all([
        apiService.dashboard.getSummary(),
        apiService.trends.getCoverage(period),
        apiService.folders.list()
      ]);
      setSummary(summaryRes);
      setTrendData(trendRes);
      setFolderHealth(folderRes);
    } catch (err) {
      console.error('Failed to fetch dashboard summary', err);
    } finally {
      setIsLoading(false);
    }
  }, [selectedRepoId, period]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleViolationRefresh = () => {
    // Re-fetch only violation/summary related data
    fetchData();
  };

  const activeRepoName = useFilterStore(state => 
    state.repositories.find(r => r.id === selectedRepoId)?.name || 'Default Repository'
  );

  return (
    <PageContainer
      title="Release Readiness Dashboard"
      subtitle={`Git Governance & Merge Intelligence for ${activeRepoName}`}
    >
      {/* 1. Top KPI Cards Row */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-6">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, idx) => (
            <Skeleton key={idx} className="h-28 rounded-xl" variant="rect" />
          ))
        ) : (
          <>
            <KPICard
              title="Total Jiras Ingested"
              value={summary?.kpis.total_jiras ?? 0}
              icon={Ticket}
              color="blue"
              description="Jira issues mapped from commits"
            />
            <KPICard
              title="Overall Folder Coverage"
              value={formatPercent(summary?.kpis.overall_coverage_pct ?? 0)}
              icon={Grid3x3}
              color="emerald"
              description="Percentage of folder targets merged"
            />
            <KPICard
              title="Avg Propagation Delay"
              value={`${(summary?.kpis.avg_propagation_delay_days ?? 0).toFixed(1)}d`}
              icon={Clock}
              color="amber"
              description="Mean time to replicate changes"
            />
            <KPICard
              title="Active Violations"
              value={summary?.kpis.active_violations_count ?? 0}
              icon={ShieldAlert}
              color={summary?.kpis.active_violations_count && summary.kpis.active_violations_count > 0 ? "rose" : "blue"}
              description="Unresolved exceptions found"
            />
          </>
        )}
      </div>

      {/* 2. Visualization Row: circular gauge + line trend chart */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3 mb-6">
        <div className="lg:col-span-1">
          <GovernanceGauge data={summary?.governance_score} isLoading={isLoading} />
        </div>
        <div className="lg:col-span-2">
          <CoverageChart data={trendData} isLoading={isLoading} />
        </div>
      </div>

      {/* 3. Folder Health Heatmap */}
      <div className="mb-6">
        <FolderHeatmap data={folderHealth} isLoading={isLoading} />
      </div>

      {/* 4. Violations and Activity Feeds */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div>
          <RecentViolations 
            data={summary?.critical_items ?? []} 
            isLoading={isLoading} 
            onRefresh={handleViolationRefresh}
          />
        </div>
        <div>
          <ActivityFeed 
            data={summary?.recent_activity ?? []} 
            isLoading={isLoading} 
          />
        </div>
      </div>
    </PageContainer>
  );
}
