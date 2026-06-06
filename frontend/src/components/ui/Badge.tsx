import React from 'react';
import { cn } from '@/lib/utils';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'muted';
  outline?: boolean;
}

export default function Badge({
  children,
  className,
  variant = 'default',
  outline = false,
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold tracking-wide border transition-colors duration-150",
        // Solid styles
        !outline && {
          'bg-slate-800 text-slate-200 border-transparent': variant === 'default',
          'bg-emerald-500/10 text-emerald-400 border-emerald-500/20': variant === 'success',
          'bg-yellow-500/10 text-yellow-400 border-yellow-500/20': variant === 'warning',
          'bg-rose-500/10 text-rose-400 border-rose-500/20': variant === 'error',
          'bg-blue-500/10 text-blue-400 border-blue-500/20': variant === 'info',
          'bg-zinc-800 text-zinc-400 border-zinc-700/50': variant === 'muted',
        },
        // Outline styles
        outline && {
          'bg-transparent text-slate-300 border-slate-700': variant === 'default',
          'bg-transparent text-emerald-400 border-emerald-500/30': variant === 'success',
          'bg-transparent text-yellow-400 border-yellow-500/30': variant === 'warning',
          'bg-transparent text-rose-400 border-rose-500/30': variant === 'error',
          'bg-transparent text-blue-400 border-blue-500/30': variant === 'info',
          'bg-transparent text-zinc-500 border-zinc-800': variant === 'muted',
        },
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
