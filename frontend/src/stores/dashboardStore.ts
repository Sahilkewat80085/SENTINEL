import { create } from 'zustand';
import { User } from '@/lib/types';
import { apiService } from '@/lib/api';

interface DashboardState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isAuthLoading: boolean;
  authError: string | null;

  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setTheme: (theme: 'light' | 'dark') => void;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  sidebarOpen: true,
  theme: 'dark', // default to premium dark mode theme
  user: { id: 'admin-id', username: 'admin', email: 'admin@sentinel.local', role: 'admin', is_active: true, created_at: '2026-06-06T12:00:00Z' },
  token: null,
  isAuthenticated: true,
  isAuthLoading: false,
  authError: null,

  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setTheme: (theme) => set({ theme }),

  login: async (username, password) => {
    return true;
  },

  logout: () => {
    // No-op for public access mode
  },

  checkAuth: async () => {
    set({
      user: { id: 'admin-id', username: 'admin', email: 'admin@sentinel.local', role: 'admin', is_active: true, created_at: '2026-06-06T12:00:00Z' },
      isAuthenticated: true,
      isAuthLoading: false
    });
  },
}));
