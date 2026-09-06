import React, { useState, useEffect } from 'react';
import { NeoGlassCard } from '../components/ui/NeoGlassCard';
import { NeoGlassButton } from '../components/ui/NeoGlassButton';
import { StatusBadge } from '../components/ui/StatusBadge';
import { Invoice, Customer } from '../types';
import { billingApi } from '../services/billingApi';
import { customerApi } from '../services/customerApi';
import { gstApi, GSTTaxCalculationResponse } from '../services/gstApi';
import { RecordPaymentModal } from '../components/billing/RecordPaymentModal';
import { CreditNoteModal } from '../components/billing/CreditNoteModal';
import { GstTaxBreakdownCard } from '../components/gst/GstTaxBreakdownCard';
import { EInvoiceEWayBillModal } from '../components/gst/EInvoiceEWayBillModal';
import {
  FileText,
  CreditCard,
  Ban,
  CheckCircle,
  RefreshCw,
  Eye,
  FileCode,
} from 'lucide-react';

export const InvoicesPage: React.FC = () => {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  // Active Modals
  const [paymentInvoice, setPaymentInvoice] = useState<Invoice | null>(null);
  const [creditNoteInvoice, setCreditNoteInvoice] = useState<Invoice | null>(null);
  const [detailInvoice, setDetailInvoice] = useState<Invoice | null>(null);
  const [complianceModalInvoice, setComplianceModalInvoice] = useState<Invoice | null>(null);
  const [gstBreakdown, setGstBreakdown] = useState<GSTTaxCalculationResponse | null>(null);
  const [gstLoading, setGstLoading] = useState<boolean>(false);

  const handleOpenDetail = async (inv: Invoice) => {
    setDetailInvoice(inv);
    setGstLoading(true);
    try {
      const cust = customers.find((c) => c.id === inv.customer_id);
      const buyerState = cust?.state || 'Maharashtra';
      const itemsPayload = (inv.items || []).map((item) => ({
        description: item.description,
        hsn_sac_code: (item as any).hsn_sac_code || '8471',
        quantity: Number(item.quantity),
        unit_price: Number(item.unit_price),
        discount_amount: Number(item.discount_amount),
        line_subtotal: Number(item.line_subtotal),
        gst_rate: (item as any).gst_rate || 18,
      }));

      const res = await gstApi.calculateTax({
        seller_state: 'Karnataka',
        buyer_state: buyerState,
        items: itemsPayload.length > 0 ? itemsPayload : [{ description: 'General Item', quantity: 1, unit_price: Number(inv.subtotal), gst_rate: 18 }],
      });
      setGstBreakdown(res);
    } catch (err) {
      console.error('Failed to calculate GST breakdown:', err);
      setGstBreakdown(null);
    } finally {
      setGstLoading(false);
    }
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const [invList, custList] = await Promise.all([
        billingApi.listInvoices(),
        customerApi.getCustomers(),
      ]);
      setInvoices(invList);
      setCustomers(custList);
    } catch (err) {
      console.error('Failed to load invoices:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleIssue = async (invoiceId: string) => {
    try {
      await billingApi.issueInvoice(invoiceId);
      await loadData();
    } catch (err: any) {
      alert(err?.message || 'Failed to issue invoice');
    }
  };

  const handleVoid = async (invoiceId: string) => {
    if (!window.confirm('Are you sure you want to void this invoice?')) return;
    try {
      await billingApi.voidInvoice(invoiceId);
      await loadData();
    } catch (err: any) {
      alert(err?.message || 'Failed to void invoice');
    }
  };

  const filteredInvoices = invoices.filter((inv) => {
    if (statusFilter === 'ALL') return true;
    return inv.status === statusFilter;
  });

  const totalInvoiced = invoices
    .filter((i) => i.status !== 'VOID')
    .reduce((sum, i) => sum + Number(i.total), 0);

  const totalCollected = invoices
    .filter((i) => i.status !== 'VOID')
    .reduce((sum, i) => sum + Number(i.amount_paid), 0);

  const totalOutstanding = invoices
    .filter((i) => i.status !== 'VOID')
    .reduce((sum, i) => sum + Number(i.amount_due), 0);

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 tracking-tight flex items-center gap-2">
            <FileText className="w-7 h-7 text-indigo-400" />
            Invoices & Revenue Ledger
          </h1>
          <p className="text-sm text-slate-400 font-mono mt-1">
            Phase 46–47 deterministic invoice generation, payment recording, and balance tracking
          </p>
        </div>
        <div className="flex items-center gap-3">
          <NeoGlassButton variant="default" onClick={loadData}>
            <RefreshCw className="w-4 h-4 mr-1.5" />
            Refresh
          </NeoGlassButton>
        </div>
      </div>

      {/* Metrics Header */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <NeoGlassCard className="p-4">
          <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">Total Revenue Invoiced</div>
          <div className="text-2xl font-black font-mono text-slate-100 mt-1">
            ${totalInvoiced.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </NeoGlassCard>
        <NeoGlassCard className="p-4">
          <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">Payments Collected</div>
          <div className="text-2xl font-black font-mono text-emerald-400 mt-1">
            ${totalCollected.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </NeoGlassCard>
        <NeoGlassCard className="p-4">
          <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">Outstanding Balance Due</div>
          <div className="text-2xl font-black font-mono text-amber-400 mt-1">
            ${totalOutstanding.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </NeoGlassCard>
      </div>

      {/* Main Content Card */}
      <NeoGlassCard className="p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 mb-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-slate-100 font-mono uppercase tracking-wider">
              Issued Invoices
            </h2>
            <span className="text-xs font-mono text-slate-400">({filteredInvoices.length})</span>
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-2 overflow-x-auto">
            {['ALL', 'DRAFT', 'ISSUED', 'PARTIALLY_PAID', 'PAID', 'VOID'].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${
                  statusFilter === st
                    ? 'bg-indigo-600 text-white font-bold'
                    : 'bg-slate-900 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12 text-slate-500 font-mono text-sm">Loading invoices...</div>
        ) : filteredInvoices.length === 0 ? (
          <div className="text-center py-12 text-slate-500 font-mono text-sm">
            No invoices found matching status filter '{statusFilter}'.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider">
                  <th className="py-3 px-3">Invoice #</th>
                  <th className="py-3 px-3">Customer</th>
                  <th className="py-3 px-3">Date</th>
                  <th className="py-3 px-3">Due Date</th>
                  <th className="py-3 px-3">Total (₹)</th>
                  <th className="py-3 px-3">Paid (₹)</th>
                  <th className="py-3 px-3">Balance Due (₹)</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredInvoices.map((inv) => {
                  const cust = customers.find((c) => c.id === inv.customer_id);
                  return (
                    <tr key={inv.id} className="hover:bg-slate-800/40">
                      <td className="py-3 px-3 font-bold text-indigo-400">{inv.invoice_number}</td>
                      <td className="py-3 px-3 text-slate-200">{cust ? cust.name : inv.customer_id.substring(0, 8)}</td>
                      <td className="py-3 px-3 text-slate-400">{inv.invoice_date}</td>
                      <td className="py-3 px-3 text-slate-400">{inv.due_date}</td>
                      <td className="py-3 px-3 font-bold text-slate-100">₹{Number(inv.total).toFixed(2)}</td>
                      <td className="py-3 px-3 font-bold text-emerald-400">₹{Number(inv.amount_paid).toFixed(2)}</td>
                      <td className="py-3 px-3 font-bold text-amber-400">₹{Number(inv.amount_due).toFixed(2)}</td>
                      <td className="py-3 px-3">
                        <StatusBadge status={inv.status} size="sm" />
                      </td>
                      <td className="py-3 px-3 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => handleOpenDetail(inv)}
                            className="p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded"
                            title="View Invoice Details"
                          >
                            <Eye className="w-4 h-4" />
                          </button>

                          {inv.status === 'DRAFT' && (
                            <button
                              onClick={() => handleIssue(inv.id)}
                              className="px-2 py-1 bg-emerald-950 border border-emerald-500/30 text-emerald-300 hover:bg-emerald-900 rounded text-[11px] font-semibold flex items-center gap-1"
                              title="Issue Invoice"
                            >
                              <CheckCircle className="w-3 h-3" /> Issue
                            </button>
                          )}

                          {(inv.status === 'ISSUED' || inv.status === 'PARTIALLY_PAID') && Number(inv.amount_due) > 0 && (
                            <button
                              onClick={() => setPaymentInvoice(inv)}
                              className="px-2 py-1 bg-indigo-950 border border-indigo-500/30 text-indigo-300 hover:bg-indigo-900 rounded text-[11px] font-semibold flex items-center gap-1"
                              title="Record Payment"
                            >
                              <CreditCard className="w-3 h-3" /> Pay
                            </button>
                          )}

                          {inv.status !== 'VOID' && inv.status !== 'DRAFT' && (
                            <button
                              onClick={() => setCreditNoteInvoice(inv)}
                              className="px-2 py-1 bg-amber-950 border border-amber-500/30 text-amber-300 hover:bg-amber-900 rounded text-[11px] font-semibold"
                              title="Issue Credit Note"
                            >
                              Credit
                            </button>
                          )}

                          {inv.status === 'DRAFT' && (
                            <button
                              onClick={() => handleVoid(inv.id)}
                              className="p-1 text-slate-500 hover:text-rose-400 hover:bg-slate-800 rounded"
                              title="Void Invoice"
                            >
                              <Ban className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </NeoGlassCard>

      {/* Record Payment Modal */}
      {paymentInvoice && (
        <RecordPaymentModal
          isOpen={!!paymentInvoice}
          onClose={() => setPaymentInvoice(null)}
          invoice={paymentInvoice}
          onSuccess={loadData}
        />
      )}

      {/* Credit Note Modal */}
      {creditNoteInvoice && (
        <CreditNoteModal
          isOpen={!!creditNoteInvoice}
          onClose={() => setCreditNoteInvoice(null)}
          invoice={creditNoteInvoice}
          onSuccess={loadData}
        />
      )}

      {/* Invoice Detail Drawer/Modal */}
      {detailInvoice && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl p-6 max-w-2xl w-full space-y-4 font-mono">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-lg font-bold text-slate-100">{detailInvoice.invoice_number}</h3>
                <p className="text-xs text-slate-400">Date: {detailInvoice.invoice_date} | Due: {detailInvoice.due_date}</p>
              </div>
              <button
                onClick={() => setDetailInvoice(null)}
                className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs"
              >
                Close
              </button>
            </div>

            <div className="space-y-2">
              <h4 className="text-xs font-bold text-indigo-400 uppercase">Line Items</h4>
              <div className="border border-slate-800 rounded-lg overflow-hidden">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-950 text-slate-400">
                    <tr>
                      <th className="p-2">Description</th>
                      <th className="p-2">Type</th>
                      <th className="p-2 text-center">Qty</th>
                      <th className="p-2 text-right">Price</th>
                      <th className="p-2 text-right">Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {(detailInvoice.items || []).map((item) => (
                      <tr key={item.id}>
                        <td className="p-2 text-slate-200">{item.description}</td>
                        <td className="p-2 text-indigo-400">{item.billing_type}</td>
                        <td className="p-2 text-center">{item.quantity}</td>
                        <td className="p-2 text-right">₹{Number(item.unit_price).toFixed(2)}</td>
                        <td className="p-2 text-right font-bold text-slate-100">₹{Number(item.line_total).toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs space-y-1">
              <div className="flex justify-between text-slate-400">
                <span>Subtotal:</span>
                <span>₹{Number(detailInvoice.subtotal).toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Discount Total:</span>
                <span>-₹{Number(detailInvoice.discount_total).toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Tax Total:</span>
                <span>+₹{Number(detailInvoice.tax_total).toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-slate-100 font-bold border-t border-slate-800 pt-1 text-sm">
                <span>Grand Total:</span>
                <span>₹{Number(detailInvoice.total).toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-amber-400 font-bold text-sm border-t border-slate-800 pt-1">
                <span>Remaining Balance Due:</span>
                <span>₹{Number(detailInvoice.amount_due).toFixed(2)}</span>
              </div>
            </div>

            <GstTaxBreakdownCard gstData={gstBreakdown} loading={gstLoading} />

            <div className="flex items-center justify-between pt-2 border-t border-slate-800">
              <button
                onClick={() => setComplianceModalInvoice(detailInvoice)}
                className="px-3.5 py-2 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 rounded-xl text-xs font-bold flex items-center gap-2 transition"
              >
                <FileCode className="w-4 h-4 text-indigo-400" />
                🇮🇳 Generate E-Invoice & E-Way Bill JSON Vault
              </button>
              <button
                onClick={() => setDetailInvoice(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Compliance E-Invoice & E-Way Bill Modal */}
      {complianceModalInvoice && (
        <EInvoiceEWayBillModal
          invoiceId={complianceModalInvoice.id}
          invoiceNumber={complianceModalInvoice.invoice_number}
          customerName={customers.find((c) => c.id === complianceModalInvoice.customer_id)?.name || 'Valued Customer'}
          onClose={() => setComplianceModalInvoice(null)}
        />
      )}
    </div>
  );
};
