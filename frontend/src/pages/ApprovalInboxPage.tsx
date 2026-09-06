import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { NeoGlassCard } from '../components/ui/NeoGlassCard';
import { NeoGlassButton } from '../components/ui/NeoGlassButton';
import { StatusBadge } from '../components/ui/StatusBadge';
import { GlassModal } from '../components/ui/GlassModal';
import { QuotationApproval } from '../types';
import { commercialGovernanceApi } from '../services/commercialGovernanceApi';
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Clock,
  RefreshCw,
  Search,
  Check,
  X,
  UserCheck,
  FileText,
} from 'lucide-react';

export const ApprovalInboxPage: React.FC = () => {
  const [approvals, setApprovals] = useState<QuotationApproval[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [filterStatus, setFilterStatus] = useState<'ALL' | 'PENDING' | 'APPROVED' | 'REJECTED'>('PENDING');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Decision Modal State
  const [selectedApproval, setSelectedApproval] = useState<QuotationApproval | null>(null);
  const [decisionType, setDecisionType] = useState<'APPROVED' | 'REJECTED'>('APPROVED');
  const [decisionNote, setDecisionNote] = useState<string>('');
  const [decisionLoading, setDecisionLoading] = useState<boolean>(false);

  const showToast = (type: 'success' | 'error', message: string) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 5000);
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await commercialGovernanceApi.getApprovalInbox(
        filterStatus === 'ALL' ? undefined : filterStatus
      );
      setApprovals(data);
    } catch (err: any) {
      console.error('Failed to load approval inbox:', err);
      showToast('error', err?.message || 'Failed to fetch approval requests.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filterStatus]);

  const handleOpenDecisionModal = (appr: QuotationApproval, decision: 'APPROVED' | 'REJECTED') => {
    setSelectedApproval(appr);
    setDecisionType(decision);
    setDecisionNote(decision === 'APPROVED' ? 'Approved as per enterprise commercial guidelines.' : 'Rejected due to excessive discount margin erosion.');
  };

  const handleSubmitDecision = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedApproval) return;

    setDecisionLoading(true);
    try {
      await commercialGovernanceApi.submitApprovalDecision(selectedApproval.quotation_id, {
        decision: decisionType,
        note: decisionNote,
      });

      showToast('success', `Quotation authorization decision set to ${decisionType}!`);
      setSelectedApproval(null);
      await loadData();
    } catch (err: any) {
      showToast('error', err?.message || 'Failed to record decision.');
    } finally {
      setDecisionLoading(false);
    }
  };

  // KPI Calculations
  const pendingCount = approvals.filter((a) => a.status === 'PENDING').length;
  const approvedCount = approvals.filter((a) => a.status === 'APPROVED').length;
  const rejectedCount = approvals.filter((a) => a.status === 'REJECTED').length;

  const filteredApprovals = approvals.filter((a) => {
    const qStr = searchQuery.toLowerCase();
    const matchSearch =
      (a.quotation_id && a.quotation_id.toLowerCase().includes(qStr)) ||
      (a.requested_by_user_name && a.requested_by_user_name.toLowerCase().includes(qStr)) ||
      (a.reasons && a.reasons.toLowerCase().includes(qStr));
    return matchSearch;
  });

  return (
    <div className="p-6 space-y-6">
      {/* Toast Notification Banner */}
      {toast && (
        <div
          className={`p-4 rounded-xl border flex items-center justify-between text-xs font-mono transition-all animate-fadeIn ${
            toast.type === 'success'
              ? 'bg-emerald-950/80 border-emerald-500/50 text-emerald-200'
              : 'bg-rose-950/80 border-rose-500/50 text-rose-200'
          }`}
        >
          <div className="flex items-center gap-2.5">
            {toast.type === 'success' ? <CheckCircle2 className="w-5 h-5 text-emerald-400" /> : <XCircle className="w-5 h-5 text-rose-400" />}
            <span className="font-semibold">{toast.message}</span>
          </div>
          <button onClick={() => setToast(null)} className="p-1 hover:bg-white/10 rounded">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 tracking-tight flex items-center gap-2.5">
            <ShieldCheck className="w-7 h-7 text-emerald-400" />
            Executive Approval Center
          </h1>
          <p className="text-sm text-slate-400 font-mono mt-1">
            Commercial governance Inbox for discount thresholds, margin violations, and segregation-of-duties authorization
          </p>
        </div>
        <div className="flex items-center gap-3">
          <NeoGlassButton variant="default" onClick={loadData}>
            <RefreshCw className="w-4 h-4 mr-1.5" />
            Refresh Inbox
          </NeoGlassButton>
        </div>
      </div>

      {/* Executive KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <NeoGlassCard className="p-4 flex items-center justify-between border-amber-500/30">
          <div>
            <div className="text-xs font-mono text-amber-400 font-semibold uppercase tracking-wider">Pending Approvals</div>
            <div className="text-2xl font-black text-slate-100 font-mono mt-1">{pendingCount}</div>
          </div>
          <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl">
            <Clock className="w-6 h-6 text-amber-400" />
          </div>
        </NeoGlassCard>

        <NeoGlassCard className="p-4 flex items-center justify-between border-emerald-500/30">
          <div>
            <div className="text-xs font-mono text-emerald-400 font-semibold uppercase tracking-wider">Approved Decisions</div>
            <div className="text-2xl font-black text-slate-100 font-mono mt-1">{approvedCount}</div>
          </div>
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl">
            <CheckCircle2 className="w-6 h-6 text-emerald-400" />
          </div>
        </NeoGlassCard>

        <NeoGlassCard className="p-4 flex items-center justify-between border-rose-500/30">
          <div>
            <div className="text-xs font-mono text-rose-400 font-semibold uppercase tracking-wider">Rejected Requests</div>
            <div className="text-2xl font-black text-slate-100 font-mono mt-1">{rejectedCount}</div>
          </div>
          <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl">
            <XCircle className="w-6 h-6 text-rose-400" />
          </div>
        </NeoGlassCard>
      </div>

      {/* Main Inbox Panel */}
      <NeoGlassCard className="p-5">
        {/* Controls */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 mb-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            {(['PENDING', 'APPROVED', 'REJECTED', 'ALL'] as const).map((st) => (
              <button
                key={st}
                onClick={() => setFilterStatus(st)}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all ${
                  filterStatus === st
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20'
                    : 'bg-slate-900/60 border border-slate-800 text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                }`}
              >
                {st === 'PENDING' ? '⏳ Pending' : st === 'APPROVED' ? '✅ Approved' : st === 'REJECTED' ? '❌ Rejected' : 'All Requests'}
              </button>
            ))}
          </div>

          <div className="relative w-full md:w-64">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search request or requester..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        {/* Table */}
        {loading ? (
          <div className="text-center py-12 text-slate-500 font-mono text-sm">Loading approval inbox...</div>
        ) : filteredApprovals.length === 0 ? (
          <div className="text-center py-12 space-y-3 font-mono">
            <UserCheck className="w-10 h-10 text-slate-600 mx-auto" />
            <p className="text-slate-400 text-sm">No approval requests found matching status "{filterStatus}".</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider">
                  <th className="py-3 px-3">Quotation Ref</th>
                  <th className="py-3 px-3">Submitted By</th>
                  <th className="py-3 px-3">Violation Trigger / Policy</th>
                  <th className="py-3 px-3">Approval Level</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3">Decision Notes</th>
                  <th className="py-3 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredApprovals.map((appr) => (
                  <tr key={appr.id} className="hover:bg-slate-800/40">
                    <td className="py-3 px-3">
                      <Link
                        to={`/quotations/${appr.quotation_id}`}
                        className="font-bold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        {appr.quotation_id.substring(0, 8)}...
                      </Link>
                    </td>

                    <td className="py-3 px-3 text-slate-200 font-medium">
                      {appr.requested_by_user_name || 'Sales Representative'}
                    </td>

                    <td className="py-3 px-3 max-w-xs">
                      <span className="text-amber-300 font-semibold block truncate" title={appr.reasons || 'Discount policy threshold exceeded'}>
                        {appr.reasons || 'Discount policy threshold exceeded'}
                      </span>
                    </td>

                    <td className="py-3 px-3 text-slate-300">
                      Level {appr.approval_level} (Executive Admin)
                    </td>

                    <td className="py-3 px-3">
                      <StatusBadge status={appr.status} size="sm" />
                    </td>

                    <td className="py-3 px-3 text-slate-400 italic">
                      {appr.decision_note || (appr.approved_by_user_name ? `By ${appr.approved_by_user_name}` : '-')}
                    </td>

                    <td className="py-3 px-3 text-right">
                      {appr.status === 'PENDING' ? (
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => handleOpenDecisionModal(appr, 'APPROVED')}
                            className="px-2.5 py-1 bg-emerald-950 border border-emerald-500/40 text-emerald-300 hover:bg-emerald-900 rounded text-[11px] font-bold flex items-center gap-1 transition-colors"
                          >
                            <Check className="w-3.5 h-3.5" /> Approve
                          </button>
                          <button
                            onClick={() => handleOpenDecisionModal(appr, 'REJECTED')}
                            className="px-2.5 py-1 bg-rose-950 border border-rose-500/40 text-rose-300 hover:bg-rose-900 rounded text-[11px] font-bold flex items-center gap-1 transition-colors"
                          >
                            <X className="w-3.5 h-3.5" /> Reject
                          </button>
                        </div>
                      ) : (
                        <span className="text-slate-500 text-[11px]">Finalized</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </NeoGlassCard>

      {/* Decision Modal */}
      {selectedApproval && (
        <GlassModal
          isOpen={!!selectedApproval}
          onClose={() => setSelectedApproval(null)}
          title={`Confirm ${decisionType === 'APPROVED' ? 'Approval Authorization' : 'Rejection'}`}
          subtitle={`Quotation ID: ${selectedApproval.quotation_id}`}
          maxWidth="md"
        >
          <form onSubmit={handleSubmitDecision} className="space-y-4 font-mono text-xs">
            <div className="p-3 rounded-lg border bg-slate-950 border-slate-800 space-y-1.5">
              <div className="text-slate-400">Trigger Reason:</div>
              <div className="text-amber-300 font-semibold">{selectedApproval.reasons || 'Discount policy threshold exceeded'}</div>
              <div className="text-slate-500 text-[11px] pt-1">
                Requested By: {selectedApproval.requested_by_user_name || 'Sales Representative'}
              </div>
            </div>

            <div>
              <label className="block text-slate-400 mb-1 font-semibold">Decision Note / Rationale</label>
              <textarea
                rows={3}
                value={decisionNote}
                onChange={(e) => setDecisionNote(e.target.value)}
                placeholder="Add commercial rationale for audit log..."
                className="w-full p-2.5 bg-slate-950 border border-slate-800 rounded text-slate-200 focus:outline-none focus:border-indigo-500 text-xs"
                required
              />
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setSelectedApproval(null)}
                className="px-4 py-2 bg-slate-800 text-slate-300 rounded hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={decisionLoading}
                className={`px-4 py-2 rounded font-bold text-white ${
                  decisionType === 'APPROVED' ? 'bg-emerald-600 hover:bg-emerald-500' : 'bg-rose-600 hover:bg-rose-500'
                }`}
              >
                {decisionLoading ? 'Submitting...' : `Confirm ${decisionType}`}
              </button>
            </div>
          </form>
        </GlassModal>
      )}
    </div>
  );
};
