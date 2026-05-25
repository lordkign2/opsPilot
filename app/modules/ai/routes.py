"""
OpsPilot — AI Module: Routes.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.modules.auth.dependencies import CurrentBusinessId
from app.modules.ai.dependencies import AIServiceDep
from app.modules.ai.schemas import (
    AIChatRequest,
    AIChatResponse,
    AISummaryRequest,
    AISummaryResponse,
    AIRecommendationsResponse,
    AICustomerInsightsRequest,
    AICustomerInsightsResponse,
)
from app.shared.response import success_response

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/chat", response_model=None)
async def chat_with_assistant(
    payload: AIChatRequest,
    business_id: CurrentBusinessId,
    ai_service: AIServiceDep,
):
    """Interact session-less with the AI business operations assistant."""
    reply = await ai_service.chat_with_assistant(business_id, payload.message)
    return success_response(
        data=AIChatResponse(reply=reply).model_dump(),
        message="AI assistant response generated successfully."
    )


@router.post("/summary", response_model=None)
async def generate_business_summary(
    payload: AISummaryRequest,
    business_id: CurrentBusinessId,
    ai_service: AIServiceDep,
):
    """Generate professional workspace performance summaries."""
    summary = await ai_service.generate_business_summary(business_id, payload.timeframe)
    return success_response(
        data=AISummaryResponse(summary=summary).model_dump(),
        message="Operations summary generated successfully."
    )


@router.post("/recommendations", response_model=None)
async def generate_recommendations(
    business_id: CurrentBusinessId,
    ai_service: AIServiceDep,
):
    """Get operational optimization recommendations."""
    recs = await ai_service.generate_recommendations(business_id)
    return success_response(
        data=AIRecommendationsResponse(recommendations=recs).model_dump(),
        message="Operational recommendations compiled successfully."
    )


@router.post("/customer-insights", response_model=None)
async def generate_customer_insights(
    payload: AICustomerInsightsRequest,
    business_id: CurrentBusinessId,
    ai_service: AIServiceDep,
):
    """Analyze behavior segmentation and churn likelihood for a specific customer."""
    insights = await ai_service.generate_customer_insights(business_id, payload.customer_id)
    return success_response(
        data=AICustomerInsightsResponse(
            customer_id=payload.customer_id,
            insights=insights
        ).model_dump(),
        message="Customer behavioral insights compiled successfully."
    )
