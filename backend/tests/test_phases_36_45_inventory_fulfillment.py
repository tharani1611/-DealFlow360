import uuid
from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.organization import Organization
from app.models.user import User
from app.models.customer import Customer
from app.models.product import Product
from app.models.quotation import Quotation, QuotationItem
from app.models.warehouses import Warehouse
from app.models.inventory import InventoryStock, InventoryMovement, InventoryReservation
from app.models.fulfillment import WarehouseAllocation, Shipment, Backorder, DeliveryPromise, BillingClassification
from app.core.security import create_access_token, hash_password
from app.services import inventory as inventory_service
from app.services import reservations as reservation_service
from app.services import fulfillment_allocation as allocation_service
from app.services import shipments as shipment_service
from app.services import backorders as backorder_service
from app.services import delivery_promise as delivery_service
from app.services import hybrid_billing as billing_service
from app.schemas.inventory import (
    WarehouseCreate,
    ProductVariantCreate,
    StockReceiptRequest,
    ManualOverrideRequest,
    ShipmentCreateRequest,
)


@pytest.mark.asyncio
async def test_phase_36_inventory_model_and_stock_receipt():
    async with AsyncSessionLocal() as db_session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Inventory Corp 1", slug=f"inv-corp-{org_id.hex[:6]}")
        db_session.add(org)

        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            organization_id=org_id,
            email=f"manager-{user_id.hex[:6]}@invcorp.com",
            password_hash=hash_password("Password123!"),
            full_name="Inventory Manager",
            is_admin=True,
            is_active=True,
        )
        db_session.add(user)

        prod_id = uuid.uuid4()
        product = Product(
            id=prod_id,
            organization_id=org_id,
            name="Enterprise Server R740",
            sku=f"HW-R740-{org_id.hex[:4]}",
            unit_price=Decimal("2500.00"),
            unit_cost=Decimal("1500.00"),
            currency="USD",
            is_active=True,
        )
        db_session.add(product)

        wh1 = Warehouse(
            id=uuid.uuid4(),
            organization_id=org_id,
            code=f"WH-E-{org_id.hex[:4]}",
            name="East Coast Hub",
            priority=1,
            is_active=True,
        )
        db_session.add(wh1)
        await db_session.commit()

        # Record stock receipt in WH-EAST (100 units)
        receipt_req = StockReceiptRequest(
            warehouse_id=wh1.id,
            product_id=prod_id,
            quantity=100,
            notes="Initial stock arrival",
        )
        stock = await inventory_service.record_stock_receipt(db_session, org_id, receipt_req)

        assert stock.on_hand_quantity == 100
        assert stock.reserved_quantity == 0
        assert stock.available_quantity == 100

        # Verify immutable movement log
        stmt = select(InventoryMovement).where(
            InventoryMovement.organization_id == org_id,
            InventoryMovement.product_id == prod_id,
        )
        movements = list((await db_session.execute(stmt)).scalars().all())
        assert len(movements) == 1
        assert movements[0].movement_type == "RECEIPT"
        assert movements[0].quantity == 100


@pytest.mark.asyncio
async def test_phase_37_38_stock_availability_and_reservation():
    async with AsyncSessionLocal() as db_session:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Inventory Corp 2", slug=f"inv-corp-{org_id.hex[:6]}")
        db_session.add(org)

        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            organization_id=org_id,
            email=f"manager-{user_id.hex[:6]}@invcorp.com",
            password_hash=hash_password("Password123!"),
            full_name="Inventory Manager",
            is_admin=True,
            is_active=True,
        )
        db_session.add(user)

        cust_id = uuid.uuid4()
        customer = Customer(
            id=cust_id,
            organization_id=org_id,
            name="Apex Logistics LLC",
            email=f"contact-{org_id.hex[:4]}@apex.com",
            is_active=True,
        )
        db_session.add(customer)

        prod_id = uuid.uuid4()
        product = Product(
            id=prod_id,
            organization_id=org_id,
            name="Enterprise Server R740",
            sku=f"HW-R740-{org_id.hex[:4]}",
            unit_price=Decimal("2500.00"),
            unit_cost=Decimal("1500.00"),
            currency="USD",
            is_active=True,
        )
        db_session.add(product)

        wh1 = Warehouse(
            id=uuid.uuid4(),
            organization_id=org_id,
            code=f"WH-E-{org_id.hex[:4]}",
            name="East Coast Hub",
            priority=1,
            is_active=True,
        )
        db_session.add(wh1)
        await db_session.commit()

        # Add stock: 50 units in WH-EAST
        await inventory_service.record_stock_receipt(db_session, org_id, StockReceiptRequest(warehouse_id=wh1.id, product_id=prod_id, quantity=50))

        # Create quotation for 30 units
        q_id = uuid.uuid4()
        quotation = Quotation(
            id=q_id,
            organization_id=org_id,
            quotation_number=f"QT-{org_id.hex[:6]}",
            customer_id=cust_id,
            created_by_user_id=user.id,
            status="sent",
            subtotal=Decimal("75000.00"),
            total_amount=Decimal("75000.00"),
            currency="USD",
        )
        db_session.add(quotation)

        q_item = QuotationItem(
            id=uuid.uuid4(),
            quotation_id=q_id,
            product_id=prod_id,
            product_name="Enterprise Server R740",
            sku=f"HW-R740-{org_id.hex[:4]}",
            quantity=Decimal("30.00"),
            unit_price=Decimal("2500.00"),
            unit_cost=Decimal("1500.00"),
            line_total=Decimal("75000.00"),
        )
        db_session.add(q_item)
        await db_session.commit()

        # Phase 37: Check availability
        avail = await inventory_service.calculate_quotation_availability(db_session, org_id, q_id)
        assert avail.overall_status == "AVAILABLE"
        assert avail.total_requested == 30
        assert avail.total_available == 30
        assert avail.total_shortfall == 0

        # Phase 38: Reserve stock
        reservations = await reservation_service.reserve_stock_for_quotation(db_session, org_id, q_id)
        assert len(reservations) == 1
        assert reservations[0].quantity == 30
        assert reservations[0].status == "ACTIVE"

        # Verify stock balance updated
        stocks = await inventory_service.get_inventory_stocks(db_session, org_id, wh1.id, prod_id)
        assert stocks[0].on_hand_quantity == 50
        assert stocks[0].reserved_quantity == 30
        assert stocks[0].available_quantity == 20


@pytest.mark.asyncio
async def test_phase_39_40_smart_allocation_and_manual_override():
    async with AsyncSessionLocal() as db_session:
        try:
            org_id = uuid.uuid4()
            org = Organization(id=org_id, name="Inventory Corp 3", slug=f"inv-corp-{org_id.hex[:6]}")
            db_session.add(org)

            user_id = uuid.uuid4()
            user = User(
                id=user_id,
                organization_id=org_id,
                email=f"manager-{user_id.hex[:6]}@invcorp.com",
                password_hash=hash_password("Password123!"),
                full_name="Inventory Manager",
                is_admin=True,
                is_active=True,
            )
            db_session.add(user)

            cust_id = uuid.uuid4()
            customer = Customer(
                id=cust_id,
                organization_id=org_id,
                name="Apex Logistics LLC",
                email=f"contact-{org_id.hex[:4]}@apex.com",
                is_active=True,
            )
            db_session.add(customer)

            prod_id = uuid.uuid4()
            product = Product(
                id=prod_id,
                organization_id=org_id,
                name="Enterprise Server R740",
                sku=f"HW-R740-{org_id.hex[:4]}",
                unit_price=Decimal("2500.00"),
                unit_cost=Decimal("1500.00"),
                currency="USD",
                is_active=True,
            )
            db_session.add(product)

            wh1 = Warehouse(id=uuid.uuid4(), organization_id=org_id, code=f"WH1-{org_id.hex[:4]}", name="East Coast Hub", priority=1, is_active=True)
            wh2 = Warehouse(id=uuid.uuid4(), organization_id=org_id, code=f"WH2-{org_id.hex[:4]}", name="West Coast Hub", priority=2, is_active=True)
            db_session.add_all([wh1, wh2])
            await db_session.commit()

            # Add stock: WH1=30, WH2=30 (multi-warehouse split required for 50 units)
            await inventory_service.record_stock_receipt(db_session, org_id, StockReceiptRequest(warehouse_id=wh1.id, product_id=prod_id, quantity=30))
            await inventory_service.record_stock_receipt(db_session, org_id, StockReceiptRequest(warehouse_id=wh2.id, product_id=prod_id, quantity=30))

            # Create quotation for 50 units (cannot be satisfied by WH1 alone, split required)
            q_id = uuid.uuid4()
            quotation = Quotation(
                id=q_id,
                organization_id=org_id,
                quotation_number=f"QT-{org_id.hex[:6]}",
                customer_id=cust_id,
                created_by_user_id=user.id,
                status="sent",
                subtotal=Decimal("125000.00"),
                total_amount=Decimal("125000.00"),
                currency="USD",
            )
            db_session.add(quotation)

            q_item = QuotationItem(
                id=uuid.uuid4(),
                quotation_id=q_id,
                product_id=prod_id,
                product_name="Enterprise Server R740",
                sku=f"HW-R740-{org_id.hex[:4]}",
                quantity=Decimal("50.00"),
                unit_price=Decimal("2500.00"),
                unit_cost=Decimal("1500.00"),
                line_total=Decimal("125000.00"),
            )
            db_session.add(q_item)
            await db_session.commit()

            # Phase 39: Smart Allocation (Priority 1 WH1 gets 30, Priority 2 WH2 gets 20)
            print("STEP 1: calculate_smart_warehouse_allocation")
            summary = await allocation_service.calculate_smart_warehouse_allocation(db_session, org_id, q_id)
            print("SUMMARY:", summary)
            assert summary.is_fully_allocated is True
            assert summary.total_allocated == 50
            assert len(summary.allocations) == 2

            # Phase 40: Manual Override by authorized user to allocate 50 directly to WH2
            print("STEP 2: apply_manual_fulfillment_override")
            override_req = ManualOverrideRequest(
                quotation_id=q_id,
                quotation_item_id=q_item.id,
                new_warehouse_id=wh2.id,
                allocated_quantity=50,
                reason="Customer requested single dispatch from West Coast warehouse",
            )
            override_alloc = await allocation_service.apply_manual_fulfillment_override(db_session, org_id, override_req, user)
            print("OVERRIDE:", override_alloc)
            assert override_alloc.warehouse_id == wh2.id
            assert override_alloc.allocated_quantity == 50
            assert override_alloc.allocation_strategy == "MANUAL_OVERRIDE"
        except Exception as e:
            print("ERROR IN TEST 3:", type(e), e)
            raise e


@pytest.mark.asyncio
async def test_phase_41_42_43_44_45_shipment_backorder_promise_billing():
    async with AsyncSessionLocal() as db_session:
        try:
            org_id = uuid.uuid4()
            org = Organization(id=org_id, name="Inventory Corp 4", slug=f"inv-corp-{org_id.hex[:6]}")
            db_session.add(org)

            user_id = uuid.uuid4()
            user = User(
                id=user_id,
                organization_id=org_id,
                email=f"manager-{user_id.hex[:6]}@invcorp.com",
                password_hash=hash_password("Password123!"),
                full_name="Inventory Manager",
                is_admin=True,
                is_active=True,
            )
            db_session.add(user)

            cust_id = uuid.uuid4()
            customer = Customer(
                id=cust_id,
                organization_id=org_id,
                name="Apex Logistics LLC",
                email=f"contact-{org_id.hex[:4]}@apex.com",
                is_active=True,
            )
            db_session.add(customer)

            prod_id = uuid.uuid4()
            product = Product(
                id=prod_id,
                organization_id=org_id,
                name="Enterprise Server R740",
                sku=f"HW-R740-{org_id.hex[:4]}",
                unit_price=Decimal("2500.00"),
                unit_cost=Decimal("1500.00"),
                currency="USD",
                is_active=True,
            )
            db_session.add(product)

            sub_prod_id = uuid.uuid4()
            sub_product = Product(
                id=sub_prod_id,
                organization_id=org_id,
                name="Annual Maintenance Subscription Plan",
                sku=f"SUB-MAINT-{org_id.hex[:4]}",
                unit_price=Decimal("300.00"),
                unit_cost=Decimal("50.00"),
                currency="USD",
                is_active=True,
            )
            db_session.add(sub_product)

            wh1 = Warehouse(id=uuid.uuid4(), organization_id=org_id, code=f"WH1-{org_id.hex[:4]}", name="East Coast Hub", priority=1, is_active=True)
            db_session.add(wh1)
            await db_session.commit()

            # Add stock: WH1=40 units
            await inventory_service.record_stock_receipt(db_session, org_id, StockReceiptRequest(warehouse_id=wh1.id, product_id=prod_id, quantity=40))

            # Create hybrid quotation: 60 Physical Servers (shortfall of 20) + 5 Annual Subscription Plans
            q_id = uuid.uuid4()
            quotation = Quotation(
                id=q_id,
                organization_id=org_id,
                quotation_number=f"QT-{org_id.hex[:6]}",
                customer_id=cust_id,
                created_by_user_id=user.id,
                status="accepted",
                subtotal=Decimal("151500.00"),
                total_amount=Decimal("151500.00"),
                currency="USD",
            )
            db_session.add(quotation)

            item1 = QuotationItem(
                id=uuid.uuid4(),
                quotation_id=q_id,
                product_id=prod_id,
                product_name="Enterprise Server R740",
                sku=f"HW-R740-{org_id.hex[:4]}",
                quantity=Decimal("60.00"),
                unit_price=Decimal("2500.00"),
                unit_cost=Decimal("1500.00"),
                line_total=Decimal("150000.00"),
            )
            item2 = QuotationItem(
                id=uuid.uuid4(),
                quotation_id=q_id,
                product_id=sub_prod_id,
                product_name="Annual Maintenance Subscription Plan",
                sku=f"SUB-MAINT-{org_id.hex[:4]}",
                quantity=Decimal("5.00"),
                unit_price=Decimal("300.00"),
                unit_cost=Decimal("50.00"),
                line_total=Decimal("1500.00"),
            )
            db_session.add_all([item1, item2])
            await db_session.commit()

            # Reserve stock & allocate available 40 units
            await reservation_service.reserve_stock_for_quotation(db_session, org_id, q_id)
            await allocation_service.calculate_smart_warehouse_allocation(db_session, org_id, q_id)

            # Phase 41: Create Shipment for allocated 40 units
            shp_req = ShipmentCreateRequest(
                quotation_id=q_id,
                warehouse_id=wh1.id,
                carrier="FedEx Express",
                tracking_number="FX-99887766",
            )
            shipment = await shipment_service.create_shipment_from_allocation(db_session, org_id, shp_req)
            assert shipment.shipment_number.startswith("SHP-")
            assert shipment.status == "DRAFT"

            # Phase 42 & 43: Backorder Engine for shortfall (20 units remaining)
            shortfalls = {item1.id: 20}
            backorders = await backorder_service.create_backorders_for_quotation_shortfall(db_session, org_id, q_id, shortfalls)
            assert len(backorders) == 1
            assert backorders[0].remaining_quantity == 20
            assert backorders[0].status == "OPEN"

            # Test backorder consolidation query
            consolidation = await backorder_service.get_customer_backorder_consolidation(db_session, org_id, cust_id)
            assert consolidation.total_open_backorders == 1
            assert consolidation.total_remaining_quantity == 20

            # Phase 44: Delivery Promise Calculation (detects AT_RISK or DELAYED due to backorder shortfall)
            promise = await delivery_service.calculate_or_update_delivery_promise(db_session, org_id, q_id)
            assert promise.status in ["AT_RISK", "DELAYED"]
            assert promise.promised_date is not None

            # Phase 45: Hybrid Billing Classification (Physical Goods $150,000 + Subscription $1,500 = HYBRID)
            billing = await billing_service.classify_quotation_hybrid_billing(db_session, org_id, q_id)
            assert billing.commercial_model == "HYBRID"
            assert billing.one_time_total == Decimal("150000.00")
            assert billing.recurring_monthly_total == Decimal("1500.00")
        except Exception as e:
            print("ERROR IN TEST 4:", type(e), e)
            raise e
