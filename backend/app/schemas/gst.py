import uuid
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class GSTLineItemInput(BaseModel):
    description: Optional[str] = Field(None, description="Product description or name")
    hsn_sac_code: Optional[str] = Field("8471", max_length=10, description="HSN/SAC Code")
    quantity: Decimal = Field(Decimal("1.00"), ge=Decimal("0.01"))
    unit_price: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"))
    discount_amount: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"))
    line_subtotal: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    gst_rate: Decimal = Field(Decimal("18.00"), ge=Decimal("0.00"), le=Decimal("28.00"))


class GSTTaxCalculationRequest(BaseModel):
    seller_state: str = Field("Karnataka", description="State of seller / origin warehouse")
    buyer_state: str = Field("Karnataka", description="State of buyer / customer destination")
    items: List[GSTLineItemInput] = Field(..., min_length=1)


class GSTProcessedLineItem(BaseModel):
    item_index: int
    product_name: str
    hsn_sac_code: str
    quantity: Decimal
    unit_price: Decimal
    taxable_value: Decimal
    gst_rate: Decimal
    cgst_rate: Decimal
    cgst_amount: Decimal
    sgst_rate: Decimal
    sgst_amount: Decimal
    igst_rate: Decimal
    igst_amount: Decimal
    total_line_tax: Decimal
    total_line_value: Decimal


class GSTTaxCalculationResponse(BaseModel):
    tax_type: str
    is_intra_state: bool
    seller_state: str
    seller_state_code: str
    buyer_state: str
    buyer_state_code: str
    total_taxable_value: Decimal
    total_cgst_amount: Decimal
    total_sgst_amount: Decimal
    total_igst_amount: Decimal
    total_tax_amount: Decimal
    grand_total: Decimal
    items: List[GSTProcessedLineItem]


class EWayBillPayloadRequest(BaseModel):
    transporter_id: Optional[str] = Field("29AAACT1234F1Z1", description="15-character GSTIN of Transport Agent")
    vehicle_no: Optional[str] = Field("KA-01-EA-9821", description="Vehicle Registration Number")
    distance_km: int = Field(350, ge=1, le=5000, description="Estimated dispatch distance in KM")
    seller_state: Optional[str] = Field("Karnataka", description="Seller origin state override")
