'use client';

import React, { useEffect, useState } from 'react';
import PageContainer from '@/components/layout/PageContainer';
import FilterBar from '@/components/data/FilterBar';
import SearchInput from '@/components/data/SearchInput';
import CoverageMatrix from '@/components/data/CoverageMatrix';
import { apiService } from '@/lib/api';
import { CoverageMatrix as MatrixType } from '@/lib/types';
import { useFilterStore } from '@/stores/filterStore';

export default function CoveragePage() {
  const { selectedRepoId } = useFilterStore();
  const [matrix, setMatrix] = useState<MatrixType | undefined>(undefined);
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

    const fetchMatrix = async () => {
      setIsLoading(true);
      try {
        // Fetch matrix with filters
        const res = await apiService.coverage.getMatrix(page, 15, statusFilter || undefined);
        
        // Apply client-side search filtering on rows if search is active
        if (debouncedSearch) {
          const filteredRows = res.rows.filter(r => 
            r.jira_id.toLowerCase().includes(debouncedSearch.toLowerCase())
          );
          setMatrix({ ...res, rows: filteredRows });
        } else {
          setMatrix(res);
        }
      } catch (err) {
        console.error('Failed to fetch coverage matrix', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchMatrix();
  }, [selectedRepoId, page, statusFilter, debouncedSearch]);

  const totalRows = matrix?.rows.length || 0;

  return (
    <PageContainer
      title="Environment Coverage Matrix"
      subtitle="Comprehensive grid mapping Jira tickets against all customer configuration folders"
      breadcrumbs={[{ name: 'Coverage' }]}
    >
      {/* Search and Filters Bar */}
      <FilterBar>
        <SearchInput 
          onSearchChange={setSearchQuery} 
          placeholder="Filter matrix by Jira ID..." 
          containerClassName="max-w-md"
        />

        <div className="flex items-center gap-2">
          <label htmlFor="status-select" className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Merge Status:
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
            <option value="MERGED">Merged (100%)</option>
            <option value="PARTIAL">Partial (1-99%)</option>
            <option value="MISSING">Missing (0%)</option>
          </select>
        </div>
      </FilterBar>

      {/* Main Grid Matrix */}
      <CoverageMatrix 
        matrix={matrix} 
        isLoading={isLoading} 
      />

      {/* Pagination controls */}
      {!isLoading && matrix && matrix.rows.length > 0 && (
        <div className="mt-4 flex items-center justify-between">
          <p className="text-xs font-semibold text-gray-500">
            Showing {(page - 1) * 15 + 1} to {Math.min(page * 15, page * 15)} records
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
              // Simple check for next page availability (e.g. if we retrieved exactly 15 rows)
              disabled={matrix.rows.length < 15}
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
