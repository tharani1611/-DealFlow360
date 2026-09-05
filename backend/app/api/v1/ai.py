import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.ai import (
    CustomerSummaryResponse,
    DealAnalysisResponse,
    NextActionResponse,
    ActivityInsightResponse,
    AssistantRequest,
    AssistantResponse
)
from app.ai.service import ai_service

router = APIRouter()


@router.post(
    "/customers/{customer_id}/summary",
    response_model=CustomerSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="AI Customer Relationship Summary",
    description="Generates concise AI summary and health estimation for a specific customer."
)
async def get_customer_ai_summary(
    customer_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> CustomerSummaryResponse:
    """Generates AI customer summary."""
    return await ai_service.summarize_customer(db, current_user.organization_id, customer_id)


@router.post(
    "/deals/{deal_id}/analysis",
    response_model=DealAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="AI Deal Analysis & Risk Evaluation",
    description="Generates AI risk evaluation, positive signals, and advisory sales actions for a deal."
)
async def analyze_deal(
    deal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> DealAnalysisResponse:
    """Generates AI deal analysis."""
    return await ai_service.analyze_deal(db, current_user.organization_id, deal_id)


@router.post(
    "/deals/{deal_id}/next-action",
    response_model=NextActionResponse,
    status_code=status.HTTP_200_OK,
    summary="AI Recommended Next Best Action",
    description="Recommends the single most effective next sales action for a deal."
)
async def recommend_next_action(
    deal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> NextActionResponse:
    """Recommends next best action."""
    return await ai_service.recommend_next_action(db, current_user.organization_id, deal_id)


@router.post(
    "/deals/{deal_id}/activity-insights",
    response_model=ActivityInsightResponse,
    status_code=status.HTTP_200_OK,
    summary="AI Deal Activity & Engagement Insights",
    description="Analyzes deal activity engagement velocity, overdue items, and follow-up recommendations."
)
async def analyze_deal_activities(
    deal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ActivityInsightResponse:
    """Analyzes deal activity insights."""
    return await ai_service.analyze_deal_activities(db, current_user.organization_id, deal_id)


@router.post(
    "/assistant",
    response_model=AssistantResponse,
    status_code=status.HTTP_200_OK,
    summary="AI General CRM Assistant",
    description="Answers natural language user questions using tenant-scoped CRM context."
)
async def answer_assistant_question(
    payload: AssistantRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AssistantResponse:
    """Answers CRM assistant questions."""
    return await ai_service.answer_assistant_question(db, current_user.organization_id, payload.question)
