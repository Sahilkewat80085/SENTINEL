'use client';

import React, { useEffect, useState, useCallback } from 'react';
import PageContainer from '@/components/layout/PageContainer';
import { apiService } from '@/lib/api';
import { TrendPoint, ViolationTrendPoint } from '@/lib/types';
import { useFilterStore } from '@/stores/filterStore';
import Skeleton from '@/components/ui/Skeleton';
import {
  AreaChart, Area, LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { TrendingUp, TrendingDown, Activity, ShieldAlert, Clock, BarChart2 } from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { cn } from '@/lib/utils';

const PERIODS = [
  { label: '7 Days', value: '7d' },
  { label: '30 Days', value: '30d' },
  { label: '90 Days', value: '90d' },
  { label: '180 Days', value: '180d' },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl border border-white/10 bg-[#0d1526]/95 backdrop-blur p-3 shadow-2xl">
      <p className="text-xs font-bold text-gray-400 mb-2">{label}</p>
      {payload.map((entry: any, i: number) => (
        <div key={i} className="flex items-center gap-2 text-xs">
          <span className="w-2 h-2 rounded-full" style={{ background: entry.color }} />
          <span className="text-gray-300">{entry.name}:</span>
          <span className="font-bold text-white">
            {typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}
          </span>
        </div>
      ))}
    </div>
  );
};

interface MetricCardProps {
  title: string;
  icon: React.ElementType;
  color: string;
  data: TrendPoint[];
  loading: boolean;
  unit?: string;
  description: string;
  invertTrend?: boolean;
}

const MetricTrendCard: React.FC<MetricCardProps> = ({
  title, icon: Icon, color, data, loading, unit = '', description, invertTrend = false
}) => {
  const lastValue = data[data.length - 1]?.value ?? 0;
  const firstValue = data[0]?.value ?? 0;
  const delta = lastValue - firstValue;
  const isPositive = invertTrend ? delta < 0 : delta > 0;

  const gradId = `grad-${title.replace(/\s+/g, '-')}`;

  const formattedData = data.map(d => ({
    date: format(parseISO(d.date), 'MMM dd'),
    value: d.value,
  }));

  return (
    <div className="rounded-2xl border border-white/8 bg-gradient-to-br from-[#111726]/80 to-[#0d1526]/80 backdrop-blur-sm p-5">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`flex h-9 w-9 items-center justify-center rounded-xl ${color}`}>
            <Icon className="h-4.5 w-4.5 text-white" />
          </div>
          <div>
            <p className="text-sm font-bold text-white">{title}</p>
            <p className="text-xs text-gray-500 mt-0.5">{description}</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-xl font-black text-white">
            {lastValue.toFixed(1)}{unit}
          </p>
          <div className={cn(
            'flex items-center justify-end gap-1 text-xs font-bold mt-0.5',
            isPositive ? 'text-emerald-400' : 'text-rose-400'
          )}>
            {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
            {delta > 0 ? '+' : ''}{delta.toFixed(1)}{unit}
          </div>
        </div>
      </div>

      {loading ? (
        <Skeleton className="h-28 w-full rounded-lg" variant="rect" />
      ) : (
        <ResponsiveContainer width="100%" height={112}>
          <AreaChart data={formattedData} margin={{ top: 4, right: 0, left: -30, bottom: 0 }}>
            <defs>
              <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color.includes('blue') ? '#3b82f6' : color.includes('emerald') ? '#10b981' : color.includes('amber') ? '#f59e0b' : '#f43f5e'} stopOpacity={0.3} />
                <stop offset="95%" stopColor={color.includes('blue') ? '#3b82f6' : color.includes('emerald') ? '#10b981' : color.includes('amber') ? '#f59e0b' : '#f43f5e'} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
            <XAxis dataKey="date" tick={{ fill: '#4b5563', fontSize: 10 }} tickLine={false} axisLine={false} interval="preserveStartEnd" />
            <YAxis tick={{ fill: '#4b5563', fontSize: 10 }} tickLine={false} axisLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="value"
              name={title}
              stroke={color.includes('blue') ? '#3b82f6' : color.includes('emerald') ? '#10b981' : color.includes('amber') ? '#f59e0b' : '#f43f5e'}
              strokeWidth={2}
              fill={`url(#${gradId})`}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};

export default function TrendsPage() {
  const { selectedRepoId } = useFilterStore();
  const [period, setPeriod] = useState('30d');
  const [coverageTrend, setCoverageTrend] = useState<TrendPoint[]>([]);
  const [healthTrend, setHealthTrend] = useState<TrendPoint[]>([]);
  const [delayTrend, setDelayTrend] = useState<TrendPoint[]>([]);
  const [violationsTrend, setViolationsTrend] = useState<TrendPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchTrends = useCallback(async () => {
    if (!selectedRepoId) return;
    setIsLoading(true);
    try {
      const [cov, health, delay, violations] = await Promise.all([
        apiService.trends.getCoverage(period),
        apiService.trends.getHealth(undefined, period),
        apiService.trends.getDelay(period),
        apiService.trends.getViolations(period),
      ]);
      setCoverageTrend(cov);
      setHealthTrend(health);
      setDelayTrend(delay);
      setViolationsTrend(violations);
    } catch (err) {
      console.error('Failed to fetch trends', err);
    } finally {
      setIsLoading(false);
    }
  }, [selectedRepoId, period]);

  useEffect(() => {
    fetchTrends();
  }, [fetchTrends]);

  // Build combined chart data for the overview
  const combinedData = React.useMemo(() => {
    const allDates = new Set<string>([
      ...coverageTrend.map(d => d.date),
      ...healthTrend.map(d => d.date),
      ...violationsTrend.map(d => d.date),
    ]);
    const coverageMap = new Map(coverageTrend.map(d => [d.date, d.value]));
    const healthMap = new Map(healthTrend.map(d => [d.date, d.value]));
    const violationsMap = new Map(violationsTrend.map(d => [d.date, d.value]));
    return Array.from(allDates).sort().map(date => ({
      date: format(parseISO(date), 'MMM dd'),
      coverage: coverageMap.get(date) ?? null,
      health: healthMap.get(date) ?? null,
      violations: violationsMap.get(date) ?? null,
    }));
  }, [coverageTrend, healthTrend, violationsTrend]);

  return (
    <PageContainer
      title="Historical Trend Analytics"
      subtitle="Time-series governance metrics and 30/90/180-day trend analysis"
      breadcrumbs={[{ name: 'Trends' }]}
      action={
        <div className="flex items-center gap-1.5 rounded-xl border border-white/10 bg-card p-1">
          {PERIODS.map(p => (
            <button
              key={p.value}
              onClick={() => setPeriod(p.value)}
              className={cn(
                'rounded-lg px-3 py-1.5 text-xs font-bold transition-all',
                period === p.value
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-gray-400 hover:text-white'
              )}
            >
              {p.label}
            </button>
          ))}
        </div>
      }
    >
      {/* Overview Combined Chart */}
      <div className="rounded-2xl border border-white/8 bg-gradient-to-br from-[#111726]/80 to-[#0d1526]/80 backdrop-blur-sm p-5 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <BarChart2 className="h-4 w-4 text-blue-400" />
          <h3 className="text-sm font-bold text-white">Composite Governance Overview</h3>
          <span className="ml-auto text-xs text-gray-500">Coverage % · Health Score · Active Violations</span>
        </div>
        {isLoading ? (
          <Skeleton className="h-52 w-full rounded-lg" variant="rect" />
        ) : (
          <ResponsiveContainer width="100%" height={210}>
            <LineChart data={combinedData} margin={{ top: 4, right: 20, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="date" tick={{ fill: '#4b5563', fontSize: 10 }} tickLine={false} axisLine={false} interval="preserveStartEnd" />
              <YAxis tick={{ fill: '#4b5563', fontSize: 10 }} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ color: '#9ca3af', fontSize: 11, paddingTop: 8 }} />
              <Line type="monotone" dataKey="coverage" name="Coverage %" stroke="#3b82f6" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="health" name="Health Score" stroke="#10b981" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="violations" name="Active Violations" stroke="#f43f5e" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* 4 Metric Cards */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <MetricTrendCard
          title="Coverage Rate"
          icon={Activity}
          color="bg-blue-500/20 border border-blue-500/30"
          data={coverageTrend}
          loading={isLoading}
          unit="%"
          description="Jira-to-folder merge coverage over time"
        />
        <MetricTrendCard
          title="Folder Health Score"
          icon={TrendingUp}
          color="bg-emerald-500/20 border border-emerald-500/30"
          data={healthTrend}
          loading={isLoading}
          unit="%"
          description="Average weighted folder health score"
        />
        <MetricTrendCard
          title="Avg. Propagation Delay"
          icon={Clock}
          color="bg-amber-500/20 border border-amber-500/30"
          data={delayTrend}
          loading={isLoading}
          unit="d"
          description="Average commit merge propagation delay in days"
          invertTrend
        />
        <MetricTrendCard
          title="Active Violations"
          icon={ShieldAlert}
          color="bg-rose-500/20 border border-rose-500/30"
          data={violationsTrend}
          loading={isLoading}
          description="Open governance rule violations count"
          invertTrend
        />
      </div>
    </PageContainer>
  );
}
