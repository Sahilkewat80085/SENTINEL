import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { format, formatDistanceToNow as dateFnsFormatDistanceToNow, parseISO } from 'date-fns';

// Merges class names safely for Tailwind CSS styling
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Formats an ISO date string to a human-readable format
export function formatDate(dateString: string | Date | null | undefined, pattern = 'yyyy-MM-dd HH:mm'): string {
  if (!dateString) return '—';
  try {
    const date = typeof dateString === 'string' ? parseISO(dateString) : dateString;
    return format(date, pattern);
  } catch (error) {
    return '—';
  }
}

// Formats an ISO date string as relative distance (e.g. "3 days ago")
export function formatDistanceToNow(dateString: string | Date | null | undefined): string {
  if (!dateString) return '—';
  try {
    const date = typeof dateString === 'string' ? parseISO(dateString) : dateString;
    return dateFnsFormatDistanceToNow(date, { addSuffix: true });
  } catch (error) {
    return '—';
  }
}

// Formats a float percentage (e.g. 73.123 -> "73.1%")
export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) return '0.0%';
  return `${value.toFixed(1)}%`;
}

// Formats bytes into human-readable files sizes
export function formatBytes(bytes: number | null | undefined): string {
  if (bytes === null || bytes === undefined || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

// Formats propagation delay durations (in days)
export function formatDuration(days: number | null | undefined): string {
  if (days === null || days === undefined) return 'Pending';
  if (days === 0) return 'Same day';
  if (days === 1) return '1 day';
  if (days < 1) {
    const hours = Math.round(days * 24);
    return hours === 1 ? '1 hour' : `${hours} hours`;
  }
  return `${days.toFixed(1)} days`;
}

// Shortens a commit SHA to 7 characters
export function truncateSha(sha: string | null | undefined): string {
  if (!sha) return '—';
  return sha.slice(0, 7);
}

// Gets letter grade color mapping
export function getGradeColorClass(grade: string): string {
  switch (grade?.toUpperCase()) {
    case 'A':
      return 'text-emerald-500 border-emerald-500 bg-emerald-500/10';
    case 'B':
      return 'text-teal-500 border-teal-500 bg-teal-500/10';
    case 'C':
      return 'text-yellow-500 border-yellow-500 bg-yellow-500/10';
    case 'D':
      return 'text-orange-500 border-orange-500 bg-orange-500/10';
    case 'F':
    default:
      return 'text-rose-500 border-rose-500 bg-rose-500/10';
  }
}

// Gets health score classification color mapping
export function getClassificationColorClass(classification: string): string {
  switch (classification?.toUpperCase()) {
    case 'EXCELLENT':
      return 'text-emerald-500 bg-emerald-500/10';
    case 'GOOD':
      return 'text-teal-400 bg-teal-400/10';
    case 'WARNING':
      return 'text-yellow-500 bg-yellow-500/10';
    case 'POOR':
      return 'text-orange-500 bg-orange-500/10';
    case 'CRITICAL':
    default:
      return 'text-rose-500 bg-rose-500/10';
  }
}

// Gets violation severity color mapping
export function getSeverityColorClass(severity: string): string {
  switch (severity?.toUpperCase()) {
    case 'CRITICAL':
      return 'text-rose-500 border-rose-500/30 bg-rose-500/10';
    case 'HIGH':
      return 'text-orange-500 border-orange-500/30 bg-orange-500/10';
    case 'MEDIUM':
      return 'text-yellow-500 border-yellow-500/30 bg-yellow-500/10';
    case 'LOW':
    default:
      return 'text-blue-500 border-blue-500/30 bg-blue-500/10';
  }
}

// Gets status color mapping
export function getStatusColorClass(status: string): string {
  switch (status?.toUpperCase()) {
    case 'MERGED':
    case 'HEALTHY':
    case 'IDENTICAL':
    case 'ACTIVE':
      return 'text-emerald-500 bg-emerald-500/10';
    case 'PARTIAL':
    case 'WARNING':
    case 'DIFFERENT':
    case 'STALE':
      return 'text-yellow-500 bg-yellow-500/10';
    case 'MISSING':
    case 'CRITICAL':
    case 'DORMANT':
      return 'text-rose-500 bg-rose-500/10';
    case 'ARCHIVED':
    default:
      return 'text-zinc-500 bg-zinc-500/10';
  }
}
