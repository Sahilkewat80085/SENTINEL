'use client';

import React from 'react';
import { CoverageMatrix as MatrixType, JiraCoverageRow } from '@/lib/types';
import Badge from '../ui/Badge';
import Progress from '../ui/Progress';
import { formatDate, getStatusColorClass } from '@/lib/utils';
import { CheckCircle, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import Skeleton from '../ui/Skeleton';
import Link from 'next/link';

interface CoverageMatrixProps {
  matrix?: MatrixType;
  isLoading: boolean;
}

export default function CoverageMatrix({ matrix, isLoading }: CoverageMatrixProps) {
  if (isLoading) {
    return (
      <div className="rounded-xl border border-card-border bg-card overflow-hidden">
        <div className="h-12 border-b border-card-border bg-card-border/30 px-6 flex items-center justify-between">
          <Skeleton className="h-5 w-1/4 rounded" variant="text" />
        </div>
        <div className="p-6 space-y-4">
          {Array.from({ length: 4 }).map((_, idx) => (
            <Skeleton key={idx} className="h-12 w-full rounded" variant="rect" />
          ))}
        </div>
      </div>
    );
  }

  if (!matrix || matrix.rows.length === 0) {
    return (
      <div className="rounded-xl border border-card-border bg-card p-12 text-center text-sm font-semibold text-gray-500">
        No coverage matrix data available. Make sure to sync commits first.
      </div>
    );
  }

  const { folders_list, rows } = matrix;

  return (
    <div className="w-full overflow-hidden rounded-xl border border-card-border bg-card shadow-lg">
      <div className="w-full overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-card-border bg-[#111726]/40">
              <th className="px-6 py-4.5 text-left text-xs font-semibold uppercase tracking-wider text-gray-400 w-44">
                Jira ID
              </th>
              {folders_list.map((folder) => (
                <th
                  key={folder}
                  className="px-4 py-4.5 text-center text-xs font-semibold uppercase tracking-wider text-gray-400 min-w-[100px]"
                >
                  {folder}
                </th>
              ))}
              <th className="px-6 py-4.5 text-left text-xs font-semibold uppercase tracking-wider text-gray-400 w-48">
                Coverage
              </th>
              <th className="px-6 py-4.5 text-center text-xs font-semibold uppercase tracking-wider text-gray-400 w-32">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-card-border/30">
            {rows.map((row) => (
              <tr key={row.jira_id} className="hover:bg-slate-800/10 transition-colors">
                {/* Jira ID Link */}
                <td className="px-6 py-4 text-sm font-bold text-white">
                  <Link 
                    href={`/jiras/${row.jira_id}`}
                    className="text-blue-400 hover:text-blue-300 hover:underline transition-colors font-mono"
                  >
                    {row.jira_id}
                  </Link>
                </td>

                {/* Grid Cells for each target Folder */}
                {folders_list.map((folder) => {
                  const cell = row.folders.find((f) => f.folder_name === folder);
                  const isMerged = cell?.is_merged ?? false;
                  
                  return (
                    <td key={folder} className="px-4 py-4 text-center">
                      <div className="flex justify-center">
                        {isMerged ? (
                          <div 
                            className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-500/10 border border-emerald-500/25 text-emerald-400"
                            title={`Merged: ${cell?.merge_date ? formatDate(cell.merge_date) : 'N/A'}`}
                          >
                            <CheckCircle className="h-4.5 w-4.5" />
                          </div>
                        ) : (
                          <div 
                            className="flex h-7 w-7 items-center justify-center rounded-lg bg-rose-500/10 border border-rose-500/25 text-rose-400"
                            title="Missing merge"
                          >
                            <XCircle className="h-4.5 w-4.5" />
                          </div>
                        )}
                      </div>
                    </td>
                  );
                })}

                {/* Coverage bar */}
                <td className="px-6 py-4 text-sm font-medium">
                  <div className="flex items-center gap-3">
                    <span className="w-10 text-right font-mono font-bold text-gray-300">
                      {row.coverage_pct.toFixed(0)}%
                    </span>
                    <Progress value={row.coverage_pct} color="dynamic" className="h-1.5 flex-1 min-w-[80px]" />
                  </div>
                </td>

                {/* Status Badge */}
                <td className="px-6 py-4 text-center">
                  <Badge className={cn("font-bold font-mono text-[10px]", getStatusColorClass(row.status))}>
                    {row.status}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
