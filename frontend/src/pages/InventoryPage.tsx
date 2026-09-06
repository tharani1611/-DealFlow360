import React, { useState, useEffect } from 'react';
import { NeoGlassCard } from '../components/ui/NeoGlassCard';
import { NeoGlassButton } from '../components/ui/NeoGlassButton';
import { GlassInput } from '../components/ui/GlassInput';
import { GlassSelect } from '../components/ui/GlassSelect';
import { GlassModal } from '../components/ui/GlassModal';
import { StatusBadge } from '../components/ui/StatusBadge';
import { Tabs } from '../components/ui/Tabs';
import {
  Warehouse,
  InventoryStock,
  InventoryMovement,
  Product,
  WarehouseCreate,
  StockReceiptRequest,
} from '../types';
import { inventoryApi } from '../services/inventoryApi';
import { productApi } from '../services/productApi';
import { Warehouse as WarehouseIcon, PackageCheck, RefreshCw, Plus, ArrowDownRight } from 'lucide-react';

import { useToast } from '../context/ToastContext';

export const InventoryPage: React.FC = () => {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<string>('stocks');
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [stocks, setStocks] = useState<InventoryStock[]>([]);
  const [movements, setMovements] = useState<InventoryMovement[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  // Modals state
  const [isWarehouseModalOpen, setIsWarehouseModalOpen] = useState<boolean>(false);
  const [isReceiptModalOpen, setIsReceiptModalOpen] = useState<boolean>(false);

  // Form states
  const [newWhCode, setNewWhCode] = useState<string>('');
  const [newWhName, setNewWhName] = useState<string>('');
  const [newWhAddress, setNewWhAddress] = useState<string>('');
  const [newWhPriority, setNewWhPriority] = useState<number>(1);

  const [receiptWarehouseId, setReceiptWarehouseId] = useState<string>('');
  const [receiptProductId, setReceiptProductId] = useState<string>('');
  const [receiptQty, setReceiptQty] = useState<number>(10);
  const [receiptNotes, setReceiptNotes] = useState<string>('');

  const loadData = async () => {
    try {
      const [whList, stockList, moveList, prodList] = await Promise.all([
        inventoryApi.getWarehouses().catch(() => []),
        inventoryApi.getStocks().catch(() => []),
        inventoryApi.getMovements().catch(() => []),
        productApi.getProducts().catch(() => []),
      ]);
      setWarehouses(whList);
      setStocks(stockList);
      setMovements(moveList);
      setProducts(prodList);

      if (whList.length > 0) {
        setReceiptWarehouseId((prev) => prev || whList[0].id);
      }
      if (prodList.length > 0) {
        setReceiptProductId((prev) => prev || prodList[0].id);
      }
    } catch (err: any) {
      console.error('Failed to load inventory data:', err);
      showToast(err.message || 'Failed to load inventory data.', 'error');
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateWarehouse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newWhCode || !newWhName) return;

    setIsSubmitting(true);
    try {
      const payload: WarehouseCreate = {
        code: newWhCode.toUpperCase(),
        name: newWhName,
        address: newWhAddress || undefined,
        priority: newWhPriority,
      };
      const createdWh = await inventoryApi.createWarehouse(payload);
      showToast(`Warehouse '${payload.name}' created successfully!`, 'success');
      setNewWhCode('');
      setNewWhName('');
      setNewWhAddress('');
      setIsWarehouseModalOpen(false);
      if (createdWh?.id) {
        setReceiptWarehouseId((prev) => prev || createdWh.id);
      }
      await loadData();
    } catch (err: any) {
      console.error('Failed to create warehouse:', err);
      showToast(err.message || 'Failed to create warehouse.', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRecordReceipt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!receiptWarehouseId || !receiptProductId || receiptQty <= 0) return;

    setIsSubmitting(true);
    try {
      const payload: StockReceiptRequest = {
        warehouse_id: receiptWarehouseId,
        product_id: receiptProductId,
        quantity: receiptQty,
        notes: receiptNotes || undefined,
      };
      await inventoryApi.recordStockReceipt(payload);
      showToast('Stock receipt recorded successfully!', 'success');
      setReceiptQty(10);
      setReceiptNotes('');
      setIsReceiptModalOpen(false);
      await loadData();
    } catch (err: any) {
      console.error('Failed to record stock receipt:', err);
      showToast(err.message || 'Failed to record stock receipt.', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const tabOptions = [
    { id: 'stocks', label: 'Stock Balance', icon: PackageCheck },
    { id: 'warehouses', label: 'Warehouses', icon: WarehouseIcon },
    { id: 'movements', label: 'Movement Logs', icon: ArrowDownRight },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 tracking-tight flex items-center gap-2">
            <WarehouseIcon className="w-7 h-7 text-indigo-400" />
            Inventory & Warehouse Hub
          </h1>
          <p className="text-sm text-slate-400 font-mono mt-1">
            Real-time stock availability, multi-warehouse allocations, and movement tracking
          </p>
        </div>
        <div className="flex items-center gap-3">
          <NeoGlassButton variant="default" onClick={() => loadData()}>
            <RefreshCw className="w-4 h-4 mr-1.5" />
            Refresh
          </NeoGlassButton>
          <NeoGlassButton variant="default" onClick={() => setIsWarehouseModalOpen(true)}>
            <Plus className="w-4 h-4 mr-1.5" />
            Add Warehouse
          </NeoGlassButton>
          <NeoGlassButton variant="primary" onClick={() => setIsReceiptModalOpen(true)}>
            <Plus className="w-4 h-4 mr-1.5" />
            Receive Stock
          </NeoGlassButton>
        </div>
      </div>

      {/* Navigation Tabs */}
      <Tabs tabs={tabOptions} activeTab={activeTab} onChange={setActiveTab} />

      {/* Tab Content: Stock Balance */}
      {activeTab === 'stocks' && (
        <NeoGlassCard className="p-5">
          <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
            <h2 className="text-base font-bold text-slate-100 font-mono uppercase tracking-wider">
              Current Stock Levels Across Warehouses
            </h2>
            <span className="text-xs font-mono text-slate-400">{stocks.length} Stock Records</span>
          </div>

          {stocks.length === 0 ? (
            <div className="text-center py-12 text-slate-500 font-mono text-sm">
              No inventory stock records found. Click "Receive Stock" to record incoming stock.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider">
                    <th className="py-3 px-3">Warehouse</th>
                    <th className="py-3 px-3">Product ID</th>
                    <th className="py-3 px-3">On-Hand</th>
                    <th className="py-3 px-3">Reserved</th>
                    <th className="py-3 px-3">Available</th>
                    <th className="py-3 px-3">Location</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {stocks.map((stock) => {
                    const wh = warehouses.find((w) => w.id === stock.warehouse_id);
                    const prod = products.find((p) => p.id === stock.product_id);
                    return (
                      <tr key={stock.id} className="hover:bg-slate-800/40">
                        <td className="py-3 px-3 font-bold text-slate-200">
                          {wh ? `${wh.code} (${wh.name})` : stock.warehouse_id}
                        </td>
                        <td className="py-3 px-3 text-sky-400">
                          {prod ? `${prod.name} [${prod.sku}]` : stock.product_id}
                        </td>
                        <td className="py-3 px-3 text-slate-100 font-bold">{stock.on_hand_quantity}</td>
                        <td className="py-3 px-3 text-amber-400 font-bold">{stock.reserved_quantity}</td>
                        <td className="py-3 px-3 text-emerald-400 font-bold">{stock.available_quantity}</td>
                        <td className="py-3 px-3 text-slate-400">{stock.location_code || 'MAIN'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </NeoGlassCard>
      )}

      {/* Tab Content: Warehouses */}
      {activeTab === 'warehouses' && (
        <NeoGlassCard className="p-5">
          <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
            <h2 className="text-base font-bold text-slate-100 font-mono uppercase tracking-wider">
              Fulfillment Warehouses
            </h2>
            <span className="text-xs font-mono text-slate-400">{warehouses.length} Active Warehouses</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {warehouses.map((wh) => (
              <div key={wh.id} className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 bg-indigo-950/80 border border-indigo-500/40 text-indigo-300 font-mono font-bold text-xs rounded">
                    {wh.code}
                  </span>
                  <span className="text-[11px] font-mono text-slate-400">Priority #{wh.priority}</span>
                </div>
                <h3 className="text-base font-bold text-slate-100">{wh.name}</h3>
                {wh.address && <p className="text-xs text-slate-400 font-mono">{wh.address}</p>}
                <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between">
                  <StatusBadge status={wh.is_active ? 'ACTIVE' : 'INACTIVE'} size="sm" />
                  <span className="text-[10px] font-mono text-slate-500">ID: {wh.id.substring(0, 8)}...</span>
                </div>
              </div>
            ))}
          </div>
        </NeoGlassCard>
      )}

      {/* Tab Content: Movement Logs */}
      {activeTab === 'movements' && (
        <NeoGlassCard className="p-5">
          <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
            <h2 className="text-base font-bold text-slate-100 font-mono uppercase tracking-wider">
              Immutable Stock Movement Ledger
            </h2>
            <span className="text-xs font-mono text-slate-400">{movements.length} Movements</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider">
                  <th className="py-3 px-3">Date</th>
                  <th className="py-3 px-3">Type</th>
                  <th className="py-3 px-3">Qty</th>
                  <th className="py-3 px-3">Warehouse</th>
                  <th className="py-3 px-3">Product</th>
                  <th className="py-3 px-3">Notes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {movements.map((m) => (
                  <tr key={m.id} className="hover:bg-slate-800/40">
                    <td className="py-3 px-3 text-slate-400">{new Date(m.created_at).toLocaleString()}</td>
                    <td className="py-3 px-3 font-bold text-sky-400">{m.movement_type}</td>
                    <td className={`py-3 px-3 font-bold ${m.quantity >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {m.quantity > 0 ? `+${m.quantity}` : m.quantity}
                    </td>
                    <td className="py-3 px-3 text-slate-300">{m.warehouse_id.substring(0, 8)}...</td>
                    <td className="py-3 px-3 text-slate-300">{m.product_id.substring(0, 8)}...</td>
                    <td className="py-3 px-3 text-slate-400">{m.notes || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </NeoGlassCard>
      )}

      {/* Modal: Add Warehouse */}
      <GlassModal isOpen={isWarehouseModalOpen} onClose={() => setIsWarehouseModalOpen(false)} title="Create Fulfillment Warehouse">
        <form onSubmit={handleCreateWarehouse} className="space-y-4">
          <GlassInput label="Warehouse Code (e.g. WH-EAST)" value={newWhCode} onChange={(e) => setNewWhCode(e.target.value)} required />
          <GlassInput label="Warehouse Name" value={newWhName} onChange={(e) => setNewWhName(e.target.value)} required />
          <GlassInput label="Location Address" value={newWhAddress} onChange={(e) => setNewWhAddress(e.target.value)} />
          <GlassInput label="Allocation Priority (1 = Highest)" type="number" min={1} value={newWhPriority} onChange={(e) => setNewWhPriority(parseInt(e.target.value) || 1)} />

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
            <NeoGlassButton type="button" variant="default" onClick={() => setIsWarehouseModalOpen(false)}>
              Cancel
            </NeoGlassButton>
            <NeoGlassButton type="submit" variant="primary" disabled={isSubmitting}>
              Create Warehouse
            </NeoGlassButton>
          </div>
        </form>
      </GlassModal>

      {/* Modal: Stock Receipt */}
      <GlassModal isOpen={isReceiptModalOpen} onClose={() => setIsReceiptModalOpen(false)} title="Record Stock Receipt">
        <form onSubmit={handleRecordReceipt} className="space-y-4">
          <GlassSelect
            label="Target Warehouse"
            value={receiptWarehouseId}
            onChange={(e) => setReceiptWarehouseId(e.target.value)}
            options={warehouses.map((w) => ({ value: w.id, label: `${w.code} - ${w.name}` }))}
          />
          <GlassSelect
            label="Product"
            value={receiptProductId}
            onChange={(e) => setReceiptProductId(e.target.value)}
            options={products.map((p) => ({ value: p.id, label: `${p.name} (${p.sku})` }))}
          />
          <GlassInput label="Received Quantity" type="number" min={1} value={receiptQty} onChange={(e) => setReceiptQty(parseInt(e.target.value) || 1)} required />
          <GlassInput label="Receipt Notes / Purchase Order #" value={receiptNotes} onChange={(e) => setReceiptNotes(e.target.value)} />

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
            <NeoGlassButton type="button" variant="default" onClick={() => setIsReceiptModalOpen(false)}>
              Cancel
            </NeoGlassButton>
            <NeoGlassButton type="submit" variant="primary" disabled={isSubmitting}>
              Record Stock Arrival
            </NeoGlassButton>
          </div>
        </form>
      </GlassModal>
    </div>
  );
};
