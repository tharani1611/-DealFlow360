from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict, Field


# --- Phase 36: Warehouses & Variants & Stocks ---
class WarehouseBase(BaseModel):
    code: str
    name: str
    address: Optional[str] = None
    priority: int = 1
    is_active: bool = True

class WarehouseCreate(WarehouseBase):
    pass

class WarehouseResponse(WarehouseBase):
    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProductVariantBase(BaseModel):
    sku: str
    name: str
    unit_price_override: Optional[Decimal] = None
    is_active: bool = True

class ProductVariantCreate(ProductVariantBase):
    product_id: UUID

class ProductVariantResponse(ProductVariantBase):
    id: UUID
    organization_id: UUID
    product_id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class StockAdjustmentRequest(BaseModel):
    warehouse_id: UUID
    product_id: UUID
    variant_id: Optional[UUID] = None
    location_code: Optional[str] = "MAIN"
    quantity_delta: int = Field(..., description="Positive for addition/receipt, negative for reduction/issue")
    notes: Optional[str] = None

class StockReceiptRequest(BaseModel):
    warehouse_id: UUID
    product_id: UUID
    variant_id: Optional[UUID] = None
    quantity: int = Field(..., gt=0)
    notes: Optional[str] = None


class InventoryStockResponse(BaseModel):
    id: UUID
    organization_id: UUID
    warehouse_id: UUID
    product_id: UUID
    variant_id: Optional[UUID] = None
    location_code: Optional[str] = None
    on_hand_quantity: int
    reserved_quantity: int
    available_quantity: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class InventoryMovementResponse(BaseModel):
    id: UUID
    organization_id: UUID
    warehouse_id: UUID
    product_id: UUID
    variant_id: Optional[UUID] = None
    quantity: int
    movement_type: str
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    actor_id: Optional[UUID] = None
    actor_name: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Phase 37: Stock Availability ---
class LineAvailabilityItem(BaseModel):
    quotation_item_id: UUID
    product_id: UUID
    variant_id: Optional[UUID] = None
    product_name: str
    requested_quantity: int
    on_hand_quantity: int
    reserved_quantity: int
    available_quantity: int
    shortfall_quantity: int
    status: str  # AVAILABLE, PARTIALLY_AVAILABLE, OUT_OF_STOCK

class QuotationAvailabilitySummary(BaseModel):
    quotation_id: UUID
    overall_status: str  # AVAILABLE, PARTIALLY_AVAILABLE, OUT_OF_STOCK
    total_requested: int
    total_available: int
    total_shortfall: int
    line_availabilities: List[LineAvailabilityItem]


# --- Phase 38: Inventory Reservation ---
class ReservationCreateRequest(BaseModel):
    quotation_id: UUID

class InventoryReservationResponse(BaseModel):
    id: UUID
    organization_id: UUID
    quotation_id: UUID
    quotation_item_id: UUID
    product_id: UUID
    variant_id: Optional[UUID] = None
    warehouse_id: UUID
    quantity: int
    status: str
    expires_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Phase 39 & 40: Warehouse Allocation & Override ---
class WarehouseAllocationResponse(BaseModel):
    id: UUID
    organization_id: UUID
    quotation_id: UUID
    quotation_item_id: UUID
    warehouse_id: UUID
    allocated_quantity: int
    allocation_strategy: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class SmartAllocationSummary(BaseModel):
    quotation_id: UUID
    is_fully_allocated: bool
    total_requested: int
    total_allocated: int
    total_shortfall: int
    allocations: List[WarehouseAllocationResponse]

class ManualOverrideRequest(BaseModel):
    quotation_id: UUID
    quotation_item_id: UUID
    new_warehouse_id: UUID
    allocated_quantity: int = Field(..., gt=0)
    reason: str = Field(..., min_length=3)

class FulfillmentOverrideAuditResponse(BaseModel):
    id: UUID
    organization_id: UUID
    quotation_id: UUID
    quotation_item_id: Optional[UUID] = None
    actor_id: UUID
    actor_name: str
    original_allocation: Dict[str, Any]
    new_allocation: Dict[str, Any]
    reason: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Phase 41: Shipment Creation ---
class ShipmentLineResponse(BaseModel):
    id: UUID
    organization_id: UUID
    shipment_id: UUID
    quotation_item_id: UUID
    product_id: UUID
    variant_id: Optional[UUID] = None
    quantity: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ShipmentCreateRequest(BaseModel):
    quotation_id: UUID
    warehouse_id: UUID
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    expected_delivery_date: Optional[date] = None

class ShipmentResponse(BaseModel):
    id: UUID
    organization_id: UUID
    shipment_number: str
    quotation_id: UUID
    warehouse_id: UUID
    status: str
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    shipped_at: Optional[datetime] = None
    expected_delivery_date: Optional[date] = None
    actual_delivery_date: Optional[date] = None
    lines: List[ShipmentLineResponse] = []
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Phase 42 & 43: Backorders & Consolidation ---
class BackorderResponse(BaseModel):
    id: UUID
    organization_id: UUID
    backorder_number: str
    quotation_id: UUID
    quotation_item_id: UUID
    customer_id: UUID
    product_id: UUID
    variant_id: Optional[UUID] = None
    requested_quantity: int
    fulfilled_quantity: int
    remaining_quantity: int
    warehouse_id: Optional[UUID] = None
    status: str
    promised_delivery_date: Optional[date] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class BackorderConsolidationSummary(BaseModel):
    customer_id: UUID
    total_open_backorders: int
    total_remaining_quantity: int
    backorders: List[BackorderResponse]


# --- Phase 44: Delivery Promise Tracking ---
class DeliveryPromiseResponse(BaseModel):
    id: UUID
    organization_id: UUID
    quotation_id: UUID
    shipment_id: Optional[UUID] = None
    backorder_id: Optional[UUID] = None
    promised_date: date
    expected_date: date
    actual_date: Optional[date] = None
    status: str
    slippage_days: int
    notes: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Phase 45: Hybrid Billing ---
class LineBillingClassification(BaseModel):
    quotation_item_id: UUID
    product_id: UUID
    product_name: str
    billing_type: str  # ONE_TIME, RECURRING
    unit_price: Decimal
    quantity: int
    line_total: Decimal

class BillingClassificationResponse(BaseModel):
    id: UUID
    organization_id: UUID
    quotation_id: UUID
    commercial_model: str  # ONE_TIME, RECURRING, HYBRID
    one_time_total: Decimal
    recurring_monthly_total: Decimal
    billing_frequency: str
    line_classifications: List[LineBillingClassification]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
