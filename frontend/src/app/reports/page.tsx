'use client';

import React, { useEffect, useState } from 'react';
import PageContainer from '@/components/layout/PageContainer';
import { apiService } from '@/lib/api';
import { useFilterStore } from '@/stores/filterStore';
import { formatDate, formatDistanceToNow } from '@/lib/utils';
import { FileSpreadsheet, FileText, Download, Plus, RefreshCw, CheckCircle2, Clock, AlertCircle, Loader2 } from 'lucide-react';
import Badge from '@/components/ui/Badge';
import Skeleton from '@/components/ui/Skeleton';
import { cn } from '@/lib/utils';

interface ReportRecord {
  id: string;
  repository_id: string;
  report_type: 'EXCEL' | 'PDF';
  status: 'PENDING' | 'GENERATING' | 'COMPLETE' | 'FAILED';
  filename?: string;
  file_size_bytes?: number;
  generated_at?: string;
  created_at: string;
  config?: Record<string, any>;
}

const StatusBadge = ({ status }: { status: string }) => {
  switch (status) {
    case 'COMPLETE': return <Badge variant="success" className="text-[10px] font-mono font-bold">Complete</Badge>;
    case 'GENERATING': return <Badge variant="warning" className="text-[10px] font-mono font-bold animate-pulse">Generating…</Badge>;
    case 'PENDING': return <Badge variant="info" className="text-[10px] font-mono font-bold">Pending</Badge>;
    case 'FAILED': return <Badge variant="error" className="text-[10px] font-mono font-bold">Failed</Badge>;
    default: return <Badge className="text-[10px]">{status}</Badge>;
  }
};

const StatusIcon = ({ status }: { status: string }) => {
  switch (status) {
    case 'COMPLETE': return <CheckCircle2 className="h-4 w-4 text-emerald-400" />;
    case 'GENERATING': return <Loader2 className="h-4 w-4 text-amber-400 animate-spin" />;
    case 'PENDING': return <Clock className="h-4 w-4 text-blue-400" />;
    case 'FAILED': return <AlertCircle className="h-4 w-4 text-rose-400" />;
    default: return null;
  }
};

const formatBytes = (bytes?: number) => {
  if (!bytes) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

export default function ReportsPage() {
  const { selectedRepoId } = useFilterStore();
  const [reports, setReports] = useState<ReportRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState<'excel' | 'pdf' | null>(null);

  const fetchReports = async () => {
    setIsLoading(true);
    try {
      const data = await apiService.reports.list();
      setReports(data as ReportRecord[]);
    } catch (err) {
      console.error('Failed to fetch reports', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, [selectedRepoId]);

  const handleGenerate = async (type: 'excel' | 'pdf') => {
    if (!selectedRepoId) return;
    setIsGenerating(type);
    try {
      if (type === 'excel') {
        await apiService.reports.generateExcel(selectedRepoId);
      } else {
        await apiService.reports.generatePdf(selectedRepoId);
      }
      // Poll for completion after a short delay
      setTimeout(fetchReports, 1500);
    } catch (err) {
      alert(`Failed to trigger ${type.toUpperCase()} generation`);
    } finally {
      setIsGenerating(null);
    }
  };

  const downloadableReports = reports.filter(r => r.status === 'COMPLETE');
  const pendingReports = reports.filter(r => r.status !== 'COMPLETE');

  return (
    <PageContainer
      title="Report Builder"
      subtitle="Generate compliance-ready Excel and PDF governance reports for stakeholders"
      breadcrumbs={[{ name: 'Reports' }]}
      action={
        <button
          onClick={fetchReports}
          className="inline-flex items-center gap-1.5 rounded-lg border border-card-border px-3.5 py-1.5 text-sm font-semibold text-gray-400 hover:text-white hover:bg-card-border transition-all"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </button>
      }
    >
      {/* Generate Report Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 mb-8">
        {/* Excel Card */}
        <div className="relative overflow-hidden rounded-2xl border border-emerald-500/20 bg-gradient-to-br from-emerald-950/40 to-[#0d1526]/80 p-6">
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent pointer-events-none" />
          <div className="relative">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-500/15 border border-emerald-500/25">
                <FileSpreadsheet className="h-5 w-5 text-emerald-400" />
              </div>
              <div>
                <p className="font-bold text-white">Excel Report</p>
                <p className="text-xs text-gray-500">9-Sheet Workbook (.xlsx)</p>
              </div>
            </div>
            <ul className="text-xs text-gray-400 space-y-1.5 mb-5">
              {['Jira Coverage Matrix', 'Folder Health Rankings', 'Merge Delay Analysis', 'Content Drift Report', 'Violation Log', 'Trend Snapshots', 'Commit Activity', 'Governance Score Summary', 'Audit Trail'].map(item => (
                <li key={item} className="flex items-center gap-2">
                  <span className="h-1 w-1 rounded-full bg-emerald-400 flex-shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
            <button
              onClick={() => handleGenerate('excel')}
              disabled={isGenerating !== null || !selectedRepoId}
              className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-bold text-white hover:bg-emerald-700 disabled:opacity-50 transition-all shadow-lg shadow-emerald-900/30"
            >
              {isGenerating === 'excel' ? (
                <><Loader2 className="h-4 w-4 animate-spin" />Generating…</>
              ) : (
                <><Plus className="h-4 w-4" />Generate Excel Report</>
              )}
            </button>
          </div>
        </div>

        {/* PDF Card */}
        <div className="relative overflow-hidden rounded-2xl border border-rose-500/20 bg-gradient-to-br from-rose-950/40 to-[#0d1526]/80 p-6">
          <div className="absolute inset-0 bg-gradient-to-br from-rose-500/5 to-transparent pointer-events-none" />
          <div className="relative">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-rose-500/15 border border-rose-500/25">
                <FileText className="h-5 w-5 text-rose-400" />
              </div>
              <div>
                <p className="font-bold text-white">PDF Executive Report</p>
                <p className="text-xs text-gray-500">Executive Summary (.pdf)</p>
              </div>
            </div>
            <ul className="text-xs text-gray-400 space-y-1.5 mb-5">
              {['Governance Score Overview', 'Chart Visualizations', 'Critical Violations Summary', 'Trend Analysis Graphs', 'Folder Health Matrix', 'Coverage Heatmap', 'Compliance Status', 'Stakeholder-ready Layout', 'Branded PDF Export'].map(item => (
                <li key={item} className="flex items-center gap-2">
                  <span className="h-1 w-1 rounded-full bg-rose-400 flex-shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
            <button
              onClick={() => handleGenerate('pdf')}
              disabled={isGenerating !== null || !selectedRepoId}
              className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-rose-600 px-4 py-2.5 text-sm font-bold text-white hover:bg-rose-700 disabled:opacity-50 transition-all shadow-lg shadow-rose-900/30"
            >
              {isGenerating === 'pdf' ? (
                <><Loader2 className="h-4 w-4 animate-spin" />Generating…</>
              ) : (
                <><Plus className="h-4 w-4" />Generate PDF Report</>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Reports List */}
      <div className="rounded-2xl border border-white/8 bg-gradient-to-br from-[#111726]/80 to-[#0d1526]/80 backdrop-blur-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-white/8 flex items-center justify-between">
          <h3 className="text-sm font-bold text-white">Report History</h3>
          <span className="text-xs text-gray-500">{reports.length} total reports</span>
        </div>

        {isLoading ? (
          <div className="p-5 space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-14 rounded-xl" variant="rect" />
            ))}
          </div>
        ) : reports.length === 0 ? (
          <div className="py-16 text-center">
            <FileSpreadsheet className="h-10 w-10 text-gray-700 mx-auto mb-3" />
            <p className="text-sm font-semibold text-gray-500">No reports generated yet</p>
            <p className="text-xs text-gray-600 mt-1">Use the cards above to generate your first report</p>
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {reports.map((report) => (
              <div key={report.id} className="flex items-center gap-4 px-5 py-3.5 hover:bg-white/2 transition-colors">
                <div className={cn(
                  "flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg",
                  report.report_type === 'EXCEL' ? "bg-emerald-500/10 border border-emerald-500/20" : "bg-rose-500/10 border border-rose-500/20"
                )}>
                  {report.report_type === 'EXCEL' ? (
                    <FileSpreadsheet className="h-4 w-4 text-emerald-400" />
                  ) : (
                    <FileText className="h-4 w-4 text-rose-400" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-white truncate">
                    {report.filename || `${report.report_type} Report`}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {formatDistanceToNow(report.created_at)} · {formatBytes(report.file_size_bytes)}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <StatusBadge status={report.status} />
                  {report.status === 'COMPLETE' && (
                    <a
                      href={apiService.reports.downloadUrl(report.id)}
                      download
                      className="inline-flex items-center gap-1.5 rounded-lg border border-blue-500/30 bg-blue-500/10 px-3 py-1.5 text-xs font-bold text-blue-400 hover:text-blue-300 hover:border-blue-400/40 transition-all"
                    >
                      <Download className="h-3.5 w-3.5" />
                      Download
                    </a>
                  )}
                  {(report.status === 'GENERATING' || report.status === 'PENDING') && (
                    <StatusIcon status={report.status} />
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </PageContainer>
  );
}
