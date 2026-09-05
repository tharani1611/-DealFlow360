import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { quotationApi } from '../services/quotationApi';
import { customerApi } from '../services/customerApi';
import { productApi } from '../services/productApi';
import { Quotation, Customer, Product } from '../types';
import { DataTable, Column } from '../components/ui/DataTable';
import { StatusBadge } from '../components/ui/StatusBadge';
import { BrutalButton } from '../components/ui/BrutalButton';
import { GlassInput } from '../components/ui/GlassInput';
import { GlassSelect } from '../components/ui/GlassSelect';
import { GlassModal } from '../components/ui/GlassModal';
import { LoadingState, ErrorState } from '../components/ui/EmptyState';
import { useToast } from '../context/ToastContext';
import { Plus, ExternalLink } from 'lucide-react';

export const QuotationsPage: React.FC = () => {
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [quotations, setQuotations] = useState<Quotation[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [customerId, setCustomerId] = useState('');
  const [selectedProductId, setSelectedProductId] = useState('');
  const [itemQty, setItemQty] = useState('1');
  const [notes, setNotes] = useState('');

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [quotesData, custData, prodData] = await Promise.all([
        quotationApi.getQuotations(),
        customerApi.getCustomers(),
        productApi.getProducts(),
      ]);
      setQuotations(quotesData);
      setCustomers(custData);
      setProducts(prodData);
      if (custData.length > 0 && !customerId) setCustomerId(custData[0].id);
      if (prodData.length > 0 && !selectedProductId) setSelectedProductId(prodData[0].id);
    } catch (err: any) {
      setError(err.message || 'Failed to load commercial quotations.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateQuotation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customerId || !selectedProductId) return;

    const prod = products.find((p) => p.id === selectedProductId);
    if (!prod) return;

    setIsSaving(true);
    try {
      const newQuote = await quotationApi.createQuotation({
        customer_id: customerId,
        notes: notes.trim() || undefined,
        items: [
          {
            product_id: prod.id,
            description: prod.name,
            quantity: parseInt(itemQty, 10) || 1,
            unit_price: parseFloat(prod.unit_price),
          },
        ],
      });
      showToast(`Quotation ${newQuote.quotation_number} generated!`, 'success');
      setIsModalOpen(false);
      setNotes('');
      loadData();
    } catch (err: any) {
      showToast(err.message || 'Failed to generate quotation.', 'error');
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
          <span className="text-[10px] font-mono text-slate-500 block">{new Date(r.created_at).toLocaleDateString()}</span>
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
          ${Number(r.total_amount).toLocaleString()}
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
            Commercial proposals, itemized pricing, and status state machine
          </p>
        </div>

        <BrutalButton variant="primary" icon={Plus} onClick={() => setIsModalOpen(true)}>
          New Quotation
        </BrutalButton>
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
        subtitle="Generate itemized pricing proposal for customer"
      >
        <form onSubmit={handleCreateQuotation} className="space-y-4">
          <GlassSelect
            label="Customer Account"
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
            options={customers.map((c) => ({ value: c.id, label: c.name }))}
            required
          />

          <div className="grid grid-cols-3 gap-3">
            <div className="col-span-2">
              <GlassSelect
                label="Product Item"
                value={selectedProductId}
                onChange={(e) => setSelectedProductId(e.target.value)}
                options={products.map((p) => ({
                  value: p.id,
                  label: `${p.name} ($${p.unit_price})`,
                }))}
                required
              />
            </div>
            <GlassInput
              label="Quantity"
              type="number"
              min="1"
              value={itemQty}
              onChange={(e) => setItemQty(e.target.value)}
              required
            />
          </div>

          <GlassInput
            label="Quotation Notes"
            placeholder="Special commercial terms..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />

          <div className="pt-4 flex items-center justify-end gap-3 border-t border-slate-800">
            <BrutalButton type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </BrutalButton>
            <BrutalButton type="submit" variant="primary" isLoading={isSaving}>
              Generate Quotation
            </BrutalButton>
          </div>
        </form>
      </GlassModal>
    </div>
  );
};
