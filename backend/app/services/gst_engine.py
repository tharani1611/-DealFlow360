import math
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional

STATE_CODE_MAP = {
    "karnataka": "29",
    "maharashtra": "27",
    "delhi": "07",
    "tamil nadu": "33",
    "telangana": "36",
    "gujarat": "24",
    "haryana": "06",
    "uttar pradesh": "09",
    "west bengal": "19",
    "rajasthan": "08",
    "kerala": "32",
    "andhra pradesh": "37",
    "punjab": "03",
}


def _d(val: float) -> Decimal:
    """Helper to convert float to Decimal rounded to 2 decimal places."""
    return Decimal(str(round(val, 2))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_state_code(state_name: Optional[str]) -> str:
    """Resolves Indian State name to 2-digit GST State Code (e.g. Karnataka -> 29)."""
    if not state_name:
        return "29"
    norm = state_name.lower().strip()
    return STATE_CODE_MAP.get(norm, "29")


def calculate_gst_breakdown(
    seller_state: str,
    buyer_state: str,
    line_items: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Computes Indian GST regulatory tax breakdowns.
    Determines Intra-State (CGST + SGST) vs Inter-State (IGST) split based on seller vs buyer state.
    """
    s_state_clean = (seller_state or "Karnataka").strip()
    b_state_clean = (buyer_state or "Karnataka").strip()
    is_intra_state = s_state_clean.lower() == b_state_clean.lower()

    tax_type = "INTRA_STATE_CGST_SGST" if is_intra_state else "INTER_STATE_IGST"
    seller_state_code = get_state_code(s_state_clean)
    buyer_state_code = get_state_code(b_state_clean)

    processed_items = []
    total_taxable_value = 0.0
    total_cgst_amount = 0.0
    total_sgst_amount = 0.0
    total_igst_amount = 0.0

    for idx, item in enumerate(line_items, start=1):
        hsn_sac_code = str(item.get("hsn_sac_code") or "8471")
        gst_rate = float(item.get("gst_rate") if item.get("gst_rate") is not None else 18.0)
        
        qty = float(item.get("quantity") or 1.0)
        unit_price = float(item.get("unit_price") or 0.0)
        disc_amt = float(item.get("discount_amount") or 0.0)

        line_subtotal = float(item.get("line_subtotal") or item.get("line_total") or (qty * unit_price - disc_amt))
        taxable_val = max(0.0, line_subtotal)

        if is_intra_state:
            cgst_rate = gst_rate / 2.0
            sgst_rate = gst_rate / 2.0
            igst_rate = 0.0

            cgst_amt = taxable_val * (cgst_rate / 100.0)
            sgst_amt = taxable_val * (sgst_rate / 100.0)
            igst_amt = 0.0
        else:
            cgst_rate = 0.0
            sgst_rate = 0.0
            igst_rate = gst_rate

            cgst_amt = 0.0
            sgst_amt = 0.0
            igst_amt = taxable_val * (igst_rate / 100.0)

        item_tax_amt = cgst_amt + sgst_amt + igst_amt
        line_total_val = taxable_val + item_tax_amt

        total_taxable_value += taxable_val
        total_cgst_amount += cgst_amt
        total_sgst_amount += sgst_amt
        total_igst_amount += igst_amt

        processed_items.append({
            "item_index": idx,
            "product_name": item.get("description") or item.get("product_name") or f"Item {idx}",
            "hsn_sac_code": hsn_sac_code,
            "quantity": _d(qty),
            "unit_price": _d(unit_price),
            "taxable_value": _d(taxable_val),
            "gst_rate": _d(gst_rate),
            "cgst_rate": _d(cgst_rate),
            "cgst_amount": _d(cgst_amt),
            "sgst_rate": _d(sgst_rate),
            "sgst_amount": _d(sgst_amt),
            "igst_rate": _d(igst_rate),
            "igst_amount": _d(igst_amt),
            "total_line_tax": _d(item_tax_amt),
            "total_line_value": _d(line_total_val),
        })

    total_tax_amount = total_cgst_amount + total_sgst_amount + total_igst_amount
    grand_total = total_taxable_value + total_tax_amount

    return {
        "tax_type": tax_type,
        "is_intra_state": is_intra_state,
        "seller_state": s_state_clean,
        "seller_state_code": seller_state_code,
        "buyer_state": b_state_clean,
        "buyer_state_code": buyer_state_code,
        "total_taxable_value": _d(total_taxable_value),
        "total_cgst_amount": _d(total_cgst_amount),
        "total_sgst_amount": _d(total_sgst_amount),
        "total_igst_amount": _d(total_igst_amount),
        "total_tax_amount": _d(total_tax_amount),
        "grand_total": _d(grand_total),
        "items": processed_items,
    }
