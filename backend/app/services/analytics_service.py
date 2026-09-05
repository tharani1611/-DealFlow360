import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.reporting_engine import reporting_engine
from app.services.deal_health_engine import deal_health_engine
from app.services.stalled_quote_engine import stalled_quote_engine
from app.services.discount_anomaly_engine import discount_anomaly_engine
from app.services.delivery_slippage_engine import delivery_slippage_engine
from app.services.nudge_engine import nudge_engine


class AnalyticsService:
    """Phase 59 — Authoritative Analytics Service.
    
    Consolidates reporting, health telemetry, monitoring events, and nudges into unified
    executive dashboard payloads. Uses database aggregations and limit pagination.
    """

    @staticmethod
    async def get_dashboard_executive_analytics(
        session: AsyncSession,
        organization_id: uuid.UUID,
        period: str = "this_month",
    ) -> Dict[str, Any]:
        # 1. Executive Reporting Summary
        report = await reporting_engine.generate_executive_report(session, organization_id, period)

        # 2. Stalled Quotes Count & Highlights
        stalled_resp = await stalled_quote_engine.detect_stalled_quotes(session, organization_id)

        # 3. Discount Anomalies Count & Highlights
        disc_resp = await discount_anomaly_engine.monitor_discount_anomalies(session, organization_id)

        # 4. Delivery Slippage Count & Highlights
        deliv_resp = await delivery_slippage_engine.monitor_delivery_slippage(session, organization_id)

        # 5. Active Nudges
        nudges = await nudge_engine.list_nudges(session, organization_id, status="OPEN")

        return {
            "period": period,
            "reporting": report.model_dump(mode="json"),
            "monitoring_summary": {
                "stalled_quotes_count": stalled_resp.total_stalled_count,
                "stalled_quotes_value": str(stalled_resp.total_stalled_value),
                "discount_anomalies_count": disc_resp.anomalous_count,
                "delivery_at_risk_count": deliv_resp.at_risk_count,
                "delivery_delayed_count": deliv_resp.delayed_count,
                "open_nudges_count": len(nudges),
            },
            "top_stalled_quotes": [sq.model_dump(mode="json") for sq in stalled_resp.stalled_quotes[:3]],
            "top_discount_anomalies": [da.model_dump(mode="json") for da in disc_resp.anomalies[:3]],
            "top_delivery_risks": [dr.model_dump(mode="json") for dr in deliv_resp.deliveries[:3]],
            "top_open_nudges": [n.id for n in nudges[:5]],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }


analytics_service = AnalyticsService()
