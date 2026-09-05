import React, { useEffect, useState } from 'react';
import { ApprovalAuditLog } from '../../types';
import { negotiationApi } from '../../services/negotiationApi';
import { ShieldCheck, FileText, CheckCircle2, XCircle, RefreshCw, Clock } from 'lucide-react';

interface ApprovalAuditTimelineProps {
  quotationId: string;
}

export const ApprovalAuditTimeline: React.FC<ApprovalAuditTimelineProps> = ({ quotationId }) => {
  const [logs, setLogs] = useState<ApprovalAuditLog[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await negotiationApi.getAuditLogs(quotationId);
      setLogs(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load approval audit logs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [quotationId]);

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'APPROVAL_APPROVED':
        return <CheckCircle2 className="w-5 h-5 text-emerald-400" />;
      case 'APPROVAL_REJECTED':
        return <XCircle className="w-5 h-5 text-rose-400" />;
      case 'APPROVAL_INVALIDATED':
        return <RefreshCw className="w-5 h-5 text-amber-400" />;
      case 'APPROVAL_SUBMITTED':
        return <Clock className="w-5 h-5 text-sky-400" />;
      default:
        return <FileText className="w-5 h-5 text-slate-400" />;
    }
  };

  if (loading) {
    return (
      <div className="p-4 text-center text-slate-400 text-sm animate-pulse">
        Loading approval audit logs...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-lg text-rose-300 text-sm">
        {error}
      </div>
    );
  }

  if (logs.length === 0) {
    return (
      <div className="p-6 text-center text-slate-400 text-sm border border-slate-700/50 rounded-xl bg-slate-800/30">
        No approval audit events recorded for this quotation yet.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold text-white flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-emerald-400" />
          Approval Audit Trail
        </h3>
        <span className="text-xs text-slate-400 bg-slate-800 px-2.5 py-1 rounded-full border border-slate-700">
          {logs.length} Events Recorded
        </span>
      </div>

      <div className="relative border-l border-slate-700/70 ml-3 space-y-6 py-2">
        {logs.map((log) => (
          <div key={log.id} className="relative pl-6">
            <div className="absolute -left-2.5 top-0.5 bg-slate-900 rounded-full p-0.5">
              {getEventIcon(log.event_type)}
            </div>

            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">
                  {log.event_type.replace('_', ' ')}
                </span>
                <span className="text-xs text-slate-400">
                  {new Date(log.created_at).toLocaleString()}
                </span>
              </div>

              <div className="text-sm text-slate-200">
                <span className="font-medium text-white">{log.actor_name || 'System / Automated'}</span>
                {' transitioned status to '}
                <span className="font-semibold text-slate-100 px-2 py-0.5 bg-slate-700/70 rounded text-xs">
                  {log.new_status}
                </span>
              </div>

              {log.reason && (
                <div className="text-xs text-slate-300 bg-slate-900/50 p-2.5 rounded-lg border border-slate-700/40">
                  <span className="text-slate-400 font-medium">Trigger Details: </span>
                  {log.reason}
                </div>
              )}

              {log.notes && (
                <div className="text-xs text-emerald-300 bg-emerald-950/30 p-2.5 rounded-lg border border-emerald-800/40">
                  <span className="text-emerald-400 font-medium">Approver Note: </span>
                  {log.notes}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
