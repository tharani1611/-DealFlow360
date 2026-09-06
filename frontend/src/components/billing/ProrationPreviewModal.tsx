import React, { useState } from 'react';
import { GlassModal } from '../ui/GlassModal';
import { Subscription, ProrationCalculation } from '../../types';
import { billingApi } from '../../services/billingApi';
import { Calculator, CheckCircle2 } from 'lucide-react';

interface ProrationPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  subscription: Subscription;
  onSuccess: () => void;
}

export const ProrationPreviewModal: React.FC<ProrationPreviewModalProps> = ({
  isOpen,
  onClose,
  subscription,
  onSuccess,
}) => {
  const [newQuantity, setNewQuantity] = useState<number>(Number(subscription.quantity));
  const [newUnitPrice, setNewUnitPrice] = useState<string>(subscription.unit_price);
  const [notes, setNotes] = useState<string>('');
  const [calculation, setCalculation] = useState<ProrationCalculation | null>(null);
  const [loadingCalc, setLoadingCalc] = useState<boolean>(false);
  const [loadingApply, setLoadingApply] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleCalculate = async () => {
    setLoadingCalc(true);
    setError(null);
    try {
      const calc = await billingApi.calculateProration(subscription.id, {
        new_quantity: newQuantity,
        new_unit_price: newUnitPrice,
      });
      setCalculation(calc);
    } catch (err: any) {
      setError(err?.message || 'Failed to calculate proration preview');
    } finally {
      setLoadingCalc(false);
    }
  };

  const handleApply = async () => {
    setLoadingApply(true);
    setError(null);
    try {
      await billingApi.applyProration(subscription.id, {
        new_quantity: newQuantity,
        new_unit_price: newUnitPrice,
        notes: notes || undefined,
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to apply proration');
    } finally {
      setLoadingApply(false);
    }
  };

  return (
    <GlassModal
      isOpen={isOpen}
      onClose={onClose}
      title={`Mid-Cycle Proration: ${subscription.subscription_number}`}
      subtitle={`Plan: ${subscription.plan_name} (${subscription.billing_interval})`}
      maxWidth="lg"
    >
      <div className="space-y-4">
        {error && (
          <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}

        <div className="grid grid-cols-2 gap-4 bg-slate-950/60 p-3 rounded-lg border border-slate-800">
          <div>
            <div className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Current State</div>
            <div className="text-sm font-mono text-slate-200 mt-1">
              Quantity: {subscription.quantity} @ ₹{Number(subscription.unit_price).toFixed(2)}
            </div>
            <div className="text-xs text-slate-400 mt-1">
              Next Billing: {subscription.next_billing_date}
            </div>
          </div>
          <div>
            <div className="text-xs text-indigo-400 uppercase tracking-wider font-semibold">Target State</div>
            <div className="flex gap-2 mt-1">
              <div>
                <label className="text-[10px] text-slate-500">New Qty</label>
                <input
                  type="number"
                  min="0.01"
                  step="1"
                  value={newQuantity}
                  onChange={(e) => setNewQuantity(Number(e.target.value))}
                  className="w-full px-2 py-1 bg-slate-900 border border-slate-700 rounded text-slate-200 font-mono text-xs"
                />
              </div>
              <div>
                <label className="text-[10px] text-slate-500">Unit Price (₹)</label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={newUnitPrice}
                  onChange={(e) => setNewUnitPrice(e.target.value)}
                  className="w-full px-2 py-1 bg-slate-900 border border-slate-700 rounded text-slate-200 font-mono text-xs"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="button"
            onClick={handleCalculate}
            disabled={loadingCalc}
            className="px-3 py-1.5 bg-indigo-600/30 hover:bg-indigo-600/50 border border-indigo-500/50 text-indigo-200 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            <Calculator className="w-3.5 h-3.5" />
            {loadingCalc ? 'Calculating...' : 'Preview Proration Math'}
          </button>
        </div>

        {calculation && (
          <div className="bg-slate-950 p-4 rounded-lg border border-indigo-500/30 space-y-2">
            <h4 className="text-xs font-bold text-indigo-300 uppercase tracking-wider">
              Proration Math Breakdown
            </h4>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs font-mono">
              <span className="text-slate-400">Total Period Days:</span>
              <span className="text-slate-200 text-right">{calculation.total_period_days} days</span>

              <span className="text-slate-400">Remaining Days in Cycle:</span>
              <span className="text-slate-200 text-right">{calculation.remaining_days} days</span>

              <span className="text-slate-400">Unused Credit (Current Plan):</span>
              <span className="text-emerald-400 text-right">-₹{Number(calculation.unused_amount).toFixed(2)}</span>

              <span className="text-slate-400">Prorated Charge (New Plan):</span>
              <span className="text-indigo-400 text-right">+₹{Number(calculation.new_amount).toFixed(2)}</span>

              <div className="col-span-2 border-t border-slate-800 my-1"></div>

              <span className="text-slate-200 font-bold">Net Prorated Adjustment:</span>
              <span className="text-amber-400 font-bold text-right text-sm">
                ₹{Number(calculation.net_prorated_amount).toFixed(2)}
              </span>
            </div>
          </div>
        )}

        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">
            Reason / Audit Notes
          </label>
          <textarea
            rows={2}
            placeholder="e.g. Added 5 seats mid-billing cycle per agreement"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500 text-sm resize-none"
          />
        </div>

        <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleApply}
            disabled={loadingApply || !calculation}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-semibold flex items-center gap-2 transition-colors disabled:opacity-50"
          >
            <CheckCircle2 className="w-4 h-4" />
            {loadingApply ? 'Applying...' : 'Apply Mid-Cycle Proration'}
          </button>
        </div>
      </div>
    </GlassModal>
  );
};
