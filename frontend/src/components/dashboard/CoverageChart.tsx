'use client';

import React from 'react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip,
  TooltipProps
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/Card';
import { TrendPoint } from '@/lib/types';
import { formatDate } from '@/lib/utils';
import Skeleton from '../ui/Skeleton';

interface CoverageChartProps {
  data: TrendPoint[];
  isLoading: boolean;
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="rounded-lg border border-card-border bg-card p-3 shadow-xl glow-primary">
        <p className="text-xs font-semibold text-gray-400">
          {formatDate(payload[0].payload.date, 'MMMM d, yyyy')}
        </p>
        <p className="mt-1.5 text-sm font-extrabold text-blue-400">
          Coverage: {payload[0].value?.toFixed(1)}%
        </p>
      </div>
    );
  }
  return null;
};

export default function CoverageChart({ data, isLoading }: CoverageChartProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-1/3 rounded" variant="text" />
          <Skeleton className="h-4 w-1/2 rounded" variant="text" />
        </CardHeader>
        <CardContent className="h-72">
          <Skeleton className="h-full w-full rounded-lg" variant="rect" />
        </CardContent>
      </Card>
    );
  }

  // Format date values for XAxis
  const chartData = data.map(pt => ({
    ...pt,
    formattedDate: formatDate(pt.date, 'MMM d')
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Release Readiness Trend</CardTitle>
        <CardDescription>Historical tracking of repository-wide folder coverage percentage</CardDescription>
      </CardHeader>
      <CardContent className="h-72">
        {chartData.length === 0 ? (
          <div className="flex h-full w-full items-center justify-center text-sm font-semibold text-gray-500">
            No historical trend data recorded yet.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={chartData}
              margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
            >
              <defs>
                <linearGradient id="coverageGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" opacity={0.3} />
              <XAxis 
                dataKey="formattedDate" 
                stroke="#6b7280" 
                fontSize={11} 
                tickLine={false} 
              />
              <YAxis 
                stroke="#6b7280" 
                fontSize={11} 
                domain={[0, 100]} 
                tickLine={false} 
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#3b82f6"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#coverageGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
