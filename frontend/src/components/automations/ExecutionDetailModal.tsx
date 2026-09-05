import React from 'react';
import { GlassModal } from '../ui/GlassModal';
import { BrutalButton } from '../ui/BrutalButton';
import { AutomationExecution } from '../../types';
import { AlertTriangle, RefreshCw, CheckCircle2, XCircle } from 'lucide-react';

interface ExecutionDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  execution: AutomationExecution | null;
  onRetry: (executionId: string) => Promise<void>;
  isRetrying?: boolean;
}

export const ExecutionDetailModal: React.FC<ExecutionDetailModalProps> = ({
  isOpen,
  onClose,
  execution,
  onRetry,
  isRetrying = false
}) => {
  if (!execution) return null;

  const isSuccess = execution.status === 'SUCCESS';
  const isFailed = execution.status === 'FAILED';
  const isPartial = execution.status === 'PARTIAL_SUCCESS';

  return (
    <GlassModal
      isOpen={isOpen}
      onClose={onClose}
      title={`Workflow Audit Trace — ${execution.rule_name || 'Execution'}`}
      maxWidth="2xl"
    >
      <div className="space-y-6 font-mono text-xs">
        {/* Header KPI Banner */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-xl bg-slate-950/80 border border-slate-800 gap-3">
          <div>
            <span className="text-[10px] text-slate-400 uppercase font-sans font-bold block">Execution ID</span>
            <span className="text-sm font-bold text-slate-100">{execution.id}</span>
          </div>

          <div className="flex items-center gap-3">
            <span className={`px-3 py-1 rounded-lg text-xs font-bold uppercase border ${
              isSuccess
                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                : isPartial
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                : isFailed
                ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                : 'bg-slate-800 text-slate-400 border-slate-700'
            }`}>
              {execution.status}
            </span>

            {(isFailed || isPartial) && execution.retry_count < 3 && (
              <BrutalButton
                variant="secondary"
                size="sm"
                icon={RefreshCw}
                onClick={() => onRetry(execution.id)}
                isLoading={isRetrying}
              >
                Retry Workflow ({execution.retry_count}/3)
              </BrutalButton>
            )}
          </div>
        </div>

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-[11px] p-3.5 bg-slate-950/60 rounded-xl border border-slate-800">
          <div>
            <span className="text-slate-400 block text-[10px] uppercase">Trigger Event</span>
            <span className="font-bold text-indigo-300">{execution.event_type}</span>
          </div>
          <div>
            <span className="text-slate-400 block text-[10px] uppercase">Target Entity</span>
            <span className="font-bold text-slate-200">{execution.entity_type} #{execution.entity_id.substring(0, 8)}</span>
          </div>
          <div>
            <span className="text-slate-400 block text-[10px] uppercase">Conditions Matched</span>
            <span className={`font-bold ${execution.conditions_matched ? 'text-emerald-400' : 'text-slate-500'}`}>
              {execution.conditions_matched ? 'YES' : 'NO (SKIPPED)'}
            </span>
          </div>
          <div>
            <span className="text-slate-400 block text-[10px] uppercase">Actions (Success/Total)</span>
            <span className="font-bold text-slate-100">{execution.actions_succeeded} / {execution.actions_total}</span>
          </div>
        </div>

        {/* Idempotency Key */}
        <div className="p-3 rounded-lg bg-slate-950/90 border border-slate-800 text-[10px] text-slate-400 flex items-center justify-between">
          <span>Idempotency Hash: <code className="text-slate-300">{execution.idempotency_key}</code></span>
          <span>Started: {new Date(execution.started_at).toLocaleTimeString()}</span>
        </div>

        {/* Error Details if any */}
        {execution.error_message && (
          <div className="p-3.5 rounded-xl bg-rose-950/20 border border-rose-500/30 text-rose-300 space-y-1">
            <span className="font-bold uppercase tracking-wider text-[10px] flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 text-rose-400" />
              Workflow Execution Error Log
            </span>
            <p className="text-[11px] font-mono leading-relaxed">{execution.error_message}</p>
          </div>
        )}

        {/* Action Logs Table */}
        <div className="space-y-2">
          <span className="font-bold text-slate-200 uppercase tracking-wider text-[11px] block">
            Action Execution Outcomes ({execution.actions.length})
          </span>

          {execution.actions.length > 0 ? (
            <div className="space-y-2">
              {execution.actions.map((act) => (
                <div
                  key={act.id}
                  className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col gap-1 text-[11px]"
                >
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-indigo-300 flex items-center gap-1.5">
                      {act.status === 'SUCCESS' ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <XCircle className="w-3.5 h-3.5 text-rose-400" />
                      )}
                      {act.action_type}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      act.status === 'SUCCESS' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
                    }`}>
                      {act.status}
                    </span>
                  </div>

                  {act.error_message && (
                    <span className="text-rose-400 text-[10px] pt-1">Error: {act.error_message}</span>
                  )}

                  {Object.keys(act.result_payload).length > 0 && (
                    <pre className="p-2 bg-slate-900 rounded border border-slate-800/80 text-[10px] text-slate-300 overflow-x-auto mt-1">
                      {JSON.stringify(act.result_payload, null, 2)}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="p-4 bg-slate-950/40 rounded-xl border border-slate-800/60 text-center text-slate-500 text-xs">
              No actions executed for this workflow run (Conditions evaluated to false).
            </div>
          )}
        </div>
      </div>
    </GlassModal>
  );
};
