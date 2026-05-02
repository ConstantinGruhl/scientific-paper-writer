from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


STAGE_ORDER = [
    "intake",
    "research_plan",
    "evidence",
    "outline",
    "drafting",
    "review",
    "export",
    "completed",
]

STAGE_GATES = {
    "intake": [
        "title_or_topic_recorded",
        "paper_type_selected",
        "output_mode_selected",
        "word_target_policy_recorded",
    ],
    "research_plan": [
        "research_plan_recorded",
        "structure_strategy_recorded",
    ],
    "evidence": [
        "sources_registered",
        "claims_linked_or_explicitly_deferred",
    ],
    "outline": [
        "section_structure_present",
        "section_budgets_assigned",
    ],
    "drafting": [
        "draft_sections_present",
        "unsupported_claims_marked",
    ],
    "review": [
        "review_findings_recorded",
        "word_count_validated",
        "export_readiness_checked",
    ],
    "export": [
        "requested_outputs_generated",
        "export_validations_passed",
    ],
    "completed": ["final_outputs_present"],
}


def now_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_workflow_state(run_mode: str = "guided") -> dict[str, Any]:
    return {
        "schema_version": 2,
        "run_mode": run_mode,
        "active_stage": "intake",
        "status": "in_progress",
        "completion_signal": {
            "status": "partial",
            "reason": "Workflow initialized",
            "updated_at": now_timestamp(),
        },
        "stages": {
            stage: {
                "status": "in_progress" if stage == "intake" else "not_started",
                "owner": "manager",
                "gate_criteria": STAGE_GATES[stage],
                "outcome": "",
                "blocker": "",
                "started_at": now_timestamp() if stage == "intake" else "",
                "completed_at": "",
            }
            for stage in STAGE_ORDER
        },
        "tasks": [],
        "checkpoints": [],
    }


def new_task(
    role: str,
    description: str,
    stage: str,
    owned_paths: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": f"task-{uuid.uuid4().hex[:10]}",
        "role": role,
        "description": description,
        "stage": stage,
        "owned_paths": owned_paths or [],
        "status": "pending",
        "outcome": "",
        "blocker": "",
        "created_at": now_timestamp(),
        "started_at": "",
        "completed_at": "",
    }


def add_task(workflow_state: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    workflow_state["tasks"].append(task)
    return workflow_state


def update_task(
    workflow_state: dict[str, Any],
    task_id: str,
    *,
    status: str | None = None,
    outcome: str | None = None,
    blocker: str | None = None,
) -> dict[str, Any]:
    for task in workflow_state["tasks"]:
        if task["id"] != task_id:
            continue
        if status:
            task["status"] = status
            if status == "in_progress" and not task["started_at"]:
                task["started_at"] = now_timestamp()
            if status in {"completed", "blocked", "failed", "partial"}:
                task["completed_at"] = now_timestamp()
        if outcome is not None:
            task["outcome"] = outcome
        if blocker is not None:
            task["blocker"] = blocker
        break
    return workflow_state


def set_stage_status(
    workflow_state: dict[str, Any],
    stage: str,
    *,
    status: str,
    outcome: str = "",
    blocker: str = "",
    owner: str | None = None,
) -> dict[str, Any]:
    stage_record = workflow_state["stages"][stage]
    stage_record["status"] = status
    stage_record["outcome"] = outcome
    stage_record["blocker"] = blocker
    if owner:
        stage_record["owner"] = owner
    if status == "in_progress" and not stage_record["started_at"]:
        stage_record["started_at"] = now_timestamp()
    if status in {"completed", "blocked", "failed", "partial"}:
        stage_record["completed_at"] = now_timestamp()
    workflow_state["completion_signal"]["updated_at"] = now_timestamp()
    return workflow_state


def advance_stage(workflow_state: dict[str, Any], next_stage: str) -> dict[str, Any]:
    workflow_state["active_stage"] = next_stage
    workflow_state["status"] = "completed" if next_stage == "completed" else "in_progress"
    stage_record = workflow_state["stages"][next_stage]
    if stage_record["status"] == "not_started":
        stage_record["status"] = "in_progress"
        stage_record["started_at"] = now_timestamp()
    workflow_state["completion_signal"]["reason"] = f"Advanced to {next_stage}"
    workflow_state["completion_signal"]["status"] = (
        "success" if next_stage == "completed" else "partial"
    )
    workflow_state["completion_signal"]["updated_at"] = now_timestamp()
    return workflow_state


def record_checkpoint(
    workflow_state: dict[str, Any],
    *,
    stage: str,
    status: str,
    summary: str,
    unresolved_risks: list[str] | None = None,
    next_owner: str = "manager",
) -> dict[str, Any]:
    workflow_state["checkpoints"].append(
        {
            "id": f"checkpoint-{uuid.uuid4().hex[:10]}",
            "stage": stage,
            "status": status,
            "summary": summary,
            "unresolved_risks": unresolved_risks or [],
            "next_owner": next_owner,
            "created_at": now_timestamp(),
        }
    )
    return workflow_state


def visible_task_rows(workflow_state: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task in workflow_state["tasks"]:
        rows.append(
            {
                "id": task["id"],
                "role": task["role"],
                "stage": task["stage"],
                "status": task["status"],
                "description": task["description"],
                "owned_paths": task["owned_paths"],
                "blocker": task["blocker"],
            }
        )
    return rows
