'use client';

import React from 'react';
import { JiraTimelineItem } from '@/lib/types';
import { formatDate, truncateSha } from '@/lib/utils';
import { GitCommit, Folder, User, Calendar } from 'lucide-react';
import Badge from '../ui/Badge';

interface TimelineViewProps {
  timeline: JiraTimelineItem[];
}

export default function TimelineView({ timeline }: TimelineViewProps) {
  if (timeline.length === 0) {
    return (
      <div className="rounded-xl border border-card-border bg-card p-12 text-center text-sm font-semibold text-gray-500">
        No commit records found on this timeline.
      </div>
    );
  }

  // Sort timeline chronologically by date
  const sortedTimeline = [...timeline].sort(
    (a, b) => new Date(a.commit_date).getTime() - new Date(b.commit_date).getTime()
  );

  return (
    <div className="relative pl-6 border-l-2 border-slate-800 space-y-8 ml-4 py-2">
      {sortedTimeline.map((item, idx) => (
        <div key={item.sha + idx} className="relative">
          {/* Node Icon Indicator */}
          <span className="absolute -left-[37px] top-1.5 flex h-7.5 w-7.5 items-center justify-center rounded-full border border-card-border bg-[#111726] text-blue-400 shadow-md">
            <GitCommit className="h-4 w-4" />
          </span>

          {/* Node details */}
          <div className="rounded-xl border border-card-border bg-card p-5 hover:border-slate-700 transition-all duration-150 shadow-md glow-primary">
            {/* Header: Commit SHA & Date */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-card-border/40 pb-3">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-blue-400 bg-blue-500/10 px-2.5 py-1 rounded border border-blue-500/20">
                  {truncateSha(item.sha)}
                </span>
                <span className="text-xs font-semibold text-gray-400 flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5" />
                  {formatDate(item.commit_date)}
                </span>
              </div>
              <div className="flex items-center gap-1 text-xs text-gray-400 font-semibold">
                <User className="h-3.5 w-3.5" />
                <span>{item.author_name}</span>
                <span className="text-gray-600">({item.author_email})</span>
              </div>
            </div>

            {/* Commit Message */}
            <p className="mt-3 text-sm font-medium text-gray-200 leading-relaxed">
              {item.message}
            </p>

            {/* Affected Folders and Files count */}
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-1.5 text-xs text-gray-400 font-semibold">
                <Folder className="h-3.5 w-3.5 text-gray-500" />
                <span>Target Folders:</span>
              </div>
              
              <div className="flex flex-wrap gap-1.5">
                {item.folders.map((folder) => (
                  <Badge 
                    key={folder}
                    variant={folder === 'vanilla' ? 'default' : 'info'}
                    className="font-mono font-bold text-[9px]"
                  >
                    {folder}
                  </Badge>
                ))}
                {item.folders.length === 0 && (
                  <span className="text-xs text-gray-500 italic">None matched</span>
                )}
              </div>

              <div className="ml-auto text-xs font-semibold text-gray-500">
                {item.files_count} {item.files_count === 1 ? 'file' : 'files'} changed
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
