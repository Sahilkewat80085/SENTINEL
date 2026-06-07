'use client';

import React, { useEffect, useState } from 'react';
import PageContainer from '@/components/layout/PageContainer';
import DataTable from '@/components/data/DataTable';
import Badge from '@/components/ui/Badge';
import Progress from '@/components/ui/Progress';
import { apiService } from '@/lib/api';
import { FolderHealthResult } from '@/lib/types';
import { useFilterStore } from '@/stores/filterStore';
import { getClassificationColorClass, cn } from '@/lib/utils';
import Link from 'next/link';
import { Eye, ShieldAlert, Award, AlertCircle } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/Card';

export default function FoldersPage() {
  const { selectedRepoId } = useFilterStore();
  const [folders, setFolders] = useState<FolderHealthResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!selectedRepoId) return;

    const fetchFolders = async () => {
      setIsLoading(true);
      try {
        const res = await apiService.folders.list();
        // Sort folders by health score descending (highest health first)
        const sorted = [...res].sort((a, b) => b.health_score - a.health_score);
        setFolders(sorted);
      } catch (err) {
        console.error('Failed to fetch folders', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchFolders();
  }, [selectedRepoId]);

  const columns = [
    {
      key: 'rank',
      header: 'Rank',
      render: (row: FolderHealthResult) => {
        const idx = folders.findIndex(f => f.folder_name === row.folder_name);
        return <span className="font-bold font-mono text-white text-base">#{idx + 1}</span>;
      },
    },
    {
      key: 'folder_name',
      header: 'Folder Name',
      render: (row: FolderHealthResult) => (
        <span className="font-bold font-mono text-white text-sm">{row.folder_name}</span>
      ),
    },
    {
      key: 'coverage_score',
      header: 'Coverage (35%)',
      render: (row: FolderHealthResult) => (
        <div className="flex items-center gap-2">
          <span className="w-12 text-right font-mono font-bold">{row.coverage_score.toFixed(1)}%</span>
          <Progress value={row.coverage_score} color="dynamic" className="h-1.5 w-16" />
        </div>
      ),
    },
    {
      key: 'consistency_score',
      header: 'Consistency (30%)',
      render: (row: FolderHealthResult) => (
        <div className="flex items-center gap-2">
          <span className="w-12 text-right font-mono font-bold">{row.consistency_score.toFixed(1)}%</span>
          <Progress value={row.consistency_score} color="dynamic" className="h-1.5 w-16" />
        </div>
      ),
    },
    {
      key: 'timeliness_score',
      header: 'Timeliness (20%)',
      render: (row: FolderHealthResult) => (
        <div className="flex items-center gap-2">
          <span className="w-12 text-right font-mono font-bold">{row.timeliness_score.toFixed(1)}%</span>
          <Progress value={row.timeliness_score} color="dynamic" className="h-1.5 w-16" />
        </div>
      ),
    },
    {
      key: 'completeness_score',
      header: 'Completeness (15%)',
      render: (row: FolderHealthResult) => (
        <div className="flex items-center gap-2">
          <span className="w-12 text-right font-mono font-bold">{row.completeness_score.toFixed(1)}%</span>
          <Progress value={row.completeness_score} color="dynamic" className="h-1.5 w-16" />
        </div>
      ),
    },
    {
      key: 'health_score',
      header: 'Overall Health',
      render: (row: FolderHealthResult) => (
        <span className="font-extrabold font-mono text-white text-sm bg-blue-500/10 border border-blue-500/25 px-2.5 py-1 rounded-lg">
          {row.health_score.toFixed(1)}%
        </span>
      ),
    },
    {
      key: 'classification',
      header: 'Grade',
      render: (row: FolderHealthResult) => (
        <Badge className={cn("font-bold text-[10px] font-mono", getClassificationColorClass(row.classification))}>
          {row.classification}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row: FolderHealthResult) => (
        <Link 
          href={`/folders/${row.folder_name}`}
          className="inline-flex items-center gap-1.5 rounded-lg border border-card-border px-3 py-1.5 text-xs font-semibold text-gray-400 hover:text-white hover:bg-card-border transition-all"
        >
          <Eye className="h-3.5 w-3.5" />
          View
        </Link>
      ),
    },
  ];

  // Weakest and Strongest folders for stats
  const strongestFolder = folders[0];
  const weakestFolder = folders[folders.length - 1];

  return (
    <PageContainer
      title="Target Folders Overview"
      subtitle="Comprehensive health metrics, performance grades, and propagation delays mapped by customer configuration folder"
      breadcrumbs={[{ name: 'Folders' }]}
    >
      {/* Cards summary */}
      {!isLoading && folders.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-6">
          {/* Strongest folder widget */}
          <Card className="glow-success border-emerald-500/20 bg-emerald-500/5">
            <CardContent className="p-5 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1">
                  <Award className="h-4 w-4" /> Leading Folder
                </span>
                <h4 className="text-xl font-black text-white mt-1.5 font-mono">{strongestFolder.folder_name}</h4>
                <p className="text-xs text-gray-400 font-semibold mt-1">
                  Health score is {strongestFolder.health_score.toFixed(1)}% ({strongestFolder.classification})
                </p>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400 font-black text-xl border border-emerald-500/20 shadow-inner">
                A
              </div>
            </CardContent>
          </Card>

          {/* Weakest folder widget */}
          <Card className={cn(
            weakestFolder.health_score < 50 ? "glow-danger border-rose-500/20 bg-rose-500/5" : "glow-warning border-yellow-500/20 bg-yellow-500/5"
          )}>
            <CardContent className="p-5 flex items-center justify-between">
              <div>
                <span className={cn(
                  "text-xs font-bold uppercase tracking-wider flex items-center gap-1",
                  weakestFolder.health_score < 50 ? "text-rose-400" : "text-yellow-400"
                )}>
                  <ShieldAlert className="h-4 w-4" /> Attention Required
                </span>
                <h4 className="text-xl font-black text-white mt-1.5 font-mono">{weakestFolder.folder_name}</h4>
                <p className="text-xs text-gray-400 font-semibold mt-1">
                  Health score is {weakestFolder.health_score.toFixed(1)}% ({weakestFolder.classification})
                </p>
              </div>
              <div className={cn(
                "flex h-12 w-12 items-center justify-center rounded-xl font-black text-xl border shadow-inner",
                weakestFolder.health_score < 50 
                  ? "bg-rose-500/10 text-rose-400 border-rose-500/20" 
                  : "bg-yellow-500/10 text-yellow-400 border-yellow-500/20"
              )}>
                {weakestFolder.health_score >= 70 ? 'B' : weakestFolder.health_score >= 50 ? 'C' : 'F'}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main rankings Table */}
      <DataTable
        columns={columns}
        data={folders}
        isLoading={isLoading}
      />
    </PageContainer>
  );
}
