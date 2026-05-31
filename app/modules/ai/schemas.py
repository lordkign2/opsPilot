"""
OpsPilot — AI Module: Schemas.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class AIChatRequest(BaseModel):
    message: str = Field(..., description="Message payload to send to the AI business assistant.")


class AIChatResponse(BaseModel):
    reply: str = Field(..., description="AI assistant generated textual response.")


class AISummaryRequest(BaseModel):
    timeframe: str = Field("daily", description="Format timeframe, e.g. daily, weekly, monthly.")


class AISummaryResponse(BaseModel):
    summary: str = Field(..., description="AI generated markdown performance and sales summary.")


class AIRecommendation(BaseModel):
    title: str
    description: str
    action_type: str
    impact_score: int = Field(..., ge=1, le=5)
    metadata: dict | None = None


class AIRecommendationsResponse(BaseModel):
    recommendations: list[AIRecommendation] = Field(
        ..., description="Identified operations alerts and customer follow-up actions."
    )


class AICustomerInsightsRequest(BaseModel):
    customer_id: uuid.UUID = Field(..., description="Target customer ID for segmentation and behavior insights.")


class AICustomerInsightsResponse(BaseModel):
    customer_id: uuid.UUID
    insights: str = Field(
        ...,
        description="Behavior analysis, churn likelihood, and personalized action recommendations.",
    )
