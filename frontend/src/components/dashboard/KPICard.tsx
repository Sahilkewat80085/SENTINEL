import React from 'react';
import { Card, CardContent } from '../ui/Card';
import { cn } from '@/lib/utils';

interface KPICardProps {
  title: string;
  value: string | number;
  icon: React.ComponentType<any>;
  description?: string;
  trend?: {
    value: string;
    isPositive: boolean;
  };
  color?: 'blue' | 'emerald' | 'amber' | 'rose' | 'indigo';
}

export default function KPICard({
  title,
  value,
  icon: Icon,
  description,
  trend,
  color = 'blue',
}: KPICardProps) {
  const getColorClasses = () => {
    switch (color) {
      case 'emerald':
        return {
          glow: 'glow-success border-emerald-500/20 bg-emerald-500/5',
          iconBg: 'bg-emerald-500/10 text-emerald-400',
        };
      case 'amber':
        return {
          glow: 'glow-warning border-amber-500/20 bg-amber-500/5',
          iconBg: 'bg-amber-500/10 text-amber-400',
        };
      case 'rose':
        return {
          glow: 'glow-danger border-rose-500/20 bg-rose-500/5',
          iconBg: 'bg-rose-500/10 text-rose-400',
        };
      case 'indigo':
        return {
          glow: 'border-indigo-500/20 bg-indigo-500/5',
          iconBg: 'bg-indigo-500/10 text-indigo-400',
        };
      case 'blue':
      default:
        return {
          glow: 'glow-primary border-blue-500/20 bg-blue-500/5',
          iconBg: 'bg-blue-500/10 text-blue-400',
        };
    }
  };

  const themeColors = getColorClasses();

  return (
    <Card className={cn("transition-all duration-300 hover:scale-[1.02]", themeColors.glow)}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">
              {title}
            </p>
            <h3 className="mt-2 text-3xl font-extrabold tracking-tight text-white">
              {value}
            </h3>
          </div>
          <div className={cn("flex h-12 w-12 items-center justify-center rounded-xl", themeColors.iconBg)}>
            <Icon className="h-6 w-6" />
          </div>
        </div>
        
        {(description || trend) && (
          <div className="mt-4 flex items-center justify-between">
            {description && (
              <span className="text-xs font-medium text-gray-500 truncate">
                {description}
              </span>
            )}
            {trend && (
              <span
                className={cn(
                  "text-xs font-semibold px-2 py-0.5 rounded-full border",
                  trend.isPositive
                    ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/10"
                    : "text-rose-400 bg-rose-500/10 border-rose-500/10"
                )}
              >
                {trend.value}
              </span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
