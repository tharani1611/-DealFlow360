import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { quotationApi } from '../services/quotationApi';
import { commercialGovernanceApi } from '../services/commercialGovernanceApi';
import { inventoryApi } from '../services/inventoryApi';
import {
  Quotation,
  QuotationStatus,
  QuotationStateHistoryItem,
  CommercialGovernanceSummaryResponse,
  QuotationAvailabilitySummary,
  SmartAllocationSummary,
  BillingClassification,
  DeliveryPromise,
  Warehouse,
} from '../types';
import { StockAvailabilityBadge } from '../components/inventory/StockAvailabilityBadge';
import { ManualOverrideModal } from '../components/inventory/ManualOverrideModal';
import { HybridBillingSummaryCard } from '../components/inventory/HybridBillingSummaryCard';
import { GlassCard } from '../components/ui/GlassCard';
import { StatusBadge } from '../components/ui/StatusBadge';
import { BrutalButton } from '../components/ui/BrutalButton';
import { GlassModal } from '../components/ui/GlassModal';
import { GlassInput } from '../components/ui/GlassInput';
import { LoadingState, ErrorState } from '../components/ui/EmptyState';
import { useToast } from '../context/ToastContext';
import { ApprovalAuditTimeline } from '../components/approvals/ApprovalAuditTimeline';
import { LineCommentsModal } from '../components/negotiation/LineCommentsModal';
import { ChangeRequestModal } from '../components/negotiation/ChangeRequestModal';
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Ban,
  Send,
  History,
  DollarSign,
  RotateCcw,
  Zap,
  Clock,
  ShieldCheck,
  MessageSquare,
  Edit3,
  PackageCheck,
  Settings,
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

  // Negotiation modals
  const [selectedItemForComments, setSelectedItemForComments] = useState<{ id: string; name: string } | null>(null);
  const [showCounterDiscountModal, setShowCounterDiscountModal] = useState<boolean>(false);

  // Transition modal state
  const [isTransitionModalOpen, setIsTransitionModalOpen] = useState(false);
  const [targetStatus, setTargetStatus] = useState<QuotationStatus | null>(null);
  const [transitionReason, setTransitionReason] = useState('');

  // Inventory & Fulfillment telemetry (Phases 36–45)
  const [availability, setAvailability] = useState<QuotationAvailabilitySummary | null>(null);
  const [allocation, setAllocation] = useState<SmartAllocationSummary | null>(null);
  const [hybridBilling, setHybridBilling] = useState<BillingClassification | null>(null);
  const [deliveryPromise, setDeliveryPromise] = useState<DeliveryPromise | null>(null);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [showOverrideModal, setShowOverrideModal] = useState<boolean>(false);

  const loadQuotationData = async () => {
    if (!id) return;
    setIsLoading(true);
    setError(null);
    try {
      const [qData, histData, govData, availData, allocData, billData, promiseData, whList] = await Promise.all([
        quotationApi.getQuotation(id),
        quotationApi.getQuotationHistory(id),
        commercialGovernanceApi.getQuotationGovernanceSummary(id).catch(() => null),
        inventoryApi.getQuotationAvailability(id).catch(() => null),
        inventoryApi.getSmartAllocation(id).catch(() => null),
        inventoryApi.getQuotationHybridBilling(id).catch(() => null),
        inventoryApi.getQuotationDeliveryPromise(id).catch(() => null),
        inventoryApi.getWarehouses().catch(() => []),
      ]);
      setQuotation(qData);
      setHistory(histData);
      setGovernanceSummary(govData);
      setAvailability(availData);
      setAllocation(allocData);
      setHybridBilling(billData);
      setDeliveryPromise(promiseData);
      setWarehouses(whList);
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve quotation details.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReserveStock = async () => {
    if (!id) return;
    setIsUpdating(true);
    try {
      await inventoryApi.reserveStockForQuotation(id);
      showToast('Inventory stock successfully reserved for quotation.', 'success');
      loadQuotationData();
    } catch (err: any) {
      showToast(err.message || 'Failed to reserve stock.', 'error');
    } finally {
      setIsUpdating(false);
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

  const approvalStatus = governanceSummary?.approval?.status || 'NOT_REQUIRED';
  const isApprovalPending = approvalStatus === 'PENDING';
  const isApprovalBlocked = ['PENDING', 'REJECTED', 'INVALIDATED'].includes(approvalStatus);

  const renderWorkflowActions = () => {
    const status = quotation.status;

    return (
      <div className="flex items-center gap-2 flex-wrap">
        <BrutalButton
          variant="secondary"
          size="sm"
          icon={Edit3}
          onClick={() => setShowCounterDiscountModal(true)}
          isLoading={isUpdating}
        >
          Counter-Discount
        </BrutalButton>

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

      {/* Inventory Telemetry & Warehouse Fulfillment (Phases 36–44) */}
      {availability && (
        <GlassCard className="border border-slate-800 bg-slate-900/70">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
            <div className="flex items-center gap-2">
              <PackageCheck className="w-5 h-5 text-emerald-400" />
              <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-slate-100">
                Inventory Stock & Smart Warehouse Allocation (Phases 36–44)
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <BrutalButton variant="secondary" size="sm" icon={PackageCheck} onClick={handleReserveStock} isLoading={isUpdating}>
                Reserve Stock
              </BrutalButton>
              <BrutalButton variant="ghost" size="sm" icon={Settings} onClick={() => setShowOverrideModal(true)}>
                Manual Override
              </BrutalButton>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            {/* Availability */}
            <div className="p-3 bg-slate-950/80 border border-slate-800/80 rounded-lg space-y-1.5">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">Stock Availability</span>
              <StockAvailabilityBadge
                status={availability.overall_status}
                totalAvailable={availability.total_available}
                totalRequested={availability.total_requested}
                totalShortfall={availability.total_shortfall}
              />
            </div>

            {/* Smart Allocation */}
            <div className="p-3 bg-slate-950/80 border border-slate-800/80 rounded-lg space-y-1.5">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">Warehouse Allocation</span>
              <div className="flex items-center gap-2 font-mono text-xs">
                <StatusBadge
                  status={allocation?.is_fully_allocated ? 'FULLY ALLOCATED' : 'PARTIAL ALLOCATION'}
                  variant={allocation?.is_fully_allocated ? 'success' : 'warning'}
                  size="sm"
                />
                <span className="text-slate-300 font-bold">
                  {allocation?.total_allocated || 0}/{availability.total_requested} Allocated
                </span>
              </div>
            </div>

            {/* Delivery Promise */}
            <div className="p-3 bg-slate-950/80 border border-slate-800/80 rounded-lg space-y-1.5">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">Delivery Promise Tracking</span>
              {deliveryPromise ? (
                <div className="flex items-center gap-2">
                  <StatusBadge
                    status={deliveryPromise.status}
                    variant={
                      deliveryPromise.status === 'ON_TIME' || deliveryPromise.status === 'MET'
                        ? 'success'
                        : deliveryPromise.status === 'AT_RISK'
                        ? 'warning'
                        : 'danger'
                    }
                    size="sm"
                  />
                  <span className="text-xs font-mono text-slate-300">
                    Promised: {deliveryPromise.promised_date}
                    {deliveryPromise.slippage_days > 0 && (
                      <span className="text-rose-400 font-bold ml-1">(+{deliveryPromise.slippage_days}d delay)</span>
                    )}
                  </span>
                </div>
              ) : (
                <span className="text-xs font-mono text-slate-500">Calculated on dispatch</span>
              )}
            </div>
          </div>
        </GlassCard>
      )}

      {/* Hybrid Commercial Billing Summary (Phase 45) */}
      <HybridBillingSummaryCard billing={hybridBilling} currency={quotation.currency || 'USD'} />

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
            </div>
          </div>
        </GlassCard>
      )}

      {/* Line Items Card */}
      <GlassCard title="Quotation Line Items & Discussion">
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
                <th className="text-center">Discussion</th>
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
                    </td>
                    <td className="text-right font-mono text-xs">{Number(item.quantity).toLocaleString()}</td>
                    <td className="text-right font-mono text-xs">${Number(item.unit_price).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                    <td className="text-right font-mono text-xs text-slate-400">{Number(item.discount_percent || 0).toFixed(1)}%</td>
                    <td className="text-right font-mono text-xs text-slate-400">{Number(item.tax_rate || 0).toFixed(1)}%</td>
                    <td className="text-right font-mono text-xs font-bold text-slate-100">${Number(item.line_total).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                    <td className="text-center">
                      <button
                        onClick={() => setSelectedItemForComments({ id: item.id, name: item.product_name })}
                        className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs font-medium inline-flex items-center gap-1 transition"
                      >
                        <MessageSquare className="w-3.5 h-3.5 text-indigo-400" /> Discussion
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="text-center text-slate-400 font-mono text-xs py-4">
                    No line items attached.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </GlassCard>

      {/* Approval Audit Trail Timeline (Phase 28) */}
      <GlassCard>
        <ApprovalAuditTimeline quotationId={quotation.id} />
      </GlassCard>

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
                </div>
              </div>
            ))}
          </div>
        )}
      </GlassCard>

      {/* Line Comments Modal */}
      {selectedItemForComments && (
        <LineCommentsModal
          quotationId={quotation.id}
          quotationItemId={selectedItemForComments.id}
          itemName={selectedItemForComments.name}
          isPortal={false}
          onClose={() => setSelectedItemForComments(null)}
        />
      )}

      {/* Counter-Discount Modal */}
      {showCounterDiscountModal && (
        <ChangeRequestModal
          quotationId={quotation.id}
          isPortal={false}
          onClose={() => setShowCounterDiscountModal(false)}
          onSuccess={() => loadQuotationData()}
        />
      )}

      {/* State Transition Modal */}
      <GlassModal
        isOpen={isTransitionModalOpen}
        onClose={() => setIsTransitionModalOpen(false)}
        title={`Transition Status to ${targetStatus?.toUpperCase()}`}
        subtitle="State machine lifecycle governance action"
      >
        <form onSubmit={handleExecuteTransition} className="space-y-4">
          <p className="text-xs font-mono text-slate-300">
            Transitioning quotation <strong>{quotation.quotation_number}</strong> to{' '}
            <span className="text-cyan-400">{targetStatus?.toUpperCase()}</span>.
          </p>
          <GlassInput
            label="Audit Notes / Reason (Optional)"
            placeholder="Enter reason for status transition..."
            value={transitionReason}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTransitionReason(e.target.value)}
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

      {/* Manual Fulfillment Override Modal */}
      {showOverrideModal && (
        <ManualOverrideModal
          isOpen={showOverrideModal}
          onClose={() => setShowOverrideModal(false)}
          quotationId={quotation.id}
          quotationItems={quotation.items || []}
          warehouses={warehouses}
          onOverrideComplete={() => loadQuotationData()}
        />
      )}
    </div>
  );
};
