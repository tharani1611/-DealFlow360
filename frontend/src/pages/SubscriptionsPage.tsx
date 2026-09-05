import React, { useState, useEffect } from 'react';
import { NeoGlassCard } from '../components/ui/NeoGlassCard';
import { NeoGlassButton } from '../components/ui/NeoGlassButton';
import { StatusBadge } from '../components/ui/StatusBadge';
import { GlassModal } from '../components/ui/GlassModal';
import { Subscription, BillingSchedule, Customer } from '../types';
import { billingApi } from '../services/billingApi';
import { customerApi } from '../services/customerApi';
import { ProrationPreviewModal } from '../components/billing/ProrationPreviewModal';
import {
  Repeat,
  Calendar,
  Zap,
  Calculator,
  Ban,
  RefreshCw,
  FileText,
} from 'lucide-react';

export const SubscriptionsPage: React.FC = () => {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Active Modals
  const [selectedSubscription, setSelectedSubscription] = useState<Subscription | null>(null);
  const [schedules, setSchedules] = useState<BillingSchedule[]>([]);
  const [showSchedulesModal, setShowSchedulesModal] = useState<boolean>(false);
  const [prorationSub, setProrationSub] = useState<Subscription | null>(null);
  const [cancelSub, setCancelSub] = useState<Subscription | null>(null);

  // Cancellation Form state
  const [cancelType, setCancelType] = useState<'IMMEDIATE' | 'END_OF_PERIOD'>('END_OF_PERIOD');
  const [cancelReason, setCancelReason] = useState<string>('');
  const [cancelLoading, setCancelLoading] = useState<boolean>(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [subList, custList] = await Promise.all([
        billingApi.listSubscriptions(),
        customerApi.getCustomers(),
      ]);
      setSubscriptions(subList);
      setCustomers(custList);
    } catch (err) {
      console.error('Failed to load subscriptions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleGenerateDue = async () => {
    try {
      const created = await billingApi.generateDueSchedules();
      alert(`Generated ${created.length} due billing schedules.`);
      await loadData();
    } catch (err: any) {
      alert(err?.message || 'Failed to generate due schedules');
    }
  };

  const handleViewSchedules = async (sub: Subscription) => {
    setSelectedSubscription(sub);
    try {
      const scheds = await billingApi.listSchedulesForSubscription(sub.id);
      setSchedules(scheds);
      setShowSchedulesModal(true);
    } catch (err: any) {
      alert(err?.message || 'Failed to fetch schedules');
    }
  };

  const handleExecuteInvoice = async (scheduleId: string) => {
    try {
      const inv = await billingApi.executeScheduleInvoice(scheduleId);
      alert(`Invoice ${inv.invoice_number} generated for schedule!`);
      if (selectedSubscription) {
        const scheds = await billingApi.listSchedulesForSubscription(selectedSubscription.id);
        setSchedules(scheds);
      }
      await loadData();
    } catch (err: any) {
      alert(err?.message || 'Failed to execute schedule invoice');
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
      setCancelSub(null);
      setCancelReason('');
      await loadData();
    } catch (err: any) {
      alert(err?.message || 'Failed to cancel subscription');
    } finally {
      setCancelLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
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
        <div className="flex items-center gap-3">
          <NeoGlassButton variant="default" onClick={loadData}>
            <RefreshCw className="w-4 h-4 mr-1.5" />
            Refresh
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
          <div className="text-center py-12 text-slate-500 font-mono text-sm">
            No active subscriptions found. Subscriptions are created automatically from accepted quotations or API.
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
                      <td className="py-3 px-3 text-slate-200 font-bold">${Number(sub.unit_price).toFixed(2)}</td>
                      <td className="py-3 px-3 text-amber-400">{sub.next_billing_date}</td>
                      <td className="py-3 px-3">
                        <StatusBadge status={sub.status} size="sm" />
                      </td>
                      <td className="py-3 px-3 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => handleViewSchedules(sub)}
                            className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-[11px] font-semibold flex items-center gap-1"
                            title="View Billing Schedules"
                          >
                            <Calendar className="w-3 h-3" /> Schedules
                          </button>

                          {sub.status === 'ACTIVE' && (
                            <button
                              onClick={() => setProrationSub(sub)}
                              className="px-2 py-1 bg-indigo-950 border border-indigo-500/30 text-indigo-300 hover:bg-indigo-900 rounded text-[11px] font-semibold flex items-center gap-1"
                              title="Prorate Subscription"
                            >
                              <Calculator className="w-3 h-3" /> Prorate
                            </button>
                          )}

                          {sub.status === 'ACTIVE' && (
                            <button
                              onClick={() => setCancelSub(sub)}
                              className="px-2 py-1 bg-rose-950 border border-rose-500/30 text-rose-300 hover:bg-rose-900 rounded text-[11px] font-semibold flex items-center gap-1"
                              title="Cancel Subscription"
                            >
                              <Ban className="w-3 h-3" /> Cancel
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
                      <th className="p-2 text-right">Amount ($)</th>
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
                        <td className="p-2 text-right font-bold text-slate-100">${Number(s.amount).toFixed(2)}</td>
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
