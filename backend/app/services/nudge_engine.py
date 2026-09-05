import uuid
import hashlib
from datetime import datetime, timezone, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException, BusinessRuleViolationException
from app.models.nudge import Nudge, NudgeHistory
from app.models.user import User
from app.schemas.health_monitoring import NudgeResponse, NudgeHistoryResponse
from app.services.deal_health_engine import deal_health_engine
from app.services.stalled_quote_engine import stalled_quote_engine
from app.services.discount_anomaly_engine import discount_anomaly_engine
from app.services.delivery_slippage_engine import delivery_slippage_engine


class NudgeEngine:
    """Phase 57 — Controlled Nudge & Escalation Engine.
    
    Consumes telemetry signals from Phases 53-56 to generate actionable nudges.
    Enforces idempotency and deduplication via sha256 hashes.
    Manages complete lifecycle: OPEN -> ACKNOWLEDGED -> COMPLETED / DISMISSED -> ESCALATED.
    """

    @staticmethod
    def generate_dedup_hash(organization_id: uuid.UUID, nudge_type: str, entity_id: uuid.UUID, window_key: Optional[str] = None) -> str:
        w_key = window_key or datetime.now(timezone.utc).strftime("%Y-%m-%W")  # Weekly window deduplication default
        raw = f"{organization_id}:{nudge_type}:{entity_id}:{w_key}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    async def create_nudge_if_not_exists(
        session: AsyncSession,
        organization_id: uuid.UUID,
        nudge_type: str,
        severity: str,
        title: str,
        message: str,
        entity_type: str,
        entity_id: uuid.UUID,
        action_payload: Optional[Dict[str, Any]] = None,
        assigned_user_id: Optional[uuid.UUID] = None,
    ) -> Optional[Nudge]:
        dedup_hash = NudgeEngine.generate_dedup_hash(organization_id, nudge_type, entity_id)

        # Check existing nudge with same hash
        stmt = select(Nudge).where(Nudge.organization_id == organization_id, Nudge.dedup_hash == dedup_hash)
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            return None

        now_utc = datetime.now(timezone.utc)
        nudge = Nudge(
            organization_id=organization_id,
            nudge_type=nudge_type,
            severity=severity,
            title=title,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id,
            dedup_hash=dedup_hash,
            status="OPEN",
            assigned_user_id=assigned_user_id,
            action_payload=action_payload,
            created_at=now_utc,
            updated_at=now_utc,
        )
        session.add(nudge)
        await session.flush()

        history_item = NudgeHistory(
            organization_id=organization_id,
            nudge_id=nudge.id,
            from_status=None,
            to_status="OPEN",
            notes="Nudge created deterministically from system monitoring telemetry.",
        )
        session.add(history_item)
        await session.commit()
        return nudge

    @staticmethod
    async def evaluate_and_generate_system_nudges(
        session: AsyncSession,
        organization_id: uuid.UUID,
    ) -> List[Nudge]:
        created_nudges: List[Nudge] = []

        # 1. Stalled Quotes signals
        stalled_resp = await stalled_quote_engine.detect_stalled_quotes(session, organization_id)
        for sq in stalled_resp.stalled_quotes:
            n = await NudgeEngine.create_nudge_if_not_exists(
                session,
                organization_id=organization_id,
                nudge_type="QUOTE_STALLED",
                severity="CRITICAL" if sq.stall_category == "CRITICAL" else "WARNING",
                title=f"Stalled Quotation {sq.quotation_number}",
                message=f"Quotation for customer '{sq.customer_name}' is inactive for {sq.days_inactive} days. {sq.stall_reason}",
                entity_type="quotation",
                entity_id=sq.quotation_id,
                action_payload={"quotation_number": sq.quotation_number, "customer_name": sq.customer_name},
            )
            if n:
                created_nudges.append(n)

        # 2. Discount Anomalies signals
        disc_resp = await discount_anomaly_engine.monitor_discount_anomalies(session, organization_id)
        for da in disc_resp.anomalies:
            if da.severity in ("ANOMALOUS", "CRITICAL"):
                n = await NudgeEngine.create_nudge_if_not_exists(
                    session,
                    organization_id=organization_id,
                    nudge_type="DISCOUNT_ANOMALY",
                    severity="CRITICAL" if da.severity == "CRITICAL" else "WARNING",
                    title=f"Unusual Discount Anomaly on {da.quotation_number}",
                    message=f"Quotation for '{da.customer_name}' has a blended discount of {da.blended_discount_percent}% (+{da.variance_percent}% above baseline).",
                    entity_type="quotation",
                    entity_id=da.quotation_id,
                    action_payload={"blended_discount_percent": str(da.blended_discount_percent), "variance_percent": str(da.variance_percent)},
                )
                if n:
                    created_nudges.append(n)

        # 3. Delivery Slippage signals
        deliv_resp = await delivery_slippage_engine.monitor_delivery_slippage(session, organization_id)
        for ds in deliv_resp.deliveries:
            if ds.status in ("AT_RISK", "DELAYED"):
                n = await NudgeEngine.create_nudge_if_not_exists(
                    session,
                    organization_id=organization_id,
                    nudge_type="DELIVERY_RISK",
                    severity="URGENT" if ds.status == "DELAYED" else "WARNING",
                    title=f"Delivery Risk: Quote {ds.quotation_number}",
                    message=f"Delivery for '{ds.customer_name}' is {ds.status.replace('_', ' ')}. Promised {ds.promised_date}, expected {ds.expected_date} (+{ds.slippage_days} days). Root cause: {ds.root_cause}",
                    entity_type="quotation",
                    entity_id=ds.quotation_id,
                    action_payload={"promised_date": str(ds.promised_date), "expected_date": str(ds.expected_date), "slippage_days": ds.slippage_days},
                )
                if n:
                    created_nudges.append(n)

        return created_nudges

    @staticmethod
    async def transition_nudge_status(
        session: AsyncSession,
        organization_id: uuid.UUID,
        nudge_id: uuid.UUID,
        target_status: str,
        actor_id: Optional[uuid.UUID] = None,
        notes: Optional[str] = None,
    ) -> Nudge:
        stmt = select(Nudge).where(Nudge.id == nudge_id, Nudge.organization_id == organization_id)
        nudge = (await session.execute(stmt)).scalar_one_or_none()
        if not nudge:
            raise NotFoundException(f"Nudge {nudge_id} not found")

        valid_statuses = ["OPEN", "ACKNOWLEDGED", "COMPLETED", "DISMISSED", "ESCALATED"]
        if target_status not in valid_statuses:
            raise BusinessRuleViolationException(f"Invalid nudge status '{target_status}'. Allowed: {valid_statuses}")

        old_status = nudge.status
        nudge.status = target_status
        now_utc = datetime.now(timezone.utc)

        if target_status == "ACKNOWLEDGED":
            nudge.acknowledged_at = now_utc
        elif target_status == "COMPLETED":
            nudge.completed_at = now_utc
        elif target_status == "DISMISSED":
            nudge.dismissed_at = now_utc
        elif target_status == "ESCALATED":
            nudge.escalated_at = now_utc

        actor_name = None
        if actor_id:
            u_stmt = select(User).where(User.id == actor_id)
            user = (await session.execute(u_stmt)).scalar_one_or_none()
            if user:
                actor_name = user.full_name or user.email

        history_item = NudgeHistory(
            organization_id=organization_id,
            nudge_id=nudge.id,
            from_status=old_status,
            to_status=target_status,
            actor_id=actor_id,
            actor_name=actor_name,
            notes=notes,
        )
        session.add(history_item)
        await session.commit()
        await session.refresh(nudge)
        return nudge

    @staticmethod
    async def list_nudges(
        session: AsyncSession,
        organization_id: uuid.UUID,
        status: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> List[Nudge]:
        stmt = select(Nudge).options(selectinload(Nudge.history)).where(Nudge.organization_id == organization_id)
        if status:
            stmt = stmt.where(Nudge.status == status)
        if severity:
            stmt = stmt.where(Nudge.severity == severity)
        stmt = stmt.order_by(Nudge.created_at.desc())
        return list((await session.execute(stmt)).scalars().all())


nudge_engine = NudgeEngine()
