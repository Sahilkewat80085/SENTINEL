'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import PageContainer from '@/components/layout/PageContainer';
import TimelineView from '@/components/data/TimelineView';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import { apiService } from '@/lib/api';
import { JiraDetail, Repository } from '@/lib/types';
import { useFilterStore } from '@/stores/filterStore';
import { formatDate, getStatusColorClass } from '@/lib/utils';
import { ArrowLeft, Clock, User, GitCommit, FolderClosed, Calendar } from 'lucide-react';
import Skeleton from '@/components/ui/Skeleton';

export default function JiraDetailPage() {
  const router = useRouter();
  const { id } = useParams() as { id: string };
  const { selectedRepoId, repositories } = useFilterStore();
  const [detail, setDetail] = useState<JiraDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    const fetchDetail = async () => {
      setIsLoading(true);
      try {
        const res = await apiService.jiras.get(id);
        setDetail(res);
      } catch (err) {
        console.error('Failed to fetch Jira detail', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchDetail();
  }, [id]);

  const currentRepo = repositories.find(r => r.id === selectedRepoId);
  const totalFolders = currentRepo?.folders.length || 1;
  const mergedCount = detail?.summary.touched_folders.length || 0;
  const coveragePct = (mergedCount / totalFolders) * 100;

  return (
    <PageContainer
      title={`Ticket: ${id}`}
      subtitle={`Commit propagation and release timeline for ticket ${id}`}
      breadcrumbs={[
        { name: 'Jiras', href: '/jiras' },
        { name: id }
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
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="lg:col-span-1">
            <Skeleton className="h-80 rounded-xl" variant="rect" />
          </div>
          <div className="lg:col-span-2">
            <Skeleton className="h-96 rounded-xl" variant="rect" />
          </div>
        </div>
      ) : !detail ? (
        <div className="rounded-xl border border-card-border bg-card p-12 text-center text-sm font-semibold text-gray-500">
          Jira ticket details could not be found.
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* 1. Summary Card */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle>Ticket Summary</CardTitle>
                <CardDescription>Aggregation KPIs for this ticket</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Status Badge */}
                <div className="flex justify-between items-center text-sm">
                  <span className="font-semibold text-gray-400">Activity Status:</span>
                  <Badge className={cn("font-bold font-mono text-[10px]", getStatusColorClass(detail.summary.status))}>
                    {detail.summary.status}
                  </Badge>
                </div>

                {/* Folder Coverage Metrics */}
                <div className="flex justify-between items-center text-sm">
                  <span className="font-semibold text-gray-400">Folder Coverage:</span>
                  <span className="font-bold text-white font-mono">
                    {mergedCount} / {totalFolders} folders ({coveragePct.toFixed(0)}%)
                  </span>
                </div>

                <div className="flex justify-between items-center text-sm">
                  <span className="font-semibold text-gray-400">Commits Count:</span>
                  <span className="font-bold text-white font-mono flex items-center gap-1">
                    <GitCommit className="h-4 w-4 text-gray-500" />
                    {detail.summary.commit_count}
                  </span>
                </div>

                <div className="flex justify-between items-center text-sm">
                  <span className="font-semibold text-gray-400">Contributing Authors:</span>
                  <span className="font-bold text-white font-mono flex items-center gap-1">
                    <User className="h-4 w-4 text-gray-500" />
                    {detail.summary.author_count}
                  </span>
                </div>

                <hr className="border-card-border/40" />

                {/* Date block */}
                <div className="space-y-2.5">
                  <div className="text-xs">
                    <p className="font-semibold text-gray-400 mb-0.5">First Committed:</p>
                    <p className="font-bold text-white flex items-center gap-1">
                      <Calendar className="h-3.5 w-3.5 text-gray-500" />
                      {formatDate(detail.summary.first_seen)}
                    </p>
                  </div>
                  <div className="text-xs">
                    <p className="font-semibold text-gray-400 mb-0.5">Last Activity:</p>
                    <p className="font-bold text-white flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5 text-gray-500" />
                      {formatDate(detail.summary.last_updated)}
                    </p>
                  </div>
                </div>

                <hr className="border-card-border/40" />

                {/* List of merged folders */}
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1">
                    <FolderClosed className="h-3.5 w-3.5 text-gray-500" />
                    Merged Folders
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {detail.summary.touched_folders.map(f => (
                      <Badge key={f} variant={f === 'vanilla' ? 'default' : 'info'} className="text-[10px] font-mono font-bold">
                        {f}
                      </Badge>
                    ))}
                    {detail.summary.touched_folders.length === 0 && (
                      <span className="text-xs text-gray-500 italic">No folder targets merged</span>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 2. Timeline view Column */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Commit Propagation Timeline</CardTitle>
                <CardDescription>Chronological sequence of commit ingestion across config folders</CardDescription>
              </CardHeader>
              <CardContent className="h-[480px] overflow-y-auto">
                <TimelineView timeline={detail.timeline} />
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </PageContainer>
  );
}
