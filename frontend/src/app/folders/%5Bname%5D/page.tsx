'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import PageContainer from '@/components/layout/PageContainer';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import Progress from '@/components/ui/Progress';
import DataTable from '@/components/data/DataTable';
import { apiService } from '@/lib/api';
import { FolderHealthResult, MissingMerge, TrendPoint } from '@/lib/types';
import { useFilterStore } from '@/stores/filterStore';
import { getClassificationColorClass, formatDate } from '@/lib/utils';
import { ArrowLeft, Clock, Grid, ShieldAlert, Award, FileSpreadsheet, CheckCircle2 } from 'lucide-react';
import Skeleton from '@/components/ui/Skeleton';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, TooltipProps } from 'recharts';

export default function FolderDetailPage() {
  const router = useRouter();
  const { name } = useParams() as { name: string };
  const { selectedRepoId, period } = useFilterStore();
  const [health, setHealth] = useState<FolderHealthResult | null>(null);
  const [missingMerges, setMissingMerges] = useState<MissingMerge[]>([]);
  const [trendData, setTrendData] = useState<TrendPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!name || !selectedRepoId) return;

    const fetchFolderData = async () => {
      setIsLoading(true);
      try {
        const [foldersList, missingList, trendRes] = await Promise.all([
          apiService.folders.list(),
          apiService.coverage.getMissing(),
          apiService.trends.getHealth(name, period)
        ]);

        const folderObj = foldersList.find(f => f.folder_name === name);
        if (folderObj) setHealth(folderObj);

        const folderMissing = missingList.filter(m => m.folder === name);
        setMissingMerges(folderMissing);

        setTrendData(trendRes);
      } catch (err) {
        console.error('Failed to fetch folder details', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchFolderData();
  }, [name, selectedRepoId, period]);

  const customTooltip = ({ active, payload }: TooltipProps<number, string>) => {
    if (active && payload && payload.length) {
      return (
        <div className="rounded-lg border border-card-border bg-card p-3 shadow-xl glow-primary">
          <p className="text-xs font-semibold text-gray-400">
            {formatDate(payload[0].payload.date, 'MMMM d, yyyy')}
          </p>
          <p className="mt-1.5 text-sm font-extrabold text-blue-400">
            Health: {payload[0].value?.toFixed(1)}%
          </p>
        </div>
      );
    }
    return null;
  };

  const missingColumns = [
    {
      key: 'jira_id',
      header: 'Jira ID',
      render: (row: MissingMerge) => (
        <span className="font-bold font-mono text-white text-sm">{row.jira_id}</span>
      ),
    },
    {
      key: 'last_updated',
      header: 'Committed Date',
      render: (row: MissingMerge) => formatDate(row.last_updated),
    },
    {
      key: 'status',
      header: 'Status',
      render: () => (
        <Badge variant="error" className="font-bold font-mono text-[9px]">
          MISSING MERGE
        </Badge>
      ),
    },
  ];

  return (
    <PageContainer
      title={`Folder: ${name}`}
      subtitle={`Detailed health profile and backlog details for configuration targets`}
      breadcrumbs={[
        { name: 'Folders', href: '/folders' },
        { name }
      ]}
      action={
        <button
          onClick={() => router.back()}
          className="inline-flex items-center gap-1.5 rounded-lg border border-card-border px-3 py-1.5 text-xs font-semibold text-gray-400 hover:text-white hover:bg-card-border transition-all"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </button>
      }
    >
      {isLoading ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
            {Array.from({ length: 4 }).map((_, idx) => (
              <Skeleton key={idx} className="h-28 rounded-xl" variant="rect" />
            ))}
          </div>
          <Skeleton className="h-96 rounded-xl" variant="rect" />
        </div>
      ) : !health ? (
        <div className="rounded-xl border border-card-border bg-card p-12 text-center text-sm font-semibold text-gray-500">
          Folder health statistics could not be loaded.
        </div>
      ) : (
        <div className="space-y-6">
          {/* 1. Core Health Cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {/* Overall Score */}
            <Card className="glow-primary border-blue-500/20 bg-blue-500/5 col-span-1 sm:col-span-2 lg:col-span-1">
              <CardContent className="p-5 flex flex-col items-center justify-center text-center">
                <span className="text-[10px] font-bold text-blue-400 uppercase tracking-wider">
                  Health Score
                </span>
                <span className="text-3xl font-black text-white mt-1.5 font-mono">
                  {health.health_score.toFixed(1)}%
                </span>
                <Badge className={cn("font-bold text-[9px] font-mono mt-2", getClassificationColorClass(health.classification))}>
                  {health.classification}
                </Badge>
              </CardContent>
            </Card>

            {/* Coverage Card */}
            <Card className="border-card-border/60 bg-[#111726]/20">
              <CardContent className="p-5">
                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block">
                  Coverage
                </span>
                <span className="text-2xl font-extrabold text-white mt-1 block font-mono">
                  {health.coverage_score.toFixed(1)}%
                </span>
                <Progress value={health.coverage_score} color="dynamic" className="h-1.5 mt-3" />
              </CardContent>
            </Card>

            {/* Consistency Card */}
            <Card className="border-card-border/60 bg-[#111726]/20">
              <CardContent className="p-5">
                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block">
                  Consistency
                </span>
                <span className="text-2xl font-extrabold text-white mt-1 block font-mono">
                  {health.consistency_score.toFixed(1)}%
                </span>
                <Progress value={health.consistency_score} color="dynamic" className="h-1.5 mt-3" />
              </CardContent>
            </Card>

            {/* Timeliness Card */}
            <Card className="border-card-border/60 bg-[#111726]/20">
              <CardContent className="p-5">
                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block">
                  Timeliness
                </span>
                <span className="text-2xl font-extrabold text-white mt-1 block font-mono">
                  {health.timeliness_score.toFixed(1)}%
                </span>
                <Progress value={health.timeliness_score} color="dynamic" className="h-1.5 mt-3" />
              </CardContent>
            </Card>

            {/* Completeness Card */}
            <Card className="border-card-border/60 bg-[#111726]/20">
              <CardContent className="p-5">
                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block">
                  Completeness
                </span>
                <span className="text-2xl font-extrabold text-white mt-1 block font-mono">
                  {health.completeness_score.toFixed(1)}%
                </span>
                <Progress value={health.completeness_score} color="dynamic" className="h-1.5 mt-3" />
              </CardContent>
            </Card>
          </div>

          {/* 2. Health Trend Line Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Folder Health History</CardTitle>
              <CardDescription>Historical tracking of folder health index over time</CardDescription>
            </CardHeader>
            <CardContent className="h-64">
              {trendData.length === 0 ? (
                <div className="flex h-full w-full items-center justify-center text-sm font-semibold text-gray-500">
                  No historical folder trends recorded yet.
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart
                    data={trendData.map(pt => ({ ...pt, formattedDate: formatDate(pt.date, 'MMM d') }))}
                    margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                  >
                    <defs>
                      <linearGradient id="folderHealthGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" opacity={0.3} />
                    <XAxis dataKey="formattedDate" stroke="#6b7280" fontSize={11} tickLine={false} />
                    <YAxis stroke="#6b7280" fontSize={11} domain={[0, 100]} tickLine={false} />
                    <Tooltip content={customTooltip} />
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke="#10b981"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#folderHealthGradient)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          {/* 3. Missing Merges Log */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <div>
                <CardTitle>Pending Merge Backlog</CardTitle>
                <CardDescription>Jira tickets committed to other folders but missing from {name}</CardDescription>
              </div>
              <ShieldAlert className={cn("h-5 w-5", missingMerges.length > 0 ? "text-rose-500 animate-pulse" : "text-gray-600")} />
            </CardHeader>
            <CardContent>
              {missingMerges.length === 0 ? (
                <div className="flex h-24 w-full flex-col items-center justify-center text-sm font-semibold text-gray-500">
                  <CheckCircle2 className="h-6 w-6 text-emerald-500 mb-1.5" />
                  All committed tickets successfully merged into {name}!
                </div>
              ) : (
                <DataTable
                  columns={missingColumns}
                  data={missingMerges}
                  isLoading={false}
                />
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </PageContainer>
  );
}
