'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/Card';
import { GovernanceScoreDetail } from '@/lib/types';
import { getGradeColorClass } from '@/lib/utils';
import Skeleton from '../ui/Skeleton';
import { Shield, HelpCircle, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface GovernanceGaugeProps {
  data?: GovernanceScoreDetail;
  isLoading: boolean;
}

export default function GovernanceGauge({ data, isLoading }: GovernanceGaugeProps) {
  if (isLoading) {
    return (
      <Card className="h-full">
        <CardHeader>
          <Skeleton className="h-6 w-1/3 rounded" variant="text" />
          <Skeleton className="h-4 w-1/2 rounded" variant="text" />
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center py-6">
          <Skeleton className="h-32 w-32 rounded-full" variant="circle" />
          <Skeleton className="h-6 w-1/4 rounded mt-4" variant="text" />
        </CardContent>
      </Card>
    );
  }

  const score = data?.score ?? 0;
  const grade = data?.grade ?? 'F';
  const penalty = data?.violation_penalty ?? 0;
  const folderAvg = data?.folder_health_average ?? 0;

  // Grade color class wrapper
  const gradeStyles = getGradeColorClass(grade);

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <CardTitle>Governance Rating</CardTitle>
        <CardDescription>Composite A-F grade reflecting overall release readiness</CardDescription>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col items-center justify-center py-4">
        {/* Rating Gauge Circle */}
        <div className="relative flex h-36 w-36 items-center justify-center rounded-full border-4 border-slate-800 bg-[#0d1322]/50 shadow-inner">
          {/* Rating Circle Outline depending on Score percentage */}
          <svg className="absolute inset-0 h-full w-full -rotate-90">
            <circle
              cx="72"
              cy="72"
              r="66"
              stroke="currentColor"
              strokeWidth="4"
              fill="transparent"
              className="text-slate-800"
            />
            <circle
              cx="72"
              cy="72"
              r="66"
              stroke="currentColor"
              strokeWidth="4"
              fill="transparent"
              strokeDasharray="414.6"
              strokeDashoffset={414.6 - (414.6 * score) / 100}
              className={cn(
                "transition-all duration-1000 ease-out",
                grade === 'A' || grade === 'B' ? 'text-emerald-500' : 
                grade === 'C' ? 'text-yellow-500' : 
                grade === 'D' ? 'text-orange-500' : 'text-rose-500'
              )}
            />
          </svg>
          
          {/* Inner content: Grade and Score */}
          <div className="flex flex-col items-center text-center">
            <span className={cn("text-5xl font-black tracking-tight", grade === 'A' || grade === 'B' ? 'text-emerald-500' : grade === 'C' ? 'text-yellow-500' : grade === 'D' ? 'text-orange-500' : 'text-rose-500')}>
              {grade}
            </span>
            <span className="text-sm font-bold text-white mt-1">
              Score: {score.toFixed(1)}
            </span>
          </div>
        </div>

        {/* Breakdown details */}
        <div className="w-full mt-6 space-y-3">
          <div className="flex justify-between items-center text-xs font-semibold text-gray-400">
            <span>Folder Health Average</span>
            <span className="text-white font-mono">{folderAvg.toFixed(1)}%</span>
          </div>
          <div className="flex justify-between items-center text-xs font-semibold text-gray-400">
            <span className="flex items-center gap-1">
              Active Penalty
              <span title="Score subtracted for unresolved violations">
                <HelpCircle className="h-3 w-3 text-gray-600" />
              </span>
            </span>
            <span className={cn("font-mono font-bold", penalty > 0 ? "text-rose-400" : "text-emerald-400")}>
              -{penalty.toFixed(1)}
            </span>
          </div>

          <hr className="border-card-border/40" />

          {/* Issue Count Grid */}
          <div className="grid grid-cols-4 gap-2 pt-1 text-center">
            <div className="rounded-lg bg-rose-500/5 border border-rose-500/10 p-2">
              <p className="text-[10px] font-bold text-rose-400 uppercase">Crit</p>
              <p className="text-sm font-extrabold text-white mt-0.5">{data?.active_critical_count ?? 0}</p>
            </div>
            <div className="rounded-lg bg-orange-500/5 border border-orange-500/10 p-2">
              <p className="text-[10px] font-bold text-orange-400 uppercase">High</p>
              <p className="text-sm font-extrabold text-white mt-0.5">{data?.active_high_count ?? 0}</p>
            </div>
            <div className="rounded-lg bg-yellow-500/5 border border-yellow-500/10 p-2">
              <p className="text-[10px] font-bold text-yellow-400 uppercase">Med</p>
              <p className="text-sm font-extrabold text-white mt-0.5">{data?.active_medium_count ?? 0}</p>
            </div>
            <div className="rounded-lg bg-blue-500/5 border border-blue-500/10 p-2">
              <p className="text-[10px] font-bold text-blue-400 uppercase">Low</p>
              <p className="text-sm font-extrabold text-white mt-0.5">{data?.active_low_count ?? 0}</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
