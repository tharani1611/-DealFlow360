import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.copilot import CopilotRequest, CopilotResponse, DealQARequest, DealQAResponse
from app.services.ai_sales_copilot import ai_sales_copilot_service
from app.services.deal_intelligence import deal_intelligence_service

router = APIRouter()


@router.post(
    "/chat",
    response_model=CopilotResponse,
    status_code=status.HTTP_200_OK,
    summary="AI Sales Copilot Conversation",
    description="Processes natural language sales inquiries with intent routing, context building, source transparency, and hallucination controls."
)
async def process_copilot_chat(
    payload: CopilotRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> CopilotResponse:
    """Processes AI Sales Copilot chat request."""
    return await ai_sales_copilot_service.process_copilot_inquiry(
        db, current_user.organization_id, payload
    )


@router.post(
    "/deals/{deal_id}/qa",
    response_model=DealQAResponse,
    status_code=status.HTTP_200_OK,
    summary="Deal Intelligence Q&A",
    description="Answers natural language questions about a specific deal using retrieved structured deal context."
)
async def ask_deal_question(
    deal_id: uuid.UUID,
    payload: DealQARequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> DealQAResponse:
    """Answers deal-specific natural language question."""
    return await deal_intelligence_service.answer_deal_qa(
        db, current_user.organization_id, deal_id, payload.question
    )
