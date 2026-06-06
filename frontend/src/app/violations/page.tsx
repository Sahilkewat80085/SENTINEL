'use client';

import React, { useEffect, useState } from 'react';
import PageContainer from '@/components/layout/PageContainer';
import FilterBar from '@/components/data/FilterBar';
import DataTable from '@/components/data/DataTable';
import Badge from '@/components/ui/Badge';
import Modal from '@/components/ui/Modal';
import { apiService } from '@/lib/api';
import { RuleViolation, ViolationSummary } from '@/lib/types';
import { useFilterStore } from '@/stores/filterStore';
import { formatDate, getSeverityColorClass, formatDistanceToNow } from '@/lib/utils';
import { ShieldAlert, CheckSquare, MessageSquare, AlertCircle, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import KPICard from '@/components/dashboard/KPICard';
import Skeleton from '@/components/ui/Skeleton';

export default function ViolationsPage() {
  const { selectedRepoId } = useFilterStore();
  const [violations, setViolations] = useState<RuleViolation[]>([]);
  const [summary, setSummary] = useState<ViolationSummary | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [severityFilter, setSeverityFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [isAckFilter, setIsAckFilter] = useState<boolean | undefined>(false); // default to unacknowledged
  const [isLoading, setIsLoading] = useState(true);

  // Acknowledge Dialog State
  const [selectedViolation, setSelectedViolation] = useState<RuleViolation | null>(null);
  const [ackNote, setAckNote] = useState('');
  const [ackLoading, setAckLoading] = useState(false);
  
  // Re-evaluation triggers
  const [evalLoading, setEvalLoading] = useState(false);

  const fetchData = React.useCallback(async () => {
    if (!selectedRepoId) return;
    setIsLoading(true);
    try {
      const [violationsRes, summaryRes] = await Promise.all([
        apiService.violations.list(
          page,
          15,
          severityFilter || undefined,
          categoryFilter || undefined,
          isAckFilter
        ),
        apiService.violations.getSummary()
      ]);
      setViolations(violationsRes.items);
      setTotal(violationsRes.total);
      setSummary(summaryRes);
    } catch (err) {
      console.error('Failed to fetch violations', err);
    } finally {
      setIsLoading(false);
    }
  }, [selectedRepoId, page, severityFilter, categoryFilter, isAckFilter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleAcknowledge = async () => {
    if (!selectedViolation) return;
    setAckLoading(true);
    try {
      await apiService.violations.acknowledge(selectedViolation.id, ackNote);
      setSelectedViolation(null);
      setAckNote('');
      fetchData();
    } catch (err) {
      alert('Failed to acknowledge violation');
    } finally {
      setAckLoading(false);
    }
  };

  const handleReevaluate = async () => {
    setEvalLoading(true);
    try {
      await apiService.violations.evaluate();
      fetchData();
    } catch (err) {
      alert('Failed to trigger re-evaluation');
    } finally {
      setEvalLoading(false);
    }
  };

  const columns = [
    {
      key: 'rule_id',
      header: 'Rule ID',
      render: (row: RuleViolation) => (
        <span className="font-bold font-mono text-white text-sm">{row.rule_id}</span>
      ),
    },
    {
      key: 'severity',
      header: 'Severity',
      render: (row: RuleViolation) => (
        <Badge className={cn("font-bold font-mono text-[10px]", getSeverityColorClass(row.severity))}>
          {row.severity}
        </Badge>
      ),
    },
    {
      key: 'category',
      header: 'Category',
      render: (row: RuleViolation) => (
        <span className="text-gray-400 font-semibold text-xs capitalize">{row.category}</span>
      ),
    },
    {
      key: 'description',
      header: 'Description',
      render: (row: RuleViolation) => (
        <p className="max-w-[380px] text-sm font-medium text-gray-300 leading-relaxed">
          {row.description}
        </p>
      ),
    },
    {
      key: 'detected_at',
      header: 'Detected',
      render: (row: RuleViolation) => formatDistanceToNow(row.detected_at),
    },
    {
      key: 'is_acknowledged',
      header: 'Status',
      render: (row: RuleViolation) => (
        row.is_acknowledged ? (
          <Badge variant="success" className="text-[9px] font-mono font-bold">
            Resolved / Acknowledged
          </Badge>
        ) : (
          <Badge variant="error" className="text-[9px] font-mono font-bold animate-pulse">
            Active / Alerting
          </Badge>
        )
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row: RuleViolation) => (
        !row.is_acknowledged ? (
          <button
            onClick={() => setSelectedViolation(row)}
            className="inline-flex items-center gap-1.5 rounded-lg border border-card-border px-3 py-1.5 text-xs font-semibold text-gray-400 hover:text-emerald-400 hover:border-emerald-500/30 hover:bg-emerald-500/5 transition-all"
          >
            <CheckSquare className="h-3.5 w-3.5" />
            Resolve
          </button>
        ) : (
          <button
            onClick={() => setSelectedViolation(row)}
            className="inline-flex items-center gap-1.5 rounded-lg border border-card-border px-3 py-1.5 text-xs font-semibold text-gray-400 hover:text-white hover:bg-card-border transition-all"
          >
            Details
          </button>
        )
      ),
    },
  ];

  return (
    <PageContainer
      title="Governance Exception log"
      subtitle="Deterministic governance issues identified from folder matrix audits"
      breadcrumbs={[{ name: 'Violations' }]}
      action={
        <button
          onClick={handleReevaluate}
          disabled={evalLoading}
          className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3.5 py-1.5 text-sm font-semibold text-white shadow-md hover:bg-blue-700 disabled:opacity-50 transition-all glow-primary"
        >
          <RefreshCw className={cn("h-4 w-4", evalLoading && "animate-spin")} />
          Re-evaluate Rules
        </button>
      }
    >
      {/* 1. Summary cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-6">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, idx) => (
            <Skeleton key={idx} className="h-28 rounded-xl" variant="rect" />
          ))
        ) : (
          <>
            <KPICard
              title="Active Issues Count"
              value={summary?.unacknowledged_count ?? 0}
              icon={ShieldAlert}
              color={summary?.unacknowledged_count && summary.unacknowledged_count > 0 ? "rose" : "blue"}
              description="Alerting unacknowledged violations"
            />
            <KPICard
              title="Critical Violations"
              value={summary?.critical_count ?? 0}
              icon={AlertCircle}
              color="rose"
              description="Blocking governance regressions"
            />
            <KPICard
              title="High Severity Issues"
              value={summary?.high_count ?? 0}
              icon={AlertCircle}
              color="amber"
              description="Severe release readiness risks"
            />
            <KPICard
              title="Acknowledged Items"
              value={summary?.acknowledged_count ?? 0}
              icon={CheckSquare}
              color="emerald"
              description="Exceptions resolved with comments"
            />
          </>
        )}
      </div>

      {/* 2. Search and Filters Bar */}
      <FilterBar>
        {/* Status filter (Active vs Acknowledged) */}
        <div className="flex items-center gap-2">
          <label htmlFor="ack-select" className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Status:
          </label>
          <select
            id="ack-select"
            value={isAckFilter === undefined ? 'all' : isAckFilter.toString()}
            onChange={(e) => {
              const val = e.target.value;
              setIsAckFilter(val === 'all' ? undefined : val === 'true');
              setPage(1);
            }}
            className="rounded-lg border border-card-border bg-card px-3 py-2 text-sm font-semibold text-white focus:border-blue-500 focus:outline-none"
          >
            <option value="false">Active Only</option>
            <option value="true">Acknowledged Only</option>
            <option value="all">All Exceptions</option>
          </select>
        </div>

        {/* Severity filter */}
        <div className="flex items-center gap-2">
          <label htmlFor="severity-select" className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Severity:
          </label>
          <select
            id="severity-select"
            value={severityFilter}
            onChange={(e) => {
              setSeverityFilter(e.target.value);
              setPage(1);
            }}
            className="rounded-lg border border-card-border bg-card px-3 py-2 text-sm font-semibold text-white focus:border-blue-500 focus:outline-none"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>

        {/* Category filter */}
        <div className="flex items-center gap-2">
          <label htmlFor="category-select" className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Category:
          </label>
          <select
            id="category-select"
            value={categoryFilter}
            onChange={(e) => {
              setCategoryFilter(e.target.value);
              setPage(1);
            }}
            className="rounded-lg border border-card-border bg-card px-3 py-2 text-sm font-semibold text-white focus:border-blue-500 focus:outline-none"
          >
            <option value="">All Categories</option>
            <option value="coverage">Coverage</option>
            <option value="delay">Delay</option>
            <option value="consistency">Consistency</option>
            <option value="propagation">Propagation</option>
          </select>
        </div>
      </FilterBar>

      {/* 3. Main Exceptions Table */}
      <DataTable
        columns={columns}
        data={violations}
        isLoading={isLoading}
      />

      {/* Pagination controls */}
      {total > 15 && (
        <div className="mt-4 flex items-center justify-between">
          <p className="text-xs font-semibold text-gray-500">
            Showing {(page - 1) * 15 + 1} to {Math.min(page * 15, total)} of {total} Exceptions
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(p - 1, 1))}
              disabled={page === 1}
              className="rounded-lg border border-card-border bg-card px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-card-border disabled:opacity-40 transition-colors"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={page * 15 >= total}
              className="rounded-lg border border-card-border bg-card px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-card-border disabled:opacity-40 transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Acknowledge/Detail Dialog Modal */}
      <Modal
        isOpen={selectedViolation !== null}
        onClose={() => setSelectedViolation(null)}
        title={selectedViolation?.is_acknowledged ? "Violation Details" : "Acknowledge Exception"}
        footer={
          selectedViolation?.is_acknowledged ? (
            <button
              onClick={() => setSelectedViolation(null)}
              className="rounded-lg border border-card-border px-4 py-2 text-sm font-semibold text-gray-400 hover:bg-card-border hover:text-white transition-colors"
            >
              Close
            </button>
          ) : (
            <>
              <button
                onClick={() => setSelectedViolation(null)}
                className="rounded-lg border border-card-border px-4 py-2 text-sm font-semibold text-gray-400 hover:bg-card-border hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleAcknowledge}
                disabled={ackLoading}
                className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50 transition-colors glow-success"
              >
                {ackLoading ? 'Resolving...' : 'Acknowledge'}
              </button>
            </>
          )
        }
      >
        {selectedViolation && (
          <div className="space-y-4">
            <div className="rounded-lg border border-card-border bg-[#111726]/40 p-4">
              <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Violation Description</h4>
              <p className="mt-1.5 text-sm text-white font-medium">{selectedViolation.description}</p>
            </div>

            <div className="grid grid-cols-2 gap-4 text-xs">
              <div>
                <p className="font-bold text-gray-400 uppercase">Severity</p>
                <p className="mt-1 text-sm font-bold text-white uppercase">{selectedViolation.severity}</p>
              </div>
              <div>
                <p className="font-bold text-gray-400 uppercase">Rule Category</p>
                <p className="mt-1 text-sm font-bold text-white capitalize">{selectedViolation.category}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 text-xs">
              <div>
                <p className="font-bold text-gray-400 uppercase">Jira Ticket</p>
                <p className="mt-1 text-sm font-bold text-white font-mono">{selectedViolation.jira_id || 'N/A'}</p>
              </div>
              <div>
                <p className="font-bold text-gray-400 uppercase">Target Folder</p>
                <p className="mt-1 text-sm font-bold text-white font-mono">{selectedViolation.folder_name || 'N/A'}</p>
              </div>
            </div>

            {selectedViolation.file_path && (
              <div className="text-xs">
                <p className="font-bold text-gray-400 uppercase">Affected File</p>
                <p className="mt-1 font-mono text-white break-all bg-black/20 p-2 rounded">{selectedViolation.file_path}</p>
              </div>
            )}

            {selectedViolation.is_acknowledged ? (
              <div className="rounded-lg border border-emerald-500/25 bg-emerald-500/5 p-4 space-y-2.5">
                <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Resolution Details</h4>
                <div className="text-xs grid grid-cols-2 gap-2 text-gray-300">
                  <div>
                    <span className="text-gray-500 font-semibold block">Acknowledged By:</span>
                    <span className="font-bold text-white">{selectedViolation.acknowledged_by}</span>
                  </div>
                  <div>
                    <span className="text-gray-500 font-semibold block">Resolved Date:</span>
                    <span className="font-bold text-white">{formatDate(selectedViolation.acknowledged_at)}</span>
                  </div>
                </div>
                <div className="text-xs">
                  <span className="text-gray-500 font-semibold block">Developer Note:</span>
                  <p className="mt-1 text-white font-medium italic">"{selectedViolation.acknowledge_note || 'No comments left.'}"</p>
                </div>
              </div>
            ) : (
              <div className="flex flex-col gap-1.5">
                <label htmlFor="ack-note" className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                  <MessageSquare className="h-3.5 w-3.5" />
                  Acknowledgement Justification
                </label>
                <textarea
                  id="ack-note"
                  rows={3}
                  value={ackNote}
                  onChange={(e) => setAckNote(e.target.value)}
                  placeholder="Provide context or explanation why this exception is accepted..."
                  className="w-full rounded-lg border border-card-border bg-slate-900/50 p-3 text-sm text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none"
                />
              </div>
            )}
          </div>
        )}
      </Modal>
    </PageContainer>
  );
}
