import React, { useState } from 'react';
import { GlassModal } from '../ui/GlassModal';
import { Invoice } from '../../types';
import { billingApi } from '../../services/billingApi';
import { FileText, Plus, Trash2 } from 'lucide-react';

interface CreditNoteModalProps {
  isOpen: boolean;
  onClose: () => void;
  invoice: Invoice;
  onSuccess: () => void;
}

interface CreditNoteLineItem {
  description: string;
  quantity: number;
  unit_price: string;
}

export const CreditNoteModal: React.FC<CreditNoteModalProps> = ({
  isOpen,
  onClose,
  invoice,
  onSuccess,
}) => {
  const [reason, setReason] = useState<string>('');
  const [items, setItems] = useState<CreditNoteLineItem[]>([
    {
      description: invoice.items && invoice.items.length > 0 ? invoice.items[0].description : 'Billing Correction',
      quantity: 1,
      unit_price: '0.00',
    },
  ]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const addItem = () => {
    setItems([...items, { description: '', quantity: 1, unit_price: '0.00' }]);
  };

  const removeItem = (index: number) => {
    if (items.length <= 1) return;
    setItems(items.filter((_, i) => i !== index));
  };

  const updateItem = (index: number, field: keyof CreditNoteLineItem, value: any) => {
    const next = [...items];
    next[index] = { ...next[index], [field]: value };
    setItems(next);
  };

  const calculateTotal = () => {
    return items.reduce((sum, item) => sum + item.quantity * (Number(item.unit_price) || 0), 0);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await billingApi.createCreditNote({
        invoice_id: invoice.id,
        reason: reason,
        items: items.map((i) => ({
          description: i.description,
          quantity: i.quantity,
          unit_price: i.unit_price,
        })),
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to issue credit note');
    } finally {
      setLoading(false);
    }
  };

  return (
    <GlassModal
      isOpen={isOpen}
      onClose={onClose}
      title={`Issue Credit Note for ${invoice.invoice_number}`}
      subtitle={`Invoice Total: ₹${Number(invoice.total).toFixed(2)} | Paid: ₹${Number(invoice.amount_paid).toFixed(2)}`}
      maxWidth="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}

        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">
            Reason for Credit Note
          </label>
          <input
            type="text"
            placeholder="e.g. Return of goods / billing adjustment per agreement"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500 text-sm"
            required
            minLength={3}
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-medium text-slate-400">Line Items to Credit</label>
            <button
              type="button"
              onClick={addItem}
              className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-semibold"
            >
              <Plus className="w-3.5 h-3.5" /> Add Line Item
            </button>
          </div>

          <div className="space-y-2">
            {items.map((item, idx) => (
              <div key={idx} className="flex items-center gap-2 bg-slate-950 p-2 rounded-lg border border-slate-800">
                <input
                  type="text"
                  placeholder="Description"
                  value={item.description}
                  onChange={(e) => updateItem(idx, 'description', e.target.value)}
                  className="flex-1 px-2 py-1 bg-slate-900 border border-slate-700 rounded text-slate-200 text-xs"
                  required
                />
                <input
                  type="number"
                  placeholder="Qty"
                  min="0.01"
                  step="1"
                  value={item.quantity}
                  onChange={(e) => updateItem(idx, 'quantity', Number(e.target.value))}
                  className="w-16 px-2 py-1 bg-slate-900 border border-slate-700 rounded text-slate-200 font-mono text-xs text-center"
                  required
                />
                <input
                  type="number"
                  placeholder="Unit Price (₹)"
                  min="0"
                  step="0.01"
                  value={item.unit_price}
                  onChange={(e) => updateItem(idx, 'unit_price', e.target.value)}
                  className="w-24 px-2 py-1 bg-slate-900 border border-slate-700 rounded text-slate-200 font-mono text-xs text-right"
                  required
                />
                <div className="w-20 text-right font-mono text-xs text-slate-300 font-bold">
                  ${(item.quantity * (Number(item.unit_price) || 0)).toFixed(2)}
                </div>
                {items.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeItem(idx)}
                    className="p-1 text-slate-500 hover:text-red-400"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="flex justify-between items-center p-3 bg-slate-950/80 rounded-lg border border-slate-800">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Credit Amount</span>
          <span className="text-base font-bold font-mono text-amber-400">₹{calculateTotal().toFixed(2)}</span>
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
            className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-sm font-semibold flex items-center gap-2 transition-colors disabled:opacity-50"
          >
            <FileText className="w-4 h-4" />
            {loading ? 'Issuing...' : 'Issue Credit Note'}
          </button>
        </div>
      </form>
    </GlassModal>
  );
};
