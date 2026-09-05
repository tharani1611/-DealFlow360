import uuid
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fulfillment import DeliveryPromise, Shipment, Backorder
from app.models.quotation import Quotation
from app.models.customer import Customer
from app.schemas.health_monitoring import DeliverySlippageItem, DeliverySlippageResponse


class DeliverySlippageEngine:
    """Phase 56 — Authoritative Delivery Slippage Monitoring Engine.
    
    Monitors delivery promises, shipment statuses, backorders, and stock allocation.
    Determines delivery health classification (ON_TRACK, AT_RISK, DELAYED, DELIVERED)
    and identifies root causes (unfulfilled inventory, open backorders, uncreated shipments, carrier delays).
    """

    @staticmethod
    async def monitor_delivery_slippage(
        session: AsyncSession,
        organization_id: uuid.UUID,
    ) -> DeliverySlippageResponse:
        now_utc = datetime.now(timezone.utc)
        today_utc = now_utc.date()

        # 1. Fetch delivery promises
        dp_stmt = select(DeliveryPromise).where(DeliveryPromise.organization_id == organization_id)
        promises = list((await session.execute(dp_stmt)).scalars().all())

        deliveries: List[DeliverySlippageItem] = []
        at_risk_count = 0
        delayed_count = 0

        if not promises:
            return DeliverySlippageResponse(
                organization_id=organization_id,
                total_promises_count=0,
                at_risk_count=0,
                delayed_count=0,
                deliveries=[],
                generated_at=now_utc,
            )

        quote_ids = [dp.quotation_id for dp in promises]

        # Batch prefetch quotations
        quote_map = {}
        if quote_ids:
            q_stmt = select(Quotation).where(Quotation.id.in_(quote_ids), Quotation.organization_id == organization_id)
            quotes = list((await session.execute(q_stmt)).scalars().all())
            quote_map = {q.id: q for q in quotes}

        # Batch prefetch customers
        cust_ids = list({q.customer_id for q in quote_map.values() if q.customer_id})
        cust_map = {}
        if cust_ids:
            c_stmt = select(Customer.id, Customer.name).where(
                Customer.organization_id == organization_id,
                Customer.id.in_(cust_ids),
            )
            cust_rows = (await session.execute(c_stmt)).all()
            cust_map = {r.id: r.name for r in cust_rows}

        # Batch prefetch open backorders
        bo_map = {}
        if quote_ids:
            bo_stmt = select(Backorder).where(
                Backorder.organization_id == organization_id,
                Backorder.quotation_id.in_(quote_ids),
                Backorder.status.in_(["OPEN", "PARTIALLY_FULFILLED"]),
            )
            bo_rows = list((await session.execute(bo_stmt)).scalars().all())
            for bo in bo_rows:
                bo_map.setdefault(bo.quotation_id, []).append(bo)

        # Batch prefetch shipments
        ship_map = {}
        if quote_ids:
            ship_stmt = select(Shipment).where(
                Shipment.organization_id == organization_id,
                Shipment.quotation_id.in_(quote_ids),
            )
            ship_rows = list((await session.execute(ship_stmt)).scalars().all())
            for s in ship_rows:
                ship_map.setdefault(s.quotation_id, []).append(s)

        for dp in promises:
            quotation = quote_map.get(dp.quotation_id)
            if not quotation:
                continue

            cust_name = cust_map.get(quotation.customer_id, "Unknown")

            promised_d = dp.promised_date if isinstance(dp.promised_date, date) else dp.promised_date.date()
            expected_d = dp.expected_date if isinstance(dp.expected_date, date) else dp.expected_date.date()
            actual_d = dp.actual_date if dp.actual_date else None

            slippage = (expected_d - promised_d).days

            evidence: List[str] = [
                f"Promised delivery date: {promised_d} | Current expected date: {expected_d}",
            ]

            root_cause = "Normal fulfillment progression"
            status = dp.status

            backorders = bo_map.get(dp.quotation_id, [])
            if backorders:
                status = "AT_RISK" if slippage <= 3 else "DELAYED"
                root_cause = f"Open backorder ({len(backorders)} item(s) awaiting stock arrival)"
                evidence.append(f"{len(backorders)} line item(s) currently backordered.")

            shipments = ship_map.get(dp.quotation_id, [])

            if not shipments and not backorders and today_utc > (promised_d - timedelta(days=3)):
                if status != "DELIVERED":
                    status = "AT_RISK"
                    root_cause = "Shipment creation pending close to promised delivery window"
                    evidence.append("No warehouse shipment created yet.")

            if expected_d > promised_d:
                if status != "DELIVERED":
                    status = "DELAYED" if slippage >= 5 else "AT_RISK"
                    if root_cause == "Normal fulfillment progression":
                        root_cause = f"Fulfillment schedule revised (+{slippage} days delay)"

            if status == "AT_RISK":
                at_risk_count += 1
            elif status == "DELAYED":
                delayed_count += 1

            deliveries.append(DeliverySlippageItem(
                delivery_promise_id=dp.id,
                quotation_id=dp.quotation_id,
                quotation_number=quotation.quotation_number,
                customer_id=quotation.customer_id,
                customer_name=cust_name,
                shipment_id=dp.shipment_id,
                backorder_id=dp.backorder_id,
                promised_date=promised_d,
                expected_date=expected_d,
                actual_date=actual_d,
                slippage_days=slippage,
                status=status,
                root_cause=root_cause,
                evidence=evidence,
            ))

        deliveries.sort(key=lambda d: d.slippage_days, reverse=True)

        return DeliverySlippageResponse(
            deliveries=deliveries,
            at_risk_count=at_risk_count,
            delayed_count=delayed_count,
            generated_at=now_utc,
        )


delivery_slippage_engine = DeliverySlippageEngine()
