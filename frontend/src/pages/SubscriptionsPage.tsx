import React, { useState, useEffect } from 'react';
import { NeoGlassCard } from '../components/ui/NeoGlassCard';
import { NeoGlassButton } from '../components/ui/NeoGlassButton';
import { StatusBadge } from '../components/ui/StatusBadge';
import { GlassModal } from '../components/ui/GlassModal';
import { Subscription, BillingSchedule, Customer, Product } from '../types';
import { billingApi } from '../services/billingApi';
import { customerApi } from '../services/customerApi';
import { productApi } from '../services/productApi';
import { ProrationPreviewModal } from '../components/billing/ProrationPreviewModal';
import {
  Repeat,
  Calendar,
  Zap,
  Calculator,
  Ban,
  RefreshCw,
  FileText,
  Plus,
  CheckCircle2,
  AlertCircle,
  Info,
  X,
  Sparkles,
} from 'lucide-react';

interface ToastNotification {
  type: 'success' | 'error' | 'info';
  message: string;
}

export const SubscriptionsPage: React.FC = () => {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [toast, setToast] = useState<ToastNotification | null>(null);

  // Active Modals
  const [selectedSubscription, setSelectedSubscription] = useState<Subscription | null>(null);
  const [schedules, setSchedules] = useState<BillingSchedule[]>([]);
  const [showSchedulesModal, setShowSchedulesModal] = useState<boolean>(false);
  const [prorationSub, setProrationSub] = useState<Subscription | null>(null);
  const [cancelSub, setCancelSub] = useState<Subscription | null>(null);
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);

  // Create Subscription Form State
  const [createCustomerId, setCreateCustomerId] = useState<string>('');
  const [createProductId, setCreateProductId] = useState<string>('');
  const [createPlanName, setCreatePlanName] = useState<string>('');
  const [createInterval, setCreateInterval] = useState<'MONTHLY' | 'QUARTERLY' | 'YEARLY'>('MONTHLY');
  const [createQuantity, setCreateQuantity] = useState<number>(1);
  const [createUnitPrice, setCreateUnitPrice] = useState<number>(5000);
  const [createStartDate, setCreateStartDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [createLoading, setCreateLoading] = useState<boolean>(false);

  // Cancellation Form state
  const [cancelType, setCancelType] = useState<'IMMEDIATE' | 'END_OF_PERIOD'>('END_OF_PERIOD');
  const [cancelReason, setCancelReason] = useState<string>('');
  const [cancelLoading, setCancelLoading] = useState<boolean>(false);

  const showToast = (type: 'success' | 'error' | 'info', message: string) => {
    setToast({ type, message });
    setTimeout(() => {
      setToast(null);
    }, 6000);
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const [subList, custList, prodList] = await Promise.all([
        billingApi.listSubscriptions(),
        customerApi.getCustomers(),
        productApi.getProducts(),
      ]);
      setSubscriptions(subList);
      setCustomers(custList);
      setProducts(prodList);
      if (custList.length > 0 && !createCustomerId) {
        setCreateCustomerId(custList[0].id);
      }
      if (prodList.length > 0 && !createProductId) {
        setCreateProductId(prodList[0].id);
        setCreatePlanName(`${prodList[0].name} Subscription Plan`);
        setCreateUnitPrice(Number(prodList[0].unit_price) || 5000);
      }
    } catch (err: any) {
      console.error('Failed to load subscriptions:', err);
      showToast('error', err?.message || 'Failed to load subscriptions data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleProductSelectChange = (prodId: string) => {
    setCreateProductId(prodId);
    const selectedProd = products.find((p) => p.id === prodId);
    if (selectedProd) {
      setCreatePlanName(`${selectedProd.name} Subscription Plan`);
      setCreateUnitPrice(Number(selectedProd.unit_price) || 5000);
    }
  };

  const handleGenerateDue = async () => {
    try {
      const created = await billingApi.generateDueSchedules();
      if (created.length > 0) {
        showToast('success', `Generated ${created.length} due billing schedules successfully!`);
      } else {
        showToast('info', 'All subscription billing schedules are up to date (0 due schedules).');
      }
      await loadData();
    } catch (err: any) {
      showToast('error', err?.message || 'Failed to generate due schedules');
    }
  };

  const handleCreateSubscriptionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createCustomerId || !createProductId || !createPlanName) {
      showToast('error', 'Please fill in all required subscription fields.');
      return;
    }

    setCreateLoading(true);
    try {
      const newSub = await billingApi.createSubscription({
        customer_id: createCustomerId,
        product_id: createProductId,
        plan_name: createPlanName,
        billing_interval: createInterval,
        quantity: Number(createQuantity),
        unit_price: Number(createUnitPrice),
        start_date: createStartDate,
      });

      showToast('success', `Subscription ${newSub.subscription_number} created successfully!`);
      setShowCreateModal(false);
      await loadData();
    } catch (err: any) {
      showToast('error', err?.message || 'Failed to create subscription.');
    } finally {
      setCreateLoading(false);
    }
  };

  const handleQuickSeedSubscriptions = async () => {
    setLoading(true);
    try {
      let cust = customers[0];
      if (!cust) {
        cust = await customerApi.createCustomer({
          name: 'Apex Global Enterprises',
          email: 'subscriptions@apexglobal.com',
          phone: '+91-9876543210',
          city: 'Mumbai',
          country: 'India',
        });
      }
      let prod = products[0];
      if (!prod) {
        prod = await productApi.createProduct({
          name: 'DealFlow360 Enterprise Cloud Suite',
          sku: 'SAAS-ENT-001',
          description: 'Full Platform Access with AI Co-Negotiator',
          unit_price: 15000,
          currency: 'INR',
          is_active: true,
        });
      }

      const samplePlans = [
        { name: 'DealFlow360 Cloud Platform Annual Subscription', interval: 'MONTHLY' as const, qty: 5, price: 12500 },
        { name: 'High-Performance Dedicated Infrastructure Cluster', interval: 'QUARTERLY' as const, qty: 2, price: 45000 },
        { name: '24/7 Platinum SLA & Dedicated TAM Support', interval: 'MONTHLY' as const, qty: 1, price: 8500 },
      ];

      for (const plan of samplePlans) {
        await billingApi.createSubscription({
          customer_id: cust.id,
          product_id: prod.id,
          plan_name: plan.name,
          billing_interval: plan.interval,
          quantity: plan.qty,
          unit_price: plan.price,
          start_date: new Date().toISOString().split('T')[0],
        });
      }

      showToast('success', 'Seeded 3 active enterprise subscriptions with recurring billing schedules!');
      await loadData();
    } catch (err: any) {
      showToast('error', err?.message || 'Failed to seed sample subscriptions');
    } finally {
      setLoading(false);
    }
  };

  const handleViewSchedules = async (sub: Subscription) => {
    setSelectedSubscription(sub);
    try {
      const scheds = await billingApi.listSchedulesForSubscription(sub.id);
      setSchedules(scheds);
      setShowSchedulesModal(true);
    } catch (err: any) {
      showToast('error', err?.message || 'Failed to fetch schedules');
    }
  };

  const handleExecuteInvoice = async (scheduleId: string) => {
    try {
      const inv = await billingApi.executeScheduleInvoice(scheduleId);
      showToast('success', `Invoice ${inv.invoice_number} generated for billing schedule!`);
      if (selectedSubscription) {
        const scheds = await billingApi.listSchedulesForSubscription(selectedSubscription.id);
        setSchedules(scheds);
      }
      await loadData();
    } catch (err: any) {
      showToast('error', err?.message || 'Failed to execute schedule invoice');
    }
  };

  const handleCancelSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cancelSub || !cancelReason) return;
    setCancelLoading(true);
    try {
      await billingApi.cancelSubscription(cancelSub.id, {
        cancellation_type: cancelType,
        reason: cancelReason,
      });
      showToast('success', `Subscription ${cancelSub.subscription_number} cancelled.`);
      setCancelSub(null);
      setCancelReason('');
      await loadData();
    } catch (err: any) {
      showToast('error', err?.message || 'Failed to cancel subscription');
    } finally {
      setCancelLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Toast Notification Banner */}
      {toast && (
        <div
          className={`p-4 rounded-xl border flex items-center justify-between text-xs font-mono transition-all animate-fadeIn ${
            toast.type === 'success'
              ? 'bg-emerald-950/80 border-emerald-500/50 text-emerald-200'
              : toast.type === 'error'
              ? 'bg-rose-950/80 border-rose-500/50 text-rose-200'
              : 'bg-sky-950/80 border-sky-500/50 text-sky-200'
          }`}
        >
          <div className="flex items-center gap-2.5">
            {toast.type === 'success' && <CheckCircle2 className="w-5 h-5 text-emerald-400" />}
            {toast.type === 'error' && <AlertCircle className="w-5 h-5 text-rose-400" />}
            {toast.type === 'info' && <Info className="w-5 h-5 text-sky-400" />}
            <span className="font-semibold">{toast.message}</span>
          </div>
          <button onClick={() => setToast(null)} className="p-1 hover:bg-white/10 rounded">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 tracking-tight flex items-center gap-2">
            <Repeat className="w-7 h-7 text-indigo-400" />
            Subscription Lifecycle Engine
          </h1>
          <p className="text-sm text-slate-400 font-mono mt-1">
            Phases 48–51 recurring billing schedules, proration calculation, and cancellation tracking
          </p>
        </div>
        <div className="flex items-center gap-2.5 flex-wrap">
          <NeoGlassButton variant="default" onClick={loadData}>
            <RefreshCw className="w-4 h-4 mr-1.5" />
            Refresh
          </NeoGlassButton>
          <NeoGlassButton variant="default" onClick={() => setShowCreateModal(true)}>
            <Plus className="w-4 h-4 mr-1.5" />
            New Subscription
          </NeoGlassButton>
          <NeoGlassButton variant="primary" onClick={handleGenerateDue}>
            <Zap className="w-4 h-4 mr-1.5" />
            Generate Due Schedules
          </NeoGlassButton>
        </div>
      </div>

      {/* Main Table Card */}
      <NeoGlassCard className="p-5">
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
          <h2 className="text-base font-bold text-slate-100 font-mono uppercase tracking-wider">
            Active & Historic Subscriptions
          </h2>
          <span className="text-xs font-mono text-slate-400">({subscriptions.length} Total)</span>
        </div>

        {loading ? (
          <div className="text-center py-12 text-slate-500 font-mono text-sm">Loading subscriptions...</div>
        ) : subscriptions.length === 0 ? (
          <div className="text-center py-12 space-y-4">
            <p className="text-slate-400 font-mono text-sm max-w-md mx-auto">
              No active subscriptions found for this tenant organization. Create a subscription manually or seed sample enterprise subscriptions.
            </p>
            <div className="flex items-center justify-center gap-3 pt-2">
              <NeoGlassButton variant="primary" onClick={() => setShowCreateModal(true)}>
                <Plus className="w-4 h-4 mr-1.5" />
                Create First Subscription
              </NeoGlassButton>

              <NeoGlassButton variant="default" onClick={handleQuickSeedSubscriptions}>
                <Sparkles className="w-4 h-4 mr-1.5 text-amber-400" />
                Seed Sample Subscriptions
              </NeoGlassButton>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider">
                  <th className="py-3 px-3">Sub #</th>
                  <th className="py-3 px-3">Customer</th>
                  <th className="py-3 px-3">Plan Name</th>
                  <th className="py-3 px-3">Interval</th>
                  <th className="py-3 px-3">Qty</th>
                  <th className="py-3 px-3">Unit Price</th>
                  <th className="py-3 px-3">Next Billing</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {subscriptions.map((sub) => {
                  const cust = customers.find((c) => c.id === sub.customer_id);
                  return (
                    <tr key={sub.id} className="hover:bg-slate-800/40">
                      <td className="py-3 px-3 font-bold text-indigo-400">{sub.subscription_number}</td>
                      <td className="py-3 px-3 text-slate-200">{cust ? cust.name : sub.customer_id.substring(0, 8)}</td>
                      <td className="py-3 px-3 text-slate-100 font-semibold">{sub.plan_name}</td>
                      <td className="py-3 px-3 text-sky-400">{sub.billing_interval}</td>
                      <td className="py-3 px-3 text-slate-200 font-bold">{sub.quantity}</td>
                      <td className="py-3 px-3 text-slate-200 font-bold">₹{Number(sub.unit_price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                      <td className="py-3 px-3 text-amber-400">{sub.next_billing_date}</td>
                      <td className="py-3 px-3">
                        <StatusBadge status={sub.status} size="sm" />
                      </td>
                      <td className="py-3 px-3 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => handleViewSchedules(sub)}
                            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-[11px] font-semibold flex items-center gap-1 transition-colors"
                            title="View Billing Schedules"
                          >
                            <Calendar className="w-3 h-3 text-sky-400" /> Schedules
                          </button>

                          {sub.status === 'ACTIVE' && (
                            <button
                              onClick={() => setProrationSub(sub)}
                              className="px-2.5 py-1 bg-indigo-950 border border-indigo-500/30 text-indigo-300 hover:bg-indigo-900 rounded text-[11px] font-semibold flex items-center gap-1 transition-colors"
                              title="Prorate Subscription"
                            >
                              <Calculator className="w-3 h-3 text-indigo-400" /> Prorate
                            </button>
                          )}

                          {sub.status === 'ACTIVE' && (
                            <button
                              onClick={() => setCancelSub(sub)}
                              className="px-2.5 py-1 bg-rose-950 border border-rose-500/30 text-rose-300 hover:bg-rose-900 rounded text-[11px] font-semibold flex items-center gap-1 transition-colors"
                              title="Cancel Subscription"
                            >
                              <Ban className="w-3 h-3 text-rose-400" /> Cancel
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </NeoGlassCard>

      {/* Create Subscription Modal */}
      {showCreateModal && (
        <GlassModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          title="Create New Recurring Subscription"
          subtitle="Provision recurring billing plan with automatic schedule generation"
          maxWidth="md"
        >
          <form onSubmit={handleCreateSubscriptionSubmit} className="space-y-4 font-mono text-xs">
            <div>
              <label className="block text-slate-400 mb-1 font-semibold">Select Customer</label>
              <select
                value={createCustomerId}
                onChange={(e) => setCreateCustomerId(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded text-slate-200 focus:outline-none focus:border-indigo-500"
                required
              >
                {customers.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.email})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-slate-400 mb-1 font-semibold">Select Base Product</label>
              <select
                value={createProductId}
                onChange={(e) => handleProductSelectChange(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded text-slate-200 focus:outline-none focus:border-indigo-500"
                required
              >
                {products.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} (SKU: {p.sku}) - ₹{Number(p.unit_price).toLocaleString('en-IN')}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-slate-400 mb-1 font-semibold">Plan Name</label>
              <input
                type="text"
                value={createPlanName}
                onChange={(e) => setCreatePlanName(e.target.value)}
                placeholder="e.g. Enterprise Cloud SaaS Plan"
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded text-slate-200 focus:outline-none focus:border-indigo-500"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-400 mb-1 font-semibold">Billing Interval</label>
                <select
                  value={createInterval}
                  onChange={(e) => setCreateInterval(e.target.value as any)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  <option value="MONTHLY">Monthly</option>
                  <option value="QUARTERLY">Quarterly</option>
                  <option value="YEARLY">Yearly</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-semibold">Quantity</label>
                <input
                  type="number"
                  min={1}
                  value={createQuantity}
                  onChange={(e) => setCreateQuantity(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded text-slate-200 focus:outline-none focus:border-indigo-500"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-400 mb-1 font-semibold">Unit Price (₹)</label>
                <input
                  type="number"
                  min={0}
                  step="0.01"
                  value={createUnitPrice}
                  onChange={(e) => setCreateUnitPrice(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded text-slate-200 focus:outline-none focus:border-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-semibold">Start Date</label>
                <input
                  type="date"
                  value={createStartDate}
                  onChange={(e) => setCreateStartDate(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded text-slate-200 focus:outline-none focus:border-indigo-500"
                  required
                />
              </div>
            </div>

            <div className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg flex items-center justify-between">
              <span className="text-slate-400 font-semibold">Recurring Cycle Total:</span>
              <span className="text-base font-bold text-emerald-400">
                ₹{(createQuantity * createUnitPrice).toLocaleString('en-IN', { minimumFractionDigits: 2 })} / {createInterval.toLowerCase()}
              </span>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 bg-slate-800 text-slate-300 rounded hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createLoading}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded font-bold"
              >
                {createLoading ? 'Creating...' : 'Create Subscription'}
              </button>
            </div>
          </form>
        </GlassModal>
      )}

      {/* Proration Preview Modal */}
      {prorationSub && (
        <ProrationPreviewModal
          isOpen={!!prorationSub}
          onClose={() => setProrationSub(null)}
          subscription={prorationSub}
          onSuccess={loadData}
        />
      )}

      {/* View Schedules Modal */}
      {showSchedulesModal && selectedSubscription && (
        <GlassModal
          isOpen={showSchedulesModal}
          onClose={() => setShowSchedulesModal(false)}
          title={`Billing Schedules: ${selectedSubscription.subscription_number}`}
          subtitle={`Plan: ${selectedSubscription.plan_name} (${selectedSubscription.billing_interval})`}
          maxWidth="lg"
        >
          <div className="space-y-4 font-mono">
            {schedules.length === 0 ? (
              <div className="text-center py-6 text-slate-500 text-xs">No billing schedules generated yet.</div>
            ) : (
              <div className="border border-slate-800 rounded-lg overflow-hidden">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-950 text-slate-400">
                    <tr>
                      <th className="p-2">Period Start</th>
                      <th className="p-2">Period End</th>
                      <th className="p-2">Billing Date</th>
                      <th className="p-2 text-right">Amount (₹)</th>
                      <th className="p-2">Status</th>
                      <th className="p-2 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {schedules.map((s) => (
                      <tr key={s.id}>
                        <td className="p-2 text-slate-200">{s.billing_period_start}</td>
                        <td className="p-2 text-slate-200">{s.billing_period_end}</td>
                        <td className="p-2 text-amber-400">{s.billing_date}</td>
                        <td className="p-2 text-right font-bold text-slate-100">
                          ₹{Number(s.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </td>
                        <td className="p-2">
                          <StatusBadge status={s.status} size="sm" />
                        </td>
                        <td className="p-2 text-right">
                          {s.status === 'SCHEDULED' || s.status === 'DUE' ? (
                            <button
                              onClick={() => handleExecuteInvoice(s.id)}
                              className="px-2 py-1 bg-emerald-950 border border-emerald-500/30 text-emerald-300 hover:bg-emerald-900 rounded text-[10px] font-semibold flex items-center gap-1 ml-auto"
                            >
                              <FileText className="w-3 h-3" /> Execute Invoice
                            </button>
                          ) : (
                            <span className="text-slate-500 text-[10px]">{s.invoice_id ? 'Invoiced' : '-'}</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </GlassModal>
      )}

      {/* Cancel Subscription Modal */}
      {cancelSub && (
        <GlassModal
          isOpen={!!cancelSub}
          onClose={() => setCancelSub(null)}
          title={`Cancel Subscription ${cancelSub.subscription_number}`}
          subtitle={`Customer ID: ${cancelSub.customer_id.substring(0, 8)}...`}
          maxWidth="md"
        >
          <form onSubmit={handleCancelSubmit} className="space-y-4 font-mono text-xs">
            <div>
              <label className="block text-slate-400 mb-1">Cancellation Timing</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setCancelType('END_OF_PERIOD')}
                  className={`p-2 rounded border text-center font-semibold ${
                    cancelType === 'END_OF_PERIOD'
                      ? 'bg-indigo-950 border-indigo-500 text-indigo-200'
                      : 'bg-slate-950 border-slate-800 text-slate-400'
                  }`}
                >
                  End of Billing Period
                </button>
                <button
                  type="button"
                  onClick={() => setCancelType('IMMEDIATE')}
                  className={`p-2 rounded border text-center font-semibold ${
                    cancelType === 'IMMEDIATE'
                      ? 'bg-rose-950 border-rose-500 text-rose-200'
                      : 'bg-slate-950 border-slate-800 text-slate-400'
                  }`}
                >
                  Immediate
                </button>
              </div>
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Reason for Cancellation</label>
              <input
                type="text"
                placeholder="e.g. Customer requested contract termination"
                value={cancelReason}
                onChange={(e) => setCancelReason(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded text-slate-200 text-xs"
                required
                minLength={3}
              />
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setCancelSub(null)}
                className="px-4 py-2 bg-slate-800 text-slate-300 rounded hover:bg-slate-700"
              >
                Keep Active
              </button>
              <button
                type="submit"
                disabled={cancelLoading}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded font-bold"
              >
                {cancelLoading ? 'Cancelling...' : 'Confirm Cancellation'}
              </button>
            </div>
          </form>
        </GlassModal>
      )}
    </div>
  );
};
