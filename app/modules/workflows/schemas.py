"""
OpsPilot — Workflow Automation Module: Pydantic Validation Schemas.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.workflows.models import LogDepth


class ConditionOperator(str, enum.Enum):
    """Supported logical comparison operators for condition evaluation."""
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GE = "ge"
    LT = "lt"
    LE = "le"
    CONTAINS = "contains"
    IS_TRUE = "is_true"
    IS_FALSE = "is_false"


class ActionType(str, enum.Enum):
    """Supported side-effect task executors."""
    SEND_NOTIFICATION = "send_notification"
    GENERATE_AI_MESSAGE = "generate_ai_message"
    SEND_WHATSAPP = "send_whatsapp"
    SEND_EMAIL = "send_email"
    CREATE_TASK = "create_task"


class WorkflowCondition(BaseModel):
    """Validates individual rule comparison blocks."""
    field: str = Field(..., description="JSON path or variable key from trigger payload (e.g. 'amount')")
    operator: ConditionOperator = Field(..., description="The logic comparator")
    value: Any = Field(default=None, description="Value to match against (ignored for boolean comparators)")


class WorkflowAction(BaseModel):
    """Validates individual action blocks."""
    type: ActionType = Field(..., description="Type of task to trigger")
    params: dict[str, Any] = Field(default_factory=dict, description="Task configurations support dynamic templates, e.g. {{order_id}}")


class WorkflowCreate(BaseModel):
    """Validates creation payload."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    trigger_type: str = Field(..., min_length=1, max_length=50)  # e.g., 'order.created'
    conditions: list[WorkflowCondition] = Field(default_factory=list)
    actions: list[WorkflowAction] = Field(default_factory=list)
    log_depth: LogDepth = Field(default=LogDepth.ALL)
    is_active: bool = Field(default=True)


class WorkflowUpdate(BaseModel):
    """Validates partial updates."""
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    trigger_type: str | None = Field(default=None, min_length=1, max_length=50)
    conditions: list[WorkflowCondition] | None = Field(default=None)
    actions: list[WorkflowAction] | None = Field(default=None)
    log_depth: LogDepth | None = Field(default=None)
    is_active: bool | None = Field(default=None)


class WorkflowResponse(BaseModel):
    """Serializer response payload."""
    id: UUID
    business_id: UUID
    name: str
    description: str | None
    trigger_type: str
    conditions: list[WorkflowCondition]
    actions: list[WorkflowAction]
    log_depth: LogDepth
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkflowExecutionLogResponse(BaseModel):
    """Serializer response for automation runs."""
    id: UUID
    workflow_id: UUID
    business_id: UUID
    status: str
    error_message: str | None
    created_at: datetime

    class Config:
        from_attributes = True
