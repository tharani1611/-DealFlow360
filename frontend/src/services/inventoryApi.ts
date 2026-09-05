import { fetchApi } from './apiClient';
import {
  Warehouse,
  WarehouseCreate,
  StockReceiptRequest,
  InventoryStock,
  InventoryMovement,
  QuotationAvailabilitySummary,
  InventoryReservation,
  SmartAllocationSummary,
  ManualOverrideRequest,
  WarehouseAllocation,
  FulfillmentOverrideAudit,
  Shipment,
  ShipmentCreateRequest,
  Backorder,
  BackorderConsolidationSummary,
  DeliveryPromise,
  BillingClassification,
} from '../types';

export const inventoryApi = {
  // Warehouses
  async getWarehouses(): Promise<Warehouse[]> {
    return fetchApi<Warehouse[]>('/inventory/warehouses');
  },

  async createWarehouse(payload: WarehouseCreate): Promise<Warehouse> {
    return fetchApi<Warehouse>('/inventory/warehouses', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // Stock Receipts & Balance
  async recordStockReceipt(payload: StockReceiptRequest): Promise<InventoryStock> {
    return fetchApi<InventoryStock>('/inventory/receipts', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getStocks(params?: { warehouse_id?: string; product_id?: string }): Promise<InventoryStock[]> {
    const query = new URLSearchParams();
    if (params?.warehouse_id) query.append('warehouse_id', params.warehouse_id);
    if (params?.product_id) query.append('product_id', params.product_id);
    const qStr = query.toString();
    return fetchApi<InventoryStock[]>(`/inventory/stocks${qStr ? `?${qStr}` : ''}`);
  },

  async getMovements(params?: { warehouse_id?: string; product_id?: string }): Promise<InventoryMovement[]> {
    const query = new URLSearchParams();
    if (params?.warehouse_id) query.append('warehouse_id', params.warehouse_id);
    if (params?.product_id) query.append('product_id', params.product_id);
    const qStr = query.toString();
    return fetchApi<InventoryMovement[]>(`/inventory/movements${qStr ? `?${qStr}` : ''}`);
  },

  // Availability & Reservations
  async getQuotationAvailability(quotationId: string): Promise<QuotationAvailabilitySummary> {
    return fetchApi<QuotationAvailabilitySummary>(`/inventory/availability/quotation/${quotationId}`);
  },

  async reserveStockForQuotation(quotationId: string): Promise<InventoryReservation[]> {
    return fetchApi<InventoryReservation[]>(`/inventory/reservations/quotation/${quotationId}`, {
      method: 'POST',
    });
  },

  async getQuotationReservations(quotationId: string): Promise<InventoryReservation[]> {
    return fetchApi<InventoryReservation[]>(`/inventory/reservations/quotation/${quotationId}`);
  },

  async releaseReservation(reservationId: string): Promise<InventoryReservation> {
    return fetchApi<InventoryReservation>(`/inventory/reservations/${reservationId}/release`, {
      method: 'POST',
    });
  },

  // Fulfillment & Override
  async getSmartAllocation(quotationId: string): Promise<SmartAllocationSummary> {
    return fetchApi<SmartAllocationSummary>(`/fulfillment/allocation/quotation/${quotationId}`);
  },

  async applyManualOverride(payload: ManualOverrideRequest): Promise<WarehouseAllocation> {
    return fetchApi<WarehouseAllocation>('/fulfillment/override', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getOverrideAudits(quotationId: string): Promise<FulfillmentOverrideAudit[]> {
    return fetchApi<FulfillmentOverrideAudit[]>(`/fulfillment/override/audits/quotation/${quotationId}`);
  },

  // Shipments
  async createShipment(payload: ShipmentCreateRequest): Promise<Shipment> {
    return fetchApi<Shipment>('/shipments', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getQuotationShipments(quotationId: string): Promise<Shipment[]> {
    return fetchApi<Shipment[]>(`/shipments/quotation/${quotationId}`);
  },

  async getShipment(shipmentId: string): Promise<Shipment> {
    return fetchApi<Shipment>(`/shipments/${shipmentId}`);
  },

  // Backorders
  async getQuotationBackorders(quotationId: string): Promise<Backorder[]> {
    return fetchApi<Backorder[]>(`/backorders/quotation/${quotationId}`);
  },

  async getCustomerBackorders(customerId: string): Promise<BackorderConsolidationSummary> {
    return fetchApi<BackorderConsolidationSummary>(`/backorders/customer/${customerId}`);
  },

  // Delivery Promise
  async getQuotationDeliveryPromise(quotationId: string): Promise<DeliveryPromise> {
    return fetchApi<DeliveryPromise>(`/delivery-promises/quotation/${quotationId}`);
  },

  // Hybrid Billing
  async getQuotationHybridBilling(quotationId: string): Promise<BillingClassification> {
    return fetchApi<BillingClassification>(`/hybrid-billing/quotation/${quotationId}`);
  },
};
