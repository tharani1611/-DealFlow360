import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { quotationApi } from '../services/quotationApi';
import { customerApi } from '../services/customerApi';
import { productApi } from '../services/productApi';
import { contactApi } from '../services/contactApi';
import { dealApi } from '../services/dealApi';
import { Quotation, Customer, Product, Contact, Deal, QuotationItemCreate } from '../types';
import { DataTable, Column } from '../components/ui/DataTable';
import { StatusBadge } from '../components/ui/StatusBadge';
import { BrutalButton } from '../components/ui/BrutalButton';
import { GlassInput } from '../components/ui/GlassInput';
import { GlassSelect } from '../components/ui/GlassSelect';
import { GlassModal } from '../components/ui/GlassModal';
import { LoadingState, ErrorState } from '../components/ui/EmptyState';
import { useToast } from '../context/ToastContext';
import { Plus, ExternalLink, Trash2, FileText } from 'lucide-react';

interface DraftItem {
  product_id: string;
  quantity: string;
  unit_price: string;
  description: string;
}

export const QuotationsPage: React.FC = () => {
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [statusFilter, setStatusFilter] = useState<string>('');
  const [quotations, setQuotations] = useState<Quotation[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [deals, setDeals] = useState<Deal[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [customerId, setCustomerId] = useState('');
  const [contactId, setContactId] = useState('');
  const [dealId, setDealId] = useState('');
  const [title, setTitle] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [validUntil, setValidUntil] = useState('');
  const [notes, setNotes] = useState('');
  const [terms, setTerms] = useState('');

  // Line items
  const [draftItems, setDraftItems] = useState<DraftItem[]>([]);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [quotesData, custData, prodData] = await Promise.all([
        quotationApi.getQuotations(statusFilter ? { status: statusFilter } : undefined),
        customerApi.getCustomers(),
        productApi.getProducts(),
      ]);
      setQuotations(quotesData);
      setCustomers(custData);
      setProducts(prodData);
      if (custData.length > 0 && !customerId) {
        setCustomerId(custData[0].id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load commercial quotations.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  // Fetch contacts and deals when customer changes
  useEffect(() => {
    if (!customerId) {
      setContacts([]);
      setDeals([]);
      setContactId('');
      setDealId('');
      return;
    }
    const loadCustomerRelated = async () => {
      try {
        const [cData, dData] = await Promise.all([
          contactApi.getContacts({ customer_id: customerId }),
          dealApi.getDeals({ customer_id: customerId }),
        ]);
        setContacts(cData);
        setDeals(dData);
        setContactId(cData.length > 0 ? cData[0].id : '');
        setDealId(dData.length > 0 ? dData[0].id : '');
      } catch (err) {
        console.error('Failed loading contacts/deals for customer:', err);
      }
    };
    loadCustomerRelated();
  }, [customerId]);

  // Open Modal & Reset Form
  const handleOpenModal = () => {
    if (products.length > 0) {
      setDraftItems([
        {
          product_id: products[0].id,
          quantity: '1',
          unit_price: products[0].unit_price,
          description: '',
        },
      ]);
    } else {
      setDraftItems([]);
    }
    setTitle('');
    setNotes('');
    setTerms('');
    setValidUntil('');
    setIsModalOpen(true);
  };

  const handleAddItem = () => {
    if (products.length === 0) return;
    setDraftItems([
      ...draftItems,
      {
        product_id: products[0].id,
        quantity: '1',
        unit_price: products[0].unit_price,
        description: '',
      },
    ]);
  };

  const handleRemoveItem = (index: number) => {
    if (draftItems.length <= 1) return;
    setDraftItems(draftItems.filter((_, i) => i !== index));
  };

  const handleProductChange = (index: number, prodId: string) => {
    const prod = products.find((p) => p.id === prodId);
    const updated = [...draftItems];
    updated[index].product_id = prodId;
    if (prod) {
      updated[index].unit_price = prod.unit_price;
    }
    setDraftItems(updated);
  };

  const handleItemChange = (index: number, field: keyof DraftItem, val: string) => {
    const updated = [...draftItems];
    updated[index][field] = val;
    setDraftItems(updated);
  };

  const calculateSubtotal = () => {
    return draftItems.reduce((acc, item) => {
      const q = parseFloat(item.quantity) || 0;
      const p = parseFloat(item.unit_price) || 0;
      return acc + q * p;
    }, 0);
  };

  const handleCreateQuotation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customerId || draftItems.length === 0) {
      showToast('Select a customer and at least one line item.', 'error');
      return;
    }

    const itemsPayload: QuotationItemCreate[] = draftItems.map((item, idx) => ({
      product_id: item.product_id,
      quantity: parseFloat(item.quantity) || 1,
      unit_price: item.unit_price ? parseFloat(item.unit_price) : undefined,
      description: item.description.trim() || undefined,
      sequence: idx + 1,
    }));

    setIsSaving(true);
    try {
      const newQuote = await quotationApi.createQuotation({
        customer_id: customerId,
        contact_id: contactId || undefined,
        deal_id: dealId || undefined,
        title: title.trim() || undefined,
        currency: currency.toUpperCase(),
        valid_until: validUntil ? new Date(validUntil).toISOString() : undefined,
        notes: notes.trim() || undefined,
        terms: terms.trim() || undefined,
        items: itemsPayload,
      });
      showToast(`Quotation ${newQuote.quotation_number} created successfully!`, 'success');
      setIsModalOpen(false);
      loadData();
      navigate(`/quotations/${newQuote.id}`);
    } catch (err: any) {
      showToast(err.message || 'Failed to create quotation.', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const getCustomerName = (cust_id: string) => {
    const found = customers.find((c) => c.id === cust_id);
    return found ? found.name : cust_id.substring(0, 8);
  };

  const columns: Column<Quotation>[] = [
    {
      header: 'Quotation Number',
      render: (r) => (
        <div>
          <span className="font-mono font-bold text-slate-100 text-sm">{r.quotation_number}</span>
          <span className="text-[10px] font-mono text-slate-500 block">
            {r.title ? `${r.title} • ` : ''}{new Date(r.created_at).toLocaleDateString()}
          </span>
        </div>
      ),
    },
    {
      header: 'Customer Account',
      render: (r) => <span className="font-semibold text-slate-200 text-xs">{getCustomerName(r.customer_id)}</span>,
    },
    {
      header: 'Total Amount',
      render: (r) => (
        <span className="font-mono font-black text-slate-100 text-sm">
          {r.currency || 'USD'} ${Number(r.total_amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
        </span>
      ),
    },
    {
      header: 'Status',
      render: (r) => <StatusBadge status={r.status} size="sm" />,
    },
    {
      header: 'Actions',
      render: (r) => (
        <BrutalButton
          size="sm"
          variant="ghost"
          icon={ExternalLink}
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/quotations/${r.id}`);
          }}
        >
          View Details
        </BrutalButton>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 tracking-tight">Quotations Center</h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Itemized pricing proposals, multi-currency support, and price snapshotting
          </p>
        </div>

        <BrutalButton variant="primary" icon={Plus} onClick={handleOpenModal}>
          New Quotation
        </BrutalButton>
      </div>

      <div className="flex items-center gap-2 overflow-x-auto pb-2 pt-1 border-b border-slate-800">
        {[
          { label: 'All Statuses', value: '' },
          { label: 'Draft', value: 'draft' },
          { label: 'Priced', value: 'priced' },
          { label: 'Sent', value: 'sent' },
          { label: 'Accepted', value: 'accepted' },
          { label: 'Rejected', value: 'rejected' },
          { label: 'Expired', value: 'expired' },
          { label: 'Cancelled', value: 'cancelled' },
          { label: 'Converted', value: 'converted' },
        ].map((tab) => (
          <button
            key={tab.value}
            onClick={() => setStatusFilter(tab.value)}
            className={`px-3 py-1.5 rounded-md text-xs font-mono font-bold whitespace-nowrap transition ${
              statusFilter === tab.value
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 shadow-[0_0_10px_rgba(6,182,212,0.2)]'
                : 'bg-slate-900/60 text-slate-400 border border-slate-800 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <LoadingState message="Loading quotations..." />
      ) : error ? (
        <ErrorState message={error} onRetry={loadData} />
      ) : (
        <DataTable
          columns={columns}
          data={quotations}
          keyExtractor={(r) => r.id}
          emptyMessage="No commercial quotations generated."
          onRowClick={(r) => navigate(`/quotations/${r.id}`)}
        />
      )}

      {/* Create Quotation Modal */}
      <GlassModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Create Commercial Quotation"
        subtitle="Generate transactional pricing proposal with price snapshotting"
      >
        <form onSubmit={handleCreateQuotation} className="space-y-5 max-h-[75vh] overflow-y-auto pr-1">
          {/* Header section */}
          <div className="space-y-3 p-3 bg-slate-900/60 border border-slate-800 rounded-lg">
            <h3 className="text-xs font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5" /> Header Details
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <GlassSelect
                label="Customer Account *"
                value={customerId}
                onChange={(e) => setCustomerId(e.target.value)}
                options={customers.map((c) => ({ value: c.id, label: c.name }))}
                required
              />

              <GlassInput
                label="Proposal Title"
                placeholder="e.g. Q3 Enterprise CRM Expansion"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <GlassSelect
                label="Primary Contact"
                value={contactId}
                onChange={(e) => setContactId(e.target.value)}
                options={[
                  { value: '', label: '-- None --' },
                  ...contacts.map((ct) => ({ value: ct.id, label: `${ct.first_name} ${ct.last_name}` })),
                ]}
              />

              <GlassSelect
                label="Associated Deal"
                value={dealId}
                onChange={(e) => setDealId(e.target.value)}
                options={[
                  { value: '', label: '-- None --' },
                  ...deals.map((d) => ({ value: d.id, label: d.title })),
                ]}
              />

              <GlassSelect
                label="Currency"
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                options={[
                  { value: 'USD', label: 'USD ($)' },
                  { value: 'EUR', label: 'EUR (€)' },
                  { value: 'INR', label: 'INR (₹)' },
                  { value: 'GBP', label: 'GBP (£)' },
                ]}
              />
            </div>

            <GlassInput
              label="Expiration Date (Valid Until)"
              type="date"
              value={validUntil}
              onChange={(e) => setValidUntil(e.target.value)}
            />
          </div>

          {/* Line items section */}
          <div className="space-y-3 p-3 bg-slate-900/60 border border-slate-800 rounded-lg">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-wider text-cyan-400">
                Line Items ({draftItems.length})
              </h3>
              <BrutalButton type="button" size="sm" variant="ghost" icon={Plus} onClick={handleAddItem}>
                Add Item
              </BrutalButton>
            </div>

            {draftItems.map((item, idx) => (
              <div key={idx} className="p-3 bg-slate-950/80 border border-slate-800 rounded-lg space-y-3 relative">
                <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                  <span>Line #{idx + 1}</span>
                  {draftItems.length > 1 && (
                    <button
                      type="button"
                      onClick={() => handleRemoveItem(idx)}
                      className="text-rose-400 hover:text-rose-300 transition-colors p-1"
                      title="Remove Item"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="sm:col-span-2">
                    <GlassSelect
                      label="Product *"
                      value={item.product_id}
                      onChange={(e) => handleProductChange(idx, e.target.value)}
                      options={products.map((p) => ({
                        value: p.id,
                        label: `${p.name} (Catalog: $${p.unit_price})`,
                      }))}
                      required
                    />
                  </div>

                  <GlassInput
                    label="Quantity *"
                    type="number"
                    min="1"
                    step="1"
                    value={item.quantity}
                    onChange={(e) => handleItemChange(idx, 'quantity', e.target.value)}
                    required
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <GlassInput
                    label="Unit Price Override ($)"
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="Catalog price default"
                    value={item.unit_price}
                    onChange={(e) => handleItemChange(idx, 'unit_price', e.target.value)}
                  />

                  <GlassInput
                    label="Description / Notes"
                    placeholder="Custom line details..."
                    value={item.description}
                    onChange={(e) => handleItemChange(idx, 'description', e.target.value)}
                  />
                </div>

                <div className="text-right text-xs font-mono text-slate-400">
                  Line Total: <span className="text-slate-100 font-bold">${((parseFloat(item.quantity) || 0) * (parseFloat(item.unit_price) || 0)).toFixed(2)}</span>
                </div>
              </div>
            ))}

            <div className="flex justify-between items-center pt-2 text-sm font-mono text-slate-300 border-t border-slate-800">
              <span>Estimated Subtotal:</span>
              <span className="text-lg font-black text-cyan-400">
                {currency} ${calculateSubtotal().toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>
          </div>

          {/* Notes & Terms */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <GlassInput
              label="Internal Notes"
              placeholder="Internal comments..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
            <GlassInput
              label="Commercial Terms"
              placeholder="e.g. Net 30 days payment..."
              value={terms}
              onChange={(e) => setTerms(e.target.value)}
            />
          </div>

          <div className="pt-4 flex items-center justify-end gap-3 border-t border-slate-800">
            <BrutalButton type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </BrutalButton>
            <BrutalButton type="submit" variant="primary" isLoading={isSaving}>
              Create Quotation
            </BrutalButton>
          </div>
        </form>
      </GlassModal>
    </div>
  );
};

