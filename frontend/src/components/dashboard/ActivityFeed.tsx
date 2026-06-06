'use client';

import React from 'react';
import { RecentActivity } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/Card';
import { formatDistanceToNow } from '@/lib/utils';
import { RefreshCw, ShieldAlert, CheckCircle, Shield, AlertTriangle, Key } from 'lucide-react';
import { cn } from '@/lib/utils';
import Skeleton from '../ui/Skeleton';

interface ActivityFeedProps {
  data: RecentActivity[];
  isLoading: boolean;
}

export default function ActivityFeed({ data, isLoading }: ActivityFeedProps) {
  const getActivityIcon = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'sync':
      case 'sync_completed':
      case 'sync_started':
        return {
          icon: RefreshCw,
          bg: 'bg-blue-500/10 border-blue-500/20 text-blue-400',
        };
      case 'violation_detected':
      case 'rule_violation':
        return {
          icon: AlertTriangle,
          bg: 'bg-rose-500/10 border-rose-500/20 text-rose-400',
        };
      case 'violation_acknowledged':
      case 'rule_acknowledged':
        return {
          icon: CheckCircle,
          bg: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400',
        };
      case 'user_login':
      case 'login':
        return {
          icon: Key,
          bg: 'bg-teal-500/10 border-teal-500/20 text-teal-400',
        };
      default:
        return {
          icon: Shield,
          bg: 'bg-slate-500/10 border-slate-500/20 text-slate-400',
        };
    }
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <CardTitle>System Activity Feed</CardTitle>
        <CardDescription>Real-time audit log of operational and sync activities</CardDescription>
      </CardHeader>
      
      <CardContent className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="space-y-4">
            {Array.from({ length: 4 }).map((_, idx) => (
              <div key={idx} className="flex gap-4 items-center">
                <div className="h-8 w-8 bg-slate-800 rounded-full animate-pulse" />
                <div className="flex-1 space-y-2">
                  <div className="h-3 w-3/4 bg-slate-800 rounded animate-pulse" />
                  <div className="h-2 w-1/4 bg-slate-800 rounded animate-pulse" />
                </div>
              </div>
            ))}
          </div>
        ) : data.length === 0 ? (
          <div className="flex h-36 w-full items-center justify-center text-sm font-semibold text-gray-500">
            No activity logs found.
          </div>
        ) : (
          <div className="relative pl-6 border-l-2 border-slate-800 space-y-5 ml-3">
            {data.slice(0, 10).map((activity) => {
              const theme = getActivityIcon(activity.activity_type);
              const Icon = theme.icon;
              return (
                <div key={activity.id} className="relative">
                  {/* Bullet Icon Point */}
                  <span className={cn(
                    "absolute -left-[35px] top-0.5 flex h-6.5 w-6.5 items-center justify-center rounded-full border text-[10px] bg-card",
                    theme.bg
                  )}>
                    <Icon className="h-3.5 w-3.5" />
                  </span>

                  {/* Activity Details */}
                  <div>
                    <p className="text-sm font-medium text-gray-300">
                      {activity.description}
                    </p>
                    <p className="text-[10px] font-semibold text-gray-500 uppercase mt-0.5">
                      {formatDistanceToNow(activity.timestamp)}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
