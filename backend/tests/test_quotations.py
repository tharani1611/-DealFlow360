import pytest
import uuid
from decimal import Decimal
from httpx import AsyncClient
from app.core.database import AsyncSessionLocal
from app.core.security import create_access_token, hash_password
from app.models.user import User


@pytest.mark.asyncio
async def test_create_quotation_success_and_math(async_client: AsyncClient):
    """Verify creation of quotation with line item calculations and tenant-scoped quotation number."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Quot Math Org",
        "organization_slug": f"quot-math-{uuid.uuid4().hex[:8]}",
        "email": "admin@quotmath.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    org_id = reg_resp.json()["organization"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Customer
    cust_resp = await async_client.post("/api/v1/customers", json={"name": "Acme Corp"}, headers=headers)
    cust_id = cust_resp.json()["id"]

    # Create 2 Products
    p1_resp = await async_client.post("/api/v1/products", json={"name": "Widget A", "sku": "WID-A", "unit_price": "100.00"}, headers=headers)
    p2_resp = await async_client.post("/api/v1/products", json={"name": "Widget B", "sku": "WID-B", "unit_price": "50.00"}, headers=headers)
    p1_id = p1_resp.json()["id"]
    p2_id = p2_resp.json()["id"]

    # Create Quotation:
    # Qty 2 of p1 (2 * 100.00 = 200.00)
    # Qty 3 of p2 (3 * 50.00 = 150.00)
    # Subtotal = 350.00, Discount = 50.00, Tax = 30.00 => Total = 330.00
    quot_payload = {
        "customer_id": cust_id,
        "items": [
            {"product_id": p1_id, "quantity": "2.00"},
            {"product_id": p2_id, "quantity": "3.00"}
        ],
        "discount_amount": "50.00",
        "tax_amount": "30.00",
        "notes": "Standard terms 30 days"
    }

    resp = await async_client.post("/api/v1/quotations", json=quot_payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()

    assert data["quotation_number"] == "QT-000001"
    assert data["status"] == "draft"
    assert data["organization_id"] == org_id
    assert data["customer_id"] == cust_id
    assert Decimal(data["subtotal"]) == Decimal("350.00")
    assert Decimal(data["discount_amount"]) == Decimal("50.00")
    assert Decimal(data["tax_amount"]) == Decimal("30.00")
    assert Decimal(data["total_amount"]) == Decimal("330.00")
    assert len(data["items"]) == 2
    assert data["notes"] == "Standard terms 30 days"


@pytest.mark.asyncio
async def test_mandatory_price_snapshot(async_client: AsyncClient):
    """
    CRITICAL PRICE SNAPSHOT TEST:
    Verify updating product price and name later does NOT modify historical quotation line item values.
    """
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Snapshot Org",
        "organization_slug": f"snapshot-{uuid.uuid4().hex[:8]}",
        "email": "admin@snapshot.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    cust_id = (await async_client.post("/api/v1/customers", json={"name": "Snap Customer"}, headers=headers)).json()["id"]
    prod_id = (await async_client.post("/api/v1/products", json={"name": "Original Product", "sku": "SNAP-01", "unit_price": "100.00"}, headers=headers)).json()["id"]

    # Create Quotation with original product price
    quot_resp = await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_id,
        "items": [{"product_id": prod_id, "quantity": "5.00"}]
    }, headers=headers)
    assert quot_resp.status_code == 201
    quot_id = quot_resp.json()["id"]

    assert Decimal(quot_resp.json()["subtotal"]) == Decimal("500.00")
    assert quot_resp.json()["items"][0]["product_name"] == "Original Product"
    assert Decimal(quot_resp.json()["items"][0]["unit_price"]) == Decimal("100.00")

    # UPDATE Product unit price to 999.00 and name to "Hacked Product"
    upd_prod = await async_client.put(f"/api/v1/products/{prod_id}", json={
        "name": "Hacked Product",
        "unit_price": "999.00"
    }, headers=headers)
    assert upd_prod.status_code == 200

    # RE-FETCH Quotation and ensure historical values are preserved
    get_quot = await async_client.get(f"/api/v1/quotations/{quot_id}", headers=headers)
    assert get_quot.status_code == 200
    snapshot_data = get_quot.json()

    assert snapshot_data["items"][0]["product_name"] == "Original Product"
    assert Decimal(snapshot_data["items"][0]["unit_price"]) == Decimal("100.00")
    assert Decimal(snapshot_data["items"][0]["line_total"]) == Decimal("500.00")
    assert Decimal(snapshot_data["subtotal"]) == Decimal("500.00")


@pytest.mark.asyncio
async def test_quotation_number_sequential_per_tenant(async_client: AsyncClient):
    """Verify quotation numbers start at QT-000001 independently for each organization."""
    reg_a = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Seq Org A",
        "organization_slug": f"seq-a-{uuid.uuid4().hex[:8]}",
        "email": "adminA@seqa.com",
        "password": "Password123!"
    })
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    reg_b = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Seq Org B",
        "organization_slug": f"seq-b-{uuid.uuid4().hex[:8]}",
        "email": "adminB@seqb.com",
        "password": "Password123!"
    })
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    cust_a = (await async_client.post("/api/v1/customers", json={"name": "Cust A"}, headers=headers_a)).json()["id"]
    prod_a = (await async_client.post("/api/v1/products", json={"name": "Prod A", "sku": "P-A", "unit_price": "10.00"}, headers=headers_a)).json()["id"]

    cust_b = (await async_client.post("/api/v1/customers", json={"name": "Cust B"}, headers=headers_b)).json()["id"]
    prod_b = (await async_client.post("/api/v1/products", json={"name": "Prod B", "sku": "P-B", "unit_price": "20.00"}, headers=headers_b)).json()["id"]

    # Org A: 2 quotations
    q_a1 = await async_client.post("/api/v1/quotations", json={"customer_id": cust_a, "items": [{"product_id": prod_a, "quantity": "1"}]}, headers=headers_a)
    q_a2 = await async_client.post("/api/v1/quotations", json={"customer_id": cust_a, "items": [{"product_id": prod_a, "quantity": "2"}]}, headers=headers_a)

    assert q_a1.json()["quotation_number"] == "QT-000001"
    assert q_a2.json()["quotation_number"] == "QT-000002"

    # Org B: 1 quotation -> starts at QT-000001
    q_b1 = await async_client.post("/api/v1/quotations", json={"customer_id": cust_b, "items": [{"product_id": prod_b, "quantity": "1"}]}, headers=headers_b)
    assert q_b1.json()["quotation_number"] == "QT-000001"


@pytest.mark.asyncio
async def test_status_transitions_and_finalized_immutability(async_client: AsyncClient):
    """Verify status transition state machine rules and content immutability after finalization."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Status Org",
        "organization_slug": f"status-{uuid.uuid4().hex[:8]}",
        "email": "admin@status.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    cust_id = (await async_client.post("/api/v1/customers", json={"name": "Status Cust"}, headers=headers)).json()["id"]
    prod_id = (await async_client.post("/api/v1/products", json={"name": "Status Prod", "sku": "ST-01", "unit_price": "100.00"}, headers=headers)).json()["id"]

    quot = await async_client.post("/api/v1/quotations", json={"customer_id": cust_id, "items": [{"product_id": prod_id, "quantity": "1"}]}, headers=headers)
    quot_id = quot.json()["id"]
    assert quot.json()["status"] == "draft"

    # Draft -> Sent (allowed)
    sent_res = await async_client.put(f"/api/v1/quotations/{quot_id}", json={"status": "sent"}, headers=headers)
    assert sent_res.status_code == 200
    assert sent_res.json()["status"] == "sent"

    # Sent -> Accepted (allowed)
    acc_res = await async_client.put(f"/api/v1/quotations/{quot_id}", json={"status": "accepted"}, headers=headers)
    assert acc_res.status_code == 200
    assert acc_res.json()["status"] == "accepted"

    # Accepted -> Draft (invalid state transition) -> 422 BusinessRuleViolation
    inv_res = await async_client.put(f"/api/v1/quotations/{quot_id}", json={"status": "draft"}, headers=headers)
    assert inv_res.status_code == 422

    # Finalized quotation modification attempt -> 422 BusinessRuleViolation
    mod_res = await async_client.put(f"/api/v1/quotations/{quot_id}", json={"discount_amount": "10.00"}, headers=headers)
    assert mod_res.status_code == 422


@pytest.mark.asyncio
async def test_discount_exceeding_subtotal_rejected(async_client: AsyncClient):
    """Verify discount amount greater than subtotal is rejected with 422."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Disc Org",
        "organization_slug": f"disc-{uuid.uuid4().hex[:8]}",
        "email": "admin@disc.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    cust_id = (await async_client.post("/api/v1/customers", json={"name": "Disc Cust"}, headers=headers)).json()["id"]
    prod_id = (await async_client.post("/api/v1/products", json={"name": "Disc Prod", "sku": "DISC-01", "unit_price": "50.00"}, headers=headers)).json()["id"]

    # Subtotal 50.00, Discount 100.00 -> 422
    res = await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_id,
        "items": [{"product_id": prod_id, "quantity": "1"}],
        "discount_amount": "100.00"
    }, headers=headers)
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_cross_tenant_quotation_attack_prevention(async_client: AsyncClient):
    """
    CRITICAL CROSS-TENANT SECURITY TEST:
    1. Creating quotation with cross-tenant customer or product returns 404.
    2. GET, PUT, DELETE cross-tenant quotation returns 404.
    """
    slug_a = f"q-tenant-a-{uuid.uuid4().hex[:8]}"
    slug_b = f"q-tenant-b-{uuid.uuid4().hex[:8]}"

    reg_a = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Q Tenant A",
        "organization_slug": slug_a,
        "email": "userA@qtenanta.com",
        "password": "Password123!"
    })
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    reg_b = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Q Tenant B",
        "organization_slug": slug_b,
        "email": "userB@qtenantb.com",
        "password": "Password123!"
    })
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    cust_a = (await async_client.post("/api/v1/customers", json={"name": "Cust A"}, headers=headers_a)).json()["id"]
    prod_a = (await async_client.post("/api/v1/products", json={"name": "Prod A", "sku": "PA", "unit_price": "10.00"}, headers=headers_a)).json()["id"]

    cust_b = (await async_client.post("/api/v1/customers", json={"name": "Cust B"}, headers=headers_b)).json()["id"]
    prod_b = (await async_client.post("/api/v1/products", json={"name": "Prod B", "sku": "PB", "unit_price": "20.00"}, headers=headers_b)).json()["id"]

    # User A tries using Cust B -> 404
    res_cross_cust = await async_client.post("/api/v1/quotations", json={"customer_id": cust_b, "items": [{"product_id": prod_a, "quantity": "1"}]}, headers=headers_a)
    assert res_cross_cust.status_code == 404

    # User A tries using Prod B -> 404
    res_cross_prod = await async_client.post("/api/v1/quotations", json={"customer_id": cust_a, "items": [{"product_id": prod_b, "quantity": "1"}]}, headers=headers_a)
    assert res_cross_prod.status_code == 404

    # Create valid Quotation in Org B
    quot_b_id = (await async_client.post("/api/v1/quotations", json={"customer_id": cust_b, "items": [{"product_id": prod_b, "quantity": "1"}]}, headers=headers_b)).json()["id"]

    # User A tries GET Quotation B -> 404
    assert (await async_client.get(f"/api/v1/quotations/{quot_b_id}", headers=headers_a)).status_code == 404

    # User A tries PUT Quotation B -> 404
    assert (await async_client.put(f"/api/v1/quotations/{quot_b_id}", json={"notes": "Hacked"}, headers=headers_a)).status_code == 404

    # User A tries DELETE Quotation B -> 404
    assert (await async_client.delete(f"/api/v1/quotations/{quot_b_id}", headers=headers_a)).status_code == 404


@pytest.mark.asyncio
async def test_delete_quotation_admin_authorization(async_client: AsyncClient):
    """Verify DELETE quotation succeeds for Admin (204) and is forbidden for regular user (403)."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Del Quot Org",
        "organization_slug": f"del-quot-{uuid.uuid4().hex[:8]}",
        "email": "admin@delquot.com",
        "password": "Password123!"
    })
    admin_token = reg_resp.json()["access_token"]
    org_id = reg_resp.json()["organization"]["id"]

    # Create regular user
    async with AsyncSessionLocal() as session:
        reg_user = User(
            organization_id=uuid.UUID(org_id),
            email="regular@delquot.com",
            password_hash=hash_password("Password123!"),
            is_admin=False,
            is_active=True
        )
        session.add(reg_user)
        await session.commit()
        await session.refresh(reg_user)
        reg_user_id = str(reg_user.id)

    normal_token = create_access_token(subject=reg_user_id)
    headers_norm = {"Authorization": f"Bearer {normal_token}"}
    headers_admin = {"Authorization": f"Bearer {admin_token}"}

    cust_id = (await async_client.post("/api/v1/customers", json={"name": "Del Cust"}, headers=headers_admin)).json()["id"]
    prod_id = (await async_client.post("/api/v1/products", json={"name": "Del Prod", "sku": "DP-01", "unit_price": "10.00"}, headers=headers_admin)).json()["id"]
    quot_id = (await async_client.post("/api/v1/quotations", json={"customer_id": cust_id, "items": [{"product_id": prod_id, "quantity": "1"}]}, headers=headers_admin)).json()["id"]

    # Regular user DELETE -> 403 Forbidden
    assert (await async_client.delete(f"/api/v1/quotations/{quot_id}", headers=headers_norm)).status_code == 403

    # Admin user DELETE -> 204 No Content
    assert (await async_client.delete(f"/api/v1/quotations/{quot_id}", headers=headers_admin)).status_code == 204


@pytest.mark.asyncio
async def test_list_quotations_filtering(async_client: AsyncClient):
    """Verify listing quotations with status and customer_id filters."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "List Q Org",
        "organization_slug": f"list-q-{uuid.uuid4().hex[:8]}",
        "email": "admin@listq.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    cust1 = (await async_client.post("/api/v1/customers", json={"name": "Cust 1"}, headers=headers)).json()["id"]
    cust2 = (await async_client.post("/api/v1/customers", json={"name": "Cust 2"}, headers=headers)).json()["id"]
    prod = (await async_client.post("/api/v1/products", json={"name": "Item 1", "sku": "IT1", "unit_price": "100.00"}, headers=headers)).json()["id"]

    q1 = (await async_client.post("/api/v1/quotations", json={"customer_id": cust1, "items": [{"product_id": prod, "quantity": "1"}]}, headers=headers)).json()["id"]
    q2 = (await async_client.post("/api/v1/quotations", json={"customer_id": cust2, "items": [{"product_id": prod, "quantity": "1"}]}, headers=headers)).json()["id"]

    # Transition q1 to sent
    await async_client.put(f"/api/v1/quotations/{q1}", json={"status": "sent"}, headers=headers)

    # Filter status=sent -> 1 result (q1)
    res_sent = await async_client.get("/api/v1/quotations?status=sent", headers=headers)
    assert res_sent.status_code == 200
    assert len(res_sent.json()) == 1
    assert res_sent.json()[0]["id"] == q1

    # Filter customer_id=cust2 -> 1 result (q2)
    res_cust2 = await async_client.get(f"/api/v1/quotations?customer_id={cust2}", headers=headers)
    assert res_cust2.status_code == 200
    assert len(res_cust2.json()) == 1
    assert res_cust2.json()[0]["id"] == q2


@pytest.mark.asyncio
async def test_quotation_contact_and_deal_relationships(async_client: AsyncClient):
    """Verify associating valid Contact and Deal with Quotation within same customer/tenant."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Rel Quot Org",
        "organization_slug": f"rel-q-{uuid.uuid4().hex[:8]}",
        "email": "admin@relq.com",
        "password": "Password123!"
    })
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Customer, Contact, Deal, Product
    cust = (await async_client.post("/api/v1/customers", json={"name": "Rel Customer"}, headers=headers)).json()
    cust_id = cust["id"]

    contact = (await async_client.post("/api/v1/contacts", json={"customer_id": cust_id, "first_name": "Jane", "last_name": "Doe"}, headers=headers)).json()
    contact_id = contact["id"]

    deal = (await async_client.post("/api/v1/deals", json={"customer_id": cust_id, "title": "Big Enterprise Expansion", "value": "50000.00"}, headers=headers)).json()
    deal_id = deal["id"]

    prod = (await async_client.post("/api/v1/products", json={"name": "Enterprise Software", "sku": "ENT-SOFT-01", "unit_price": "25000.00"}, headers=headers)).json()
    prod_id = prod["id"]

    # Create Quotation with Contact & Deal IDs
    quot_payload = {
        "customer_id": cust_id,
        "contact_id": contact_id,
        "deal_id": deal_id,
        "title": "Q3 Enterprise Proposal",
        "currency": "EUR",
        "terms": "Payment due within 45 days of invoice date.",
        "items": [
            {
                "product_id": prod_id,
                "quantity": "2.00",
                "description": "2x Annual Licenses with Premium Support",
                "sku": "ENT-SOFT-01",
                "sequence": 1
            }
        ]
    }

    res = await async_client.post("/api/v1/quotations", json=quot_payload, headers=headers)
    assert res.status_code == 201
    data = res.json()

    assert data["contact_id"] == contact_id
    assert data["deal_id"] == deal_id
    assert data["title"] == "Q3 Enterprise Proposal"
    assert data["currency"] == "EUR"
    assert data["terms"] == "Payment due within 45 days of invoice date."
    assert len(data["items"]) == 1
    assert data["items"][0]["sku"] == "ENT-SOFT-01"
    assert data["items"][0]["description"] == "2x Annual Licenses with Premium Support"
    assert data["items"][0]["sequence"] == 1


@pytest.mark.asyncio
async def test_quotation_cross_tenant_contact_or_deal_rejected(async_client: AsyncClient):
    """Verify passing a Contact or Deal from another customer or tenant returns 404."""
    reg_a = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "CT Rel Org A",
        "organization_slug": f"ct-rel-a-{uuid.uuid4().hex[:8]}",
        "email": "adminA@ctrel.com",
        "password": "Password123!"
    })
    headers_a = {"Authorization": f"Bearer {reg_a.json()['access_token']}"}

    reg_b = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "CT Rel Org B",
        "organization_slug": f"ct-rel-b-{uuid.uuid4().hex[:8]}",
        "email": "adminB@ctrel.com",
        "password": "Password123!"
    })
    headers_b = {"Authorization": f"Bearer {reg_b.json()['access_token']}"}

    cust_a = (await async_client.post("/api/v1/customers", json={"name": "Cust A"}, headers=headers_a)).json()["id"]
    cust_a2 = (await async_client.post("/api/v1/customers", json={"name": "Cust A2"}, headers=headers_a)).json()["id"]
    contact_a2 = (await async_client.post("/api/v1/contacts", json={"customer_id": cust_a2, "first_name": "Other", "last_name": "Customer"}, headers=headers_a)).json()["id"]
    prod_a = (await async_client.post("/api/v1/products", json={"name": "Prod A", "sku": "PA", "unit_price": "100.00"}, headers=headers_a)).json()["id"]

    cust_b = (await async_client.post("/api/v1/customers", json={"name": "Cust B"}, headers=headers_b)).json()["id"]
    deal_b = (await async_client.post("/api/v1/deals", json={"customer_id": cust_b, "title": "Deal B", "value": "1000.00"}, headers=headers_b)).json()["id"]

    # 1. User A tries creating quotation for Cust A using Contact belonging to Cust A2 -> 404
    res1 = await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_a,
        "contact_id": contact_a2,
        "items": [{"product_id": prod_a, "quantity": "1"}]
    }, headers=headers_a)
    assert res1.status_code == 404

    # 2. User A tries creating quotation for Cust A using Deal from Org B -> 404
    res2 = await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_a,
        "deal_id": deal_b,
        "items": [{"product_id": prod_a, "quantity": "1"}]
    }, headers=headers_a)
    assert res2.status_code == 404


@pytest.mark.asyncio
async def test_quotation_line_item_snapshots_and_commercial_fields(async_client: AsyncClient):
    """Verify line item price snapshot, SKU snapshot, custom unit price override, and line level discount/tax fields."""
    reg_resp = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Line Snapshot Org",
        "organization_slug": f"line-snap-{uuid.uuid4().hex[:8]}",
        "email": "admin@linesnap.com",
        "password": "Password123!"
    })
    headers = {"Authorization": f"Bearer {reg_resp.json()['access_token']}"}

    cust_id = (await async_client.post("/api/v1/customers", json={"name": "Line Cust"}, headers=headers)).json()["id"]
    prod_id = (await async_client.post("/api/v1/products", json={"name": "Base Server", "sku": "SRV-BASE-01", "unit_price": "5000.00"}, headers=headers)).json()["id"]

    # Create quotation line item with custom unit price override (4500.00), discount_amount (500.00), tax_amount (200.00)
    quot = await async_client.post("/api/v1/quotations", json={
        "customer_id": cust_id,
        "items": [
            {
                "product_id": prod_id,
                "quantity": "2.00",
                "unit_price": "4500.00",
                "discount_percent": "10.00",
                "discount_amount": "500.00",
                "tax_rate": "5.00",
                "tax_amount": "200.00",
                "description": "Discounted bundle price"
            }
        ]
    }, headers=headers)
    assert quot.status_code == 201
    q_data = quot.json()

    # line_total = (2 * 4500.00) - 500.00 + 200.00 = 9000 - 500 + 200 = 8700.00
    item = q_data["items"][0]
    assert item["sku"] == "SRV-BASE-01"
    assert Decimal(item["unit_price"]) == Decimal("4500.00")
    assert Decimal(item["line_total"]) == Decimal("8700.00")
    assert Decimal(item["discount_percent"]) == Decimal("10.00")
    assert Decimal(item["discount_amount"]) == Decimal("500.00")
    assert Decimal(item["tax_rate"]) == Decimal("5.00")
    assert Decimal(item["tax_amount"]) == Decimal("200.00")

