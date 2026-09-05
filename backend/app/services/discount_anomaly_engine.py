import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.quotation import Quotation, QuotationItem
from app.models.customer import Customer
from app.schemas.health_monitoring import DiscountAnomalyItem, DiscountAnomaliesResponse


class DiscountAnomalyEngine:
    """Phase 55 — Authoritative Discount Anomaly Monitoring Engine.
    
    Monitors unusual commercial discount behavior by comparing a quotation's blended discount
    against historical customer baselines and organization-wide baselines.
    
    Distinguishes risk (governance policy limits) from anomaly (statistically unusual variance).
    Safely handles low-volume historical data using confidence and sample-size flags.
    """

    @staticmethod
    async def monitor_discount_anomalies(
        session: AsyncSession,
        organization_id: uuid.UUID,
        variance_threshold_percent: Decimal = Decimal("15.00"),
    ) -> DiscountAnomaliesResponse:
        now_utc = datetime.now(timezone.utc)

        # 1. Fetch organization-wide baseline average discount
        all_q_stmt = select(Quotation).where(
            Quotation.organization_id == organization_id,
            Quotation.status.in_(["accepted", "sent", "converted"]),
        )
        all_quotes = list((await session.execute(all_q_stmt)).scalars().all())

        if all_quotes:
            org_discounts = []
            for q in all_quotes:
                if q.subtotal > Decimal("0.00"):
                    disc_pct = (q.discount_amount / q.subtotal) * Decimal("100.00")
                    org_discounts.append(disc_pct)
            org_avg_discount = sum(org_discounts, Decimal("0.00")) / Decimal(len(org_discounts)) if org_discounts else Decimal("0.00")
        else:
            org_avg_discount = Decimal("5.00")  # Default org baseline assumption

        # 2. Evaluate active draft/sent/priced quotations
        active_q_stmt = select(Quotation).options(selectinload(Quotation.items)).where(
            Quotation.organization_id == organization_id,
            Quotation.status.in_(["draft", "priced", "sent"]),
        )
        active_quotes = list((await session.execute(active_q_stmt)).scalars().all())

        anomalies: List[DiscountAnomalyItem] = []

        for q in active_quotes:
            if q.subtotal == Decimal("0.00"):
                continue

            blended_disc_pct = (q.discount_amount / q.subtotal) * Decimal("100.00")

            # Historical customer baseline
            cust_q_stmt = select(Quotation).where(
                Quotation.organization_id == organization_id,
                Quotation.customer_id == q.customer_id,
                Quotation.id != q.id,
                Quotation.status.in_(["accepted", "converted"]),
            )
            cust_past_quotes = list((await session.execute(cust_q_stmt)).scalars().all())

            cust_sample_size = len(cust_past_quotes)
            insufficient_data = cust_sample_size < 2

            if not insufficient_data:
                cust_discounts = [
                    (pq.discount_amount / pq.subtotal) * Decimal("100.00")
                    for pq in cust_past_quotes if pq.subtotal > Decimal("0.00")
                ]
                cust_avg_discount = sum(cust_discounts, Decimal("0.00")) / Decimal(len(cust_discounts)) if cust_discounts else org_avg_discount
                baseline_reference = cust_avg_discount
            else:
                cust_avg_discount = None
                baseline_reference = org_avg_discount

            variance = blended_disc_pct - baseline_reference

            # Anomaly scoring logic
            if variance >= Decimal("25.00"):
                score = 90
                severity = "CRITICAL"
            elif variance >= Decimal("15.00"):
                score = 75
                severity = "ANOMALOUS"
            elif variance >= Decimal("8.00"):
                score = 50
                severity = "WATCH"
            else:
                score = 10
                severity = "NORMAL"

            if severity in ("WATCH", "ANOMALOUS", "CRITICAL"):
                # Customer name lookup
                cust_stmt = select(Customer).where(Customer.id == q.customer_id, Customer.organization_id == organization_id)
                customer = (await session.execute(cust_stmt)).scalar_one_or_none()
                cust_name = customer.name if customer else "Unknown"

                evidence: List[str] = [
                    f"Quotation discount is {blended_disc_pct:.2f}% (Total discount: ${q.discount_amount:,.2f})",
                    f"Baseline discount reference: {baseline_reference:.2f}% (Variance: +{variance:.2f}%)",
                ]

                if insufficient_data:
                    evidence.append(f"Insufficient customer historical sample size ({cust_sample_size} past quotes); compared against org baseline.")
                else:
                    evidence.append(f"Customer historical baseline based on {cust_sample_size} past accepted quotation(s).")

                if q.discount_amount > Decimal("10000.00"):
                    evidence.append(f"High absolute discount dollar impact: ${q.discount_amount:,.2f}")

                anomalies.append(DiscountAnomalyItem(
                    quotation_id=q.id,
                    quotation_number=q.quotation_number,
                    customer_id=q.customer_id,
                    customer_name=cust_name,
                    blended_discount_percent=Decimal(f"{blended_disc_pct:.2f}"),
                    historical_customer_avg_discount=Decimal(f"{cust_avg_discount:.2f}") if cust_avg_discount is not None else None,
                    historical_product_avg_discount=None,
                    organization_avg_discount=Decimal(f"{org_avg_discount:.2f}"),
                    variance_percent=Decimal(f"{variance:.2f}"),
                    anomaly_score=score,
                    severity=severity,
                    insufficient_historical_data=insufficient_data,
                    sample_size=cust_sample_size,
                    evidence=evidence,
                    created_at=q.created_at or now_utc,
                ))

        anomalies.sort(key=lambda a: a.anomaly_score, reverse=True)

        return DiscountAnomaliesResponse(
            anomalies=anomalies,
            anomalous_count=len(anomalies),
            generated_at=now_utc,
        )


discount_anomaly_engine = DiscountAnomalyEngine()
