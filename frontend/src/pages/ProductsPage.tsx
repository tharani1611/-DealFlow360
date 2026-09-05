import React, { useState, useEffect } from 'react';
import { productApi } from '../services/productApi';
import { Product } from '../types';
import { DataTable, Column } from '../components/ui/DataTable';
import { StatusBadge } from '../components/ui/StatusBadge';
import { BrutalButton } from '../components/ui/BrutalButton';
import { GlassInput } from '../components/ui/GlassInput';
import { GlassTextarea } from '../components/ui/GlassTextarea';
import { GlassModal } from '../components/ui/GlassModal';
import { LoadingState, ErrorState } from '../components/ui/EmptyState';
import { ProductIntelligenceModal } from '../components/intelligence/ProductIntelligenceModal';
import { useToast } from '../context/ToastContext';
import { Plus, BarChart2 } from 'lucide-react';

export const ProductsPage: React.FC = () => {
  const { showToast } = useToast();

  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form & Intelligence State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedIntelProductId, setSelectedIntelProductId] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [name, setName] = useState('');
  const [sku, setSku] = useState('');
  const [unitPrice, setUnitPrice] = useState('');
  const [currency] = useState('USD');
  const [description, setDescription] = useState('');

  const loadProducts = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await productApi.getProducts();
      setProducts(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load product catalog.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, []);

  const handleCreateProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !sku.trim() || !unitPrice) return;

    setIsSaving(true);
    try {
      await productApi.createProduct({
        name: name.trim(),
        sku: sku.trim().toUpperCase(),
        unit_price: parseFloat(unitPrice),
        currency: currency.trim() || 'USD',
        description: description.trim() || undefined,
      });
      showToast(`Product "${name}" created!`, 'success');
      setIsModalOpen(false);
      setName('');
      setSku('');
      setUnitPrice('');
      setDescription('');
      loadProducts();
    } catch (err: any) {
      showToast(err.message || 'Failed to create product in catalog.', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const columns: Column<Product>[] = [
    {
      header: 'Product Name',
      render: (r) => (
        <div>
          <span className="font-extrabold text-slate-100 text-sm">{r.name}</span>
          {r.description && <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">{r.description}</p>}
        </div>
      ),
    },
    {
      header: 'SKU',
      render: (r) => <span className="font-mono text-xs font-bold text-indigo-400">{r.sku}</span>,
    },
    {
      header: 'Unit Price',
      render: (r) => (
        <span className="font-mono font-black text-slate-100 text-sm">
          ${Number(r.unit_price).toLocaleString()} {r.currency}
        </span>
      ),
    },
    {
      header: 'Status',
      render: (r) => <StatusBadge status={r.is_active ? 'active' : 'inactive'} size="sm" />,
    },
    {
      header: 'Intelligence',
      render: (r) => (
        <BrutalButton
          variant="secondary"
          size="sm"
          icon={BarChart2}
          onClick={() => setSelectedIntelProductId(r.id)}
        >
          Product 360
        </BrutalButton>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 tracking-tight">Product Catalog</h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Commercial product SKUs, pricing models, and service items
          </p>
        </div>

        <BrutalButton variant="primary" icon={Plus} onClick={() => setIsModalOpen(true)}>
          New Product SKU
        </BrutalButton>
      </div>

      {isLoading ? (
        <LoadingState message="Loading catalog inventory..." />
      ) : error ? (
        <ErrorState message={error} onRetry={loadProducts} />
      ) : (
        <DataTable
          columns={columns}
          data={products}
          keyExtractor={(r) => r.id}
          emptyMessage="No products configured in catalog."
        />
      )}

      {/* Create Product Modal */}
      <GlassModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Add Product to Catalog"
        subtitle="Define commercial product SKU and unit pricing"
      >
        <form onSubmit={handleCreateProduct} className="space-y-4">
          <GlassInput
            label="Product Name"
            placeholder="e.g. Enterprise License Tier 1"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />

          <div className="grid grid-cols-2 gap-4">
            <GlassInput
              label="SKU Code"
              placeholder="e.g. ENT-LIC-001"
              value={sku}
              onChange={(e) => setSku(e.target.value)}
              required
            />
            <GlassInput
              label="Unit Price ($)"
              type="number"
              step="0.01"
              placeholder="999.00"
              value={unitPrice}
              onChange={(e) => setUnitPrice(e.target.value)}
              required
            />
          </div>

          <GlassTextarea
            label="Description"
            placeholder="Commercial product specifications..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />

          <div className="pt-4 flex items-center justify-end gap-3 border-t border-slate-800">
            <BrutalButton type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </BrutalButton>
            <BrutalButton type="submit" variant="primary" isLoading={isSaving}>
              Save Product SKU
            </BrutalButton>
          </div>
        </form>
      </GlassModal>

      {/* Product Intelligence 360 Modal */}
      {selectedIntelProductId && (
        <ProductIntelligenceModal
          isOpen={Boolean(selectedIntelProductId)}
          onClose={() => setSelectedIntelProductId(null)}
          productId={selectedIntelProductId}
        />
      )}
    </div>
  );
};
