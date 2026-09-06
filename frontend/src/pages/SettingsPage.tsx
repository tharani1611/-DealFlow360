import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { GlassCard } from '../components/ui/GlassCard';
import { StatusBadge } from '../components/ui/StatusBadge';
import { BrutalButton } from '../components/ui/BrutalButton';
import { useToast } from '../context/ToastContext';
import { recommendationRuleApi } from '../services/recommendationRuleApi';
import { productApi } from '../services/productApi';
import { ProductRecommendationRule, ProductRecommendationRuleCreate, Product } from '../types';
import { Plus, Trash2, ArrowUpRight, Sparkles } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const { user } = useAuth();
  const { showToast } = useToast();

  const [rules, setRules] = useState<ProductRecommendationRule[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoadingRules, setIsLoadingRules] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);

  // Form State
  const [sourceProductId, setSourceProductId] = useState('');
  const [targetProductId, setTargetProductId] = useState('');
  const [ruleType, setRuleType] = useState<'upsell' | 'cross_sell'>('upsell');
  const [priority, setPriority] = useState(1);
  const [description, setDescription] = useState('');
  const [minDealCount, setMinDealCount] = useState<string>('');
  const [minPipelineValue, setMinPipelineValue] = useState<string>('');
  const [minActivityCount, setMinActivityCount] = useState<string>('');

  const loadRulesAndProducts = async () => {
    setIsLoadingRules(true);
    try {
      const [rulesData, productsData] = await Promise.all([
        recommendationRuleApi.getRules(),
        productApi.getProducts({ is_active: true }),
      ]);
      setRules(rulesData);
      setProducts(productsData);
      if (productsData.length >= 2) {
        if (!sourceProductId) setSourceProductId(productsData[0].id);
        if (!targetProductId) setTargetProductId(productsData[1].id);
      }
    } catch (err: any) {
      showToast(err.message || 'Failed to load recommendation rules.', 'error');
    } finally {
      setIsLoadingRules(false);
    }
  };

  useEffect(() => {
    loadRulesAndProducts();
  }, []);

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!sourceProductId || !targetProductId) {
      showToast('Please select both source and target products.', 'error');
      return;
    }

    if (sourceProductId === targetProductId) {
      showToast('Source product and target product must be different.', 'error');
      return;
    }

    setIsSubmitting(true);
    try {
      const payload: ProductRecommendationRuleCreate = {
        source_product_id: sourceProductId,
        target_product_id: targetProductId,
        rule_type: ruleType,
        priority: Number(priority) || 1,
        description: description.trim() || undefined,
        min_customer_deal_count: minDealCount ? Number(minDealCount) : undefined,
        min_customer_pipeline_value: minPipelineValue ? Number(minPipelineValue) : undefined,
        min_customer_activity_count: minActivityCount ? Number(minActivityCount) : undefined,
        is_active: true,
      };

      await recommendationRuleApi.createRule(payload);
      showToast(`Created new ${ruleType} recommendation rule successfully.`, 'success');
      setShowAddForm(false);
      setDescription('');
      setMinDealCount('');
      setMinPipelineValue('');
      setMinActivityCount('');
      loadRulesAndProducts();
    } catch (err: any) {
      showToast(err.message || 'Failed to create recommendation rule.', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    if (!confirm('Are you sure you want to delete this recommendation rule?')) return;

    try {
      await recommendationRuleApi.deleteRule(ruleId);
      showToast('Recommendation rule deleted.', 'success');
      loadRulesAndProducts();
    } catch (err: any) {
      showToast(err.message || 'Failed to delete rule.', 'error');
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-black text-slate-100 tracking-tight">System Settings & Governance</h1>
        <p className="text-xs text-slate-400 font-mono mt-0.5">
          User profile telemetry, tenant organization attributes, AI provider status, and intelligence rules engine
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* User Profile Card */}
        <GlassCard title="User Profile Telemetry">
          <div className="space-y-3 text-xs">
            <div className="flex justify-between py-2 border-b border-slate-800">
              <span className="text-slate-400">Full Name:</span>
              <span className="font-bold text-slate-100">{user?.full_name || 'Not provided'}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-800">
              <span className="text-slate-400">Email Address:</span>
              <span className="font-mono text-slate-200">{user?.email}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-800">
              <span className="text-slate-400">Assigned Role:</span>
              <StatusBadge status={user?.is_admin ? 'admin' : 'user'} size="sm" />
            </div>
            <div className="flex justify-between py-2 border-b border-slate-800">
              <span className="text-slate-400">Account Status:</span>
              <StatusBadge status={user?.is_active ? 'active' : 'inactive'} size="sm" />
            </div>
          </div>
        </GlassCard>

        {/* Organization Card */}
        <GlassCard title="Tenant Organization Attributes">
          <div className="space-y-3 text-xs">
            <div className="flex justify-between py-2 border-b border-slate-800">
              <span className="text-slate-400">Organization ID:</span>
              <span className="font-mono text-slate-200">{user?.organization_id}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-800">
              <span className="text-slate-400">Security Scope:</span>
              <span className="font-mono text-indigo-400 font-bold">Multi-Tenant Isolated</span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-800">
              <span className="text-slate-400">RBAC Enforcement:</span>
              <span className="font-mono text-emerald-400 font-bold">Active</span>
            </div>
          </div>
        </GlassCard>
      </div>

      {/* Product Recommendation Rules Management Card */}
      <GlassCard
        title={
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-2 text-indigo-300">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              Product Recommendation Rules Engine (Admin)
            </span>
            {user?.is_admin && (
              <BrutalButton
                size="sm"
                variant={showAddForm ? 'ghost' : 'primary'}
                icon={Plus}
                onClick={() => setShowAddForm(!showAddForm)}
              >
                {showAddForm ? 'Cancel' : 'Add New Rule'}
              </BrutalButton>
            )}
          </div>
        }
        subtitle="Manage deterministic upsell & cross-sell mapping logic across active product catalogs"
      >
        {/* Add New Rule Form */}
        {showAddForm && user?.is_admin && (
          <form onSubmit={handleCreateRule} className="p-4 mb-6 rounded-xl bg-slate-950/90 border border-indigo-500/40 space-y-4 text-xs font-mono">
            <h3 className="font-bold text-slate-100 uppercase tracking-wider text-[11px] text-indigo-300">
              Configure New Recommendation Mapping Rule
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-slate-400 mb-1">Source Product (Current Ownership)</label>
                <select
                  value={sourceProductId}
                  onChange={(e) => setSourceProductId(e.target.value)}
                  className="w-full p-2 rounded bg-slate-900 border border-slate-700 text-slate-100"
                  required
                >
                  {products.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.sku})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Target Product (Recommendation)</label>
                <select
                  value={targetProductId}
                  onChange={(e) => setTargetProductId(e.target.value)}
                  className="w-full p-2 rounded bg-slate-900 border border-slate-700 text-slate-100"
                  required
                >
                  {products.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.sku})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-slate-400 mb-1">Rule Type</label>
                <select
                  value={ruleType}
                  onChange={(e) => setRuleType(e.target.value as 'upsell' | 'cross_sell')}
                  className="w-full p-2 rounded bg-slate-900 border border-slate-700 text-slate-100 font-bold"
                >
                  <option value="upsell">Upsell (Higher Tier)</option>
                  <option value="cross_sell">Cross-Sell (Complementary)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Priority (1 = Highest)</label>
                <input
                  type="number"
                  min={1}
                  max={100}
                  value={priority}
                  onChange={(e) => setPriority(Number(e.target.value))}
                  className="w-full p-2 rounded bg-slate-900 border border-slate-700 text-slate-100"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Min. Customer Open Deals</label>
                <input
                  type="number"
                  min={0}
                  placeholder="Optional (e.g. 1)"
                  value={minDealCount}
                  onChange={(e) => setMinDealCount(e.target.value)}
                  className="w-full p-2 rounded bg-slate-900 border border-slate-700 text-slate-100"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-slate-400 mb-1">Min. Customer Pipeline Value (₹)</label>
                <input
                  type="number"
                  min={0}
                  placeholder="Optional (e.g. 5000)"
                  value={minPipelineValue}
                  onChange={(e) => setMinPipelineValue(e.target.value)}
                  className="w-full p-2 rounded bg-slate-900 border border-slate-700 text-slate-100"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Rule Description / Rationale</label>
                <input
                  type="text"
                  placeholder="e.g. Upgrade cloud tier for active customer"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full p-2 rounded bg-slate-900 border border-slate-700 text-slate-100"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <BrutalButton type="submit" variant="success" isLoading={isSubmitting}>
                Save Rule Mapping
              </BrutalButton>
            </div>
          </form>
        )}

        {/* Existing Rules Table */}
        {isLoadingRules ? (
          <div className="p-4 text-xs font-mono text-slate-400 text-center">Loading recommendation rule telemetry...</div>
        ) : rules.length === 0 ? (
          <div className="p-6 text-center text-xs font-mono text-slate-400 bg-slate-950/40 rounded-xl border border-slate-800">
            No recommendation rules configured yet. Admins can add rules mapping source products to target upsell/cross-sell opportunities.
          </div>
        ) : (
          <div className="space-y-3">
            {rules.map((rule) => {
              const sourceProd = products.find((p) => p.id === rule.source_product_id);
              const targetProd = products.find((p) => p.id === rule.target_product_id);
              const isUpsell = rule.rule_type === 'upsell';

              return (
                <div
                  key={rule.id}
                  className={`p-3.5 rounded-xl bg-slate-950/80 border text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                    isUpsell ? 'border-emerald-500/30' : 'border-indigo-500/30'
                  }`}
                >
                  <div>
                    <div className="flex items-center gap-2 font-mono flex-wrap">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        isUpsell ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' : 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40'
                      }`}>
                        {rule.rule_type}
                      </span>

                      <span className="font-bold text-slate-100">
                        {rule.source_product_name || sourceProd?.name || rule.source_product_id}
                      </span>

                      <ArrowUpRight className="w-3.5 h-3.5 text-slate-500" />

                      <span className="font-bold text-emerald-300">
                        {rule.target_product_name || targetProd?.name || rule.target_product_id}
                      </span>

                      <span className="text-[10px] text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded">
                        Priority: {rule.priority}
                      </span>
                    </div>

                    {rule.description && (
                      <p className="text-[11px] text-slate-400 font-mono mt-1">
                        {rule.description}
                      </p>
                    )}

                    {(rule.min_customer_deal_count || rule.min_customer_pipeline_value) && (
                      <div className="text-[10px] font-mono text-indigo-400 mt-1 flex items-center gap-2">
                        <span>Eligibility triggers:</span>
                        {rule.min_customer_deal_count && <span>• Min Deals: {rule.min_customer_deal_count}</span>}
                        {rule.min_customer_pipeline_value && <span>• Min Value: ₹{rule.min_customer_pipeline_value}</span>}
                      </div>
                    )}
                  </div>

                  {user?.is_admin && (
                    <button
                      onClick={() => handleDeleteRule(rule.id)}
                      className="p-1.5 rounded bg-rose-950/60 text-rose-300 border border-rose-800/60 hover:bg-rose-900 transition self-end sm:self-center"
                      title="Delete Rule"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </GlassCard>

      {/* Forecast Intelligence Governance */}
      <GlassCard title="Revenue Forecast Engine Governance">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
          <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800">
            <span className="text-slate-400 block mb-1 text-[10px] uppercase font-bold">Calculation Engine</span>
            <span className="text-indigo-400 font-extrabold text-sm">Deterministic Synchronous</span>
          </div>

          <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800">
            <span className="text-slate-400 block mb-1 text-[10px] uppercase font-bold">Financial Calculations</span>
            <span className="text-emerald-400 font-extrabold text-sm">Backend Authoritative (Decimal)</span>
          </div>

          <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800">
            <span className="text-slate-400 block mb-1 text-[10px] uppercase font-bold">AI Role</span>
            <span className="text-cyan-300 font-extrabold text-sm">Advisory / Explanation Layer Only</span>
          </div>
        </div>
      </GlassCard>

      {/* AI Telemetry Status */}
      <GlassCard title="AI Intelligence Provider Telemetry">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
          <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800">
            <span className="text-slate-400 block mb-1 text-[10px] uppercase font-bold">Active Provider</span>
            <span className="text-indigo-400 font-extrabold text-sm">Google Gemini REST / Mock</span>
          </div>

          <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800">
            <span className="text-slate-400 block mb-1 text-[10px] uppercase font-bold">Default Model</span>
            <span className="text-slate-200 font-extrabold text-sm">gemini-1.5-flash</span>
          </div>

          <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800">
            <span className="text-slate-400 block mb-1 text-[10px] uppercase font-bold">Security Boundary</span>
            <span className="text-emerald-400 font-extrabold text-sm">Strict Prompt Defense</span>
          </div>
        </div>
      </GlassCard>
    </div>
  );
};
