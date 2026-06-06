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
  user: null,
  token: typeof window !== 'undefined' ? localStorage.getItem('sentinel_token') : null,
  isAuthenticated: false,
  isAuthLoading: true,
  authError: null,

  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setTheme: (theme) => set({ theme }),

  login: async (username, password) => {
    set({ isAuthLoading: true, authError: null });
    try {
      const tokenObj = await apiService.auth.login(username, password);
      localStorage.setItem('sentinel_token', tokenObj.access_token);
      set({ token: tokenObj.access_token });
      
      const userObj = await apiService.auth.getProfile();
      set({ user: userObj, isAuthenticated: true, isAuthLoading: false });
      return true;
    } catch (err: any) {
      set({ 
        authError: err.response?.data?.errors?.[0]?.message || err.message || 'Login failed', 
        isAuthLoading: false, 
        isAuthenticated: false 
      });
      return false;
    }
  },

  logout: () => {
    localStorage.removeItem('sentinel_token');
    set({ user: null, token: null, isAuthenticated: false });
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  },

  checkAuth: async () => {
    if (typeof window === 'undefined') {
      set({ isAuthLoading: false });
      return;
    }
    const token = localStorage.getItem('sentinel_token');
    if (!token) {
      set({ user: null, token: null, isAuthenticated: false, isAuthLoading: false });
      return;
    }
    
    set({ isAuthLoading: true, authError: null });
    try {
      const userObj = await apiService.auth.getProfile();
      set({ user: userObj, isAuthenticated: true, isAuthLoading: false, token });
    } catch (err) {
      localStorage.removeItem('sentinel_token');
      set({ user: null, token: null, isAuthenticated: false, isAuthLoading: false });
    }
  },
}));
