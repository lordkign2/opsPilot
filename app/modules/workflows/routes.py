"""
OpsPilot — Workflow Automation Module: APIRouter Endpoints.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.modules.auth.dependencies import CurrentBusinessId
from app.modules.workflows.models import Workflow, WorkflowExecutionLog
from app.modules.workflows.repository import WorkflowExecutionLogRepository, WorkflowRepository
from app.modules.workflows.schemas import WorkflowCreate, WorkflowResponse, WorkflowUpdate
from app.modules.workflows.triggers import invalidate_workflow_cache
from app.shared.response import success_response

router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.post("/", response_model=dict[str, Any])
async def create_workflow(
    payload: WorkflowCreate,
    business_id: CurrentBusinessId,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Create a new operational workflow rule.

    Automatically invalidates the Redis active cache for the specified trigger event.
    """
    repo = WorkflowRepository(db)
    
    # Instantiate new rule structure
    workflow = Workflow(
        name=payload.name,
        description=payload.description,
        trigger_type=payload.trigger_type,
        is_active=payload.is_active,
        conditions=[c.model_dump() for c in payload.conditions],
        actions=[a.model_dump() for a in payload.actions],
        log_depth=payload.log_depth.value,
        business_id=business_id,
    )

    created_w = await repo.create(workflow)
    await db.commit()

    # Clear active Redis caches
    await invalidate_workflow_cache(business_id, payload.trigger_type)

    return success_response(
        data=WorkflowResponse.from_orm(created_w).model_dump(),
        message="Workflow created successfully.",
    )


@router.get("/", response_model=dict[str, Any])
async def list_workflows(
    business_id: CurrentBusinessId,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    List all workflow automation rules for the active business workspace.
    """
    repo = WorkflowRepository(db)
    workflows = await repo.get_by_business(business_id, limit=100)
    
    serialized = [WorkflowResponse.from_orm(w).model_dump() for w in workflows]
    return success_response(data=serialized)


@router.get("/logs", response_model=dict[str, Any])
async def list_execution_logs(
    business_id: CurrentBusinessId,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Fetch the execution audit logs for active business rule runs.
    """
    repo = WorkflowExecutionLogRepository(db)
    logs = await repo.get_by_business(
        business_id=business_id,
        offset=offset,
        limit=limit,
        order_by="created_at",
        descending=True,
    )
    
    serialized = []
    for log in logs:
        serialized.append({
            "id": str(log.id),
            "workflow_id": str(log.workflow_id),
            "workflow_name": log.workflow.name if log.workflow else "Deleted Workflow",
            "business_id": str(log.business_id),
            "status": log.status,
            "error_message": log.error_message,
            "created_at": log.created_at.isoformat(),
        })

    return success_response(data=serialized)


@router.patch("/{workflow_id}", response_model=dict[str, Any])
async def update_workflow(
    workflow_id: uuid.UUID,
    payload: WorkflowUpdate,
    business_id: CurrentBusinessId,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Update workflow configurations dynamically.
    """
    repo = WorkflowRepository(db)
    workflow = await repo.get_one_by(id=workflow_id, business_id=business_id)
    if not workflow:
        raise NotFoundError("Workflow not found.")

    updates: dict[str, Any] = {}
    if payload.name is not None:
        updates["name"] = payload.name
    if payload.description is not None:
        updates["description"] = payload.description
    if payload.trigger_type is not None:
        # Invalidate old trigger cache first
        await invalidate_workflow_cache(business_id, workflow.trigger_type)
        updates["trigger_type"] = payload.trigger_type
    if payload.is_active is not None:
        updates["is_active"] = payload.is_active
    if payload.log_depth is not None:
        updates["log_depth"] = payload.log_depth.value
    if payload.conditions is not None:
        updates["conditions"] = [c.model_dump() for c in payload.conditions]
    if payload.actions is not None:
        updates["actions"] = [a.model_dump() for a in payload.actions]

    updated_w = await repo.update(workflow, **updates)
    await db.commit()

    # Clear active Redis caches
    await invalidate_workflow_cache(business_id, updated_w.trigger_type)

    return success_response(
        data=WorkflowResponse.from_orm(updated_w).model_dump(),
        message="Workflow updated successfully.",
    )


@router.delete("/{workflow_id}", response_model=dict[str, Any])
async def delete_workflow(
    workflow_id: uuid.UUID,
    business_id: CurrentBusinessId,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Delete a workflow rule.
    """
    repo = WorkflowRepository(db)
    workflow = await repo.get_one_by(id=workflow_id, business_id=business_id)
    if not workflow:
        raise NotFoundError("Workflow not found.")

    trigger_type = workflow.trigger_type
    await repo.delete(workflow)
    await db.commit()

    # Clear active Redis caches
    await invalidate_workflow_cache(business_id, trigger_type)

    return success_response(message="Workflow deleted successfully.")
