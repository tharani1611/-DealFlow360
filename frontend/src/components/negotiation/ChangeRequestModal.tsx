import React, { useState } from 'react';
import { ChangeRequestCreate, CounterDiscountApply } from '../../types';
import { portalApi } from '../../services/portalApi';
import { negotiationApi } from '../../services/negotiationApi';
import { Percent, Edit3, X, AlertCircle } from 'lucide-react';

interface ChangeRequestModalProps {
  quotationId: string;
  quotationItemId?: string | null;
  itemName?: string;
  isPortal?: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const ChangeRequestModal: React.FC<ChangeRequestModalProps> = ({
  quotationId,
  quotationItemId = null,
  itemName,
  isPortal = false,
  onClose,
  onSuccess,
}) => {
  const [changeType, setChangeType] = useState<'quantity_change' | 'counter_discount' | 'validity_extension' | 'general_terms'>('counter_discount');
  const [requestedDiscount, setRequestedDiscount] = useState<string>('15.00');
  const [requestedQuantity, setRequestedQuantity] = useState<string>('1');
  const [details, setDetails] = useState<string>('');
  const [reason, setReason] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      setSubmitting(true);
      if (isPortal) {
        const payload: ChangeRequestCreate = {
          quotation_item_id: quotationItemId,
          change_type: changeType,
          requested_discount_percent: changeType === 'counter_discount' ? parseFloat(requestedDiscount) : undefined,
          requested_quantity: changeType === 'quantity_change' ? parseFloat(requestedQuantity) : undefined,
          request_details: details.trim(),
        };
        await portalApi.createChangeRequest(quotationId, payload);
      } else {
        // Internal user applying counter-discount directly
        const payload: CounterDiscountApply = {
          quotation_item_id: quotationItemId,
          requested_discount_percent: parseFloat(requestedDiscount),
          change_reason: reason.trim() || details.trim() || 'Counter discount applied',
        };
        await negotiationApi.applyCounterDiscount(quotationId, payload);
      }
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Operation failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full overflow-hidden shadow-2xl">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <Edit3 className="w-5 h-5 text-emerald-400" />
            {isPortal ? 'Submit Proposal / Change Request' : 'Apply Counter-Discount'}
          </h3>
          <button onClick={onClose} className="p-1 text-slate-400 hover:text-white rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs rounded-lg flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {itemName && (
            <div className="text-xs text-slate-400 bg-slate-800/50 p-2.5 rounded-lg border border-slate-700/50">
              <span className="text-slate-300 font-medium">Target Item: </span>
              {itemName}
            </div>
          )}

          {isPortal && (
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Request Type</label>
              <select
                value={changeType}
                onChange={(e: any) => setChangeType(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500"
              >
                <option value="counter_discount">Counter-Discount Proposal (%)</option>
                <option value="quantity_change">Quantity Adjustment</option>
                <option value="validity_extension">Validity Extension</option>
                <option value="general_terms">Commercial Terms Modification</option>
              </select>
            </div>
          )}

          {(changeType === 'counter_discount' || !isPortal) && (
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Requested Counter Discount (%)
              </label>
              <div className="relative">
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="100"
                  value={requestedDiscount}
                  onChange={(e) => setRequestedDiscount(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500 pr-8"
                  required
                />
                <Percent className="w-4 h-4 text-slate-400 absolute right-3 top-3" />
              </div>
            </div>
          )}

          {isPortal && changeType === 'quantity_change' && (
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Requested Quantity</label>
              <input
                type="number"
                step="1"
                min="1"
                value={requestedQuantity}
                onChange={(e) => setRequestedQuantity(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500"
                required
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              {isPortal ? 'Request Details & Justification' : 'Commercial Change Reason'}
            </label>
            <textarea
              rows={3}
              value={isPortal ? details : reason}
              onChange={(e) => (isPortal ? setDetails(e.target.value) : setReason(e.target.value))}
              placeholder={isPortal ? 'Explain your proposed counter-offer or terms request...' : 'Explain why this counter discount is being applied...'}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-emerald-500 placeholder-slate-500"
              required
            />
          </div>

          {!isPortal && (
            <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg text-amber-300 text-xs">
              <strong>Notice:</strong> Applying a counter-discount will recalculate quotation totals, invalidate previous commercial approvals, and record a new version snapshot.
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm rounded-xl"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold rounded-xl transition disabled:opacity-50"
            >
              {submitting ? 'Submitting...' : isPortal ? 'Submit Proposal' : 'Apply Counter-Discount'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
