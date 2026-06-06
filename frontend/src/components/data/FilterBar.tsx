import React from 'react';
import { cn } from '@/lib/utils';

interface FilterBarProps {
  children: React.ReactNode;
  className?: string;
}

export default function FilterBar({ children, className }: FilterBarProps) {
  return (
    <div className={cn("flex flex-wrap items-center gap-4 border border-card-border/40 bg-[#111726]/10 rounded-xl p-4 mb-6", className)}>
      {children}
    </div>
  );
}
