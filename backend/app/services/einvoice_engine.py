import uuid
from datetime import datetime, date
from typing import Dict, Any, List, Optional

from app.models.invoice import Invoice, InvoiceItem
from app.models.organization import Organization
from app.models.customer import Customer
from app.services.gst_engine import get_state_code, calculate_gst_breakdown


def build_einvoice_irn_payload(
    invoice: Invoice,
    organization: Organization,
    customer: Customer,
    items: List[InvoiceItem],
    seller_state: str = "Karnataka",
) -> Dict[str, Any]:
    """
    Generates NIC Compliant E-Invoice IRN Draft JSON Payload (v1.03 Schema).
    """
    buyer_state = customer.state or "Karnataka"
    raw_items = [
        {
            "product_name": item.description,
            "hsn_sac_code": getattr(item, "hsn_sac_code", "8471"),
            "gst_rate": getattr(item, "gst_rate", 18.0),
            "quantity": float(item.quantity),
            "unit_price": float(item.unit_price),
            "discount_amount": float(item.discount_amount),
            "line_subtotal": float(item.line_subtotal),
            "line_total": float(item.line_total),
        }
        for item in items
    ]

    gst_res = calculate_gst_breakdown(seller_state, buyer_state, raw_items)

    formatted_date = invoice.invoice_date.strftime("%d/%m/%Y") if isinstance(invoice.invoice_date, (datetime, date)) else datetime.now().strftime("%d/%m/%Y")

    item_list = []
    for item_data in gst_res["items"]:
        item_list.append({
            "SlNo": str(item_data["item_index"]),
            "PrdDesc": item_data["product_name"],
            "IsServc": "N",
            "HsnCd": item_data["hsn_sac_code"],
            "Qty": float(item_data["quantity"]),
            "Unit": "NOS",
            "UnitPrice": float(item_data["unit_price"]),
            "TotAmt": float(item_data["taxable_value"]),
            "Discount": 0.0,
            "AssVal": float(item_data["taxable_value"]),
            "GstRt": float(item_data["gst_rate"]),
            "CgstVal": float(item_data["cgst_amount"]),
            "SgstVal": float(item_data["sgst_amount"]),
            "IgstVal": float(item_data["igst_amount"]),
            "TotItemVal": float(item_data["total_line_value"]),
        })

    return {
        "Version": "1.03",
        "TranDtls": {
            "TaxSch": "GST",
            "SupTyp": "B2B",
            "RegRev": "N",
            "EcmGstin": None,
            "IgstOnIntra": "N"
        },
        "DocDtls": {
            "Typ": "INV",
            "No": invoice.invoice_number,
            "Dt": formatted_date,
        },
        "SellerDtls": {
            "Gstin": "29AAAAA0000A1Z5",
            "LglNm": organization.name,
            "TrdNm": organization.name,
            "Addr1": "Plot 42, Tech Park Sector 4",
            "Loc": "Bengaluru",
            "State": gst_res["seller_state_code"],
            "Pin": 560001
        },
        "BuyerDtls": {
            "Gstin": "27BBBBB1111B1Z2",
            "LglNm": customer.name,
            "TrdNm": customer.name,
            "Pos": gst_res["buyer_state_code"],
            "Addr1": customer.address or "Commercial Complex",
            "Loc": customer.city or "Mumbai",
            "State": gst_res["buyer_state_code"],
            "Pin": 400001
        },
        "ItemList": item_list,
        "ValDtls": {
            "AssVal": float(gst_res["total_taxable_value"]),
            "CgstVal": float(gst_res["total_cgst_amount"]),
            "SgstVal": float(gst_res["total_sgst_amount"]),
            "IgstVal": float(gst_res["total_igst_amount"]),
            "CesVal": 0.0,
            "Discount": 0.0,
            "OthChrg": 0.0,
            "RndOffAmt": 0.0,
            "TotInvVal": float(gst_res["grand_total"]),
        },
        "gst_breakdown_summary": {
            "tax_type": gst_res["tax_type"],
            "is_intra_state": gst_res["is_intra_state"],
            "seller_state": gst_res["seller_state"],
            "buyer_state": gst_res["buyer_state"],
        }
    }


def build_eway_bill_payload(
    invoice: Invoice,
    organization: Organization,
    customer: Customer,
    items: List[InvoiceItem],
    transporter_id: Optional[str] = None,
    vehicle_no: Optional[str] = None,
    distance_km: int = 350,
    seller_state: str = "Karnataka",
) -> Dict[str, Any]:
    """
    Generates NIC Compliant E-Way Bill Dispatch JSON Payload.
    """
    buyer_state = customer.state or "Maharashtra"
    formatted_date = invoice.invoice_date.strftime("%d/%m/%Y") if isinstance(invoice.invoice_date, (datetime, date)) else datetime.now().strftime("%d/%m/%Y")
    
    seller_code = get_state_code(seller_state)
    buyer_code = get_state_code(buyer_state)

    item_summaries = [
        {
            "productName": item.description,
            "hsnCode": getattr(item, "hsn_sac_code", "8471"),
            "quantity": float(item.quantity),
            "taxableAmount": float(item.line_subtotal),
        }
        for item in items
    ]

    return {
        "supplyType": "Outward",
        "subSupplyType": "Supply",
        "docType": "INV",
        "docNo": invoice.invoice_number,
        "docDate": formatted_date,
        "fromGstin": "29AAAAA0000A1Z5",
        "fromTrdName": organization.name,
        "fromAddr1": "Plot 42, Tech Park Sector 4",
        "fromPlace": "Bengaluru",
        "fromPincode": 560001,
        "actFromStateCode": int(seller_code),
        "fromStateCode": int(seller_code),
        "toGstin": "27BBBBB1111B1Z2",
        "toTrdName": customer.name,
        "toAddr1": customer.address or "Industrial Estate",
        "toPlace": customer.city or "Mumbai",
        "toPincode": 400001,
        "actToStateCode": int(buyer_code),
        "toStateCode": int(buyer_code),
        "totalValue": float(invoice.subtotal or invoice.total),
        "cgstValue": float(invoice.tax_total) / 2.0 if seller_code == buyer_code else 0.0,
        "sgstValue": float(invoice.tax_total) / 2.0 if seller_code == buyer_code else 0.0,
        "igstValue": float(invoice.tax_total) if seller_code != buyer_code else 0.0,
        "totInvValue": float(invoice.total),
        "transporterId": transporter_id or "29AAACT1234F1Z1",
        "transporterName": "Express National Logistics",
        "transDocNo": f"TRN-{uuid.uuid4().hex[:6].upper()}",
        "transMode": "1",  # Road
        "distance": distance_km,
        "vehicleNo": vehicle_no or "KA-01-EA-9821",
        "vehicleType": "Regular",
        "itemList": item_summaries,
    }
