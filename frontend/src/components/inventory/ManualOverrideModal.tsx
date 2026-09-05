import React, { useState, useEffect } from 'react';
import { GlassModal } from '../ui/GlassModal';
import { GlassSelect } from '../ui/GlassSelect';
import { GlassInput } from '../ui/GlassInput';
import { GlassTextarea } from '../ui/GlassTextarea';
import { NeoGlassButton } from '../ui/NeoGlassButton';
import { Warehouse, QuotationItem, ManualOverrideRequest } from '../../types';
import { inventoryApi } from '../../services/inventoryApi';

interface ManualOverrideModalProps {
  isOpen: boolean;
  onClose: () => void;
  quotationId: string;
  quotationItems: QuotationItem[];
  warehouses: Warehouse[];
  onOverrideComplete: () => void;
}

export const ManualOverrideModal: React.FC<ManualOverrideModalProps> = ({
  isOpen,
  onClose,
  quotationId,
  quotationItems,
  warehouses,
  onOverrideComplete,
}) => {
  const [selectedItemId, setSelectedItemId] = useState<string>('');
  const [selectedWarehouseId, setSelectedWarehouseId] = useState<string>('');
  const [allocatedQuantity, setAllocatedQuantity] = useState<number>(1);
  const [reason, setReason] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (quotationItems.length > 0) {
      setSelectedItemId(quotationItems[0].id);
      setAllocatedQuantity(Number(quotationItems[0].quantity));
    }
    if (warehouses.length > 0) {
      setSelectedWarehouseId(warehouses[0].id);
    }
  }, [quotationItems, warehouses, isOpen]);

  const handleItemChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const itemId = e.target.value;
    setSelectedItemId(itemId);
    const item = quotationItems.find((i) => i.id === itemId);
    if (item) {
      setAllocatedQuantity(Number(item.quantity));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedItemId || !selectedWarehouseId || allocatedQuantity <= 0 || !reason.trim()) {
      setError('Please fill in all fields with a valid reason (min 3 characters).');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const payload: ManualOverrideRequest = {
        quotation_id: quotationId,
        quotation_item_id: selectedItemId,
        new_warehouse_id: selectedWarehouseId,
        allocated_quantity: allocatedQuantity,
        reason: reason.trim(),
      };
      await inventoryApi.applyManualOverride(payload);
      onOverrideComplete();
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to apply manual override');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <GlassModal isOpen={isOpen} onClose={onClose} title="Manual Fulfillment Override" subtitle="Override automated warehouse allocation with mandatory audit logging">
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 bg-rose-950/80 border border-rose-500/40 rounded-lg text-rose-300 text-xs font-mono">
            {error}
          </div>
        )}

        <GlassSelect
          label="Select Quotation Item"
          value={selectedItemId}
          onChange={handleItemChange}
          options={quotationItems.map((item) => ({
            value: item.id,
            label: `${item.product_name} (Qty: ${item.quantity})`,
          }))}
        />

        <GlassSelect
          label="Target Warehouse Override"
          value={selectedWarehouseId}
          onChange={(e) => setSelectedWarehouseId(e.target.value)}
          options={warehouses.map((wh) => ({
            value: wh.id,
            label: `${wh.code} - ${wh.name} (Priority ${wh.priority})`,
          }))}
        />

        <GlassInput
          label="Allocated Quantity"
          type="number"
          min={1}
          value={allocatedQuantity}
          onChange={(e) => setAllocatedQuantity(parseInt(e.target.value) || 1)}
        />

        <GlassTextarea
          label="Override Reason (Mandatory Audit Note)"
          rows={3}
          placeholder="Explain why this dispatch is being manually assigned to this warehouse..."
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />

        <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
          <NeoGlassButton type="button" variant="default" onClick={onClose}>
            Cancel
          </NeoGlassButton>
          <NeoGlassButton type="submit" variant="primary" disabled={isSubmitting}>
            {isSubmitting ? 'Saving Override...' : 'Apply & Audit Override'}
          </NeoGlassButton>
        </div>
      </form>
    </GlassModal>
  );
};
