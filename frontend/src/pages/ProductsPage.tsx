import React, { useState, useEffect, useRef } from 'react';
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
import { Plus, BarChart2, Package, Upload, X, Check } from 'lucide-react';

export const ProductsPage: React.FC = () => {
  const { showToast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

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
  const [currency] = useState('INR');
  const [description, setDescription] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);

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

  const handleDeviceFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Check size limit (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      showToast('Image file size must be less than 5MB.', 'error');
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        setImageUrl(reader.result);
        setUploadedFileName(file.name);
        showToast(`Image "${file.name}" loaded from device!`, 'success');
      }
    };
    reader.readAsDataURL(file);
  };

  const handleClearImage = () => {
    setImageUrl('');
    setUploadedFileName(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleCreateProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !sku.trim() || !unitPrice) return;

    setIsSaving(true);
    try {
      await productApi.createProduct({
        name: name.trim(),
        sku: sku.trim().toUpperCase(),
        unit_price: parseFloat(unitPrice),
        currency: currency.trim() || 'INR',
        description: description.trim() || undefined,
        image_url: imageUrl.trim() || undefined,
      });
      showToast(`Product "${name}" created!`, 'success');
      setIsModalOpen(false);
      setName('');
      setSku('');
      setUnitPrice('');
      setDescription('');
      setImageUrl('');
      setUploadedFileName(null);
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
        <div className="flex items-center gap-3">
          {r.image_url ? (
            <img
              src={r.image_url}
              alt={r.name}
              className="w-10 h-10 rounded-lg object-cover border border-slate-700/80 shrink-0 bg-slate-900 shadow-sm"
              onError={(e) => {
                (e.target as HTMLElement).style.display = 'none';
              }}
            />
          ) : (
            <div className="w-10 h-10 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center shrink-0 text-slate-500">
              <Package className="w-5 h-5" />
            </div>
          )}
          <div>
            <span className="font-extrabold text-slate-100 text-sm">{r.name}</span>
            {r.description && <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">{r.description}</p>}
          </div>
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
          ₹{Number(r.unit_price).toLocaleString()} {r.currency}
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
        subtitle="Define commercial product SKU, unit pricing, and product picture"
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
              label="Unit Price (₹)"
              type="number"
              step="0.01"
              placeholder="999.00"
              value={unitPrice}
              onChange={(e) => setUnitPrice(e.target.value)}
              required
            />
          </div>

          {/* Device Upload & Image Selection Section */}
          <div className="space-y-2.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-mono font-semibold text-slate-300">
                Product Image (Optional)
              </label>
              <span className="text-[11px] font-mono text-slate-400">Device Upload or Web Link</span>
            </div>

            {/* Upload Button + File Input */}
            <input
              type="file"
              ref={fileInputRef}
              accept="image/*"
              onChange={handleDeviceFileUpload}
              className="hidden"
            />

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="px-3 py-2 bg-indigo-950/80 border border-indigo-500/50 hover:bg-indigo-900 text-indigo-200 rounded-lg text-xs font-mono font-semibold flex items-center gap-2 transition-all shadow-sm"
              >
                <Upload className="w-4 h-4 text-indigo-400" />
                Upload Image from Device
              </button>

              <span className="text-slate-500 font-mono text-xs">or</span>

              <div className="flex-1">
                <input
                  type="text"
                  placeholder="Paste image URL (https://...)"
                  value={uploadedFileName ? `Device File: ${uploadedFileName}` : imageUrl}
                  onChange={(e) => {
                    setUploadedFileName(null);
                    setImageUrl(e.target.value);
                  }}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            {/* Live Image Preview Thumbnail */}
            {imageUrl.trim() && (
              <div className="p-3 bg-slate-950/90 border border-emerald-500/30 rounded-xl flex items-center justify-between gap-3 shadow-lg">
                <div className="flex items-center gap-3">
                  <img
                    src={imageUrl.trim()}
                    alt="Live Preview"
                    className="w-12 h-12 rounded-lg object-cover border border-emerald-500/50 shrink-0 bg-slate-900"
                    onError={(e) => {
                      (e.target as HTMLElement).style.display = 'none';
                    }}
                  />
                  <div className="text-xs font-mono">
                    <div className="font-bold text-emerald-400 flex items-center gap-1">
                      <Check className="w-3.5 h-3.5" />
                      {uploadedFileName ? 'Uploaded Device Picture' : 'Image Ready'}
                    </div>
                    <div className="text-[10px] text-slate-400 truncate max-w-xs mt-0.5">
                      {uploadedFileName || imageUrl}
                    </div>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={handleClearImage}
                  className="p-1.5 bg-slate-900 hover:bg-rose-950 text-slate-400 hover:text-rose-300 rounded-lg transition-colors"
                  title="Remove Picture"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}
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
