import React, { useState, useEffect } from 'react';
import { NeoGlassCard } from '../components/ui/NeoGlassCard';
import { NeoGlassButton } from '../components/ui/NeoGlassButton';
import { StatusBadge } from '../components/ui/StatusBadge';
import { GlassInput } from '../components/ui/GlassInput';
import { GlassSelect } from '../components/ui/GlassSelect';
import { useAuth } from '../context/AuthContext';
import { activityApi } from '../services/activityApi';
import { Activity } from '../types';
import { ShieldCheck, RefreshCw, Search, Activity as ActivityIcon, Users, Clock, Filter } from 'lucide-react';

export const CompanyActivityPage: React.FC = () => {
  const { user } = useAuth();
  const [activities, setActivities] = useState<Activity[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedRoleFilter, setSelectedRoleFilter] = useState<string>('ALL');

  const loadActivities = async () => {
    setIsLoading(true);
    try {
      const list = await activityApi.getActivities({ limit: 50 });
      setActivities(list);
    } catch (err) {
      console.error('Failed to load company activity log:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadActivities();
  }, []);

  const filteredActivities = activities.filter((act) => {
    const matchesSearch =
      !searchQuery ||
      act.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (act.description && act.description.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesRole =
      selectedRoleFilter === 'ALL' ||
      (selectedRoleFilter === 'ADMIN' && (act.created_by_user_id || '').includes('admin')) ||
      (selectedRoleFilter === 'SALES' && (act.created_by_user_id || '').includes('sales')) ||
      (selectedRoleFilter === 'INVENTORY' && (act.created_by_user_id || '').includes('inventory')) ||
      (selectedRoleFilter === 'BILLING' && (act.created_by_user_id || '').includes('billing'));

    return matchesSearch && matchesRole;
  });

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 rounded-full bg-indigo-950 border border-indigo-500/40 text-indigo-300 font-mono text-[10px] font-bold uppercase tracking-widest flex items-center gap-1">
              <ShieldCheck className="w-3 h-3 text-emerald-400" />
              Tenant Audit Log
            </span>
            <span className="text-xs font-mono text-slate-400">Slug: {user?.organization_id?.substring(0, 8) || 'active'}</span>
          </div>
          <h1 className="text-2xl font-black text-slate-100 tracking-tight flex items-center gap-2 mt-1">
            <ActivityIcon className="w-7 h-7 text-indigo-400" />
            Company Activity & Audit Trail
          </h1>
          <p className="text-sm text-slate-400 font-mono">
            Cross-role event logging across Sales, Inventory, Billing, and Administration
          </p>
        </div>

        <NeoGlassButton variant="default" onClick={() => loadActivities()} disabled={isLoading}>
          <RefreshCw className="w-4 h-4 mr-1.5" />
          Refresh Activity Log
        </NeoGlassButton>
      </div>

      {/* Filters Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="sm:col-span-2 relative">
          <GlassInput
            placeholder="Search activity events by title or description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <Search className="w-4 h-4 text-slate-500 absolute right-3 top-3.5" />
        </div>
        <GlassSelect
          value={selectedRoleFilter}
          onChange={(e) => setSelectedRoleFilter(e.target.value)}
          options={[
            { value: 'ALL', label: '👥 All Organization Roles' },
            { value: 'ADMIN', label: '👑 Admin & Governance Events' },
            { value: 'SALES', label: '💼 Sales Representative Actions' },
            { value: 'INVENTORY', label: '📦 Inventory Manager Movements' },
            { value: 'BILLING', label: '💳 Billing Controller Transactions' },
          ]}
        />
      </div>

      {/* Audit Feed */}
      <NeoGlassCard className="p-6">
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
          <h2 className="text-base font-bold text-slate-100 font-mono uppercase tracking-wider flex items-center gap-2">
            <Filter className="w-4 h-4 text-indigo-400" />
            Activity Log ({filteredActivities.length} Events)
          </h2>
          <span className="text-xs font-mono text-slate-400">Real-Time Tenant Telemetry</span>
        </div>

        {isLoading ? (
          <div className="text-center py-12 text-slate-500 font-mono text-sm">
            Loading tenant activity log...
          </div>
        ) : filteredActivities.length === 0 ? (
          <div className="text-center py-12 text-slate-500 font-mono text-sm">
            No activity logs match the selected role filter or search query.
          </div>
        ) : (
          <div className="space-y-4">
            {filteredActivities.map((act) => (
              <div
                key={act.id}
                className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-indigo-500/40 transition flex items-start justify-between gap-4"
              >
                <div className="space-y-1.5 min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="px-2 py-0.5 rounded bg-indigo-950/80 border border-indigo-500/30 text-[10px] font-mono text-indigo-300 font-bold uppercase">
                      {act.activity_type || 'SYSTEM'}
                    </span>
                    <h3 className="font-extrabold text-slate-100 text-sm truncate">{act.title}</h3>
                    <StatusBadge status={act.status} size="sm" />
                  </div>
                  {act.description && (
                    <p className="text-xs text-slate-300 leading-relaxed font-sans">{act.description}</p>
                  )}
                  <div className="flex items-center gap-4 text-[11px] font-mono text-slate-400 pt-1">
                    <span className="flex items-center gap-1">
                      <Users className="w-3.5 h-3.5 text-indigo-400" />
                      Actor ID: {act.created_by_user_id ? act.created_by_user_id.substring(0, 8) : 'System Automated'}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      {new Date(act.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </NeoGlassCard>
    </div>
  );
};
