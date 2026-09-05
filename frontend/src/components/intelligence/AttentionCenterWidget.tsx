import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertOctagon, ArrowRight, ShieldAlert, Clock, Flame, FileText, CheckCircle2 } from 'lucide-react';
import { AttentionCenterResponse, AttentionItem } from '../../types';
import { GlassCard } from '../ui/GlassCard';
import { BrutalButton } from '../ui/BrutalButton';
import { StatusBadge } from '../ui/StatusBadge';

interface AttentionCenterWidgetProps {
  attentionData: AttentionCenterResponse | null;
  isLoading?: boolean;
}

export const AttentionCenterWidget: React.FC<AttentionCenterWidgetProps> = ({
  attentionData,
  isLoading
}) => {
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <GlassCard className="p-5 animate-pulse">
        <div className="h-6 w-40 bg-white/10 rounded mb-4"></div>
        <div className="h-20 bg-white/5 rounded mb-2"></div>
        <div className="h-20 bg-white/5 rounded"></div>
      </GlassCard>
    );
  }

  if (!attentionData || attentionData.items.length === 0) {
    return (
      <GlassCard className="p-6 text-center border-l-4 border-l-emerald-500">
        <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto mb-2 opacity-80" />
        <h3 className="text-sm font-bold text-slate-100 font-mono uppercase tracking-wider">ALL CLEAR</h3>
        <p className="text-xs text-slate-400 mt-1">No urgent sales attention items required right now.</p>
      </GlassCard>
    );
  }

  const handleActionClick = (item: AttentionItem) => {
    if (item.entity_type === 'deal') {
      navigate(`/deals/${item.entity_id}`);
    } else if (item.entity_type === 'customer') {
      navigate(`/customers/${item.entity_id}`);
    } else if (item.entity_type === 'quotation') {
      navigate(`/quotations/${item.entity_id}`);
    } else if (item.entity_type === 'activity') {
      navigate(`/activities`);
    }
  };

  const getItemIcon = (type: string) => {
    switch (type) {
      case 'activity_overdue': return Clock;
      case 'deal_risk': return ShieldAlert;
      case 'customer_cooling': return Flame;
      case 'quotation_pending': return FileText;
      default: return AlertOctagon;
    }
  };

  return (
    <GlassCard
      title={
        <div className="flex items-center gap-2 text-rose-300">
          <AlertOctagon className="w-5 h-5 text-rose-400 animate-pulse" />
          <span>NEEDS ATTENTION</span>
          {attentionData.critical_count > 0 && (
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40 font-mono font-bold">
              {attentionData.critical_count} CRITICAL
            </span>
          )}
        </div>
      }
      subtitle="Prioritized operational items requiring sales action"
      className="border-l-4 border-l-rose-500"
    >
      <div className="space-y-3">
        {attentionData.items.slice(0, 5).map((item) => {
          const Icon = getItemIcon(item.type);
          const isCrit = item.priority === 'critical';
          const isHigh = item.priority === 'high';

          return (
            <div
              key={item.id}
              onClick={() => handleActionClick(item)}
              className={`p-3.5 rounded-xl border backdrop-blur-md transition cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-3 group ${
                isCrit ? 'bg-rose-950/30 border-rose-500/40 hover:border-rose-500/70' :
                isHigh ? 'bg-amber-950/30 border-amber-500/40 hover:border-amber-500/70' :
                'bg-slate-900/60 border-slate-800 hover:border-indigo-500/40'
              }`}
            >
              <div className="flex items-start gap-3">
                <div className={`p-2 rounded-lg shrink-0 mt-0.5 ${
                  isCrit ? 'bg-rose-500/20 text-rose-400' :
                  isHigh ? 'bg-amber-500/20 text-amber-400' : 'bg-indigo-500/20 text-indigo-400'
                }`}>
                  <Icon className="w-4 h-4" />
                </div>

                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-bold text-slate-100 text-xs sm:text-sm group-hover:text-indigo-300 transition">
                      {item.title}
                    </span>
                    <StatusBadge
                      status={item.priority}
                      variant={isCrit ? 'danger' : isHigh ? 'warning' : 'info'}
                      size="sm"
                    />
                  </div>
                  <p className="text-xs text-slate-300 mt-1">{item.description}</p>
                </div>
              </div>

              <div className="shrink-0 text-right">
                <BrutalButton
                  variant={isCrit ? 'danger' : 'secondary'}
                  size="sm"
                  icon={ArrowRight}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleActionClick(item);
                  }}
                  className="text-xs py-1"
                >
                  {item.action_label}
                </BrutalButton>
              </div>
            </div>
          );
        })}
      </div>
    </GlassCard>
  );
};
