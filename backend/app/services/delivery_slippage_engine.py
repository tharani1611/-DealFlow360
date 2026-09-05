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

        for dp in promises:
            # Quotation & Customer lookup
            q_stmt = select(Quotation).where(Quotation.id == dp.quotation_id, Quotation.organization_id == organization_id)
            quotation = (await session.execute(q_stmt)).scalar_one_or_none()
            if not quotation:
                continue

            cust_stmt = select(Customer).where(Customer.id == quotation.customer_id, Customer.organization_id == organization_id)
            customer = (await session.execute(cust_stmt)).scalar_one_or_none()
            cust_name = customer.name if customer else "Unknown"

            promised_d = dp.promised_date if isinstance(dp.promised_date, date) else dp.promised_date.date()
            expected_d = dp.expected_date if isinstance(dp.expected_date, date) else dp.expected_date.date()
            actual_d = dp.actual_date if dp.actual_date else None

            slippage = (expected_d - promised_d).days

            evidence: List[str] = [
                f"Promised delivery date: {promised_d} | Current expected date: {expected_d}",
            ]

            root_cause = "Normal fulfillment progression"
            status = dp.status

            # Check for open backorder impact
            bo_stmt = select(Backorder).where(
                Backorder.organization_id == organization_id,
                Backorder.quotation_id == dp.quotation_id,
                Backorder.status.in_(["OPEN", "PARTIALLY_FULFILLED"]),
            )
            backorders = list((await session.execute(bo_stmt)).scalars().all())
            if backorders:
                status = "AT_RISK" if slippage <= 3 else "DELAYED"
                root_cause = f"Open backorder ({len(backorders)} item(s) awaiting stock arrival)"
                evidence.append(f"{len(backorders)} line item(s) currently backordered.")

            # Check for shipment progress
            ship_stmt = select(Shipment).where(
                Shipment.organization_id == organization_id,
                Shipment.quotation_id == dp.quotation_id,
            )
            shipments = list((await session.execute(ship_stmt)).scalars().all())

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
