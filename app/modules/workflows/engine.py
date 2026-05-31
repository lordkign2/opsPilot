"""
OpsPilot — Workflow Automation Module: High-Performance Execution Engine.
"""

from __future__ import annotations

import asyncio
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.modules.workflows.actions import run_action
from app.modules.workflows.models import LogDepth, Workflow, WorkflowExecutionLog
from app.modules.workflows.repository import WorkflowExecutionLogRepository

logger = get_logger("workflows.engine")

# Optimized compiled regular expression for quick curly-bracket parameter matching
TEMPLATE_REGEX = re.compile(r"\{\{([^}]+)\}\}")


def get_nested_value(data: dict[str, Any], path: str) -> Any:
    """
    Extracts a value from a nested dictionary path, supporting dot notation (e.g., 'customer.name').
    """
    parts = path.strip().split(".")
    val = data
    for part in parts:
        if isinstance(val, dict):
            val = val.get(part)
        else:
            return None
    return val


def evaluate_condition(payload: dict[str, Any], condition: dict[str, Any]) -> bool:
    """
    Evaluates a single condition filter against the triggered payload.
    """
    field_path = condition.get("field", "")
    op = condition.get("operator", "")
    target = condition.get("value")

    val = get_nested_value(payload, field_path)

    # 1. Null checks for non-boolean comparators
    if val is None and op not in ("is_true", "is_false", "ne"):
        return False

    try:
        if op == "eq":
            return str(val).lower() == str(target).lower()
        elif op == "ne":
            return str(val).lower() != str(target).lower()
        elif op == "is_true":
            return bool(val) is True
        elif op == "is_false":
            return bool(val) is False
        elif op == "contains":
            return str(target).lower() in str(val).lower()

        # Numeric comparators (try safe float cast)
        elif op in ("gt", "ge", "lt", "le"):
            numeric_val = float(val)  # type: ignore
            numeric_target = float(target)  # type: ignore

            if op == "gt":
                return numeric_val > numeric_target
            elif op == "ge":
                return numeric_val >= numeric_target
            elif op == "lt":
                return numeric_val < numeric_target
            elif op == "le":
                return numeric_val <= numeric_target

    except (ValueError, TypeError) as e:
        logger.debug("Failed condition cast evaluation for operator '%s' on val '%s': %s", op, val, e)
        return False

    return False


def resolve_string(template: str, payload: dict[str, Any]) -> str:
    """
    Resolves a string with dynamic template keys, e.g. replacing 'Hello {{customer.name}}'
    with 'Hello Alice'.
    """

    def replacer(match: re.Match) -> str:
        path = match.group(1).strip()
        val = get_nested_value(payload, path)
        return str(val) if val is not None else ""

    return TEMPLATE_REGEX.sub(replacer, template)


def resolve_templates(params: Any, payload: dict[str, Any]) -> Any:
    """
    Recursively interpolates payload values into parameters.
    """
    if isinstance(params, str):
        return resolve_string(params, payload)
    elif isinstance(params, dict):
        return {key: resolve_templates(val, payload) for key, val in params.items()}
    elif isinstance(params, list):
        return [resolve_templates(item, payload) for item in params]
    return params


async def evaluate_and_run_workflow(db: AsyncSession, workflow: Workflow, payload: dict[str, Any]) -> None:
    """
    Evaluates rule conditions against trigger payloads and executes actions concurrently.

    Throttles database I/O writes based on the configuration of Workflow.log_depth.
    """
    b_id = workflow.business_id
    w_id = workflow.id
    depth = workflow.log_depth

    logger.debug("Starting out-of-band workflow evaluation for rule: %s [id=%s]", workflow.name, w_id)

    # 1. Evaluate all logical filters
    conditions_matched = True
    for cond in workflow.conditions:
        # Conditions represent standard key-value filters
        if not evaluate_condition(payload, cond):
            conditions_matched = False
            break

    log_repo = WorkflowExecutionLogRepository(db)

    # 2. Skip if conditions do not match
    if not conditions_matched:
        logger.debug("Workflow '%s' [id=%s] filters not met. Skipped.", workflow.name, w_id)
        if depth == LogDepth.ALL.value:
            log_entry = WorkflowExecutionLog(
                workflow_id=w_id,
                business_id=b_id,
                status="skipped",
                error_message="Trigger conditions not met.",
            )
            await log_repo.create(log_entry)
            await db.commit()
        return

    # 3. Resolve templates and run all actions concurrently
    actions_tasks = []
    for action in workflow.actions:
        a_type = action.get("type", "")
        raw_params = action.get("params", {})

        # Render template keys
        resolved_params = resolve_templates(raw_params, payload)

        actions_tasks.append(
            run_action(
                db=db,
                action_type=a_type,
                business_id=b_id,
                params=resolved_params,
            )
        )

    try:
        results = await asyncio.gather(*actions_tasks, return_exceptions=True)

        # Parse for failures inside gathered actions
        failures = [r for r in results if isinstance(r, Exception)]

        if failures:
            err_msg = "; ".join(str(f) for f in failures)
            logger.error("Workflow '%s' [id=%s] completed with errors: %s", workflow.name, w_id, err_msg)

            if depth in (LogDepth.ALL.value, LogDepth.ERRORS_ONLY.value):
                log_entry = WorkflowExecutionLog(
                    workflow_id=w_id,
                    business_id=b_id,
                    status="failed",
                    error_message=err_msg[:255],
                )
                await log_repo.create(log_entry)
                await db.commit()
        else:
            logger.info("Workflow '%s' [id=%s] executed successfully.", workflow.name, w_id)

            if depth == LogDepth.ALL.value:
                log_entry = WorkflowExecutionLog(
                    workflow_id=w_id,
                    business_id=b_id,
                    status="success",
                )
                await log_repo.create(log_entry)
                await db.commit()

    except Exception as e:
        logger.error("System failure executing workflow '%s' [id=%s]: %s", workflow.name, w_id, e, exc_info=True)
        if depth in (LogDepth.ALL.value, LogDepth.ERRORS_ONLY.value):
            log_entry = WorkflowExecutionLog(
                workflow_id=w_id,
                business_id=b_id,
                status="failed",
                error_message=str(e)[:255],
            )
            await log_repo.create(log_entry)
            await db.commit()
