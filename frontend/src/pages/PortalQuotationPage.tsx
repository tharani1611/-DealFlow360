import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { PortalQuotationDetailResponse, PortalQuotationListItemResponse, PortalUserResponse } from '../types';
import { portalApi } from '../services/portalApi';
import { LineCommentsModal } from '../components/negotiation/LineCommentsModal';
import { ChangeRequestModal } from '../components/negotiation/ChangeRequestModal';
import { CoNegotiatorSimulatorModal } from '../components/negotiation/CoNegotiatorSimulatorModal';
import { Shield, FileText, CheckCircle2, XCircle, MessageSquare, Edit3, LogOut, Calendar, Bot } from 'lucide-react';

export const PortalQuotationPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [portalUser, setPortalUser] = useState<PortalUserResponse | null>(null);
  const [quotationList, setQuotationList] = useState<PortalQuotationListItemResponse[]>([]);
  const [activeQuotation, setActiveQuotation] = useState<PortalQuotationDetailResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Modals
  const [selectedItemForComments, setSelectedItemForComments] = useState<{ id: string; name: string } | null>(null);
  const [showChangeRequestModal, setShowChangeRequestModal] = useState<boolean>(false);
  const [showCoNegotiatorModal, setShowCoNegotiatorModal] = useState<boolean>(false);
  const [selectedItemForCR, setSelectedItemForCR] = useState<{ id: string; name: string } | null>(null);
  const [actionReason, setActionReason] = useState<string>('');
  const [submittingAction, setSubmittingAction] = useState<boolean>(false);

  useEffect(() => {
    initPortal();
  }, [id]);

  const initPortal = async () => {
    try {
      setLoading(true);
      setError(null);

      const me = await portalApi.getMe();
      setPortalUser(me);

      const list = await portalApi.getQuotations();
      setQuotationList(list);

      const targetId = id || (list.length > 0 ? list[0].id : null);
      if (targetId) {
        const detail = await portalApi.getQuotationDetail(targetId);
        setActiveQuotation(detail);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load customer portal data');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectQuotation = async (qId: string) => {
    try {
      setLoading(true);
      setError(null);
      navigate(`/portal/quotations/${qId}`);
      const detail = await portalApi.getQuotationDetail(qId);
      setActiveQuotation(detail);
    } catch (err: any) {
      setError(err.message || 'Failed to load quotation details');
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = async () => {
    if (!activeQuotation) return;
    try {
      setSubmittingAction(true);
      await portalApi.acceptQuotation(activeQuotation.id, actionReason || 'Accepted via portal');
      setActionReason('');
      await initPortal();
    } catch (err: any) {
      setError(err.message || 'Failed to accept quotation');
    } finally {
      setSubmittingAction(false);
    }
  };

  const handleReject = async () => {
    if (!activeQuotation) return;
    try {
      setSubmittingAction(true);
      await portalApi.rejectQuotation(activeQuotation.id, actionReason || 'Rejected via portal');
      setActionReason('');
      await initPortal();
    } catch (err: any) {
      setError(err.message || 'Failed to reject quotation');
    } finally {
      setSubmittingAction(false);
    }
  };

  const handleLogout = () => {
    portalApi.logout();
    navigate('/portal/login');
  };

  if (loading && !activeQuotation) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-slate-400 text-sm">Loading Customer Quotation Portal...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Portal Navigation Header */}
      <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur-xl px-6 py-4 flex items-center justify-between sticky top-0 z-40">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
            <Shield className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white leading-tight">Customer Quotation Portal</h1>
            <p className="text-xs text-slate-400">
              {portalUser ? `${portalUser.full_name} (${portalUser.email})` : 'Portal Access'}
            </p>
          </div>
        </div>

        <button
          onClick={handleLogout}
          className="px-3.5 py-2 text-xs font-medium text-slate-400 hover:text-white bg-slate-800/80 hover:bg-slate-800 border border-slate-700 rounded-xl flex items-center gap-2 transition"
        >
          <LogOut className="w-4 h-4" /> Sign Out
        </button>
      </header>

      {/* Main Content Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Quotation Selection Sidebar */}
        <aside className="w-80 border-r border-slate-800 bg-slate-900/40 p-4 space-y-3 overflow-y-auto hidden md:block">
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-2">
            Your Proposals ({quotationList.length})
          </h2>
          {quotationList.map((item) => (
            <button
              key={item.id}
              onClick={() => handleSelectQuotation(item.id)}
              className={`w-full text-left p-3.5 rounded-xl border transition flex flex-col gap-1.5 ${
                activeQuotation?.id === item.id
                  ? 'bg-indigo-600/15 border-indigo-500/50 shadow-lg shadow-indigo-600/10'
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-bold text-white">{item.quotation_number}</span>
                <span
                  className={`text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase ${
                    item.status === 'accepted'
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      : item.status === 'rejected'
                      ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                      : 'bg-sky-500/20 text-sky-300 border border-sky-500/30'
                  }`}
                >
                  {item.status}
                </span>
              </div>
              <div className="text-xs text-slate-400 flex items-center justify-between">
                <span>Total: ₹{parseFloat(item.total_amount).toLocaleString()}</span>
                <span>{new Date(item.created_at).toLocaleDateString()}</span>
              </div>
            </button>
          ))}
        </aside>

        {/* Right Active Quotation Detail Workspace */}
        <main className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-300 text-sm">
              {error}
            </div>
          )}

          {activeQuotation ? (
            <div className="max-w-4xl mx-auto space-y-6">
              {/* Proposal Header Banner */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
                  <div>
                    <div className="flex items-center gap-3">
                      <h2 className="text-2xl font-bold text-white">{activeQuotation.quotation_number}</h2>
                      <span
                        className={`text-xs font-semibold px-3 py-1 rounded-full uppercase ${
                          activeQuotation.status === 'accepted'
                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                            : activeQuotation.status === 'rejected'
                            ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                            : 'bg-sky-500/20 text-sky-300 border border-sky-500/30'
                        }`}
                      >
                        {activeQuotation.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">
                      Prepared for <strong className="text-slate-200">{activeQuotation.customer_name || 'Valued Customer'}</strong>
                    </p>
                  </div>

                  <div className="text-right">
                    <div className="text-2xl font-black text-emerald-400">
                      ₹{parseFloat(activeQuotation.total_amount).toLocaleString()} {activeQuotation.currency}
                    </div>
                    <div className="text-xs text-slate-400 mt-0.5">
                      Subtotal: ₹{parseFloat(activeQuotation.subtotal).toLocaleString()} | Tax: ₹{parseFloat(activeQuotation.tax_amount).toLocaleString()}
                    </div>
                  </div>
                </div>

                {/* Metadata row */}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs text-slate-400 pt-1">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-slate-500" />
                    <span>Issue Date: {new Date(activeQuotation.issue_date || activeQuotation.created_at).toLocaleDateString()}</span>
                  </div>
                  {activeQuotation.expiration_date && (
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-amber-400" />
                      <span>Valid Until: {new Date(activeQuotation.expiration_date).toLocaleDateString()}</span>
                    </div>
                  )}
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-slate-500" />
                    <span>Items Count: {activeQuotation.items.length}</span>
                  </div>
                </div>

                {activeQuotation.notes && (
                  <div className="bg-slate-800/50 p-3.5 rounded-xl border border-slate-700/50 text-xs text-slate-300">
                    <span className="font-semibold text-slate-200">Commercial Notes: </span>
                    {activeQuotation.notes}
                  </div>
                )}
              </div>

              {/* Line Items Table */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
                <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-white">Line Items</h3>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setShowCoNegotiatorModal(true)}
                      className="px-3 py-1.5 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition"
                    >
                      <Bot className="w-3.5 h-3.5 text-indigo-400" /> AI Co-Negotiator Simulator
                    </button>
                    <button
                      onClick={() => {
                        setSelectedItemForCR(null);
                        setShowChangeRequestModal(true);
                      }}
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition"
                    >
                      <Edit3 className="w-3.5 h-3.5" /> Propose Adjustment
                    </button>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-850 text-slate-400 border-b border-slate-800 uppercase tracking-wider">
                      <tr>
                        <th className="p-3.5">Product / Item</th>
                        <th className="p-3.5 text-right">Quantity</th>
                        <th className="p-3.5 text-right">Unit Price</th>
                        <th className="p-3.5 text-right">Discount</th>
                        <th className="p-3.5 text-right">Total</th>
                        <th className="p-3.5 text-center">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-slate-200">
                      {activeQuotation.items.map((item) => (
                        <tr key={item.id} className="hover:bg-slate-850/50 transition">
                          <td className="p-3.5">
                            <div className="font-semibold text-white">{item.product_name || 'Line Item'}</div>
                            {item.sku && <div className="text-[11px] text-slate-400">SKU: {item.sku}</div>}
                          </td>
                          <td className="p-3.5 text-right font-medium">{item.quantity}</td>
                          <td className="p-3.5 text-right">₹{parseFloat(item.unit_price).toFixed(2)}</td>
                          <td className="p-3.5 text-right text-emerald-400">
                            {parseFloat(item.discount_percent as string) > 0 ? `₹${item.discount_percent}%` : '-'}
                          </td>
                          <td className="p-3.5 text-right font-bold text-white">₹{parseFloat(item.line_total).toFixed(2)}</td>
                          <td className="p-3.5 text-center">
                            <button
                              onClick={() => setSelectedItemForComments({ id: item.id, name: item.product_name || 'Line Item' })}
                              className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-md text-[11px] font-medium flex items-center gap-1 mx-auto transition"
                            >
                              <MessageSquare className="w-3 h-3 text-indigo-400" /> Discuss
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Action Controls for Customer */}
              {activeQuotation.status === 'sent' && (
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
                  <h3 className="text-sm font-semibold text-white">Commercial Decision</h3>

                  <div>
                    <label className="block text-xs text-slate-400 mb-1">Optional Note / Feedback</label>
                    <input
                      type="text"
                      value={actionReason}
                      onChange={(e) => setActionReason(e.target.value)}
                      placeholder="Add comments regarding your decision..."
                      className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  <div className="flex gap-4">
                    <button
                      onClick={handleAccept}
                      disabled={submittingAction}
                      className="flex-1 py-3 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold text-sm rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-emerald-600/20 transition"
                    >
                      <CheckCircle2 className="w-5 h-5" /> Accept Proposal
                    </button>
                    <button
                      onClick={handleReject}
                      disabled={submittingAction}
                      className="flex-1 py-3 bg-rose-600/80 hover:bg-rose-600 disabled:opacity-50 text-white font-semibold text-sm rounded-xl flex items-center justify-center gap-2 transition"
                    >
                      <XCircle className="w-5 h-5" /> Reject Proposal
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-20 text-slate-400">Select a quotation from the left panel</div>
          )}
        </main>
      </div>

      {/* Modals */}
      {selectedItemForComments && (
        <LineCommentsModal
          quotationId={activeQuotation!.id}
          quotationItemId={selectedItemForComments.id}
          itemName={selectedItemForComments.name}
          isPortal={true}
          onClose={() => setSelectedItemForComments(null)}
        />
      )}

      {showChangeRequestModal && (
        <ChangeRequestModal
          quotationId={activeQuotation!.id}
          quotationItemId={selectedItemForCR?.id}
          itemName={selectedItemForCR?.name}
          isPortal={true}
          onClose={() => setShowChangeRequestModal(false)}
          onSuccess={() => initPortal()}
        />
      )}

      {showCoNegotiatorModal && activeQuotation && (
        <CoNegotiatorSimulatorModal
          quotationId={activeQuotation.id}
          quotationNumber={activeQuotation.quotation_number}
          initialDiscountPercent={
            parseFloat(activeQuotation.discount_amount || '0') > 0 && parseFloat(activeQuotation.subtotal || '0') > 0
              ? (parseFloat(activeQuotation.discount_amount) / parseFloat(activeQuotation.subtotal)) * 100
              : 10.0
          }
          onClose={() => setShowCoNegotiatorModal(false)}
          onSuccess={() => initPortal()}
        />
      )}
    </div>
  );
};
