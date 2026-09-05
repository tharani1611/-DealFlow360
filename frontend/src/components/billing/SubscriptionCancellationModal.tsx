import React, { useState } from 'react';
import { GlassModal } from '../ui/GlassModal';
import { GlassSelect } from '../ui/GlassSelect';
import { GlassTextarea } from '../ui/GlassTextarea';
import { BrutalButton } from '../ui/BrutalButton';
import { billingApi } from '../../services/billingApi';
import { Subscription } from '../../types';
import { useToast } from '../../context/ToastContext';
import { AlertTriangle } from 'lucide-react';

interface SubscriptionCancellationModalProps {
  isOpen: boolean;
  onClose: () => void;
  subscription: Subscription | null;
  onSuccess: () => void;
}

export const SubscriptionCancellationModal: React.FC<SubscriptionCancellationModalProps> = ({
  isOpen,
  onClose,
  subscription,
  onSuccess,
}) => {
  const { showToast } = useToast();
  const [cancelType, setCancelType] = useState<'IMMEDIATE' | 'END_OF_PERIOD'>('END_OF_PERIOD');
  const [reason, setReason] = useState('');
  const [notes, setNotes] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  if (!subscription) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reason.trim()) return;

    setIsLoading(true);
    try {
      await billingApi.cancelSubscription(subscription.id, {
        cancellation_type: cancelType,
        reason: reason.trim(),
        notes: notes.trim() || undefined,
      });
      showToast('Subscription cancelled successfully.', 'success');
      onSuccess();
      onClose();
    } catch (err: any) {
      showToast(err.message || 'Failed to cancel subscription.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <GlassModal isOpen={isOpen} onClose={onClose} title={`Cancel Subscription ${subscription.subscription_number}`}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>
            Cancelling plan <strong>{subscription.plan_name}</strong> for customer account.
          </span>
        </div>

        <GlassSelect
          label="Cancellation Type *"
          value={cancelType}
          onChange={(e) => setCancelType(e.target.value as any)}
          options={[
            { label: 'End of Current Billing Period (Recommended)', value: 'END_OF_PERIOD' },
            { label: 'Immediate Cancellation', value: 'IMMEDIATE' },
          ]}
        />

        <GlassTextarea
          label="Cancellation Reason *"
          placeholder="e.g. Customer migrated to custom enterprise contract"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          required
        />

        <GlassTextarea
          label="Additional Audit Notes"
          placeholder="Optional notes for billing history..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />

        <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
          <BrutalButton type="button" variant="secondary" onClick={onClose}>
            Close
          </BrutalButton>
          <BrutalButton type="submit" variant="danger" isLoading={isLoading}>
            Confirm Cancellation
          </BrutalButton>
        </div>
      </form>
    </GlassModal>
  );
};
