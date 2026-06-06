'use client';

import React, { useEffect, useState } from 'react';
import PageContainer from '@/components/layout/PageContainer';
import FilterBar from '@/components/data/FilterBar';
import SearchInput from '@/components/data/SearchInput';
import DataTable from '@/components/data/DataTable';
import Badge from '@/components/ui/Badge';
import { apiService } from '@/lib/api';
import { JiraSummary } from '@/lib/types';
import { useFilterStore } from '@/stores/filterStore';
import { formatDate, getStatusColorClass } from '@/lib/utils';
import Link from 'next/link';
import { Eye } from 'lucide-react';

export default function JirasPage() {
  const { selectedRepoId } = useFilterStore();
  const [jiras, setJiras] = useState<JiraSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  // Debounced search query
  const [debouncedSearch, setDebouncedSearch] = useState('');

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(searchQuery);
      setPage(1);
    }, 400);
    return () => clearTimeout(handler);
  }, [searchQuery]);

  useEffect(() => {
    if (!selectedRepoId) return;

    const fetchJiras = async () => {
      setIsLoading(true);
      try {
        const res = await apiService.jiras.list(page, 15, statusFilter || undefined, debouncedSearch || undefined);
        setJiras(res.items);
        setTotal(res.total);
      } catch (err) {
        console.error('Failed to fetch Jiras', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchJiras();
  }, [selectedRepoId, page, statusFilter, debouncedSearch]);

  const columns = [
    {
      key: 'jira_id',
      header: 'Jira ID',
      render: (row: JiraSummary) => (
        <span className="font-bold font-mono text-white">{row.jira_id}</span>
      ),
    },
    {
      key: 'commit_count',
      header: 'Commits',
      render: (row: JiraSummary) => (
        <span className="font-semibold font-mono">{row.commit_count}</span>
      ),
    },
    {
      key: 'author_count',
      header: 'Authors',
      render: (row: JiraSummary) => (
        <span className="font-semibold font-mono">{row.author_count}</span>
      ),
    },
    {
      key: 'first_seen',
      header: 'First Committed',
      render: (row: JiraSummary) => formatDate(row.first_seen),
    },
    {
      key: 'last_updated',
      header: 'Last Updated',
      render: (row: JiraSummary) => formatDate(row.last_updated),
    },
    {
      key: 'touched_folders',
      header: 'Target Folders',
      render: (row: JiraSummary) => (
        <div className="flex flex-wrap gap-1 max-w-[240px]">
          {row.touched_folders.map(f => (
            <Badge key={f} variant={f === 'vanilla' ? 'default' : 'info'} className="text-[9px] font-mono font-bold">
              {f}
            </Badge>
          ))}
          {row.touched_folders.length === 0 && <span className="text-gray-500 italic">None</span>}
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Activity Status',
      render: (row: JiraSummary) => (
        <Badge className={cn("font-bold text-[10px] font-mono", getStatusColorClass(row.status))}>
          {row.status}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row: JiraSummary) => (
        <Link 
          href={`/jiras/${row.jira_id}`}
          className="inline-flex items-center gap-1.5 rounded-lg border border-card-border px-3 py-1.5 text-xs font-semibold text-gray-400 hover:text-white hover:bg-card-border transition-all"
        >
          <Eye className="h-3.5 w-3.5" />
          View
        </Link>
      ),
    },
  ];

  return (
    <PageContainer
      title="Jira Ticket Explorer"
      subtitle="Grouped commit histories and environment coverage metrics indexed by issue key"
      breadcrumbs={[{ name: 'Jiras' }]}
    >
      {/* Search and Filters Bar */}
      <FilterBar>
        <SearchInput 
          onSearchChange={setSearchQuery} 
          placeholder="Search Jira ID, keys, or folders..." 
          containerClassName="max-w-md"
        />

        <div className="flex items-center gap-2">
          <label htmlFor="status-select" className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Status:
          </label>
          <select
            id="status-select"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="rounded-lg border border-card-border bg-card px-3 py-2 text-sm font-semibold text-white focus:border-blue-500 focus:outline-none"
          >
            <option value="">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="STALE">Stale</option>
            <option value="DORMANT">Dormant</option>
            <option value="ARCHIVED">Archived</option>
          </select>
        </div>
      </FilterBar>

      {/* Main Table view */}
      <DataTable 
        columns={columns} 
        data={jiras} 
        isLoading={isLoading} 
      />

      {/* Pagination controls */}
      {total > 15 && (
        <div className="mt-4 flex items-center justify-between">
          <p className="text-xs font-semibold text-gray-500">
            Showing {(page - 1) * 15 + 1} to {Math.min(page * 15, total)} of {total} Jiras
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
    </PageContainer>
  );
}
