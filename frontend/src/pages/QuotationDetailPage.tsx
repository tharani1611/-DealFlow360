import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { quotationApi } from '../services/quotationApi';
import { Quotation } from '../types';
import { GlassCard } from '../components/ui/GlassCard';
import { StatusBadge } from '../components/ui/StatusBadge';
import { BrutalButton } from '../components/ui/BrutalButton';
import { LoadingState, ErrorState } from '../components/ui/EmptyState';
import { useToast } from '../context/ToastContext';
import { ArrowLeft, CheckCircle2, XCircle, Ban } from 'lucide-react';

export const QuotationDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [quotation, setQuotation] = useState<Quotation | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadQuotation = async () => {
    if (!id) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await quotationApi.getQuotation(id);
      setQuotation(data);
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve quotation record.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadQuotation();
  }, [id]);

  const handleFinalize = async (action: 'accept' | 'reject' | 'cancel') => {
    if (!id) return;
    setIsUpdating(true);
    try {
      const updated = await quotationApi.finalizeQuotation(id, action);
      setQuotation(updated);
      showToast(`Quotation status changed to ${updated.status}.`, 'success');
    } catch (err: any) {
      showToast(err.message || 'Failed to transition quotation status.', 'error');
    } finally {
      setIsUpdating(false);
    }
  };

  if (isLoading) return <LoadingState message="Loading quotation telemetry..." />;
  if (error || !quotation) return <ErrorState message={error || 'Quotation not found'} onRetry={loadQuotation} />;

  const isFinalized = ['accepted', 'rejected', 'cancelled'].includes(quotation.status);

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <button
        onClick={() => navigate('/quotations')}
        className="flex items-center gap-2 text-xs font-bold text-slate-400 hover:text-slate-100 transition"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Quotations Center</span>
      </button>

      {/* Header Card */}
      <GlassCard className="border-l-4 border-l-indigo-500">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-black font-mono text-slate-100 tracking-tight">
                {quotation.quotation_number}
              </h1>
              <StatusBadge status={quotation.status} />
            </div>
            <p className="text-xs text-slate-400 font-mono mt-1">
              Date: {new Date(quotation.quotation_date).toLocaleDateString()}
            </p>
          </div>

          {!isFinalized && (
            <div className="flex items-center gap-2 flex-wrap">
              <BrutalButton
                variant="success"
                size="sm"
                icon={CheckCircle2}
                onClick={() => handleFinalize('accept')}
                isLoading={isUpdating}
              >
                Accept Proposal
              </BrutalButton>
              <BrutalButton
                variant="danger"
                size="sm"
                icon={XCircle}
                onClick={() => handleFinalize('reject')}
                isLoading={isUpdating}
              >
                Reject Proposal
              </BrutalButton>
              <BrutalButton
                variant="ghost"
                size="sm"
                icon={Ban}
                onClick={() => handleFinalize('cancel')}
                isLoading={isUpdating}
              >
                Cancel
              </BrutalButton>
            </div>
          )}
        </div>
      </GlassCard>

      {/* Items Table */}
      <GlassCard title="Quotation Line Items">
        <div className="overflow-x-auto">
          <table className="neo-glass-table">
            <thead>
              <tr>
                <th>Description</th>
                <th className="text-right">Qty</th>
                <th className="text-right">Unit Price</th>
                <th className="text-right">Line Total</th>
              </tr>
            </thead>
            <tbody>
              {quotation.items && quotation.items.length > 0 ? (
                quotation.items.map((item) => (
                  <tr key={item.id}>
                    <td className="font-semibold text-slate-100">{item.description}</td>
                    <td className="text-right font-mono">{item.quantity}</td>
                    <td className="text-right font-mono">${Number(item.unit_price).toLocaleString()}</td>
                    <td className="text-right font-mono font-bold">${Number(item.line_total).toLocaleString()}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="text-center text-slate-400 font-mono text-xs py-4">
                    No line items attached.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Financial Summary */}
        <div className="mt-6 pt-4 border-t border-slate-800 flex justify-end">
          <div className="w-64 space-y-2 text-xs font-mono">
            <div className="flex justify-between text-slate-400">
              <span>Subtotal:</span>
              <span>${Number(quotation.subtotal).toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Discount:</span>
              <span>-${Number(quotation.discount_amount).toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Tax:</span>
              <span>+${Number(quotation.tax_amount).toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-sm font-black text-slate-100 pt-2 border-t border-slate-700">
              <span>Total Amount:</span>
              <span className="text-emerald-400">${Number(quotation.total_amount).toLocaleString()}</span>
            </div>
          </div>
        </div>
      </GlassCard>

      {quotation.notes && (
        <GlassCard title="Notes & Terms">
          <p className="text-xs text-slate-300 font-mono leading-relaxed">{quotation.notes}</p>
        </GlassCard>
      )}
    </div>
  );
};
