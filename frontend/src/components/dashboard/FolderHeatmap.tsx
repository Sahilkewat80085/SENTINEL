'use client';

import React from 'react';
import { FolderHealthResult } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/Card';
import Skeleton from '../ui/Skeleton';
import { cn } from '@/lib/utils';

interface FolderHeatmapProps {
  data: FolderHealthResult[];
  isLoading: boolean;
}

export default function FolderHeatmap({ data, isLoading }: FolderHeatmapProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-1/4 rounded" variant="text" />
          <Skeleton className="h-4 w-1/3 rounded" variant="text" />
        </CardHeader>
        <CardContent className="space-y-4">
          {Array.from({ length: 4 }).map((_, idx) => (
            <Skeleton key={idx} className="h-10 w-full rounded" variant="rect" />
          ))}
        </CardContent>
      </Card>
    );
  }

  // Get cell color based on score value
  const getCellClass = (score: number) => {
    if (score >= 90) {
      return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/25';
    } else if (score >= 70) {
      return 'bg-teal-500/10 text-teal-400 border-teal-500/25';
    } else if (score >= 50) {
      return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/25';
    } else if (score >= 25) {
      return 'bg-orange-500/10 text-orange-400 border-orange-500/25';
    } else {
      return 'bg-rose-500/10 text-rose-400 border-rose-500/25';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Folder Health Heatmap</CardTitle>
        <CardDescription>Breakdown of folder scores across key governance pillars</CardDescription>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <div className="flex h-36 w-full items-center justify-center text-sm font-semibold text-gray-500">
            No folder data sync records available.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className="pb-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-400 w-1/4">
                    Folder Name
                  </th>
                  <th className="pb-3 text-center text-xs font-semibold uppercase tracking-wider text-gray-400">
                    Coverage (35%)
                  </th>
                  <th className="pb-3 text-center text-xs font-semibold uppercase tracking-wider text-gray-400">
                    Consistency (30%)
                  </th>
                  <th className="pb-3 text-center text-xs font-semibold uppercase tracking-wider text-gray-400">
                    Timeliness (20%)
                  </th>
                  <th className="pb-3 text-center text-xs font-semibold uppercase tracking-wider text-gray-400">
                    Completeness (15%)
                  </th>
                  <th className="pb-3 text-center text-xs font-semibold uppercase tracking-wider text-gray-400 font-bold text-white border-l border-card-border/40 pl-3">
                    Composite Health
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-card-border/30">
                {data.map((row) => (
                  <tr key={row.folder_name} className="hover:bg-slate-800/10 transition-colors">
                    <td className="py-3.5 text-sm font-bold text-white">
                      {row.folder_name}
                    </td>
                    
                    {/* Coverage Cell */}
                    <td className="py-2.5 px-1.5 text-center">
                      <div className={cn("rounded-lg border py-2 font-mono text-sm font-bold", getCellClass(row.coverage_score))}>
                        {row.coverage_score.toFixed(1)}%
                      </div>
                    </td>

                    {/* Consistency Cell */}
                    <td className="py-2.5 px-1.5 text-center">
                      <div className={cn("rounded-lg border py-2 font-mono text-sm font-bold", getCellClass(row.consistency_score))}>
                        {row.consistency_score.toFixed(1)}%
                      </div>
                    </td>

                    {/* Timeliness Cell */}
                    <td className="py-2.5 px-1.5 text-center">
                      <div className={cn("rounded-lg border py-2 font-mono text-sm font-bold", getCellClass(row.timeliness_score))}>
                        {row.timeliness_score.toFixed(1)}%
                      </div>
                    </td>

                    {/* Completeness Cell */}
                    <td className="py-2.5 px-1.5 text-center">
                      <div className={cn("rounded-lg border py-2 font-mono text-sm font-bold", getCellClass(row.completeness_score))}>
                        {row.completeness_score.toFixed(1)}%
                      </div>
                    </td>

                    {/* Composite Health Cell */}
                    <td className="py-2.5 pl-4 text-center border-l border-card-border/40">
                      <div className={cn("rounded-lg border py-2 font-mono text-sm font-extrabold shadow-sm glow-primary", getCellClass(row.health_score))}>
                        {row.health_score.toFixed(1)}%
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
