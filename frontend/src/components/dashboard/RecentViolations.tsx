'use client';

import React, { useState } from 'react';
import { RuleViolation } from '@/lib/types';
import { apiService } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/Card';
import Badge from '../ui/Badge';
import Modal from '../ui/Modal';
import { formatDistanceToNow, getSeverityColorClass } from '@/lib/utils';
import { AlertTriangle, CheckSquare, MessageSquare } from 'lucide-react';
import { cn } from '@/lib/utils';

interface RecentViolationsProps {
  data: RuleViolation[];
  isLoading: boolean;
  onRefresh?: () => void;
}

export default function RecentViolations({ data, isLoading, onRefresh }: RecentViolationsProps) {
  const [selectedViolation, setSelectedViolation] = useState<RuleViolation | null>(null);
  const [ackNote, setAckNote] = useState('');
  const [ackLoading, setAckLoading] = useState(false);

  const handleAcknowledge = async () => {
    if (!selectedViolation) return;
    setAckLoading(true);
    try {
      await apiService.violations.acknowledge(selectedViolation.id, ackNote);
      setSelectedViolation(null);
      setAckNote('');
      if (onRefresh) onRefresh();
    } catch (err) {
      alert('Failed to acknowledge violation');
    } finally {
      setAckLoading(false);
    }
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <div>
          <CardTitle>Recent Violations</CardTitle>
          <CardDescription>Unresolved governance exceptions requiring review</CardDescription>
        </div>
        <AlertTriangle className="h-5 w-5 text-rose-500 animate-pulse" />
      </CardHeader>
      
      <CardContent className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="space-y-4">
            {Array.from({ length: 3 }).map((_, idx) => (
              <div key={idx} className="flex gap-4 items-center">
                <div className="h-8 w-16 bg-slate-800 animate-pulse rounded" />
                <div className="flex-1 h-8 bg-slate-800 animate-pulse rounded" />
              </div>
            ))}
          </div>
        ) : data.length === 0 ? (
          <div className="flex h-36 w-full flex-col items-center justify-center text-sm font-semibold text-gray-500">
            <CheckSquare className="h-8 w-8 text-emerald-500/40 mb-2" />
            No active violations detected. Nice job!
          </div>
        ) : (
          <div className="space-y-3.5">
            {data.slice(0, 5).map((violation) => (
              <div 
                key={violation.id} 
                className="flex items-start justify-between gap-3 rounded-lg border border-card-border/60 bg-[#111726]/30 p-3 hover:border-card-border transition-all duration-150"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge className={cn("font-bold font-mono text-[10px]", getSeverityColorClass(violation.severity))}>
                      {violation.severity}
                    </Badge>
                    <span className="text-xs font-bold text-gray-400 font-mono">
                      {violation.rule_id}
                    </span>
                    {violation.folder_name && (
                      <span className="text-[10px] font-semibold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20 font-mono">
                        {violation.folder_name}
                      </span>
                    )}
                  </div>
                  <p className="mt-2 text-sm text-gray-300 font-medium leading-relaxed">
                    {violation.description}
                  </p>
                  <p className="mt-1 text-[10px] text-gray-500 font-semibold uppercase">
                    Detected {formatDistanceToNow(violation.detected_at)}
                  </p>
                </div>

                <button
                  onClick={() => setSelectedViolation(violation)}
                  className="flex-shrink-0 flex items-center justify-center p-1.5 text-gray-400 border border-card-border/60 rounded-lg hover:text-emerald-400 hover:border-emerald-500/30 hover:bg-emerald-500/5 transition-all"
                  title="Acknowledge violation"
                >
                  <CheckSquare className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </CardContent>

      {/* Acknowledge Dialog Modal */}
      <Modal
        isOpen={selectedViolation !== null}
        onClose={() => setSelectedViolation(null)}
        title={`Acknowledge Exception: ${selectedViolation?.rule_id}`}
        footer={
          <>
            <button
              onClick={() => setSelectedViolation(null)}
              className="rounded-lg border border-card-border px-4 py-2 text-sm font-semibold text-gray-400 hover:bg-card-border hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleAcknowledge}
              disabled={ackLoading}
              className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50 transition-colors glow-success"
            >
              {ackLoading ? 'Submitting...' : 'Acknowledge'}
            </button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="rounded-lg border border-card-border bg-[#111726]/40 p-4">
            <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Violation Description</h4>
            <p className="mt-1.5 text-sm text-white font-medium">{selectedViolation?.description}</p>
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="ack-note" className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
              <MessageSquare className="h-3.5 w-3.5" />
              Acknowledgement Justification
            </label>
            <textarea
              id="ack-note"
              rows={3}
              value={ackNote}
              onChange={(e) => setAckNote(e.target.value)}
              placeholder="Provide context or explanation why this exception is accepted (e.g. Approved delay, hotfix only, temporary divergence)..."
              className="w-full rounded-lg border border-card-border bg-slate-900/50 p-3 text-sm text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none"
            />
          </div>
        </div>
      </Modal>
    </Card>
  );
}
