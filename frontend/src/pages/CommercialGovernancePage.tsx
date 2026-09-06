import React, { useState, useEffect } from 'react';
import { commercialGovernanceApi } from '../services/commercialGovernanceApi';
import { DiscountPolicy, ApprovalRule } from '../types';
import { StatusBadge } from '../components/ui/StatusBadge';
import { BrutalButton } from '../components/ui/BrutalButton';
import { GlassInput } from '../components/ui/GlassInput';
import { GlassSelect } from '../components/ui/GlassSelect';
import { GlassModal } from '../components/ui/GlassModal';
import { DataTable, Column } from '../components/ui/DataTable';
import { LoadingState, ErrorState } from '../components/ui/EmptyState';
import { useToast } from '../context/ToastContext';
import { Plus, ShieldCheck, ShieldAlert, Trash2 } from 'lucide-react';

export const CommercialGovernancePage: React.FC = () => {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<'policies' | 'approvals' | 'inbox'>('policies');

  const [policies, setPolicies] = useState<DiscountPolicy[]>([]);
  const [approvalRules, setApprovalRules] = useState<ApprovalRule[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Policy Modal State
  const [isPolicyModalOpen, setIsPolicyModalOpen] = useState(false);
  const [isSavingPolicy, setIsSavingPolicy] = useState(false);
  const [polName, setPolName] = useState('');
  const [polDesc, setPolDesc] = useState('');
  const [polScope, setPolScope] = useState('organization');
  const [polPriority, setPolPriority] = useState('100');
  const [polMaxDiscPct, setPolMaxDiscPct] = useState('');
  const [polMinPrice, setPolMinPrice] = useState('');
  const [polMinMargin, setPolMinMargin] = useState('');

  // Approval Rule Modal State
  const [isRuleModalOpen, setIsRuleModalOpen] = useState(false);
  const [isSavingRule, setIsSavingRule] = useState(false);
  const [ruleName, setRuleName] = useState('');
  const [ruleDesc, setRuleDesc] = useState('');
  const [rulePriority, setRulePriority] = useState('100');
  const [ruleMinDiscPct, setRuleMinDiscPct] = useState('');
  const [ruleMinMarginPct, setRuleMinMarginPct] = useState('');
  const [ruleRiskLevel, setRuleRiskLevel] = useState('');

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [pData, rData] = await Promise.all([
        commercialGovernanceApi.getDiscountPolicies(),
        commercialGovernanceApi.getApprovalRules(),
      ]);
      setPolicies(pData);
      setApprovalRules(rData);
    } catch (err: any) {
      setError(err.message || 'Failed to load commercial governance configuration.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreatePolicy = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!polName) return;

    setIsSavingPolicy(true);
    try {
      await commercialGovernanceApi.createDiscountPolicy({
        name: polName.trim(),
        description: polDesc.trim() || undefined,
        scope: polScope,
        priority: parseInt(polPriority) || 100,
        max_discount_percent: polMaxDiscPct ? parseFloat(polMaxDiscPct) : undefined,
        minimum_unit_price: polMinPrice ? parseFloat(polMinPrice) : undefined,
        minimum_margin_percent: polMinMargin ? parseFloat(polMinMargin) : undefined,
      });
      showToast('Discount governance policy created successfully!', 'success');
      setIsPolicyModalOpen(false);
      setPolName('');
      setPolDesc('');
      setPolMaxDiscPct('');
      setPolMinPrice('');
      setPolMinMargin('');
      loadData();
    } catch (err: any) {
      showToast(err.message || 'Failed to create discount policy.', 'error');
    } finally {
      setIsSavingPolicy(false);
    }
  };

  const handleDeletePolicy = async (id: string) => {
    try {
      await commercialGovernanceApi.deleteDiscountPolicy(id);
      showToast('Discount policy deleted.', 'success');
      loadData();
    } catch (err: any) {
      showToast(err.message || 'Failed to delete policy.', 'error');
    }
  };

  const handleCreateApprovalRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ruleName) return;

    setIsSavingRule(true);
    try {
      await commercialGovernanceApi.createApprovalRule({
        name: ruleName.trim(),
        description: ruleDesc.trim() || undefined,
        priority: parseInt(rulePriority) || 100,
        min_discount_percent: ruleMinDiscPct ? parseFloat(ruleMinDiscPct) : undefined,
        min_margin_percent: ruleMinMarginPct ? parseFloat(ruleMinMarginPct) : undefined,
        risk_level: ruleRiskLevel || undefined,
      });
      showToast('Approval rule created successfully!', 'success');
      setIsRuleModalOpen(false);
      setRuleName('');
      setRuleDesc('');
      setRuleMinDiscPct('');
      setRuleMinMarginPct('');
      setRuleRiskLevel('');
      loadData();
    } catch (err: any) {
      showToast(err.message || 'Failed to create approval rule.', 'error');
    } finally {
      setIsSavingRule(false);
    }
  };

  const handleDeleteRule = async (id: string) => {
    try {
      await commercialGovernanceApi.deleteApprovalRule(id);
      showToast('Approval rule deleted.', 'success');
      loadData();
    } catch (err: any) {
      showToast(err.message || 'Failed to delete approval rule.', 'error');
    }
  };

  const policyColumns: Column<DiscountPolicy>[] = [
    {
      header: 'Policy Name',
      render: (p) => (
        <div>
          <span className="font-semibold text-slate-100 text-xs block">{p.name}</span>
          {p.description && <span className="text-[10px] font-mono text-slate-400 block">{p.description}</span>}
        </div>
      ),
    },
    {
      header: 'Scope',
      render: (p) => <span className="font-mono text-xs uppercase text-cyan-400">{p.scope}</span>,
    },
    {
      header: 'Priority',
      render: (p) => <span className="font-mono text-xs font-bold text-slate-300">P{p.priority}</span>,
    },
    {
      header: 'Max Discount %',
      render: (p) => <span className="font-mono text-xs font-bold text-amber-400">{p.max_discount_percent ? `₹${p.max_discount_percent}%` : '—'}</span>,
    },
    {
      header: 'Min Unit Price',
      render: (p) => <span className="font-mono text-xs font-bold text-emerald-400">{p.minimum_unit_price ? `₹${p.minimum_unit_price}` : '—'}</span>,
    },
    {
      header: 'Min Margin %',
      render: (p) => <span className="font-mono text-xs font-bold text-indigo-400">{p.minimum_margin_percent ? `₹${p.minimum_margin_percent}%` : '—'}</span>,
    },
    {
      header: 'Status',
      render: (p) => <StatusBadge status={p.is_active ? 'active' : 'inactive'} size="sm" />,
    },
    {
      header: 'Actions',
      render: (p) => (
        <button
          onClick={() => handleDeletePolicy(p.id)}
          className="text-rose-400 hover:text-rose-300 transition-colors p-1"
          title="Delete Policy"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      ),
    },
  ];

  const ruleColumns: Column<ApprovalRule>[] = [
    {
      header: 'Rule Name',
      render: (r) => (
        <div>
          <span className="font-semibold text-slate-100 text-xs block">{r.name}</span>
          {r.description && <span className="text-[10px] font-mono text-slate-400 block">{r.description}</span>}
        </div>
      ),
    },
    {
      header: 'Priority',
      render: (r) => <span className="font-mono text-xs font-bold text-slate-300">P{r.priority}</span>,
    },
    {
      header: 'Trigger Condition',
      render: (r) => (
        <div className="text-xs font-mono text-slate-300 space-y-0.5">
          {r.min_discount_percent && <div>Disc &ge; {r.min_discount_percent}%</div>}
          {r.min_margin_percent && <div>Margin &lt; {r.min_margin_percent}%</div>}
          {r.risk_level && <div>Risk Level = {r.risk_level}</div>}
        </div>
      ),
    },
    {
      header: 'Required Role',
      render: (r) => <span className="font-mono text-xs uppercase text-amber-400">{r.required_role}</span>,
    },
    {
      header: 'Status',
      render: (r) => <StatusBadge status={r.is_active ? 'active' : 'inactive'} size="sm" />,
    },
    {
      header: 'Actions',
      render: (r) => (
        <button
          onClick={() => handleDeleteRule(r.id)}
          className="text-rose-400 hover:text-rose-300 transition-colors p-1"
          title="Delete Rule"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 tracking-tight">Commercial Governance Center</h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Discount governance policies, blended risk evaluation, and multi-level approval rules (Phases 23–25)
          </p>
        </div>

        <div className="flex items-center gap-2">
          {activeTab === 'policies' ? (
            <BrutalButton variant="primary" icon={Plus} onClick={() => setIsPolicyModalOpen(true)}>
              New Discount Policy
            </BrutalButton>
          ) : (
            <BrutalButton variant="primary" icon={Plus} onClick={() => setIsRuleModalOpen(true)}>
              New Approval Rule
            </BrutalButton>
          )}
        </div>
      </div>

      {/* Tabs Header */}
      <div className="flex items-center gap-3 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab('policies')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-mono font-bold transition ${
            activeTab === 'policies'
              ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_10px_rgba(6,182,212,0.2)]'
              : 'bg-slate-900/60 text-slate-400 border border-slate-800 hover:text-slate-200'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          <span>Phase 23 — Discount Policies ({policies.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('approvals')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-mono font-bold transition ${
            activeTab === 'approvals'
              ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_10px_rgba(6,182,212,0.2)]'
              : 'bg-slate-900/60 text-slate-400 border border-slate-800 hover:text-slate-200'
          }`}
        >
          <ShieldAlert className="w-4 h-4" />
          <span>Phase 25 — Approval Rules ({approvalRules.length})</span>
        </button>
      </div>

      {isLoading ? (
        <LoadingState message="Loading governance rules..." />
      ) : error ? (
        <ErrorState message={error} onRetry={loadData} />
      ) : activeTab === 'policies' ? (
        <DataTable
          columns={policyColumns}
          data={policies}
          keyExtractor={(p) => p.id}
          emptyMessage="No discount governance policies configured."
        />
      ) : (
        <DataTable
          columns={ruleColumns}
          data={approvalRules}
          keyExtractor={(r) => r.id}
          emptyMessage="No approval rules configured."
        />
      )}

      {/* New Discount Policy Modal */}
      <GlassModal
        isOpen={isPolicyModalOpen}
        onClose={() => setIsPolicyModalOpen(false)}
        title="Create Discount Governance Policy"
        subtitle="Phase 23 — Configure max discount caps and price/margin protections"
      >
        <form onSubmit={handleCreatePolicy} className="space-y-4">
          <GlassInput
            label="Policy Name *"
            placeholder="e.g. Standard 15% Max Discount Policy"
            value={polName}
            onChange={(e) => setPolName(e.target.value)}
            required
          />

          <GlassInput
            label="Description"
            placeholder="Commercial scope details..."
            value={polDesc}
            onChange={(e) => setPolDesc(e.target.value)}
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <GlassSelect
              label="Scope Level"
              value={polScope}
              onChange={(e) => setPolScope(e.target.value)}
              options={[
                { value: 'organization', label: 'Organization Default' },
                { value: 'role', label: 'User Role Specific' },
                { value: 'product', label: 'Product Specific' },
                { value: 'customer', label: 'Customer Specific' },
                { value: 'user', label: 'User Specific' },
              ]}
            />

            <GlassInput
              label="Priority (1 = Highest)"
              type="number"
              min="1"
              value={polPriority}
              onChange={(e) => setPolPriority(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <GlassInput
              label="Max Discount (%)"
              type="number"
              step="0.01"
              min="0"
              max="100"
              placeholder="e.g. 15.00"
              value={polMaxDiscPct}
              onChange={(e) => setPolMaxDiscPct(e.target.value)}
            />

            <GlassInput
              label="Min Unit Price (₹)"
              type="number"
              step="0.01"
              min="0"
              placeholder="Floor unit price"
              value={polMinPrice}
              onChange={(e) => setPolMinPrice(e.target.value)}
            />

            <GlassInput
              label="Min Margin (%)"
              type="number"
              step="0.01"
              placeholder="Margin protection"
              value={polMinMargin}
              onChange={(e) => setPolMinMargin(e.target.value)}
            />
          </div>

          <div className="pt-4 flex items-center justify-end gap-3 border-t border-slate-800">
            <BrutalButton type="button" variant="ghost" onClick={() => setIsPolicyModalOpen(false)}>
              Cancel
            </BrutalButton>
            <BrutalButton type="submit" variant="primary" isLoading={isSavingPolicy}>
              Create Policy
            </BrutalButton>
          </div>
        </form>
      </GlassModal>

      {/* New Approval Rule Modal */}
      <GlassModal
        isOpen={isRuleModalOpen}
        onClose={() => setIsRuleModalOpen(false)}
        title="Create Approval Rule"
        subtitle="Phase 25 — Define conditions triggering commercial authorization"
      >
        <form onSubmit={handleCreateApprovalRule} className="space-y-4">
          <GlassInput
            label="Rule Name *"
            placeholder="e.g. High Discount >= 20% Requires Admin Approval"
            value={ruleName}
            onChange={(e) => setRuleName(e.target.value)}
            required
          />

          <GlassInput
            label="Description"
            placeholder="Condition rationale..."
            value={ruleDesc}
            onChange={(e) => setRuleDesc(e.target.value)}
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <GlassInput
              label="Priority (lower = higher precedence)"
              type="number"
              value={rulePriority}
              onChange={(e) => setRulePriority(e.target.value)}
            />
            <GlassInput
              label="Min Discount Threshold (%)"
              type="number"
              step="0.01"
              placeholder="e.g. 20.00"
              value={ruleMinDiscPct}
              onChange={(e) => setRuleMinDiscPct(e.target.value)}
            />
            <GlassInput
              label="Min Margin Threshold (%)"
              type="number"
              step="0.01"
              placeholder="e.g. 15.00"
              value={ruleMinMarginPct}
              onChange={(e) => setRuleMinMarginPct(e.target.value)}
            />
            <GlassSelect
              label="Risk Level Trigger"
              value={ruleRiskLevel}
              onChange={(e) => setRuleRiskLevel(e.target.value)}
              options={[
                { value: '', label: '-- None --' },
                { value: 'LOW', label: 'LOW' },
                { value: 'MEDIUM', label: 'MEDIUM' },
                { value: 'HIGH', label: 'HIGH' },
                { value: 'CRITICAL', label: 'CRITICAL' },
              ]}
            />
          </div>

          <div className="pt-4 flex items-center justify-end gap-3 border-t border-slate-800">
            <BrutalButton type="button" variant="ghost" onClick={() => setIsRuleModalOpen(false)}>
              Cancel
            </BrutalButton>
            <BrutalButton type="submit" variant="primary" isLoading={isSavingRule}>
              Create Rule
            </BrutalButton>
          </div>
        </form>
      </GlassModal>
    </div>
  );
};
