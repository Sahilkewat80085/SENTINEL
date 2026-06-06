import React from 'react';
import { cn } from '@/lib/utils';

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'text' | 'rect' | 'circle';
}

export default function Skeleton({
  className,
  variant = 'rect',
  ...props
}: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse bg-slate-800/60 border border-slate-700/20",
        {
          'h-4 w-full rounded': variant === 'text',
          'rounded-xl': variant === 'rect',
          'rounded-full': variant === 'circle',
        },
        className
      )}
      {...props}
    />
  );
}

// Quick layout skeletons
export function CardSkeleton() {
  return (
    <div className="rounded-xl border border-card-border bg-card p-6 space-y-4">
      <Skeleton className="h-6 w-2/5 rounded" variant="text" />
      <Skeleton className="h-4 w-4/5 rounded" variant="text" />
      <div className="space-y-2 pt-2">
        <Skeleton className="h-3 w-full rounded" variant="text" />
        <Skeleton className="h-3 w-full rounded" variant="text" />
        <Skeleton className="h-3 w-5/6 rounded" variant="text" />
      </div>
    </div>
  );
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="rounded-xl border border-card-border bg-card overflow-hidden">
      <div className="h-12 border-b border-card-border bg-card-border/30 px-6 flex items-center justify-between">
        <Skeleton className="h-5 w-1/4 rounded" variant="text" />
        <Skeleton className="h-5 w-1/12 rounded" variant="text" />
      </div>
      <div className="divide-y divide-card-border/60">
        {Array.from({ length: rows }).map((_, idx) => (
          <div key={idx} className="h-14 px-6 flex items-center gap-6">
            <Skeleton className="h-4 w-12 rounded" variant="text" />
            <Skeleton className="h-4 flex-1 rounded" variant="text" />
            <Skeleton className="h-4 w-24 rounded" variant="text" />
            <Skeleton className="h-4 w-16 rounded" variant="text" />
          </div>
        ))}
      </div>
    </div>
  );
}
