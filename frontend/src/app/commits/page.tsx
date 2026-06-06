'use client';

import React, { useEffect, useState } from 'react';
import PageContainer from '@/components/layout/PageContainer';
import FilterBar from '@/components/data/FilterBar';
import SearchInput from '@/components/data/SearchInput';
import DataTable from '@/components/data/DataTable';
import Badge from '@/components/ui/Badge';
import { apiService } from '@/lib/api';
import { Commit } from '@/lib/types';
import { useFilterStore } from '@/stores/filterStore';
import { formatDate, truncateSha } from '@/lib/utils';
import { GitCommit, User, Calendar, ExternalLink } from 'lucide-react';
import Modal from '@/components/ui/Modal';

export default function CommitsPage() {
  const { selectedRepoId } = useFilterStore();
  const [commits, setCommits] = useState<Commit[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [authorFilter, setAuthorFilter] = useState('');
  const [folderFilter, setFolderFilter] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  // Modal detail review state
  const [selectedSha, setSelectedSha] = useState<string | null>(null);
  const [commitDetail, setCommitDetail] = useState<any | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

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

    const fetchCommits = async () => {
      setIsLoading(true);
      try {
        const res = await apiService.commits.list(
          page,
          15,
          authorFilter || undefined,
          folderFilter || undefined,
          debouncedSearch || undefined
        );
        setCommits(res.items);
        setTotal(res.total);
      } catch (err) {
        console.error('Failed to fetch commits', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCommits();
  }, [selectedRepoId, page, authorFilter, folderFilter, debouncedSearch]);

  // Handle viewing specific commit details
  useEffect(() => {
    if (!selectedSha) {
      setCommitDetail(null);
      return;
    }
    const fetchDetail = async () => {
      setDetailLoading(true);
      try {
        const detailObj = await apiService.commits.get(selectedSha);
        setCommitDetail(detailObj);
      } catch (err) {
        console.error('Failed to fetch commit detail', err);
      } finally {
        setDetailLoading(false);
      }
    };
    fetchDetail();
  }, [selectedSha]);

  const columns = [
    {
      key: 'sha',
      header: 'SHA',
      render: (row: Commit) => (
        <span className="font-mono text-xs font-bold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
          {truncateSha(row.sha)}
        </span>
      ),
    },
    {
      key: 'author',
      header: 'Author',
      render: (row: Commit) => (
        <div className="flex flex-col">
          <span className="text-white text-sm font-semibold">{row.author.name}</span>
          <span className="text-xs text-gray-500 font-medium">{row.author.email}</span>
        </div>
      ),
    },
    {
      key: 'message',
      header: 'Commit Message',
      render: (row: Commit) => (
        <p className="max-w-[420px] text-sm font-medium text-gray-300 truncate" title={row.message}>
          {row.message}
        </p>
      ),
    },
    {
      key: 'commit_date',
      header: 'Committed At',
      render: (row: Commit) => formatDate(row.commit_date),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row: Commit) => (
        <button
          onClick={() => setSelectedSha(row.sha)}
          className="inline-flex items-center gap-1.5 rounded-lg border border-card-border px-3 py-1.5 text-xs font-semibold text-gray-400 hover:text-white hover:bg-card-border transition-all"
        >
          <ExternalLink className="h-3.5 w-3.5" />
          Details
        </button>
      ),
    },
  ];

  return (
    <PageContainer
      title="Repository Commit Log"
      subtitle="Complete chronological list of collected git commits and metadata mappings"
      breadcrumbs={[{ name: 'Commits' }]}
    >
      {/* Search and Filters Bar */}
      <FilterBar>
        <SearchInput 
          onSearchChange={setSearchQuery} 
          placeholder="Search commit messages, hashes, Jira ID..." 
          containerClassName="max-w-md"
        />

        <div className="flex items-center gap-2">
          <label htmlFor="folder-select" className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Folder:
          </label>
          <input
            id="folder-select"
            type="text"
            value={folderFilter}
            onChange={(e) => {
              setFolderFilter(e.target.value);
              setPage(1);
            }}
            placeholder="e.g. vanilla, MET..."
            className="rounded-lg border border-card-border bg-card px-3 py-2 text-sm font-semibold text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none"
          />
        </div>
      </FilterBar>

      {/* Main Table view */}
      <DataTable 
        columns={columns} 
        data={commits} 
        isLoading={isLoading} 
      />

      {/* Pagination controls */}
      {total > 15 && (
        <div className="mt-4 flex items-center justify-between">
          <p className="text-xs font-semibold text-gray-500">
            Showing {(page - 1) * 15 + 1} to {Math.min(page * 15, total)} of {total} Commits
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

      {/* Commit Detail Modal */}
      <Modal
        isOpen={selectedSha !== null}
        onClose={() => setSelectedSha(null)}
        title={`Commit: ${selectedSha ? truncateSha(selectedSha) : ''}`}
        footer={
          <button
            onClick={() => setSelectedSha(null)}
            className="rounded-lg border border-card-border px-4 py-2 text-sm font-semibold text-gray-400 hover:bg-card-border hover:text-white transition-colors"
          >
            Close
          </button>
        }
      >
        {detailLoading ? (
          <div className="space-y-4">
            <Skeleton className="h-6 w-1/3 rounded" variant="text" />
            <Skeleton className="h-20 w-full rounded" variant="rect" />
            <Skeleton className="h-10 w-full rounded" variant="rect" />
          </div>
        ) : !commitDetail ? (
          <p className="text-center text-sm text-gray-500 py-4">No commit details found.</p>
        ) : (
          <div className="space-y-4">
            <div className="border-b border-card-border/40 pb-3">
              <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Commit Message</h4>
              <p className="mt-1.5 text-sm text-white font-medium whitespace-pre-wrap leading-relaxed">
                {commitDetail.message}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Author</h4>
                <p className="mt-1 text-sm font-bold text-white">{commitDetail.author.name}</p>
                <p className="text-xs text-gray-500 font-semibold">{commitDetail.author.email}</p>
              </div>
              <div>
                <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Committed At</h4>
                <p className="mt-1 text-sm font-bold text-white flex items-center gap-1">
                  <Calendar className="h-4 w-4 text-gray-500" />
                  {formatDate(commitDetail.commit_date)}
                </p>
              </div>
            </div>

            {/* Mapped Jiras block */}
            <div className="pt-2">
              <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Mapped Jira Issues</h4>
              <div className="flex flex-wrap gap-1.5">
                {commitDetail.jiras.map((jira: string) => (
                  <Badge key={jira} className="font-mono font-bold text-xs text-blue-400 bg-blue-500/10 border-blue-500/20">
                    {jira}
                  </Badge>
                ))}
                {commitDetail.jiras.length === 0 && (
                  <span className="text-xs text-gray-500 italic">No tickets extracted</span>
                )}
              </div>
            </div>

            {/* Files changed list */}
            <div className="pt-2">
              <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">
                Files Changed ({commitDetail.files.length})
              </h4>
              <div className="max-h-48 overflow-y-auto rounded-lg border border-card-border bg-[#0d1322]/40 p-2 divide-y divide-card-border/30">
                {commitDetail.files.map((file: any, idx: number) => (
                  <div key={idx} className="py-2 flex items-center justify-between text-xs font-medium">
                    <span className="font-mono text-gray-300 truncate max-w-[280px]" title={file.file_path}>
                      {file.file_path}
                    </span>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {file.folder && (
                        <span className="font-mono font-bold text-[9px] text-gray-400 bg-slate-800 px-1.5 py-0.5 rounded">
                          {file.folder}
                        </span>
                      )}
                      <span className="text-emerald-400">+{file.additions}</span>
                      <span className="text-rose-400">-{file.deletions}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </PageContainer>
  );
}
