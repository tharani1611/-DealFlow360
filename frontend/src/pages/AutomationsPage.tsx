import React, { useState, useEffect } from 'react';
import { automationsApi } from '../services/automationsApi';
import {
  AutomationRule,
  AutomationExecution,
  AutomationAnalyticsSummary,
  AIRuleRecommendation,
  AutomationRuleCreate
} from '../types';
import { GlassCard } from '../components/ui/GlassCard';
import { BrutalButton } from '../components/ui/BrutalButton';
import { AIInsightCard } from '../components/ui/AIInsightCard';
import { LoadingState, ErrorState } from '../components/ui/EmptyState';
import { useToast } from '../context/ToastContext';
import { AutomationRuleModal } from '../components/automations/AutomationRuleModal';
import { ExecutionDetailModal } from '../components/automations/ExecutionDetailModal';
import {
  Workflow,
  Plus,
  Play,
  Pause,
  Trash2,
  Sparkles
} from 'lucide-react';

export const AutomationsPage: React.FC = () => {
  const { showToast } = useToast();

  const [rules, setRules] = useState<AutomationRule[]>([]);
  const [executions, setExecutions] = useState<AutomationExecution[]>([]);
  const [analytics, setAnalytics] = useState<AutomationAnalyticsSummary | null>(null);
  const [aiRecommendations, setAiRecommendations] = useState<AIRuleRecommendation[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Tabs & Filters
  const [activeTab, setActiveTab] = useState<'rules' | 'executions'>('rules');
  const [selectedStatusFilter, setSelectedStatusFilter] = useState<string>('all');

  // Modals
  const [isRuleModalOpen, setIsRuleModalOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<AutomationRule | null>(null);
  const [selectedExecution, setSelectedExecution] = useState<AutomationExecution | null>(null);
  const [isRetrying, setIsRetrying] = useState(false);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [rulesData, execsData, summaryData] = await Promise.all([
        automationsApi.getRules({ status: selectedStatusFilter !== 'all' ? selectedStatusFilter : undefined }),
        automationsApi.getExecutions(),
        automationsApi.getAnalyticsSummary()
      ]);
      setRules(rulesData);
      setExecutions(execsData);
      setAnalytics(summaryData);
    } catch (err: any) {
      setError(err.message || 'Failed to load automation data.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedStatusFilter]);

  const handleFetchAiRecommendations = async () => {
    setIsAiLoading(true);
    try {
      const recs = await automationsApi.getAiRecommendations();
      setAiRecommendations(recs);
      showToast('AI Automation Rule recommendations generated.', 'ai');
    } catch (err: any) {
      showToast(err.message || 'Failed to generate AI recommendations.', 'error');
    } finally {
      setIsAiLoading(false);
    }
  };

  const handleCreateRule = async (payload: AutomationRuleCreate) => {
    if (editingRule) {
      await automationsApi.updateRule(editingRule.id, payload);
      showToast('Automation rule updated.', 'success');
    } else {
      await automationsApi.createRule(payload);
      showToast('Automation rule created in DRAFT state.', 'success');
    }
    loadData();
  };

  const handleToggleActivate = async (rule: AutomationRule) => {
    try {
      if (rule.status === 'ACTIVE') {
        await automationsApi.pauseRule(rule.id);
        showToast(`Rule "${rule.name}" paused.`, 'info');
      } else {
        await automationsApi.activateRule(rule.id);
        showToast(`Rule "${rule.name}" activated.`, 'success');
      }
      loadData();
    } catch (err: any) {
      showToast(err.message || 'Failed to update rule status.', 'error');
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    if (!window.confirm('Are you sure you want to delete this automation rule?')) return;
    try {
      await automationsApi.deleteRule(ruleId);
      showToast('Automation rule deleted.', 'info');
      loadData();
    } catch (err: any) {
      showToast(err.message || 'Failed to delete rule.', 'error');
    }
  };

  const handleRetryExecution = async (executionId: string) => {
    setIsRetrying(true);
    try {
      const updated = await automationsApi.retryExecution(executionId);
      setSelectedExecution(updated);
      showToast('Workflow execution retried successfully.', 'success');
      loadData();
    } catch (err: any) {
      showToast(err.message || 'Retry attempt failed.', 'error');
    } finally {
      setIsRetrying(false);
    }
  };

  const handleAcceptAiRecommendation = async (rec: AIRuleRecommendation) => {
    try {
      await automationsApi.createRule({
        name: rec.rule_name,
        description: rec.description,
        trigger_type: rec.trigger_type,
        priority: 10,
        conditions: rec.recommended_conditions,
        actions: rec.recommended_actions
      });
      showToast(`Rule "${rec.rule_name}" created from AI recommendation.`, 'ai');
      loadData();
    } catch (err: any) {
      showToast(err.message || 'Failed to create rule from recommendation.', 'error');
    }
  };

  if (isLoading) return <LoadingState message="Loading automation rules & workflow execution telemetry..." />;
  if (error) return <ErrorState message={error} onRetry={loadData} />;

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-indigo-400 font-mono text-xs font-bold uppercase tracking-widest">
            <Workflow className="w-4 h-4 text-indigo-400" />
            <span>Commercial Workflow Engine</span>
          </div>
          <h1 className="text-3xl font-black text-slate-100 tracking-tight mt-1">Automation & Workflows</h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Deterministic trigger evaluation, typed condition matching, automated action execution, and audit history
          </p>
        </div>

        <div className="flex items-center gap-3">
          <BrutalButton
            variant="ai"
            size="sm"
            icon={Sparkles}
            onClick={handleFetchAiRecommendations}
            isLoading={isAiLoading}
          >
            ✦ AI Rule Recommendations
          </BrutalButton>

          <BrutalButton
            variant="primary"
            size="sm"
            icon={Plus}
            onClick={() => {
              setEditingRule(null);
              setIsRuleModalOpen(true);
            }}
          >
            New Workflow Rule
          </BrutalButton>
        </div>
      </div>

      {/* Primary Analytics KPI Hero Grid */}
      {analytics && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono">
          <GlassCard className="p-5 border-l-4 border-l-emerald-500 bg-emerald-950/10">
            <span className="text-[10px] text-slate-400 uppercase font-sans font-bold block">Active Rules</span>
            <span className="text-2xl font-black text-emerald-400 block mt-1">{analytics.active_rules}</span>
            <span className="text-[10px] text-slate-500 block mt-1">{analytics.total_rules} Total Configured</span>
          </GlassCard>

          <GlassCard className="p-5 border-l-4 border-l-indigo-500 bg-indigo-950/10">
            <span className="text-[10px] text-slate-400 uppercase font-sans font-bold block">Executions Today</span>
            <span className="text-2xl font-black text-indigo-300 block mt-1">{analytics.executions_today}</span>
            <span className="text-[10px] text-slate-500 block mt-1">{analytics.skipped_executions} Skipped Criteria</span>
          </GlassCard>

          <GlassCard className="p-5 border-l-4 border-l-cyan-500 bg-cyan-950/10">
            <span className="text-[10px] text-slate-400 uppercase font-sans font-bold block">Success Rate</span>
            <span className="text-2xl font-bold text-cyan-300 block mt-1">{analytics.success_rate_percent}%</span>
            <span className="text-[10px] text-slate-500 block mt-1">{analytics.successful_executions} Successful</span>
          </GlassCard>

          <GlassCard className="p-5 border-l-4 border-l-rose-500 bg-rose-950/10">
            <span className="text-[10px] text-slate-400 uppercase font-sans font-bold block">Failed Executions</span>
            <span className="text-2xl font-bold text-rose-400 block mt-1">{analytics.failed_executions}</span>
            <span className="text-[10px] text-slate-500 block mt-1">Requires Attention</span>
          </GlassCard>
        </div>
      )}

      {/* AI Rule Recommendations Section */}
      {aiRecommendations.length > 0 && (
        <AIInsightCard
          title="AI Automation Rule Recommendations"
          provider="DealFlow360 Intelligence Engine"
          model="Advisory Pattern Analysis Model"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
            {aiRecommendations.map((rec, idx) => (
              <div key={idx} className="p-4 bg-slate-950/90 rounded-xl border border-indigo-500/30 flex flex-col justify-between gap-3">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-100 text-xs">{rec.rule_name}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-bold">
                      {rec.trigger_type}
                    </span>
                  </div>
                  <p className="text-slate-400 text-[11px] mt-1">{rec.description}</p>
                  <span className="text-[10px] text-indigo-400 block mt-2">💡 Why: {rec.reason}</span>
                </div>

                <div className="pt-2 border-t border-slate-800 flex justify-end">
                  <BrutalButton
                    variant="ai"
                    size="sm"
                    onClick={() => handleAcceptAiRecommendation(rec)}
                  >
                    + Create Rule
                  </BrutalButton>
                </div>
              </div>
            ))}
          </div>
        </AIInsightCard>
      )}

      {/* Main Tab Navigation */}
      <div className="flex items-center gap-2 border-b border-slate-800 font-mono text-xs pb-1">
        <button
          onClick={() => setActiveTab('rules')}
          className={`px-4 py-2 font-bold uppercase transition rounded-t-lg ${
            activeTab === 'rules'
              ? 'bg-slate-900 text-indigo-300 border-t-2 border-indigo-500'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Rules Workspace ({rules.length})
        </button>

        <button
          onClick={() => setActiveTab('executions')}
          className={`px-4 py-2 font-bold uppercase transition rounded-t-lg ${
            activeTab === 'executions'
              ? 'bg-slate-900 text-indigo-300 border-t-2 border-indigo-500'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Execution History Log ({executions.length})
        </button>
      </div>

      {/* TAB 1: RULES WORKSPACE */}
      {activeTab === 'rules' && (
        <GlassCard
          title={
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <span>Automation Rules Workspace</span>
              <div className="flex items-center gap-2 flex-wrap text-xs font-mono">
                <span className="text-slate-400 uppercase text-[10px] font-bold">Status:</span>
                {['all', 'ACTIVE', 'PAUSED', 'DRAFT', 'ARCHIVED'].map((st) => (
                  <button
                    key={st}
                    onClick={() => setSelectedStatusFilter(st)}
                    className={`px-2.5 py-1 rounded-lg border text-[11px] font-bold uppercase transition ${
                      selectedStatusFilter === st
                        ? 'bg-indigo-600 text-white border-indigo-500'
                        : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
                    }`}
                  >
                    {st}
                  </button>
                ))}
              </div>
            </div>
          }
          subtitle="Configure deterministic event triggers, IF condition logic, and THEN action pipelines"
        >
          {rules.length > 0 ? (
            <div className="space-y-3 font-mono text-xs">
              {rules.map((rule) => {
                const isActive = rule.status === 'ACTIVE';
                const isPaused = rule.status === 'PAUSED';
                const isDraft = rule.status === 'DRAFT';

                return (
                  <div
                    key={rule.id}
                    className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 hover:border-slate-700 transition flex flex-col md:flex-row md:items-center justify-between gap-4"
                  >
                    <div className="space-y-1.5 flex-1 min-w-0">
                      <div className="flex items-center gap-3 flex-wrap">
                        <span className="font-extrabold text-slate-100 text-sm">{rule.name}</span>
                        <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold uppercase border ${
                          isActive
                            ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                            : isPaused
                            ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                            : isDraft
                            ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40'
                            : 'bg-slate-800 text-slate-400 border-slate-700'
                        }`}>
                          {rule.status}
                        </span>
                        <span className="text-[10px] bg-slate-900 border border-slate-800 text-slate-300 px-2 py-0.5 rounded">
                          Priority: {rule.priority}
                        </span>
                      </div>

                      {rule.description && (
                        <p className="text-slate-400 text-xs font-sans">{rule.description}</p>
                      )}

                      <div className="flex items-center gap-4 text-[11px] text-slate-400 pt-1 flex-wrap">
                        <span>Trigger: <code className="text-indigo-300 font-bold">{rule.trigger_type}</code></span>
                        <span>Conditions: <code className="text-slate-200">{rule.conditions?.conditions?.length || 0} rules</code></span>
                        <span>Actions: <code className="text-emerald-300">{rule.actions?.length || 0} steps</code></span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={() => handleToggleActivate(rule)}
                        className={`p-2 rounded-lg border transition text-xs font-bold flex items-center gap-1.5 ${
                          isActive
                            ? 'bg-amber-500/10 text-amber-300 border-amber-500/30 hover:bg-amber-500/20'
                            : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30 hover:bg-emerald-500/20'
                        }`}
                        title={isActive ? 'Pause Rule' : 'Activate Rule'}
                      >
                        {isActive ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                        <span>{isActive ? 'Pause' : 'Activate'}</span>
                      </button>

                      <button
                        onClick={() => {
                          setEditingRule(rule);
                          setIsRuleModalOpen(true);
                        }}
                        className="p-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg text-slate-300 transition"
                        title="Edit Rule"
                      >
                        Edit
                      </button>

                      <button
                        onClick={() => handleDeleteRule(rule.id)}
                        className="p-2 bg-slate-900 hover:bg-rose-500/20 border border-slate-800 hover:border-rose-500/40 text-slate-400 hover:text-rose-400 rounded-lg transition"
                        title="Delete Rule"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="p-8 text-center text-slate-500 font-mono text-xs">
              No automation rules match the selected status filter.
            </div>
          )}
        </GlassCard>
      )}

      {/* TAB 2: EXECUTION HISTORY LOG */}
      {activeTab === 'executions' && (
        <GlassCard
          title="Workflow Execution Audit History"
          subtitle="Real-time execution log, matched criteria, action outcomes, and retry traces"
        >
          {executions.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-[10px] text-slate-400 uppercase tracking-wider">
                    <th className="py-3 px-3">Status</th>
                    <th className="py-3 px-3">Rule / Trigger</th>
                    <th className="py-3 px-3">Target Entity</th>
                    <th className="py-3 px-3">Criteria Matched</th>
                    <th className="py-3 px-3">Actions (Succ/Total)</th>
                    <th className="py-3 px-3">Started</th>
                    <th className="py-3 px-3 text-right">Audit</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {executions.map((e) => (
                    <tr key={e.id} className="hover:bg-slate-900/40 transition">
                      <td className="py-3 px-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          e.status === 'SUCCESS'
                            ? 'bg-emerald-500/20 text-emerald-300'
                            : e.status === 'PARTIAL_SUCCESS'
                            ? 'bg-amber-500/20 text-amber-300'
                            : e.status === 'FAILED'
                            ? 'bg-rose-500/20 text-rose-300'
                            : 'bg-slate-800 text-slate-400'
                        }`}>
                          {e.status}
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        <span className="font-bold text-slate-100 block">{e.rule_name || 'Deleted Rule'}</span>
                        <span className="text-[10px] text-indigo-400">{e.event_type}</span>
                      </td>
                      <td className="py-3 px-3 text-[11px]">
                        <span className="text-slate-300">{e.entity_type}</span>
                        <span className="text-slate-500 block text-[10px]">#{e.entity_id.substring(0, 8)}</span>
                      </td>
                      <td className="py-3 px-3">
                        <span className={`font-bold ${e.conditions_matched ? 'text-emerald-400' : 'text-slate-500'}`}>
                          {e.conditions_matched ? 'YES' : 'NO'}
                        </span>
                      </td>
                      <td className="py-3 px-3 font-bold text-slate-200">
                        {e.actions_succeeded} / {e.actions_total}
                      </td>
                      <td className="py-3 px-3 text-[11px] text-slate-400">
                        {new Date(e.started_at).toLocaleTimeString()}
                      </td>
                      <td className="py-3 px-3 text-right">
                        <BrutalButton
                          variant="ghost"
                          size="sm"
                          onClick={() => setSelectedExecution(e)}
                        >
                          Trace Log
                        </BrutalButton>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-8 text-center text-slate-500 font-mono text-xs">
              No workflow executions recorded yet.
            </div>
          )}
        </GlassCard>
      )}

      {/* Rule Creator/Editor Modal */}
      {isRuleModalOpen && (
        <AutomationRuleModal
          isOpen={isRuleModalOpen}
          onClose={() => setIsRuleModalOpen(false)}
          onSave={handleCreateRule}
          initialRule={editingRule}
        />
      )}

      {/* Execution Audit Detail Modal */}
      {selectedExecution && (
        <ExecutionDetailModal
          isOpen={Boolean(selectedExecution)}
          onClose={() => setSelectedExecution(null)}
          execution={selectedExecution}
          onRetry={handleRetryExecution}
          isRetrying={isRetrying}
        />
      )}
    </div>
  );
};
