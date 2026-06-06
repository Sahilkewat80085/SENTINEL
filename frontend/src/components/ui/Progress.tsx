import React from 'react';
import { cn } from '@/lib/utils';

interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number; // 0 to 100
  showValue?: boolean;
  color?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'dynamic';
}

export default function Progress({
  value,
  showValue = false,
  color = 'dynamic',
  className,
  ...props
}: ProgressProps) {
  // Clamp value between 0 and 100
  const clampedValue = Math.min(Math.max(value, 0), 100);

  // Dynamic color based on thresholds
  const getDynamicColor = (val: number) => {
    if (val >= 90) return 'bg-emerald-500';
    if (val >= 70) return 'bg-teal-400';
    if (val >= 50) return 'bg-yellow-500';
    if (val >= 25) return 'bg-orange-500';
    return 'bg-rose-500';
  };

  const getColorClass = () => {
    switch (color) {
      case 'success':
        return 'bg-emerald-500';
      case 'warning':
        return 'bg-yellow-500';
      case 'danger':
        return 'bg-rose-500';
      case 'info':
        return 'bg-blue-500';
      case 'default':
        return 'bg-slate-500';
      case 'dynamic':
      default:
        return getDynamicColor(clampedValue);
    }
  };

  return (
    <div className="w-full">
      {showValue && (
        <div className="flex justify-between items-center mb-1 text-xs font-semibold text-gray-400">
          <span>Progress</span>
          <span className="text-white">{clampedValue.toFixed(1)}%</span>
        </div>
      )}
      <div
        className={cn(
          "h-2 w-full overflow-hidden rounded-full bg-slate-800 border border-card-border/50",
          className
        )}
        {...props}
      >
        <div
          className={cn("h-full transition-all duration-500 ease-out", getColorClass())}
          style={{ width: `${clampedValue}%` }}
        />
      </div>
    </div>
  );
}
