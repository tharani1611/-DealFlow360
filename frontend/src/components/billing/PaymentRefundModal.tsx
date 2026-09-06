import React, { useState } from 'react';
import { GlassModal } from '../ui/GlassModal';
import { GlassInput } from '../ui/GlassInput';
import { GlassTextarea } from '../ui/GlassTextarea';
import { BrutalButton } from '../ui/BrutalButton';
import { billingApi } from '../../services/billingApi';
import { Payment } from '../../types';
import { useToast } from '../../context/ToastContext';
import { AlertCircle } from 'lucide-react';

interface PaymentRefundModalProps {
  isOpen: boolean;
  onClose: () => void;
  payment: Payment | null;
  onSuccess: () => void;
}

export const PaymentRefundModal: React.FC<PaymentRefundModalProps> = ({
  isOpen,
  onClose,
  payment,
  onSuccess,
}) => {
  const { showToast } = useToast();
  const [refundAmount, setRefundAmount] = useState(payment?.amount || '');
  const [reason, setReason] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  if (!payment) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const amt = parseFloat(refundAmount);
    if (isNaN(amt) || amt <= 0) {
      showToast('Please enter a valid refund amount.', 'warning');
      return;
    }
    if (!reason.trim()) return;

    setIsLoading(true);
    try {
      await billingApi.createPaymentRefund({
        payment_id: payment.id,
        amount: amt,
        reason: reason.trim(),
      });
      showToast('Payment refund processed successfully.', 'success');
      onSuccess();
      onClose();
    } catch (err: any) {
      showToast(err.message || 'Failed to process payment refund.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <GlassModal isOpen={isOpen} onClose={onClose} title={`Process Refund — ${payment.payment_number}`}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>
            Original Payment Amount: <strong>₹{Number(payment.amount).toFixed(2)}</strong> ({payment.payment_method})
          </span>
        </div>

        <GlassInput
          label="Refund Amount (₹) *"
          type="number"
          step="0.01"
          max={Number(payment.amount)}
          value={refundAmount}
          onChange={(e) => setRefundAmount(e.target.value)}
          required
        />

        <GlassTextarea
          label="Refund Reason *"
          placeholder="e.g. Approved credit adjustment or duplicate charge resolution"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          required
        />

        <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
          <BrutalButton type="button" variant="secondary" onClick={onClose}>
            Cancel
          </BrutalButton>
          <BrutalButton type="submit" variant="danger" isLoading={isLoading}>
            Process Refund
          </BrutalButton>
        </div>
      </form>
    </GlassModal>
  );
};
