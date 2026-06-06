'use client';

import React, { useEffect, useState } from 'react';
import PageContainer from '@/components/layout/PageContainer';
import DataTable from '@/components/data/DataTable';
import Badge from '@/components/ui/Badge';
import { Card, CardContent } from '@/components/ui/Card';
import { apiService } from '@/lib/api';
import { DriftReport, ContentVerificationResult } from '@/lib/types';
import { useFilterStore } from '@/stores/filterStore';
import { formatPercent, getStatusColorClass } from '@/lib/utils';
import { Binary, CheckCircle, FileWarning, Eye, HelpCircle } from 'lucide-react';
import Skeleton from '@/components/ui/Skeleton';
import Modal from '@/components/ui/Modal';
import KPICard from '@/components/dashboard/KPICard';

export default function ContentPage() {
  const { selectedRepoId } = useFilterStore();
  const [report, setReport] = useState<DriftReport | null>(null);
  const [summary, setSummary] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Selected file for detail verification modal
  const [selectedFile, setSelectedFile] = useState<ContentVerificationResult | null>(null);

  useEffect(() => {
    if (!selectedRepoId) return;

    const fetchContentReport = async () => {
      setIsLoading(true);
      try {
        const [reportRes, summaryRes] = await Promise.all([
          apiService.content.getDriftReport(),
          apiService.content.getSummary()
        ]);
        setReport(reportRes);
        setSummary(summaryRes);
      } catch (err) {
        console.error('Failed to fetch content drift report', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchContentReport();
  }, [selectedRepoId]);

  const columns = [
    {
      key: 'file_path',
      header: 'File Path',
      render: (row: ContentVerificationResult) => (
        <span className="font-mono text-xs text-white max-w-[400px] block truncate" title={row.file_path}>
          {row.file_path}
        </span>
      ),
    },
    {
      key: 'drift_score',
      header: 'Drift Score',
      render: (row: ContentVerificationResult) => (
        <span className="font-mono font-bold text-white">
          {row.drift_score.toFixed(2)}
        </span>
      ),
    },
    {
      key: 'divergent_folders',
      header: 'Divergent Folders',
      render: (row: ContentVerificationResult) => (
        <div className="flex flex-wrap gap-1 max-w-[240px]">
          {row.divergent_folders.map(f => (
            <Badge key={f} variant="error" className="text-[9px] font-mono font-bold">
              {f}
            </Badge>
          ))}
          {row.divergent_folders.length === 0 && (
            <span className="text-emerald-400 text-xs font-semibold">None (Identical)</span>
          )}
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Verification Status',
      render: (row: ContentVerificationResult) => (
        <Badge className={cn("font-bold text-[10px] font-mono", getStatusColorClass(row.status))}>
          {row.status}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row: ContentVerificationResult) => (
        <button
          onClick={() => setSelectedFile(row)}
          className="inline-flex items-center gap-1.5 rounded-lg border border-card-border px-3 py-1.5 text-xs font-semibold text-gray-400 hover:text-white hover:bg-card-border transition-all"
        >
          <Eye className="h-3.5 w-3.5" />
          Compare Hashes
        </button>
      ),
    },
  ];

  return (
    <PageContainer
      title="Content Verification & Drift Analysis"
      subtitle="Deep-dive SHA256 file consistency auditing across customer deployment folders"
      breadcrumbs={[{ name: 'Content Drift' }]}
    >
      {/* 1. Summary Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-6">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, idx) => (
            <Skeleton key={idx} className="h-28 rounded-xl" variant="rect" />
          ))
        ) : (
          <>
            <KPICard
              title="Verified Files Count"
              value={summary?.total_files ?? 0}
              icon={Binary}
              color="blue"
              description="Total replicated files analyzed"
            />
            <KPICard
              title="Identical Files"
              value={summary?.identical_count ?? 0}
              icon={CheckCircle}
              color="emerald"
              description="Files with matching SHA256 hashes"
            />
            <KPICard
              title="Drifted Files"
              value={summary?.drifted_count ?? 0}
              icon={FileWarning}
              color={summary?.drifted_count && summary.drifted_count > 0 ? "rose" : "blue"}
              description="Files with content mismatches"
            />
            <KPICard
              title="Overall Drift Index"
              value={formatPercent((summary?.overall_drift_score ?? 0) * 100)}
              icon={HelpCircle}
              color="amber"
              description="Mean divergence ratio"
            />
          </>
        )}
      </div>

      {/* 2. Main Drift Table */}
      <DataTable
        columns={columns}
        data={report?.drifted_files || []}
        isLoading={isLoading}
      />

      {/* 3. Mismatched Hashes Modal */}
      <Modal
        isOpen={selectedFile !== null}
        onClose={() => setSelectedFile(null)}
        title="Compare SHA256 Hashes"
        footer={
          <button
            onClick={() => setSelectedFile(null)}
            className="rounded-lg border border-card-border px-4 py-2 text-sm font-semibold text-gray-400 hover:bg-card-border hover:text-white transition-colors"
          >
            Close
          </button>
        }
      >
        {selectedFile && (
          <div className="space-y-4">
            <div className="border-b border-card-border/40 pb-3">
              <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">File Path</h4>
              <p className="mt-1.5 text-xs text-white font-mono break-all leading-relaxed bg-[#0d1322]/40 p-2 rounded border border-card-border/50">
                {selectedFile.file_path}
              </p>
            </div>

            <div className="space-y-3">
              <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">
                Folder Mappings & Content Hashes
              </h4>
              
              <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                {Object.entries(selectedFile.folder_hashes).map(([folder, hash]) => {
                  const isDivergent = selectedFile.divergent_folders.includes(folder);
                  const fileSize = selectedFile.file_sizes[folder];
                  return (
                    <div 
                      key={folder}
                      className={cn(
                        "rounded-lg border p-3 flex flex-col gap-1 text-xs",
                        isDivergent 
                          ? "border-rose-500/25 bg-rose-500/5" 
                          : "border-card-border bg-[#111726]/40"
                      )}
                    >
                      <div className="flex justify-between items-center font-bold">
                        <span className="font-mono text-white text-sm">{folder}</span>
                        {isDivergent ? (
                          <Badge variant="error" className="text-[8px] font-mono py-0.5">Divergent</Badge>
                        ) : (
                          <Badge variant="success" className="text-[8px] font-mono py-0.5">Majority MATCH</Badge>
                        )}
                      </div>
                      <p className="font-mono text-gray-400 break-all bg-black/20 p-1.5 rounded mt-1">
                        {hash}
                      </p>
                      {fileSize !== undefined && (
                        <p className="text-[10px] text-gray-500 font-semibold mt-1">
                          File Size: {(fileSize / 1024).toFixed(1)} KB
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </PageContainer>
  );
}
