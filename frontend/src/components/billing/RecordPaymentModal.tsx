import React, { useState } from 'react';
import { GlassModal } from '../ui/GlassModal';
import { Invoice } from '../../types';
import { billingApi } from '../../services/billingApi';
import { CreditCard, DollarSign } from 'lucide-react';

interface RecordPaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  invoice: Invoice;
  onSuccess: () => void;
}

export const RecordPaymentModal: React.FC<RecordPaymentModalProps> = ({
  isOpen,
  onClose,
  invoice,
  onSuccess,
}) => {
  const [amount, setAmount] = useState<string>(invoice.amount_due);
  const [paymentMethod, setPaymentMethod] = useState<'CREDIT_CARD' | 'BANK_TRANSFER' | 'CHECK' | 'ACH' | 'CASH'>('BANK_TRANSFER');
  const [txRef, setTxRef] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await billingApi.recordPayment({
        invoice_id: invoice.id,
        payment_method: paymentMethod,
        amount: amount,
        transaction_reference: txRef || undefined,
        notes: notes || undefined,
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to record payment');
    } finally {
      setLoading(false);
    }
  };

  return (
    <GlassModal
      isOpen={isOpen}
      onClose={onClose}
      title={`Record Payment for ${invoice.invoice_number}`}
      subtitle={`Remaining Balance Due: ₹${Number(invoice.amount_due).toFixed(2)}`}
      maxWidth="md"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}

        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">
            Payment Amount (INR)
          </label>
          <div className="relative">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
              <DollarSign className="w-4 h-4" />
            </span>
            <input
              type="number"
              step="0.01"
              max={invoice.amount_due}
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500 font-mono text-sm"
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">
            Payment Method
          </label>
          <select
            value={paymentMethod}
            onChange={(e) => setPaymentMethod(e.target.value as any)}
            className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500 text-sm"
          >
            <option value="BANK_TRANSFER">Bank Transfer (Wire / ACH)</option>
            <option value="CREDIT_CARD font-sans">Credit Card</option>
            <option value="CHECK">Check</option>
            <option value="ACH">ACH Direct Debit</option>
            <option value="CASH">Cash</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">
            Transaction Reference / Check #
          </label>
          <input
            type="text"
            placeholder="e.g. TXN-998811 or Check #4402"
            value={txRef}
            onChange={(e) => setTxRef(e.target.value)}
            className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500 text-sm"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">
            Notes / Internal Reference
          </label>
          <textarea
            rows={2}
            placeholder="Optional payment notes..."
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
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-semibold flex items-center gap-2 transition-colors disabled:opacity-50"
          >
            <CreditCard className="w-4 h-4" />
            {loading ? 'Recording...' : 'Record Payment'}
          </button>
        </div>
      </form>
    </GlassModal>
  );
};
