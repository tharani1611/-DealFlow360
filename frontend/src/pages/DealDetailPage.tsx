import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { dealApi } from '../services/dealApi';
import { activityApi } from '../services/activityApi';
import { aiApi } from '../services/aiApi';
import { intelligenceApi } from '../services/intelligenceApi';
import { forecastApi } from '../services/forecastApi';
import {
  Deal,
  Activity,
  DealAnalysisResponse,
  NextActionResponse,
  DealHealthResponse,
  DealStage,
  ActivityType,
  ActivityPriority,
  DealForecastItem
} from '../types';
import { GlassCard } from '../components/ui/GlassCard';
import { StatusBadge } from '../components/ui/StatusBadge';
import { BrutalButton } from '../components/ui/BrutalButton';
import { AIInsightCard, AIRecommendation } from '../components/ui/AIInsightCard';
import { DealHealthCard } from '../components/intelligence/DealHealthCard';
import { Timeline } from '../components/ui/Timeline';
import { GlassModal } from '../components/ui/GlassModal';
import { GlassInput } from '../components/ui/GlassInput';
import { GlassSelect } from '../components/ui/GlassSelect';
import { GlassTextarea } from '../components/ui/GlassTextarea';
import { LoadingState, ErrorState } from '../components/ui/EmptyState';
import { useToast } from '../context/ToastContext';
import { ArrowLeft, Plus, TrendingUp } from 'lucide-react';

const STAGES: DealStage[] = ['new', 'qualified', 'proposal', 'negotiation', 'won', 'lost'];

export const DealDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [deal, setDeal] = useState<Deal | null>(null);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [health, setHealth] = useState<DealHealthResponse | null>(null);
  const [forecastItem, setForecastItem] = useState<DealForecastItem | null>(null);

  // AI Responses
  const [aiAnalysis, setAiAnalysis] = useState<DealAnalysisResponse | null>(null);
  const [aiNextAction, setAiNextAction] = useState<NextActionResponse | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // New Activity Modal
  const [isActivityModalOpen, setIsActivityModalOpen] = useState(false);
  const [isCreatingActivity, setIsCreatingActivity] = useState(false);
  const [actType, setActType] = useState<ActivityType>('follow_up');
  const [actTitle, setActTitle] = useState('');
  const [actDescription, setActDescription] = useState('');
  const [actPriority, setActPriority] = useState<ActivityPriority>('medium');

  const loadDealData = async () => {
    if (!id) return;
    setIsLoading(true);
    setError(null);
    try {
      const [dealData, actData, healthData, fcData] = await Promise.all([
        dealApi.getDeal(id),
        activityApi.getDealActivities(id),
        intelligenceApi.getDealHealth(id).catch(() => null),
        forecastApi.getForecast().catch(() => null),
      ]);
      setDeal(dealData);
      setActivities(actData);
      setHealth(healthData);

      if (fcData && fcData.deals) {
        const item = fcData.deals.find((d) => d.deal_id === id);
        if (item) setForecastItem(item);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve deal telemetry.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDealData();
  }, [id]);

  const handleRunAiDiagnostics = async () => {
    if (!id) return;
    setIsAiLoading(true);
    try {
      const [anaRes, nextRes, healthRes] = await Promise.all([
        aiApi.getDealAnalysis(id),
        aiApi.getNextAction(id),
        intelligenceApi.getDealHealth(id).catch(() => null),
      ]);
      setAiAnalysis(anaRes);
      setAiNextAction(nextRes);
      if (healthRes) setHealth(healthRes);
      showToast('AI Deal Intelligence telemetry refreshed.', 'success');
    } catch (err: any) {
      showToast(err.message || 'Failed to run AI deal diagnostics.', 'error');
    } finally {
      setIsAiLoading(false);
    }
  };

  const handleCreateActivitySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !deal || !actTitle.trim()) return;

    setIsCreatingActivity(true);
    try {
      await activityApi.createActivity({
        deal_id: id,
        customer_id: deal.customer_id,
        contact_id: deal.contact_id || undefined,
        activity_type: actType,
        title: actTitle.trim(),
        description: actDescription.trim() || undefined,
        priority: actPriority,
      });
      showToast('Activity logged successfully.', 'success');
      setIsActivityModalOpen(false);
      setActTitle('');
      setActDescription('');
      loadDealData();
    } catch (err: any) {
      showToast(err.message || 'Failed to log activity.', 'error');
    } finally {
      setIsCreatingActivity(false);
    }
  };

  const handleExecuteNextActionRecommendation = () => {
    if (!aiNextAction) return;
    setActType(aiNextAction.action_type);
    setActTitle(aiNextAction.title);
    setActDescription(`Recommended by AI: ${aiNextAction.reason}`);
    setActPriority(aiNextAction.priority);
    setIsActivityModalOpen(true);
  };

  const handleCompleteActivity = async (actId: string) => {
    try {
      await activityApi.completeActivity(actId);
      showToast('Activity completed.', 'success');
      loadDealData();
    } catch (err: any) {
      showToast(err.message || 'Failed to complete activity.', 'error');
    }
  };

  if (isLoading) return <LoadingState message="Loading deal telemetry..." />;
  if (error || !deal) return <ErrorState message={error || 'Deal not found'} onRetry={loadDealData} />;

  const currentStageIndex = STAGES.indexOf(deal.stage);

  return (
    <div className="space-y-8">
      {/* Back Button */}
      <button
        onClick={() => navigate('/deals')}
        className="flex items-center gap-2 text-xs font-bold text-slate-400 hover:text-slate-100 transition"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Pipeline Command</span>
      </button>

      {/* Executive Snapshot Top Bar */}
      {health && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 p-4 rounded-xl bg-slate-900/80 border border-slate-800 backdrop-blur-glass shadow-neo">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-black font-mono text-sm border ${
              health.health_score >= 80 ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' :
              health.health_score >= 60 ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40' :
              health.health_score >= 40 ? 'bg-amber-500/20 text-amber-300 border-amber-500/40' :
              'bg-rose-500/20 text-rose-300 border-rose-500/40'
            }`}>
              {health.health_score}
            </div>
            <div>
              <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">Health Telemetry</div>
              <div className="text-xs font-bold text-slate-100 uppercase">{health.health_status.replace('_', ' ')}</div>
            </div>
          </div>

          <div>
            <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">Expected Close</div>
            <div className="text-xs font-bold font-mono text-slate-200 mt-0.5">
              {health.metrics.days_until_expected_close !== null && health.metrics.days_until_expected_close !== undefined
                ? `${health.metrics.days_until_expected_close} days remaining`
                : deal.expected_close_date || 'Target date unset'}
            </div>
          </div>

          <div>
            <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">Primary Risk Factor</div>
            <div className="text-xs font-bold text-slate-200 truncate mt-0.5">
              {health.risk_factors.length > 0 ? (
                <span className="text-rose-400 flex items-center gap-1">
                  {health.risk_factors[0].title}
                </span>
              ) : (
                <span className="text-emerald-400">Zero active risk triggers</span>
              )}
            </div>
          </div>

          <div>
            <div className="text-[10px] font-mono text-slate-400 uppercase font-bold">Overdue Touchpoints</div>
            <div className="text-xs font-bold font-mono mt-0.5">
              {health.metrics.overdue_activity_count > 0 ? (
                <span className="text-amber-400">{health.metrics.overdue_activity_count} overdue activity items</span>
              ) : (
                <span className="text-emerald-400">Timeline up to date</span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Hero Deal Card */}
      <GlassCard className="border-l-4 border-l-indigo-500">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl font-black text-slate-100 tracking-tight">{deal.title}</h1>
              <StatusBadge status={deal.stage} />
              <span className="text-xs font-mono text-slate-500 font-bold">{deal.deal_number}</span>
            </div>

            <p className="text-xs text-slate-400 mt-1 font-mono">
              Customer: <span className="text-slate-200 font-bold">{deal.customer?.name || 'Account'}</span>
            </p>
          </div>

          <div className="flex items-center gap-6 flex-wrap font-mono">
            <div>
              <span className="text-[10px] text-slate-400 uppercase font-bold block">Deal Value</span>
              <span className="text-2xl font-black text-emerald-400">${Number(deal.value || 0).toLocaleString()}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 uppercase font-bold block">Win Probability</span>
              <span className="text-2xl font-black text-indigo-400">{deal.probability}%</span>
            </div>

            <BrutalButton
              variant="ai"
              onClick={handleRunAiDiagnostics}
              isLoading={isAiLoading}
            >
              ✦ Run AI Diagnostics
            </BrutalButton>
          </div>
        </div>

        {/* Stage Progress Visualizer */}
        <div className="mt-6 pt-4 border-t border-slate-800">
          <div className="flex items-center justify-between gap-1 overflow-x-auto pb-1">
            {STAGES.map((stg, idx) => {
              const isPassed = idx <= currentStageIndex;
              const isCurrent = idx === currentStageIndex;
              return (
                <div
                  key={stg}
                  className={`flex-1 text-center py-2 px-3 rounded-lg border text-xs font-mono font-bold uppercase transition ${
                    isCurrent
                      ? 'bg-indigo-600 text-white border-indigo-400 shadow-neo-sm'
                      : isPassed
                      ? 'bg-slate-800/80 text-indigo-300 border-indigo-500/30'
                      : 'bg-slate-950/40 text-slate-600 border-slate-800'
                  }`}
                >
                  {stg}
                </div>
              );
            })}
          </div>
        </div>
      </GlassCard>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column (2 spans): AI Analysis + Next Best Action + Activity History */}
        <div className="lg:col-span-2 space-y-8">
          {/* AI Deal Analysis */}
          {aiAnalysis && (
            <AIInsightCard
              title={`AI Deal Analysis: ${aiAnalysis.deal_number}`}
              provider={aiAnalysis.metadata.provider}
              model={aiAnalysis.metadata.model}
              riskLevel={aiAnalysis.risk_level}
            >
              <div className="space-y-4 text-xs">
                <div>
                  <span className="text-[10px] font-mono font-bold text-indigo-400 uppercase tracking-widest">
                    Executive Summary:
                  </span>
                  <p className="text-slate-200 leading-relaxed mt-0.5">{aiAnalysis.summary}</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {aiAnalysis.positive_signals.length > 0 && (
                    <div className="p-3 bg-emerald-950/40 border border-emerald-500/30 rounded-xl">
                      <span className="text-[10px] font-mono font-bold text-emerald-400 uppercase tracking-widest block mb-1">
                        Positive Signals:
                      </span>
                      <ul className="list-disc list-inside space-y-1 text-emerald-200">
                        {aiAnalysis.positive_signals.map((sig, i) => (
                          <li key={i}>{sig}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {aiAnalysis.risks.length > 0 && (
                    <div className="p-3 bg-rose-950/40 border border-rose-500/30 rounded-xl">
                      <span className="text-[10px] font-mono font-bold text-rose-400 uppercase tracking-widest block mb-1">
                        Execution Risks:
                      </span>
                      <ul className="list-disc list-inside space-y-1 text-rose-200">
                        {aiAnalysis.risks.map((rk, i) => (
                          <li key={i}>{rk}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </AIInsightCard>
          )}

          {/* AI Next Best Action Recommendation */}
          {aiNextAction && (
            <AIRecommendation
              title={aiNextAction.title}
              reason={aiNextAction.reason}
              actionType={aiNextAction.action_type}
              priority={aiNextAction.priority}
              onExecute={handleExecuteNextActionRecommendation}
            />
          )}

          {/* Activity Timeline */}
          <GlassCard
            title="Deal Activity Feed & History"
            subtitle="Chronological audit log of interactions"
            action={
              <BrutalButton variant="primary" size="sm" icon={Plus} onClick={() => setIsActivityModalOpen(true)}>
                Log Activity
              </BrutalButton>
            }
          >
            <Timeline activities={activities} onComplete={handleCompleteActivity} />
          </GlassCard>
        </div>

        {/* Right Column (1 span): Deal Health Telemetry & Details */}
        <div className="space-y-8">
          {/* Deal Health Telemetry Card */}
          {health && <DealHealthCard health={health} />}

          {/* Compact Forecast Position Card */}
          {forecastItem && (
            <GlassCard
              title={
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-emerald-300">
                    <TrendingUp className="w-4 h-4 text-emerald-400" />
                    Revenue Forecast Position
                  </span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                    forecastItem.forecast_category === 'COMMITTED' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' :
                    forecastItem.forecast_category === 'UPSIDE' ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40' :
                    forecastItem.forecast_category === 'AT_RISK' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' :
                    'bg-slate-800 text-slate-300'
                  }`}>
                    {forecastItem.forecast_category}
                  </span>
                </div>
              }
            >
              <div className="space-y-2 font-mono text-xs">
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-400">Base Win Probability:</span>
                  <span className="text-slate-200">{forecastItem.base_probability}%</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-400">Adjusted Forecast %:</span>
                  <span className="font-bold text-indigo-300">{forecastItem.adjusted_probability}%</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-400">Forecast Value:</span>
                  <span className="font-extrabold text-emerald-400">${Number(forecastItem.forecast_value).toLocaleString()}</span>
                </div>
                <div className="pt-2 text-[11px]">
                  <span className="text-slate-400 block mb-1">Forecast Driver Rationale:</span>
                  <p className="p-2 rounded bg-slate-950/80 border border-slate-800 text-slate-300 leading-relaxed font-sans">
                    {forecastItem.forecast_category === 'AT_RISK' ? forecastItem.primary_negative_factor : forecastItem.primary_positive_factor}
                  </p>
                </div>
              </div>
            </GlassCard>
          )}

          {/* Deal Metadata Details */}
          <GlassCard title="Deal Attributes" subtitle="Record properties">
            <div className="space-y-3 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">Deal Number</span>
                <span className="font-mono font-bold text-slate-100">{deal.deal_number}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">Status</span>
                <StatusBadge status={deal.status} size="sm" />
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">Close Date</span>
                <span className="font-mono text-slate-100">
                  {deal.expected_close_date || 'Unspecified'}
                </span>
              </div>
              {deal.notes && (
                <div className="pt-2">
                  <span className="text-[10px] uppercase text-slate-400 font-bold block mb-1">Notes</span>
                  <p className="p-2.5 bg-slate-950/80 rounded-lg text-slate-300 font-mono text-[11px] leading-relaxed">
                    {deal.notes}
                  </p>
                </div>
              )}
            </div>
          </GlassCard>
        </div>
      </div>

      {/* Log Activity Modal */}
      <GlassModal
        isOpen={isActivityModalOpen}
        onClose={() => setIsActivityModalOpen(false)}
        title="Log CRM Activity"
      >
        <form onSubmit={handleCreateActivitySubmit} className="space-y-4">
          <GlassSelect
            label="Activity Type"
            value={actType}
            onChange={(e) => setActType(e.target.value as ActivityType)}
            options={[
              { value: 'follow_up', label: 'Follow Up' },
              { value: 'call', label: 'Phone Call' },
              { value: 'meeting', label: 'Meeting' },
              { value: 'task', label: 'General Task' },
              { value: 'email', label: 'Email' },
            ]}
          />

          <GlassInput
            label="Activity Title"
            value={actTitle}
            onChange={(e) => setActTitle(e.target.value)}
            placeholder="e.g. Follow up call regarding commercial quote"
            required
          />

          <GlassTextarea
            label="Description / Context"
            value={actDescription}
            onChange={(e) => setActDescription(e.target.value)}
            placeholder="Record discussion outcomes or meeting notes..."
            rows={3}
          />

          <GlassSelect
            label="Priority Level"
            value={actPriority}
            onChange={(e) => setActPriority(e.target.value as ActivityPriority)}
            options={[
              { value: 'low', label: 'Low' },
              { value: 'medium', label: 'Medium' },
              { value: 'high', label: 'High' },
              { value: 'urgent', label: 'Urgent' },
            ]}
          />

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
            <BrutalButton variant="ghost" onClick={() => setIsActivityModalOpen(false)}>
              Cancel
            </BrutalButton>
            <BrutalButton type="submit" variant="primary" isLoading={isCreatingActivity}>
              Log Activity Record
            </BrutalButton>
          </div>
        </form>
      </GlassModal>
    </div>
  );
};
