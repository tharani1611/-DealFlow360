import React, { useState, useEffect } from 'react';
import { GlassModal } from '../ui/GlassModal';
import { GlassInput } from '../ui/GlassInput';
import { GlassSelect } from '../ui/GlassSelect';
import { BrutalButton } from '../ui/BrutalButton';
import { customerApi } from '../../services/customerApi';
import { productApi } from '../../services/productApi';
import { dealApi } from '../../services/dealApi';
import { quotationApi } from '../../services/quotationApi';
import { Customer, Product, Deal, QuotationItemCreate, QuotationCreate, Quotation } from '../../types';
import { useToast } from '../../context/ToastContext';
import { Plus, Trash2, ShieldAlert, ArrowRight, CheckCircle2 } from 'lucide-react';

interface QuotationBuilderModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (quotation: Quotation) => void;
}

export const QuotationBuilderModal: React.FC<QuotationBuilderModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const { showToast } = useToast();
  const [step, setStep] = useState<1 | 2 | 3>(1);

  const [customers, setCustomers] = useState<Customer[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [deals, setDeals] = useState<Deal[]>([]);

  const [selectedCustomerId, setSelectedCustomerId] = useState('');
  const [selectedDealId, setSelectedDealId] = useState('');
  const [title, setTitle] = useState('');

  const [items, setItems] = useState<QuotationItemCreate[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadInitialData();
    }
  }, [isOpen]);

  const loadInitialData = async () => {
    try {
      const [custData, prodData] = await Promise.all([
        customerApi.getCustomers({ limit: 100 }),
        productApi.getProducts({ limit: 100 }),
      ]);
      setCustomers(custData);
      setProducts(prodData);
    } catch (err) {
      console.error('Failed to load builder datasets:', err);
    }
  };

  const handleCustomerChange = async (cId: string) => {
    setSelectedCustomerId(cId);
    setSelectedDealId('');
    if (cId) {
      try {
        const dealData = await dealApi.getDeals({ customer_id: cId });
        setDeals(dealData);
      } catch {
        setDeals([]);
      }
    } else {
      setDeals([]);
    }
  };

  const handleAddItem = () => {
    if (products.length === 0) return;
    const p = products[0];
    setItems([
      ...items,
      {
        product_id: p.id,
        quantity: 1,
        unit_price: Number(p.unit_price || 0),
        discount_percent: 0,
        tax_rate: 0,
        sequence: items.length + 1,
      },
    ]);
  };

  const handleItemChange = (index: number, field: keyof QuotationItemCreate, value: any) => {
    const updated = [...items];
    if (field === 'product_id') {
      const selectedProd = products.find((p) => p.id === value);
      if (selectedProd) {
        updated[index].unit_price = Number(selectedProd.unit_price || 0);
      }
    }
    (updated[index] as any)[field] = value;
    setItems(updated);
  };

  const handleRemoveItem = (index: number) => {
    setItems(items.filter((_, i) => i !== index));
  };

  // Reconciled totals
  const subtotal = items.reduce((sum, item) => sum + Number(item.unit_price || 0) * Number(item.quantity || 1), 0);
  const totalDiscount = items.reduce((sum, item) => {
    const lineSub = Number(item.unit_price || 0) * Number(item.quantity || 1);
    return sum + lineSub * (Number(item.discount_percent || 0) / 100);
  }, 0);
  const totalAmount = subtotal - totalDiscount;
  const blendedDiscountPercent = subtotal > 0 ? (totalDiscount / subtotal) * 100 : 0;

  const handleSubmit = async () => {
    if (!selectedCustomerId) {
      showToast('Please select a customer.', 'warning');
      return;
    }
    if (items.length === 0) {
      showToast('Please add at least one line item.', 'warning');
      return;
    }

    setIsLoading(true);
    try {
      const payload: QuotationCreate = {
        customer_id: selectedCustomerId,
        deal_id: selectedDealId || undefined,
        title: title.trim() || undefined,
        items,
      };

      const created = await quotationApi.createQuotation(payload);
      showToast(`Quotation ${created.quotation_number} created successfully!`, 'success');
      onSuccess(created);
      onClose();
    } catch (err: any) {
      showToast(err.message || 'Failed to build quotation.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <GlassModal isOpen={isOpen} onClose={onClose} title="Phase 65 — Quotation Builder & Pricing Engine" maxWidth="2xl">
      <div className="space-y-6">
        {/* Wizard Step Navigation Header */}
        <div className="flex items-center justify-between border-b border-white/10 pb-4 text-xs">
          <div className={`flex items-center gap-2 ${step >= 1 ? 'text-indigo-400 font-bold' : 'text-slate-500'}`}>
            <span className="w-5 h-5 rounded-full bg-indigo-500/20 flex items-center justify-center font-mono">1</span>
            <span>Account & Deal</span>
          </div>
          <ArrowRight className="w-4 h-4 text-slate-600" />
          <div className={`flex items-center gap-2 ${step >= 2 ? 'text-indigo-400 font-bold' : 'text-slate-500'}`}>
            <span className="w-5 h-5 rounded-full bg-indigo-500/20 flex items-center justify-center font-mono">2</span>
            <span>Line Items & Pricing</span>
          </div>
          <ArrowRight className="w-4 h-4 text-slate-600" />
          <div className={`flex items-center gap-2 ${step >= 3 ? 'text-indigo-400 font-bold' : 'text-slate-500'}`}>
            <span className="w-5 h-5 rounded-full bg-indigo-500/20 flex items-center justify-center font-mono">3</span>
            <span>Governance & Submit</span>
          </div>
        </div>

        {/* Step 1: Account & Deal Selection */}
        {step === 1 && (
          <div className="space-y-4">
            <GlassSelect
              label="Select Customer Account *"
              value={selectedCustomerId}
              onChange={(e) => handleCustomerChange(e.target.value)}
              options={[
                { label: '-- Select Customer --', value: '' },
                ...customers.map((c) => ({ label: c.name, value: c.id })),
              ]}
            />

            <GlassSelect
              label="Link to Sales Deal (Optional)"
              value={selectedDealId}
              onChange={(e) => setSelectedDealId(e.target.value)}
              disabled={!selectedCustomerId}
              options={[
                { label: '-- Select Deal --', value: '' },
                ...deals.map((d) => ({ label: `${d.deal_number} - ${d.title}`, value: d.id })),
              ]}
            />

            <GlassInput
              label="Quotation Title / Subject"
              placeholder="e.g. Enterprise Cloud Infrastructure Renewal"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />

            <div className="flex justify-end pt-4">
              <BrutalButton
                variant="primary"
                onClick={() => {
                  if (!selectedCustomerId) {
                    showToast('Please select a customer to proceed.', 'warning');
                    return;
                  }
                  setStep(2);
                }}
              >
                Next: Configure Line Items <ArrowRight className="w-4 h-4 ml-1.5" />
              </BrutalButton>
            </div>
          </div>
        )}

        {/* Step 2: Line Items & Live Pricing */}
        {step === 2 && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                Quotation Line Items ({items.length})
              </h4>
              <button
                type="button"
                onClick={handleAddItem}
                className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-indigo-600/30 hover:bg-indigo-600/50 border border-indigo-500/40 text-indigo-200 font-semibold transition"
              >
                <Plus className="w-3.5 h-3.5" /> Add Product
              </button>
            </div>

            {items.length === 0 ? (
              <div className="p-8 text-center border border-dashed border-white/10 rounded-xl text-slate-400 text-xs">
                No items added yet. Click "Add Product" above to build commercial items.
              </div>
            ) : (
              <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
                {items.map((item, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-black/30 border border-white/10 text-xs grid grid-cols-12 gap-3 items-center">
                    <div className="col-span-4">
                      <label className="text-[10px] text-slate-400 block mb-1">Product</label>
                      <select
                        value={item.product_id}
                        onChange={(e) => handleItemChange(idx, 'product_id', e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white focus:outline-none"
                      >
                        {products.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.name} (${Number(p.unit_price).toFixed(2)})
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="col-span-2">
                      <label className="text-[10px] text-slate-400 block mb-1">Qty</label>
                      <input
                        type="number"
                        min="1"
                        value={item.quantity}
                        onChange={(e) => handleItemChange(idx, 'quantity', Math.max(1, parseInt(e.target.value) || 1))}
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white font-mono focus:outline-none"
                      />
                    </div>

                    <div className="col-span-2">
                      <label className="text-[10px] text-slate-400 block mb-1">Unit Price ($)</label>
                      <input
                        type="number"
                        step="0.01"
                        value={item.unit_price}
                        onChange={(e) => handleItemChange(idx, 'unit_price', parseFloat(e.target.value) || 0)}
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white font-mono focus:outline-none"
                      />
                    </div>

                    <div className="col-span-3">
                      <label className="text-[10px] text-slate-400 block mb-1">Discount %</label>
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        max="100"
                        value={item.discount_percent}
                        onChange={(e) => handleItemChange(idx, 'discount_percent', parseFloat(e.target.value) || 0)}
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-emerald-400 font-mono focus:outline-none"
                      />
                    </div>

                    <div className="col-span-1 flex justify-end">
                      <button
                        type="button"
                        onClick={() => handleRemoveItem(idx)}
                        className="text-rose-400 hover:text-rose-300 p-1.5 rounded transition"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="flex justify-between items-center pt-4 border-t border-white/10">
              <BrutalButton variant="secondary" onClick={() => setStep(1)}>
                Back
              </BrutalButton>
              <BrutalButton
                variant="primary"
                onClick={() => {
                  if (items.length === 0) {
                    showToast('Please add at least one line item.', 'warning');
                    return;
                  }
                  setStep(3);
                }}
              >
                Next: Review & Governance <ArrowRight className="w-4 h-4 ml-1.5" />
              </BrutalButton>
            </div>
          </div>
        )}

        {/* Step 3: Governance Review & Submit */}
        {step === 3 && (
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/30 grid grid-cols-3 gap-4 text-xs font-mono">
              <div>
                <div className="text-slate-400 text-[10px] uppercase">Subtotal</div>
                <div className="text-lg font-bold text-white">${subtotal.toFixed(2)}</div>
              </div>
              <div>
                <div className="text-slate-400 text-[10px] uppercase">Total Discount</div>
                <div className="text-lg font-bold text-amber-300">-${totalDiscount.toFixed(2)} ({blendedDiscountPercent.toFixed(1)}%)</div>
              </div>
              <div>
                <div className="text-slate-400 text-[10px] uppercase">Total Amount</div>
                <div className="text-xl font-black text-emerald-400">${totalAmount.toFixed(2)}</div>
              </div>
            </div>

            {blendedDiscountPercent > 15 && (
              <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 shrink-0" />
                <span>Blended discount ({blendedDiscountPercent.toFixed(1)}%) exceeds 15% threshold and may require commercial approval.</span>
              </div>
            )}

            <div className="flex justify-between items-center pt-4 border-t border-white/10">
              <BrutalButton variant="secondary" onClick={() => setStep(2)}>
                Back to Line Items
              </BrutalButton>
              <BrutalButton variant="primary" onClick={handleSubmit} isLoading={isLoading}>
                <CheckCircle2 className="w-4 h-4 mr-1.5" /> Generate Authoritative Quotation
              </BrutalButton>
            </div>
          </div>
        )}
      </div>
    </GlassModal>
  );
};
