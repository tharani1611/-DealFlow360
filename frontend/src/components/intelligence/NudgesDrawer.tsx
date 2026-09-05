import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, AlertTriangle, ShieldAlert, CheckCircle2, Eye } from 'lucide-react';
import { NudgesResponse, NudgeStatus } from '../../types';
import { GlassDrawer } from '../ui/GlassDrawer';
import { intelligenceApi } from '../../services/intelligenceApi';

interface NudgesDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  nudgesData: NudgesResponse | null;
  isLoading?: boolean;
  onRefresh?: () => void;
}

export const NudgesDrawer: React.FC<NudgesDrawerProps> = ({
  isOpen,
  onClose,
  nudgesData,
  isLoading,
  onRefresh
}) => {
  const navigate = useNavigate();

  const handleTransition = async (nudgeId: string, targetStatus: NudgeStatus) => {
    try {
      await intelligenceApi.transitionNudgeStatus(nudgeId, targetStatus);
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error('Failed to transition nudge:', err);
    }
  };

  const handleItemClick = (entityType?: string | null, entityId?: string | null) => {
    if (!entityType || !entityId) return;
    onClose();
    if (entityType === 'quotation') {
      navigate(`/quotations`);
    } else if (entityType === 'deal') {
      navigate(`/deals/${entityId}`);
    } else if (entityType === 'customer') {
      navigate(`/customers/${entityId}`);
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/30';
      case 'URGENT':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
      case 'WARNING':
        return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30';
      default:
        return 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30';
    }
  };

  return (
    <GlassDrawer
      isOpen={isOpen}
      onClose={onClose}
      title={
        <div className="flex items-center gap-2 text-slate-100">
          <Sparkles className="w-5 h-5 text-indigo-400" />
          <span>Phase 57 — System Nudges & Escalations</span>
        </div>
      }
    >
      {isLoading || !nudgesData ? (
        <div className="space-y-3 p-4 animate-pulse">
          <div className="h-16 bg-white/5 rounded"></div>
          <div className="h-16 bg-white/5 rounded"></div>
        </div>
      ) : nudgesData.nudges.length === 0 ? (
        <div className="text-center py-12 px-4 text-slate-400">
          <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto mb-3 opacity-80" />
          <h3 className="text-sm font-bold text-slate-200 font-mono">ALL NUDGES CLEARED</h3>
          <p className="text-xs text-slate-400 mt-1">No pending risk or anomaly nudges require action.</p>
        </div>
      ) : (
        <div className="space-y-3 text-xs">
          <div className="flex justify-between items-center px-1 text-[11px] text-slate-400 font-mono">
            <span>{nudgesData.open_count} Open Nudges</span>
            <span className="text-amber-400 font-semibold">{nudgesData.urgent_count} Urgent/Critical</span>
          </div>

          <div className="space-y-2">
            {nudgesData.nudges.map((nudge) => (
              <div
                key={nudge.id}
                className="p-3.5 rounded-xl bg-black/30 border border-white/10 hover:border-white/20 transition backdrop-blur-md relative"
              >
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-1.5 font-bold text-slate-200 text-xs">
                    {nudge.severity === 'CRITICAL' ? (
                      <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                    )}
                    <span>{nudge.title}</span>
                  </div>
                  <span className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold uppercase border ${getSeverityBadge(nudge.severity)}`}>
                    {nudge.severity}
                  </span>
                </div>

                <p className="text-slate-300 text-[11px] leading-relaxed mb-3">
                  {nudge.message}
                </p>

                <div className="flex items-center justify-between pt-2 border-t border-white/10 text-[11px]">
                  <button
                    onClick={() => handleItemClick(nudge.entity_type, nudge.entity_id)}
                    className="flex items-center gap-1 text-indigo-300 hover:text-indigo-200 font-medium transition"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>View {nudge.entity_type}</span>
                  </button>

                  <div className="flex items-center gap-1.5">
                    {nudge.status === 'OPEN' && (
                      <button
                        onClick={() => handleTransition(nudge.id, 'ACKNOWLEDGED')}
                        className="px-2 py-0.5 rounded bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 border border-blue-500/30 transition"
                      >
                        Acknowledge
                      </button>
                    )}
                    {['OPEN', 'ACKNOWLEDGED'].includes(nudge.status) && (
                      <button
                        onClick={() => handleTransition(nudge.id, 'COMPLETED')}
                        className="px-2 py-0.5 rounded bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/30 transition"
                      >
                        Complete
                      </button>
                    )}
                    {['OPEN', 'ACKNOWLEDGED'].includes(nudge.status) && (
                      <button
                        onClick={() => handleTransition(nudge.id, 'DISMISSED')}
                        className="px-2 py-0.5 rounded bg-slate-500/20 hover:bg-slate-500/30 text-slate-300 border border-slate-500/30 transition"
                      >
                        Dismiss
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </GlassDrawer>
  );
};
