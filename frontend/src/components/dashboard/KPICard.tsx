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
          glow: 'border-card-border bg-card',
          iconBg: 'bg-emerald-950/30 text-emerald-400 border border-emerald-500/20',
        };
      case 'amber':
        return {
          glow: 'border-card-border bg-card',
          iconBg: 'bg-amber-950/30 text-amber-400 border border-amber-500/20',
        };
      case 'rose':
        return {
          glow: 'border-card-border bg-card',
          iconBg: 'bg-rose-950/30 text-rose-400 border border-rose-500/20',
        };
      case 'indigo':
        return {
          glow: 'border-card-border bg-card',
          iconBg: 'bg-indigo-950/30 text-indigo-400 border border-indigo-500/20',
        };
      case 'blue':
      default:
        return {
          glow: 'border-card-border bg-card',
          iconBg: 'bg-blue-950/30 text-blue-400 border border-blue-500/20',
        };
    }
  };

  const themeColors = getColorClasses();

  return (
    <Card className={cn("transition-colors duration-200", themeColors.glow)}>
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
