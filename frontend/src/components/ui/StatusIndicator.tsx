import React from 'react';
import { cn } from '@/lib/utils';

interface StatusIndicatorProps extends React.HTMLAttributes<HTMLSpanElement> {
  status: 'healthy' | 'warning' | 'critical' | 'info' | 'offline' | string;
  pulse?: boolean;
}

export default function StatusIndicator({
  status,
  pulse = false,
  className,
  ...props
}: StatusIndicatorProps) {
  const getColors = (stat: string) => {
    switch (stat?.toLowerCase()) {
      case 'healthy':
      case 'merged':
      case 'active':
      case 'excellent':
      case 'good':
      case 'success':
        return {
          dot: 'bg-emerald-500',
          ping: 'bg-emerald-400',
          text: 'text-emerald-400'
        };
      case 'warning':
      case 'partial':
      case 'stale':
      case 'different':
        return {
          dot: 'bg-yellow-500',
          ping: 'bg-yellow-400',
          text: 'text-yellow-400'
        };
      case 'critical':
      case 'danger':
      case 'missing':
      case 'dormant':
      case 'error':
        return {
          dot: 'bg-rose-500',
          ping: 'bg-rose-400',
          text: 'text-rose-400'
        };
      case 'info':
        return {
          dot: 'bg-blue-500',
          ping: 'bg-blue-400',
          text: 'text-blue-400'
        };
      case 'offline':
      case 'archived':
      default:
        return {
          dot: 'bg-zinc-600',
          ping: 'bg-zinc-500',
          text: 'text-zinc-500'
        };
    }
  };

  const colors = getColors(status);

  return (
    <span className={cn("inline-flex items-center gap-1.5", className)} {...props}>
      <span className="relative flex h-2 w-2">
        {pulse && (
          <span className={cn("absolute inline-flex h-full w-full animate-ping rounded-full opacity-75", colors.ping)} />
        )}
        <span className={cn("relative inline-flex h-2 w-2 rounded-full", colors.dot)} />
      </span>
      <span className={cn("text-xs font-semibold uppercase tracking-wider", colors.text)}>
        {status}
      </span>
    </span>
  );
}
