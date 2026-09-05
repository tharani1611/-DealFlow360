import React, { useState, useEffect } from 'react';
import { activityApi } from '../services/activityApi';
import { intelligenceApi } from '../services/intelligenceApi';
import { Activity, ActivityProductivityMetrics } from '../types';
import { Timeline } from '../components/ui/Timeline';
import { Tabs } from '../components/ui/Tabs';
import { GlassCard } from '../components/ui/GlassCard';
import { LoadingState, ErrorState } from '../components/ui/EmptyState';
import { useToast } from '../context/ToastContext';
import { CheckCircle2, AlertTriangle, Calendar, Activity as ActivityIcon } from 'lucide-react';

export const ActivitiesPage: React.FC = () => {
  const { showToast } = useToast();

  const [activities, setActivities] = useState<Activity[]>([]);
  const [metrics, setMetrics] = useState<ActivityProductivityMetrics | null>(null);
  const [activeTab, setActiveTab] = useState('all');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadActivities = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [actData, prodMetrics] = await Promise.all([
        activityApi.getActivities(),
        intelligenceApi.getActivityProductivity().catch(() => null),
      ]);
      setActivities(actData);
      setMetrics(prodMetrics);
    } catch (err: any) {
      setError(err.message || 'Failed to load CRM activity feed.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadActivities();
  }, []);

  const handleComplete = async (id: string) => {
    try {
      await activityApi.completeActivity(id);
      showToast('Activity marked as completed.', 'success');
      loadActivities();
    } catch (err: any) {
      showToast(err.message || 'Failed to complete activity.', 'error');
    }
  };

  const handleCancel = async (id: string) => {
    try {
      await activityApi.cancelActivity(id);
      showToast('Activity cancelled.', 'success');
      loadActivities();
    } catch (err: any) {
      showToast(err.message || 'Failed to cancel activity.', 'error');
    }
  };

  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const todayEnd = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59);

  const filteredActivities = activities.filter((act) => {
    if (activeTab === 'all') return true;
    if (activeTab === 'pending') return act.status === 'pending';
    if (activeTab === 'completed') return act.status === 'completed';
    if (activeTab === 'cancelled') return act.status === 'cancelled';
    if (activeTab === 'today') {
      if (!act.due_at) return false;
      const d = new Date(act.due_at);
      return d >= todayStart && d <= todayEnd;
    }
    if (activeTab === 'upcoming') {
      if (!act.due_at) return false;
      return new Date(act.due_at) > todayEnd && act.status === 'pending';
    }
    if (activeTab === 'overdue') {
      return act.status === 'pending' && act.due_at && new Date(act.due_at) < todayStart;
    }
    return true;
  });

  const tabs = [
    { id: 'all', label: 'All Activities', count: activities.length },
    {
      id: 'today',
      label: 'Today',
      count: activities.filter((a) => a.due_at && new Date(a.due_at) >= todayStart && new Date(a.due_at) <= todayEnd).length,
    },
    {
      id: 'upcoming',
      label: 'Upcoming',
      count: activities.filter((a) => a.due_at && new Date(a.due_at) > todayEnd && a.status === 'pending').length,
    },
    {
      id: 'overdue',
      label: 'Overdue',
      count: activities.filter((a) => a.status === 'pending' && a.due_at && new Date(a.due_at) < todayStart).length,
    },
    { id: 'pending', label: 'Pending', count: activities.filter((a) => a.status === 'pending').length },
    { id: 'completed', label: 'Completed', count: activities.filter((a) => a.status === 'completed').length },
    { id: 'cancelled', label: 'Cancelled', count: activities.filter((a) => a.status === 'cancelled').length },
  ];

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-black text-slate-100 tracking-tight">CRM Activity Log & Productivity</h1>
        <p className="text-xs text-slate-400 font-mono mt-0.5">
          Global touchpoints, calls, tasks, follow-up timelines and execution metrics
        </p>
      </div>

      {/* Activity Productivity Metrics Header */}
      {metrics && (
        <GlassCard className="p-4 border-l-4 border-l-indigo-500">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
            <div className="p-2 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-[10px] font-mono text-indigo-400 uppercase font-bold flex items-center justify-center gap-1">
                <Calendar className="w-3 h-3 text-indigo-400" /> Due Today
              </div>
              <div className="text-lg font-black text-slate-100 font-mono mt-0.5">{metrics.today_count}</div>
            </div>

            <div className="p-2 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-[10px] font-mono text-cyan-400 uppercase font-bold flex items-center justify-center gap-1">
                <ActivityIcon className="w-3 h-3 text-cyan-400" /> Upcoming (7 Days)
              </div>
              <div className="text-lg font-black text-cyan-300 font-mono mt-0.5">{metrics.upcoming_7d_count}</div>
            </div>

            <div className="p-2 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-[10px] font-mono text-rose-400 uppercase font-bold flex items-center justify-center gap-1">
                <AlertTriangle className="w-3 h-3 text-rose-400" /> Overdue Tasks
              </div>
              <div className="text-lg font-black text-rose-400 font-mono mt-0.5">{metrics.overdue_count}</div>
            </div>

            <div className="p-2 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-[10px] font-mono text-emerald-400 uppercase font-bold flex items-center justify-center gap-1">
                <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Completed This Week
              </div>
              <div className="text-lg font-black text-emerald-300 font-mono mt-0.5">{metrics.completed_this_week_count}</div>
            </div>
          </div>
        </GlassCard>
      )}

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {isLoading ? (
        <LoadingState message="Loading activity timeline..." />
      ) : error ? (
        <ErrorState message={error} onRetry={loadActivities} />
      ) : (
        <Timeline
          activities={filteredActivities}
          onComplete={handleComplete}
          onCancel={handleCancel}
        />
      )}
    </div>
  );
};

