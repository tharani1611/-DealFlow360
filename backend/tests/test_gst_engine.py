import pytest
import uuid
from httpx import AsyncClient

from app.services.gst_engine import calculate_gst_breakdown, get_state_code


@pytest.mark.asyncio
async def test_gst_engine_intra_state_cgst_sgst():
    """Verify intra-state (e.g. Karnataka -> Karnataka) splits GST evenly into CGST 9% and SGST 9%."""
    line_items = [
        {
            "product_name": "Enterprise Workstation",
            "hsn_sac_code": "8471",
            "gst_rate": 18.0,
            "quantity": 10.0,
            "unit_price": 1000.0,
            "line_subtotal": 10000.0,
        }
    ]
    res = calculate_gst_breakdown("Karnataka", "Karnataka", line_items)

    assert res["is_intra_state"] is True
    assert res["tax_type"] == "INTRA_STATE_CGST_SGST"
    assert res["seller_state_code"] == "29"
    assert res["buyer_state_code"] == "29"
    assert float(res["total_taxable_value"]) == 10000.0
    assert float(res["total_cgst_amount"]) == 900.0
    assert float(res["total_sgst_amount"]) == 900.0
    assert float(res["total_igst_amount"]) == 0.0
    assert float(res["total_tax_amount"]) == 1800.0
    assert float(res["grand_total"]) == 11800.0


@pytest.mark.asyncio
async def test_gst_engine_inter_state_igst():
    """Verify inter-state (e.g. Karnataka -> Maharashtra) applies full 18% IGST."""
    line_items = [
        {
            "product_name": "Cloud Server Rack",
            "hsn_sac_code": "8517",
            "gst_rate": 18.0,
            "quantity": 2.0,
            "unit_price": 50000.0,
            "line_subtotal": 100000.0,
        }
    ]
    res = calculate_gst_breakdown("Karnataka", "Maharashtra", line_items)

    assert res["is_intra_state"] is False
    assert res["tax_type"] == "INTER_STATE_IGST"
    assert res["seller_state_code"] == "29"
    assert res["buyer_state_code"] == "27"
    assert float(res["total_taxable_value"]) == 100000.0
    assert float(res["total_cgst_amount"]) == 0.0
    assert float(res["total_sgst_amount"]) == 0.0
    assert float(res["total_igst_amount"]) == 18000.0
    assert float(res["total_tax_amount"]) == 18000.0
    assert float(res["grand_total"]) == 118000.0


@pytest.mark.asyncio
async def test_gst_api_endpoints_and_payload_generation(async_client: AsyncClient):
    """Verify GST endpoints calculate tax and return E-Invoice/E-Way Bill payloads."""
    # 1. Register Org & User
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "GST Test Corp",
        "organization_slug": f"gst-{uuid.uuid4().hex[:8]}",
        "email": "tax@gstcorp.com",
        "password": "Password123!"
    })
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test calculate-tax API
    calc_resp = await async_client.post("/api/v1/gst/calculate-tax", json={
        "seller_state": "Karnataka",
        "buyer_state": "Delhi",
        "items": [
            {
                "description": "Enterprise Software License",
                "hsn_sac_code": "998313",
                "quantity": 5,
                "unit_price": 10000,
                "discount_amount": 0,
                "gst_rate": 18
            }
        ]
    }, headers=headers)

    assert calc_resp.status_code == 200
    calc_data = calc_resp.json()
    assert calc_data["is_intra_state"] is False
    assert float(calc_data["total_igst_amount"]) == 9000.0

    # 3. Create Customer, Quotation & Invoice
    cust_resp = await async_client.post("/api/v1/customers", json={"name": "GST Customer", "state": "Maharashtra"}, headers=headers)
    cust_id = cust_resp.json()["id"]

    prod_resp = await async_client.post("/api/v1/products", json={
        "name": "Hardware Device",
        "sku": f"HW-{uuid.uuid4().hex[:4]}",
        "unit_price": "5000.00",
        "hsn_sac_code": "8471",
        "gst_rate": "18.00"
    }, headers=headers)
    prod_id = prod_resp.json()["id"]

    quote_resp = await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_id,
        "items": [{"product_id": prod_id, "quantity": 2, "unit_price": "5000.00"}]
    }, headers=headers)
    quote_id = quote_resp.json()["id"]

    # Transition to sent -> accepted & convert to invoice
    await async_client.post(f"/api/v1/quotations/{quote_id}/transition", json={"target_status": "sent"}, headers=headers)
    await async_client.post(f"/api/v1/quotations/{quote_id}/transition", json={"target_status": "accepted"}, headers=headers)
    inv_resp = await async_client.post(f"/api/v1/invoices/quotation/{quote_id}", headers=headers)
    assert inv_resp.status_code == 201
    inv_id = inv_resp.json()["id"]

    # 4. Fetch E-Invoice IRN Draft Payload
    einvoice_resp = await async_client.get(f"/api/v1/invoices/{inv_id}/einvoice-payload", headers=headers)
    assert einvoice_resp.status_code == 200
    einvoice_data = einvoice_resp.json()
    assert einvoice_data["Version"] == "1.03"
    assert einvoice_data["TranDtls"]["TaxSch"] == "GST"
    assert einvoice_data["SellerDtls"]["State"] == "29"
    assert len(einvoice_data["ItemList"]) == 1

    # 5. Fetch E-Way Bill Payload
    eway_resp = await async_client.post(f"/api/v1/invoices/{inv_id}/ewaybill-payload", json={
        "transporter_id": "29AAACT1234F1Z1",
        "vehicle_no": "KA-01-EA-9821",
        "distance_km": 420
    }, headers=headers)
    assert eway_resp.status_code == 200
    eway_data = eway_resp.json()
    assert eway_data["supplyType"] == "Outward"
    assert eway_data["vehicleNo"] == "KA-01-EA-9821"
    assert eway_data["distance"] == 420
