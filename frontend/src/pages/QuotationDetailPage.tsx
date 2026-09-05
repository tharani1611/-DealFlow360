import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { quotationApi } from '../services/quotationApi';
import { commercialGovernanceApi } from '../services/commercialGovernanceApi';
import { Quotation, QuotationStatus, QuotationStateHistoryItem, CommercialGovernanceSummaryResponse } from '../types';
import { GlassCard } from '../components/ui/GlassCard';
import { StatusBadge } from '../components/ui/StatusBadge';
import { BrutalButton } from '../components/ui/BrutalButton';
import { GlassModal } from '../components/ui/GlassModal';
import { GlassInput } from '../components/ui/GlassInput';
import { LoadingState, ErrorState } from '../components/ui/EmptyState';
import { useToast } from '../context/ToastContext';
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Ban,
  Send,
  Lock,
  History,
  DollarSign,
  RotateCcw,
  Zap,
  Clock,
  UserCheck,
  ShieldCheck,
} from 'lucide-react';

export const QuotationDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [quotation, setQuotation] = useState<Quotation | null>(null);
  const [history, setHistory] = useState<QuotationStateHistoryItem[]>([]);
  const [governanceSummary, setGovernanceSummary] = useState<CommercialGovernanceSummaryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Transition modal state
  const [isTransitionModalOpen, setIsTransitionModalOpen] = useState(false);
  const [targetStatus, setTargetStatus] = useState<QuotationStatus | null>(null);
  const [transitionReason, setTransitionReason] = useState('');

  const loadQuotationData = async () => {
    if (!id) return;
    setIsLoading(true);
    setError(null);
    try {
      const [qData, histData, govData] = await Promise.all([
        quotationApi.getQuotation(id),
        quotationApi.getQuotationHistory(id),
        commercialGovernanceApi.getQuotationGovernanceSummary(id).catch(() => null),
      ]);
      setQuotation(qData);
      setHistory(histData);
      setGovernanceSummary(govData);
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve quotation details.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadQuotationData();
  }, [id]);

  const openTransitionModal = (status: QuotationStatus) => {
    setTargetStatus(status);
    setTransitionReason('');
    setIsTransitionModalOpen(true);
  };

  const handleExecuteTransition = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !targetStatus) return;

    setIsUpdating(true);
    try {
      const updated = await quotationApi.transitionQuotation(id, {
        target_status: targetStatus,
        reason: transitionReason.trim() || undefined,
      });
      setQuotation(updated);
      showToast(`Quotation status successfully updated to ${updated.status.toUpperCase()}.`, 'success');
      setIsTransitionModalOpen(false);
      loadQuotationData();
    } catch (err: any) {
      showToast(err.message || 'Failed to transition quotation status.', 'error');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleApprovalDecision = async (decision: 'APPROVED' | 'REJECTED') => {
    if (!id) return;
    setIsUpdating(true);
    try {
      await commercialGovernanceApi.submitApprovalDecision(id, { decision });
      showToast(`Quotation approval decision set to ${decision}.`, 'success');
      loadQuotationData();
    } catch (err: any) {
      showToast(err.message || 'Failed to submit approval decision.', 'error');
    } finally {
      setIsUpdating(false);
    }
  };

  if (isLoading) return <LoadingState message="Loading quotation telemetry & commercial governance..." />;
  if (error || !quotation) return <ErrorState message={error || 'Quotation not found'} onRetry={loadQuotationData} />;

  const isLocked = ['sent', 'accepted', 'rejected', 'expired', 'cancelled', 'converted'].includes(quotation.status);
  const approvalStatus = governanceSummary?.approval?.status || 'NOT_REQUIRED';
  const isApprovalPending = approvalStatus === 'PENDING';
  const isApprovalBlocked = ['PENDING', 'REJECTED', 'INVALIDATED'].includes(approvalStatus);

  // Helper to determine allowed transition buttons for current status
  const renderWorkflowActions = () => {
    const status = quotation.status;

    return (
      <div className="flex items-center gap-2 flex-wrap">
        {status === 'draft' && (
          <>
            <BrutalButton
              variant="secondary"
              size="sm"
              icon={DollarSign}
              onClick={() => openTransitionModal('priced')}
              isLoading={isUpdating}
            >
              Mark Priced
            </BrutalButton>
            <BrutalButton
              variant="primary"
              size="sm"
              icon={Send}
              onClick={() => openTransitionModal('sent')}
              isLoading={isUpdating}
              disabled={isApprovalBlocked}
              title={isApprovalBlocked ? `Blocked: Authorization is ${approvalStatus}` : 'Send Quotation'}
            >
              Send Quotation
            </BrutalButton>
            <BrutalButton
              variant="ghost"
              size="sm"
              icon={Ban}
              onClick={() => openTransitionModal('cancelled')}
              isLoading={isUpdating}
            >
              Cancel
            </BrutalButton>
          </>
        )}

        {status === 'priced' && (
          <>
            <BrutalButton
              variant="ghost"
              size="sm"
              icon={RotateCcw}
              onClick={() => openTransitionModal('draft')}
              isLoading={isUpdating}
            >
              Revert to Draft
            </BrutalButton>
            <BrutalButton
              variant="primary"
              size="sm"
              icon={Send}
              onClick={() => openTransitionModal('sent')}
              isLoading={isUpdating}
              disabled={isApprovalBlocked}
              title={isApprovalBlocked ? `Blocked: Authorization is ${approvalStatus}` : 'Send Quotation'}
            >
              Send Quotation
            </BrutalButton>
            <BrutalButton
              variant="ghost"
              size="sm"
              icon={Ban}
              onClick={() => openTransitionModal('cancelled')}
              isLoading={isUpdating}
            >
              Cancel
            </BrutalButton>
          </>
        )}

        {status === 'sent' && (
          <>
            <BrutalButton
              variant="success"
              size="sm"
              icon={CheckCircle2}
              onClick={() => openTransitionModal('accepted')}
              isLoading={isUpdating}
            >
              Accept Proposal
            </BrutalButton>
            <BrutalButton
              variant="danger"
              size="sm"
              icon={XCircle}
              onClick={() => openTransitionModal('rejected')}
              isLoading={isUpdating}
            >
              Reject Proposal
            </BrutalButton>
            <BrutalButton
              variant="ghost"
              size="sm"
              icon={Ban}
              onClick={() => openTransitionModal('cancelled')}
              isLoading={isUpdating}
            >
              Cancel
            </BrutalButton>
          </>
        )}

        {status === 'accepted' && (
          <BrutalButton
            variant="primary"
            size="sm"
            icon={Zap}
            onClick={() => openTransitionModal('converted')}
            isLoading={isUpdating}
          >
            Convert Proposal
          </BrutalButton>
        )}

        {status === 'expired' && (
          <BrutalButton
            variant="secondary"
            size="sm"
            icon={RotateCcw}
            onClick={() => openTransitionModal('draft')}
            isLoading={isUpdating}
          >
            Re-Quote / Reset Draft
          </BrutalButton>
        )}

        {['rejected', 'cancelled', 'converted'].includes(status) && (
          <div className="flex items-center gap-1.5 text-xs font-mono text-slate-400 bg-slate-900/80 px-3 py-1.5 rounded border border-slate-800">
            <Lock className="w-3.5 h-3.5 text-slate-500" />
            <span>Terminal Lifecycle State</span>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      <button
        onClick={() => navigate('/quotations')}
        className="flex items-center gap-2 text-xs font-bold text-slate-400 hover:text-slate-100 transition"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Quotations Center</span>
      </button>

      {/* Header Card */}
      <GlassCard className="border-l-4 border-l-cyan-500">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-black font-mono text-slate-100 tracking-tight">
                {quotation.quotation_number}
              </h1>
              <StatusBadge status={quotation.status} size="md" />
            </div>
            <p className="text-xs text-slate-400 font-mono mt-1 flex items-center gap-3">
              <span>Date: {new Date(quotation.quotation_date).toLocaleDateString()}</span>
              {quotation.valid_until && (
                <span>Valid Until: {new Date(quotation.valid_until).toLocaleDateString()}</span>
              )}
            </p>
          </div>

          {renderWorkflowActions()}
        </div>
      </GlassCard>

      {/* Commercial Governance Intelligence Card (Phases 23–25) */}
      {governanceSummary && (
        <GlassCard className="border border-slate-800 bg-slate-900/70">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-cyan-400" />
              <h3 className="text-xs font-bold font-mono uppercase tracking-wider text-slate-100">
                Commercial Governance Intelligence (Phases 23–25)
              </h3>
            </div>
            {isApprovalPending && (
              <div className="flex items-center gap-2">
                <BrutalButton
                  variant="success"
                  size="sm"
                  icon={CheckCircle2}
                  onClick={() => handleApprovalDecision('APPROVED')}
                  isLoading={isUpdating}
                >
                  Approve Proposal
                </BrutalButton>
                <BrutalButton
                  variant="danger"
                  size="sm"
                  icon={XCircle}
                  onClick={() => handleApprovalDecision('REJECTED')}
                  isLoading={isUpdating}
                >
                  Reject Proposal
                </BrutalButton>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Phase 23: Discount Governance */}
            <div className="p-3 bg-slate-950/80 border border-slate-800/80 rounded-lg space-y-1.5">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
                Phase 23 — Discount Policy
              </span>
              <div className="flex items-center gap-2">
                <StatusBadge
                  status={governanceSummary.governance.status}
                  variant={governanceSummary.governance.compliant ? 'success' : 'danger'}
                  size="sm"
                />
              </div>
              <p className="text-[11px] font-mono text-slate-300 mt-1">
                Blended Discount: <strong className="text-cyan-400">{governanceSummary.governance.blended_discount_percent}%</strong>
              </p>
              {governanceSummary.governance.violations.length > 0 && (
                <div className="mt-2 space-y-1">
                  {governanceSummary.governance.violations.map((v, i) => (
                    <p key={i} className="text-[10px] font-mono text-rose-400 bg-rose-950/30 p-1.5 rounded border border-rose-500/20">
                      ⚠ {v.message}
                    </p>
                  ))}
                </div>
              )}
            </div>

            {/* Phase 24: Risk Engine */}
            <div className="p-3 bg-slate-950/80 border border-slate-800/80 rounded-lg space-y-1.5">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
                Phase 24 — Risk Engine
              </span>
              <div className="flex items-center gap-2">
                <StatusBadge
                  status={governanceSummary.risk.risk_level}
                  variant={
                    governanceSummary.risk.risk_level === 'CRITICAL' || governanceSummary.risk.risk_level === 'HIGH'
                      ? 'danger'
                      : governanceSummary.risk.risk_level === 'MEDIUM'
                      ? 'warning'
                      : 'success'
                  }
                  size="sm"
                />
                <span className="text-xs font-mono font-bold text-slate-300">
                  Score: {governanceSummary.risk.risk_score}/100
                </span>
              </div>
              <p className="text-[11px] font-mono text-slate-300 mt-1">
                Margin: <strong className="text-emerald-400">{governanceSummary.risk.overall_margin_percent}%</strong>
              </p>
              {governanceSummary.risk.risk_factors.length > 0 && (
                <div className="mt-2 space-y-1">
                  {governanceSummary.risk.risk_factors.map((rf, i) => (
                    <p key={i} className="text-[10px] font-mono text-amber-300 bg-amber-950/30 p-1 rounded border border-amber-500/20">
                      • {rf.title}: {rf.description}
                    </p>
                  ))}
                </div>
              )}
            </div>

            {/* Phase 25: Approval Engine */}
            <div className="p-3 bg-slate-950/80 border border-slate-800/80 rounded-lg space-y-1.5">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
                Phase 25 — Authorization State
              </span>
              <div className="flex items-center gap-2">
                <StatusBadge
                  status={approvalStatus}
                  variant={
                    approvalStatus === 'APPROVED'
                      ? 'success'
                      : approvalStatus === 'PENDING'
                      ? 'warning'
                      : approvalStatus === 'NOT_REQUIRED'
                      ? 'info'
                      : 'danger'
                  }
                  size="sm"
                />
              </div>
              {governanceSummary.approval.reasons && (
                <p className="text-[10px] font-mono text-slate-300 bg-slate-900 p-1.5 rounded border border-slate-800 mt-1">
                  Trigger: {governanceSummary.approval.reasons}
                </p>
              )}
              {governanceSummary.approval.decision_note && (
                <p className="text-[10px] font-mono text-emerald-400 bg-emerald-950/30 p-1 rounded border border-emerald-500/20 mt-1">
                  Note: "{governanceSummary.approval.decision_note}"
                </p>
              )}
            </div>
          </div>
        </GlassCard>
      )}

      {/* Locked Status Banner Notice */}
      {isLocked && (
        <div className="p-3 bg-amber-950/40 border border-amber-500/30 rounded-lg flex items-center justify-between gap-3 text-xs font-mono text-amber-300">
          <div className="flex items-center gap-2">
            <Lock className="w-4 h-4 text-amber-400 shrink-0" />
            <span>
              This quotation is in <strong>{quotation.status.toUpperCase()}</strong> state. Commercial line items & financial totals are strictly locked.
            </span>
          </div>
          {quotation.status === 'expired' && (
            <span className="text-[10px] text-amber-400 underline cursor-pointer" onClick={() => openTransitionModal('draft')}>
              Reset to Draft to Re-Quote
            </span>
          )}
        </div>
      )}

      {/* Line Items Card */}
      <GlassCard title="Quotation Line Items & Commercial Snapshots">
        <div className="overflow-x-auto">
          <table className="neo-glass-table">
            <thead>
              <tr>
                <th>Seq</th>
                <th>Product / Description</th>
                <th className="text-right">Qty</th>
                <th className="text-right">Unit Price</th>
                <th className="text-right">Disc %</th>
                <th className="text-right">Tax Rate</th>
                <th className="text-right">Line Total</th>
              </tr>
            </thead>
            <tbody>
              {quotation.items && quotation.items.length > 0 ? (
                quotation.items.map((item, idx) => (
                  <tr key={item.id}>
                    <td className="font-mono text-xs text-slate-400">{item.sequence || idx + 1}</td>
                    <td>
                      <div className="font-semibold text-slate-100 text-xs">{item.product_name}</div>
                      {item.sku && <span className="font-mono text-[10px] text-slate-500 block">SKU: {item.sku}</span>}
                      {item.description && <span className="text-[11px] text-slate-400 block">{item.description}</span>}
                    </td>
                    <td className="text-right font-mono text-xs">{Number(item.quantity).toLocaleString()}</td>
                    <td className="text-right font-mono text-xs">${Number(item.unit_price).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                    <td className="text-right font-mono text-xs text-slate-400">{Number(item.discount_percent || 0).toFixed(1)}%</td>
                    <td className="text-right font-mono text-xs text-slate-400">{Number(item.tax_rate || 0).toFixed(1)}%</td>
                    <td className="text-right font-mono text-xs font-bold text-slate-100">${Number(item.line_total).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="text-center text-slate-400 font-mono text-xs py-4">
                    No line items attached.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Financial Summary */}
        <div className="mt-6 pt-4 border-t border-slate-800 flex justify-end">
          <div className="w-72 space-y-2 text-xs font-mono">
            <div className="flex justify-between text-slate-400">
              <span>Subtotal:</span>
              <span>${Number(quotation.subtotal).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Discount Amount:</span>
              <span>-${Number(quotation.discount_amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Tax Amount:</span>
              <span>+${Number(quotation.tax_amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
            </div>
            <div className="flex justify-between text-sm font-black text-slate-100 pt-2 border-t border-slate-700">
              <span>Total Proposal Amount:</span>
              <span className="text-cyan-400">{quotation.currency || 'USD'} ${Number(quotation.total_amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
            </div>
          </div>
        </div>
      </GlassCard>

      {/* Notes & Terms Card */}
      {(quotation.notes || quotation.terms) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {quotation.notes && (
            <GlassCard title="Internal Notes">
              <p className="text-xs text-slate-300 font-mono leading-relaxed">{quotation.notes}</p>
            </GlassCard>
          )}
          {quotation.terms && (
            <GlassCard title="Commercial Terms & Conditions">
              <p className="text-xs text-slate-300 font-mono leading-relaxed">{quotation.terms}</p>
            </GlassCard>
          )}
        </div>
      )}

      {/* State Machine Audit History Timeline */}
      <GlassCard title="State Machine Audit History Timeline">
        {history.length === 0 ? (
          <p className="text-xs font-mono text-slate-500">No transition history logged.</p>
        ) : (
          <div className="space-y-4 relative before:absolute before:inset-0 before:left-3.5 before:w-0.5 before:bg-slate-800">
            {history.map((entry) => (
              <div key={entry.id} className="relative flex items-start gap-4 pl-8">
                <div className="absolute left-1.5 top-1.5 w-4 h-4 rounded-full bg-slate-900 border border-cyan-500/50 flex items-center justify-center text-cyan-400">
                  <History className="w-2.5 h-2.5" />
                </div>
                <div className="flex-1 bg-slate-900/60 border border-slate-800 p-3 rounded-lg space-y-1.5">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-300 uppercase">
                        {entry.from_status ? entry.from_status.toUpperCase() : 'INITIAL'}
                      </span>
                      <span className="text-xs text-slate-500 font-bold">→</span>
                      <StatusBadge status={entry.to_status} size="sm" />
                    </div>
                    <span className="text-[10px] font-mono text-slate-400 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(entry.created_at).toLocaleString()}
                    </span>
                  </div>

                  {entry.changed_by_user_name && (
                    <div className="text-[11px] font-mono text-slate-400 flex items-center gap-1">
                      <UserCheck className="w-3 h-3 text-cyan-400" />
                      <span>Initiated by: {entry.changed_by_user_name}</span>
                    </div>
                  )}

                  {entry.reason && (
                    <p className="text-xs font-mono text-slate-300 bg-slate-950/60 p-2 rounded border border-slate-800/80">
                      "{entry.reason}"
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </GlassCard>

      {/* State Transition Modal */}
      <GlassModal
        isOpen={isTransitionModalOpen}
        onClose={() => setIsTransitionModalOpen(false)}
        title={`Transition Status to ${targetStatus?.toUpperCase()}`}
        subtitle="State machine lifecycle governance action"
      >
        <form onSubmit={handleExecuteTransition} className="space-y-4">
          <p className="text-xs font-mono text-slate-300">
            Transitioning quotation <strong>{quotation.quotation_number}</strong> from status{' '}
            <span className="text-amber-400">{quotation.status.toUpperCase()}</span> to{' '}
            <span className="text-cyan-400">{targetStatus?.toUpperCase()}</span>.
          </p>

          <GlassInput
            label="Audit Notes / Reason (Optional)"
            placeholder="Enter reason for status transition..."
            value={transitionReason}
            onChange={(e) => setTransitionReason(e.target.value)}
          />

          <div className="pt-4 flex items-center justify-end gap-3 border-t border-slate-800">
            <BrutalButton type="button" variant="ghost" onClick={() => setIsTransitionModalOpen(false)}>
              Cancel
            </BrutalButton>
            <BrutalButton type="submit" variant="primary" isLoading={isUpdating}>
              Confirm Transition
            </BrutalButton>
          </div>
        </form>
      </GlassModal>
    </div>
  );
};
