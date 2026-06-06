'use client';

import React, { useEffect, useState } from 'react';
import PageContainer from '@/components/layout/PageContainer';
import { apiService } from '@/lib/api';
import { Repository } from '@/lib/types';
import { useFilterStore } from '@/stores/filterStore';
import { useDashboardStore } from '@/stores/dashboardStore';
import { formatDate } from '@/lib/utils';
import { Settings, RefreshCw, Plus, Trash2, CheckCircle2, AlertCircle, Loader2, Globe, Code2, Tag, Clock, Shield, GitBranch } from 'lucide-react';
import Badge from '@/components/ui/Badge';
import Skeleton from '@/components/ui/Skeleton';
import Modal from '@/components/ui/Modal';
import { cn } from '@/lib/utils';

const SYNC_MODES = ['api', 'git', 'hybrid'];

type NewRepoForm = {
  name: string;
  url: string;
  default_branch: string;
  sync_mode: string;
  sync_interval: number;
  folders: string;
  jira_patterns: string;
};

const defaultForm: NewRepoForm = {
  name: '',
  url: '',
  default_branch: 'main',
  sync_mode: 'api',
  sync_interval: 3600,
  folders: '',
  jira_patterns: 'PROJ-\\d+',
};

export default function SettingsPage() {
  const { user } = useDashboardStore();
  const { selectedRepoId, setSelectedRepoId } = useFilterStore();
  const [repos, setRepos] = useState<Repository[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [syncingId, setSyncingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [form, setForm] = useState<NewRepoForm>(defaultForm);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [syncStatus, setSyncStatus] = useState<Record<string, string>>({});

  const fetchRepos = async () => {
    setIsLoading(true);
    try {
      const data = await apiService.repositories.list();
      setRepos(data);
    } catch (err) {
      console.error('Failed to fetch repositories', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRepos();
  }, []);

  const handleSync = async (id: string) => {
    setSyncingId(id);
    setSyncStatus(prev => ({ ...prev, [id]: 'SYNCING' }));
    try {
      await apiService.repositories.sync(id);
      setSyncStatus(prev => ({ ...prev, [id]: 'SUCCESS' }));
      setTimeout(() => setSyncStatus(prev => ({ ...prev, [id]: '' })), 3000);
      fetchRepos();
    } catch (err) {
      setSyncStatus(prev => ({ ...prev, [id]: 'FAILED' }));
    } finally {
      setSyncingId(null);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this repository? This cannot be undone.')) return;
    setDeletingId(id);
    try {
      await apiService.repositories.delete(id);
      setRepos(prev => prev.filter(r => r.id !== id));
      if (selectedRepoId === id && repos.length > 1) {
        setSelectedRepoId(repos.find(r => r.id !== id)?.id ?? null);
      }
    } catch (err) {
      alert('Failed to delete repository');
    } finally {
      setDeletingId(null);
    }
  };

  const handleAddRepo = async () => {
    setIsSubmitting(true);
    try {
      const payload = {
        ...form,
        folders: form.folders.split(',').map(s => s.trim()).filter(Boolean),
        jira_patterns: form.jira_patterns.split(',').map(s => s.trim()).filter(Boolean),
      };
      const newRepo = await apiService.repositories.create(payload);
      setRepos(prev => [...prev, newRepo]);
      setIsAddModalOpen(false);
      setForm(defaultForm);
    } catch (err) {
      alert('Failed to add repository');
    } finally {
      setIsSubmitting(false);
    }
  };

  const activeRepo = repos.find(r => r.id === selectedRepoId);

  return (
    <PageContainer
      title="Configuration Settings"
      subtitle="Manage repository integrations, sync intervals, and system configuration"
      breadcrumbs={[{ name: 'Settings' }]}
      action={
        <button
          onClick={() => setIsAddModalOpen(true)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3.5 py-1.5 text-sm font-bold text-white hover:bg-blue-700 transition-all shadow-md glow-primary"
        >
          <Plus className="h-4 w-4" />
          Add Repository
        </button>
      }
    >
      {/* User Info Banner */}
      {user && (
        <div className="flex items-center gap-4 rounded-2xl border border-blue-500/20 bg-blue-500/5 px-5 py-3.5 mb-6">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-500/20 border border-blue-500/30">
            <Shield className="h-4.5 w-4.5 text-blue-400" />
          </div>
          <div>
            <p className="text-sm font-bold text-white">Signed in as <span className="text-blue-400">{user.username}</span></p>
            <p className="text-xs text-gray-500">{user.email} · Role: <span className="font-semibold text-gray-300 capitalize">{user.role}</span></p>
          </div>
          <div className="ml-auto">
            <Badge variant="success" className="text-[10px] font-mono font-bold">Active Session</Badge>
          </div>
        </div>
      )}

      {/* Repository Cards */}
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-bold text-white">Connected Repositories</h3>
        <span className="text-xs text-gray-500">{repos.length} configured</span>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-36 rounded-2xl" variant="rect" />
          ))}
        </div>
      ) : repos.length === 0 ? (
        <div className="py-16 text-center rounded-2xl border border-dashed border-white/10">
          <GitBranch className="h-10 w-10 text-gray-700 mx-auto mb-3" />
          <p className="text-sm font-semibold text-gray-500">No repositories configured</p>
          <p className="text-xs text-gray-600 mt-1">Add a repository to start monitoring governance</p>
        </div>
      ) : (
        <div className="space-y-4">
          {repos.map(repo => {
            const isActive = repo.id === selectedRepoId;
            const statusMsg = syncStatus[repo.id];
            return (
              <div
                key={repo.id}
                className={cn(
                  'rounded-2xl border p-5 transition-all cursor-pointer',
                  isActive
                    ? 'border-blue-500/40 bg-blue-500/5 shadow-lg shadow-blue-900/10'
                    : 'border-white/8 bg-gradient-to-br from-[#111726]/80 to-[#0d1526]/80 hover:border-white/15'
                )}
                onClick={() => setSelectedRepoId(repo.id)}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3 min-w-0">
                    <div className={cn(
                      'flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl',
                      isActive ? 'bg-blue-500/20 border border-blue-500/30' : 'bg-white/5 border border-white/10'
                    )}>
                      <GitBranch className={cn('h-5 w-5', isActive ? 'text-blue-400' : 'text-gray-400')} />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="font-bold text-white truncate">{repo.name}</p>
                        {isActive && <Badge variant="info" className="text-[9px] font-mono font-bold flex-shrink-0">Active</Badge>}
                        {repo.is_active ? (
                          <Badge variant="success" className="text-[9px] font-mono flex-shrink-0">Enabled</Badge>
                        ) : (
                          <Badge variant="error" className="text-[9px] font-mono flex-shrink-0">Disabled</Badge>
                        )}
                      </div>
                      <a
                        href={repo.url}
                        target="_blank"
                        rel="noreferrer"
                        onClick={e => e.stopPropagation()}
                        className="text-xs text-gray-500 hover:text-blue-400 truncate block mt-0.5 transition-colors"
                      >
                        {repo.url}
                      </a>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {statusMsg && (
                      <span className={cn(
                        'text-xs font-semibold',
                        statusMsg === 'SUCCESS' ? 'text-emerald-400' :
                        statusMsg === 'FAILED' ? 'text-rose-400' : 'text-amber-400'
                      )}>
                        {statusMsg === 'SYNCING' ? 'Syncing…' : statusMsg === 'SUCCESS' ? '✓ Synced' : '✕ Failed'}
                      </span>
                    )}
                    <button
                      onClick={e => { e.stopPropagation(); handleSync(repo.id); }}
                      disabled={syncingId === repo.id}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-card-border px-2.5 py-1.5 text-xs font-semibold text-gray-400 hover:text-white hover:bg-card-border disabled:opacity-50 transition-all"
                      title="Trigger sync"
                    >
                      {syncingId === repo.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
                      Sync
                    </button>
                    {user?.role === 'admin' && (
                      <button
                        onClick={e => { e.stopPropagation(); handleDelete(repo.id); }}
                        disabled={deletingId === repo.id}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-rose-500/20 px-2.5 py-1.5 text-xs font-semibold text-rose-400/70 hover:text-rose-400 hover:border-rose-500/40 hover:bg-rose-500/5 disabled:opacity-50 transition-all"
                        title="Delete repository"
                      >
                        {deletingId === repo.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" />}
                      </button>
                    )}
                  </div>
                </div>

                {/* Repo Metadata */}
                <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4 text-xs">
                  <div className="flex items-center gap-1.5 text-gray-500">
                    <Code2 className="h-3 w-3 flex-shrink-0" />
                    <span>Branch: <span className="font-mono font-semibold text-gray-300">{repo.default_branch}</span></span>
                  </div>
                  <div className="flex items-center gap-1.5 text-gray-500">
                    <Settings className="h-3 w-3 flex-shrink-0" />
                    <span>Mode: <span className="font-semibold text-gray-300 uppercase">{repo.sync_mode}</span></span>
                  </div>
                  <div className="flex items-center gap-1.5 text-gray-500">
                    <Tag className="h-3 w-3 flex-shrink-0" />
                    <span>Folders: <span className="font-semibold text-gray-300">{repo.folders?.length ?? 0}</span></span>
                  </div>
                  <div className="flex items-center gap-1.5 text-gray-500">
                    <Clock className="h-3 w-3 flex-shrink-0" />
                    <span>Synced: <span className="font-semibold text-gray-300">{repo.last_synced_at ? formatDate(repo.last_synced_at) : 'Never'}</span></span>
                  </div>
                </div>

                {repo.folders?.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {repo.folders.map(f => (
                      <span key={f} className="rounded-md border border-white/8 bg-white/5 px-2 py-0.5 text-[10px] font-mono font-semibold text-gray-400">{f}</span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Add Repository Modal */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Add New Repository"
        footer={
          <>
            <button
              onClick={() => setIsAddModalOpen(false)}
              className="rounded-lg border border-card-border px-4 py-2 text-sm font-semibold text-gray-400 hover:bg-card-border hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleAddRepo}
              disabled={isSubmitting || !form.name || !form.url}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-bold text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {isSubmitting ? 'Adding…' : 'Add Repository'}
            </button>
          </>
        }
      >
        <div className="space-y-4">
          {[
            { label: 'Repository Name', key: 'name', placeholder: 'e.g. my-microservice', type: 'text' },
            { label: 'GitHub URL', key: 'url', placeholder: 'https://github.com/org/repo', type: 'url' },
            { label: 'Default Branch', key: 'default_branch', placeholder: 'main', type: 'text' },
          ].map(field => (
            <div key={field.key}>
              <label htmlFor={field.key} className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1.5">
                {field.label}
              </label>
              <input
                id={field.key}
                type={field.type}
                value={(form as any)[field.key]}
                onChange={e => setForm(prev => ({ ...prev, [field.key]: e.target.value }))}
                placeholder={field.placeholder}
                className="w-full rounded-lg border border-card-border bg-slate-900/50 px-3 py-2 text-sm text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none"
              />
            </div>
          ))}

          <div>
            <label htmlFor="sync-mode" className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1.5">
              Sync Mode
            </label>
            <select
              id="sync-mode"
              value={form.sync_mode}
              onChange={e => setForm(prev => ({ ...prev, sync_mode: e.target.value }))}
              className="w-full rounded-lg border border-card-border bg-slate-900/50 px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none"
            >
              {SYNC_MODES.map(m => (
                <option key={m} value={m}>{m.charAt(0).toUpperCase() + m.slice(1)}</option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="sync-interval" className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1.5">
              Sync Interval (seconds)
            </label>
            <input
              id="sync-interval"
              type="number"
              value={form.sync_interval}
              onChange={e => setForm(prev => ({ ...prev, sync_interval: parseInt(e.target.value) }))}
              className="w-full rounded-lg border border-card-border bg-slate-900/50 px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label htmlFor="folders" className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1.5">
              Tracked Folders <span className="text-gray-600 normal-case">(comma-separated)</span>
            </label>
            <input
              id="folders"
              type="text"
              value={form.folders}
              onChange={e => setForm(prev => ({ ...prev, folders: e.target.value }))}
              placeholder="folder1, folder2, folder3"
              className="w-full rounded-lg border border-card-border bg-slate-900/50 px-3 py-2 text-sm text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label htmlFor="jira-patterns" className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1.5">
              Jira Patterns <span className="text-gray-600 normal-case">(comma-separated regex)</span>
            </label>
            <input
              id="jira-patterns"
              type="text"
              value={form.jira_patterns}
              onChange={e => setForm(prev => ({ ...prev, jira_patterns: e.target.value }))}
              placeholder="PROJ-\d+, FEAT-\d+"
              className="w-full rounded-lg border border-card-border bg-slate-900/50 px-3 py-2 text-sm font-mono text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none"
            />
          </div>
        </div>
      </Modal>
    </PageContainer>
  );
}
