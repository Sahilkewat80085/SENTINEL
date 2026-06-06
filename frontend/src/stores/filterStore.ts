import { create } from 'zustand';
import { Repository } from '@/lib/types';
import { apiService } from '@/lib/api';

interface FilterState {
  selectedRepoId: string | null;
  repositories: Repository[];
  period: string; // '7d' | '30d' | '90d' | 'all'
  isLoading: boolean;
  error: string | null;
  
  setSelectedRepoId: (repoId: string | null) => void;
  setPeriod: (period: string) => void;
  fetchRepositories: () => Promise<void>;
  getSelectedRepo: () => Repository | undefined;
}

export const useFilterStore = create<FilterState>((set, get) => ({
  selectedRepoId: null,
  repositories: [],
  period: '30d',
  isLoading: false,
  error: null,

  setSelectedRepoId: (repoId) => set({ selectedRepoId: repoId }),
  setPeriod: (period) => set({ period }),
  
  fetchRepositories: async () => {
    set({ isLoading: true, error: null });
    try {
      const repos = await apiService.repositories.list();
      set({ repositories: repos, isLoading: false });
      
      // Auto-select first repository if none is selected
      const currentSelected = get().selectedRepoId;
      if (repos.length > 0 && (!currentSelected || !repos.find(r => r.id === currentSelected))) {
        set({ selectedRepoId: repos[0].id });
      }
    } catch (err: any) {
      set({ error: err.message || 'Failed to fetch repositories', isLoading: false });
    }
  },

  getSelectedRepo: () => {
    const { repositories, selectedRepoId } = get();
    return repositories.find((r) => r.id === selectedRepoId);
  },
}));
