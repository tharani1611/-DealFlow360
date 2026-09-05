import React from 'react';
import { Activity } from '../../types';
import { StatusBadge, PriorityBadge } from './StatusBadge';
import { Phone, Mail, Calendar, CheckSquare, FileText, Clock, CheckCircle2, XCircle } from 'lucide-react';
import { BrutalButton } from './BrutalButton';

export interface TimelineProps {
  activities: Activity[];
  onComplete?: (id: string) => void;
  onCancel?: (id: string) => void;
  isLoading?: boolean;
}

export const Timeline: React.FC<TimelineProps> = ({
  activities,
  onComplete,
  onCancel,
  isLoading = false,
}) => {
  if (isLoading) {
    return <div className="text-slate-400 font-mono text-xs p-4">Loading activity timeline...</div>;
  }

  if (activities.length === 0) {
    return (
      <div className="p-8 text-center bg-slate-900/40 rounded-xl border border-slate-800">
        <p className="text-slate-400 font-mono text-xs">No activities recorded yet.</p>
      </div>
    );
  }

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'call': return Phone;
      case 'email': return Mail;
      case 'meeting': return Calendar;
      case 'task': return CheckSquare;
      case 'note': return FileText;
      default: return Clock;
    }
  };

  return (
    <div className="relative pl-6 border-l-2 border-slate-800 space-y-6">
      {activities.map((act) => {
        const Icon = getActivityIcon(act.activity_type);
        const isPending = act.status === 'pending';

        return (
          <div key={act.id} className="relative group">
            {/* Timeline Node */}
            <div className="absolute -left-[31px] top-1 w-6 h-6 rounded-full bg-slate-900 border border-slate-700 flex items-center justify-center text-slate-300 group-hover:border-indigo-500 group-hover:text-indigo-400 transition-colors">
              <Icon className="w-3 h-3" />
            </div>

            {/* Content Card */}
            <div className="bg-slate-900/70 backdrop-blur-glass border border-slate-700/60 rounded-xl p-4 shadow-neo-sm hover:border-slate-600 transition">
              <div className="flex items-start justify-between gap-3 mb-2">
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-extrabold text-slate-100 text-sm">{act.title}</span>
                    <StatusBadge status={act.status} size="sm" />
                    <PriorityBadge priority={act.priority} />
                  </div>
                  {act.description && (
                    <p className="text-xs text-slate-300 mt-1 leading-relaxed">{act.description}</p>
                  )}
                </div>

                <span className="text-[10px] font-mono text-slate-400 whitespace-nowrap">
                  {new Date(act.created_at).toLocaleDateString()}
                </span>
              </div>

              {/* Action Bar */}
              <div className="flex items-center justify-between gap-2 mt-3 pt-2 border-t border-slate-800 text-[11px] font-mono text-slate-400">
                <div>
                  {act.due_at && <span>Due: {new Date(act.due_at).toLocaleDateString()}</span>}
                </div>

                {isPending && (onComplete || onCancel) && (
                  <div className="flex items-center gap-2">
                    {onComplete && (
                      <BrutalButton
                        size="sm"
                        variant="success"
                        icon={CheckCircle2}
                        onClick={() => onComplete(act.id)}
                      >
                        Complete
                      </BrutalButton>
                    )}
                    {onCancel && (
                      <BrutalButton
                        size="sm"
                        variant="ghost"
                        icon={XCircle}
                        onClick={() => onCancel(act.id)}
                      >
                        Cancel
                      </BrutalButton>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
