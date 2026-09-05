import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, AlertTriangle, ShieldAlert, Info, ArrowRight, CheckCircle2 } from 'lucide-react';
import { AlertsResponse } from '../../types';
import { GlassDrawer } from '../ui/GlassDrawer';

interface NotificationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  alertsData: AlertsResponse | null;
  isLoading?: boolean;
}

export const NotificationDrawer: React.FC<NotificationDrawerProps> = ({
  isOpen,
  onClose,
  alertsData,
  isLoading
}) => {
  const navigate = useNavigate();

  const handleItemClick = (entityType?: string | null, entityId?: string | null) => {
    if (!entityType || !entityId) return;
    onClose();
    if (entityType === 'deal') {
      navigate(`/deals/${entityId}`);
    } else if (entityType === 'customer') {
      navigate(`/customers/${entityId}`);
    } else if (entityType === 'quotation') {
      navigate(`/quotations/${entityId}`);
    } else if (entityType === 'activity') {
      navigate(`/activities`);
    }
  };

  return (
    <GlassDrawer
      isOpen={isOpen}
      onClose={onClose}
      title={
        <div className="flex items-center gap-2 text-slate-100">
          <Bell className="w-5 h-5 text-indigo-400" />
          <span>In-App Alert Notifications</span>
        </div>
      }
    >
      {isLoading || !alertsData ? (
        <div className="space-y-3 p-4 animate-pulse">
          <div className="h-16 bg-white/5 rounded"></div>
          <div className="h-16 bg-white/5 rounded"></div>
        </div>
      ) : alertsData.alerts.length === 0 ? (
        <div className="text-center py-12 px-4 text-slate-400">
          <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto mb-3 opacity-80" />
          <h3 className="text-sm font-bold text-slate-200 font-mono">YOU'RE ALL CAUGHT UP</h3>
          <p className="text-xs text-slate-400 mt-1">No unread CRM alert notifications.</p>
        </div>
      ) : (
        <div className="space-y-3 text-xs">
          <div className="flex justify-between items-center px-1 text-[11px] text-slate-400 font-mono">
            <span>{alertsData.unread_count} Unread Alerts</span>
            <span>Generated UTC</span>
          </div>

          <div className="space-y-2">
            {alertsData.alerts.map((alert) => {
              const isCrit = alert.severity === 'critical';
              const isWarn = alert.severity === 'warning';

              return (
                <div
                  key={alert.id}
                  onClick={() => handleItemClick(alert.entity_type, alert.entity_id)}
                  className={`p-3.5 rounded-xl border backdrop-blur-md transition cursor-pointer group ${
                    isCrit ? 'bg-rose-500/10 border-rose-500/30 hover:border-rose-500/50' :
                    isWarn ? 'bg-amber-500/10 border-amber-500/30 hover:border-amber-500/50' :
                    'bg-slate-900/60 border-white/10 hover:border-indigo-500/30'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <span className="font-bold text-slate-100 flex items-center gap-1.5 text-sm group-hover:text-indigo-300 transition">
                      {isCrit ? <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0" /> :
                       isWarn ? <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" /> :
                       <Info className="w-4 h-4 text-cyan-400 shrink-0" />}
                      {alert.title}
                    </span>
                    <span className={`text-[9px] uppercase font-mono px-1.5 py-0.5 rounded font-bold ${
                      isCrit ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' :
                      isWarn ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                      'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                    }`}>
                      {alert.severity}
                    </span>
                  </div>

                  <p className="text-slate-300 text-xs leading-relaxed pl-5">{alert.message}</p>

                  {alert.entity_type && (
                    <div className="mt-2.5 pl-5 flex items-center justify-between text-[11px] font-mono text-indigo-300">
                      <span className="capitalize">Entity: {alert.entity_type}</span>
                      <span className="flex items-center gap-1 font-bold group-hover:translate-x-1 transition-transform">
                        Open <ArrowRight className="w-3 h-3" />
                      </span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </GlassDrawer>
  );
};
