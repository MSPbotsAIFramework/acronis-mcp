from collections.abc import Callable
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .._json import dump_json_capped
from ..api_client import AcronisClient, AcronisError
from ._common import NO_TOKEN

_BASE = "/api/task_manager/v2"
_MAX_LIMIT = 200


def register(mcp: FastMCP, client_factory: Callable[[], AcronisClient | None]) -> None:

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def acronis_get_tasks(
        state: Annotated[
            str | None, Field(description="Filter by state (enqueued/assigned/started/paused/completed).")
        ] = None,
        type: Annotated[str | None, Field(description="Filter by task type.")] = None,
        priority: Annotated[
            str | None, Field(description="Filter by priority (low/belowNormal/normal/aboveNormal/high).")
        ] = None,
        resourceId: Annotated[str | None, Field(description="Filter by resource ID.")] = None,
        policyId: Annotated[str | None, Field(description="Filter by policy ID.")] = None,
        updatedAt: Annotated[
            str | None,
            Field(description='Filter by update time (single entry, e.g. "ge(2024-11-01T08:20:36Z)").'),
        ] = None,
        limit: Annotated[
            int | None, Field(description="Tasks per page, used with `after` (hard cap 200).")
        ] = None,
        after: Annotated[
            str | None, Field(description="Pagination token for the next page (requires `limit`).")
        ] = None,
        order: Annotated[
            str | None, Field(description='e.g. "asc(updatedAt)" or "desc(startedAt)".')
        ] = None,
        lod: Annotated[
            str | None, Field(description="Level of detail — tiny/short/long/full/debug/count.")
        ] = None,
        extra_params: Annotated[
            dict[str, object] | None,
            Field(
                description=(
                    "Additional raw query params (executorId, id, uuid, queue, "
                    "startedBy, policyName, policyType, resourceName, resourceType, "
                    "workflowId, resultCode, enqueuedAt, assignedAt, startedAt, "
                    "completedAt, tag, affinityAgentId, affinityClusterId, "
                    "allow_deleted)."
                )
            ),
        ] = None,
    ) -> str:
        """Fetch a list of tasks."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        if limit is not None:
            limit = min(limit, _MAX_LIMIT)
        params = {
            "state": state,
            "type": type,
            "priority": priority,
            "resourceId": resourceId,
            "policyId": policyId,
            "updatedAt": updatedAt,
            "limit": limit,
            "after": after,
            "order": order,
            "lod": lod,
            **(extra_params or {}),
        }
        try:
            result = await client.get(f"{_BASE}/tasks", params=params)
            return dump_json_capped(result)
        except AcronisError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def acronis_get_task_activities(
        state: Annotated[
            str | None, Field(description="Filter by state (enqueued/assigned/started/paused/completed).")
        ] = None,
        type: Annotated[str | None, Field(description="Filter by activity type.")] = None,
        taskId: Annotated[int | None, Field(description="Filter by parent task ID.")] = None,
        resourceId: Annotated[str | None, Field(description="Filter by resource ID.")] = None,
        policyId: Annotated[str | None, Field(description="Filter by policy ID.")] = None,
        updatedAt: Annotated[
            str | None, Field(description="Filter by update time (single entry).")
        ] = None,
        limit: Annotated[
            int | None, Field(description="Activities per page, used with `after` (hard cap 200).")
        ] = None,
        after: Annotated[
            str | None, Field(description="Pagination token for the next page (requires `limit`).")
        ] = None,
        order: Annotated[
            str | None, Field(description='e.g. "asc(createdAt)" or "desc(completedAt)".')
        ] = None,
        lod: Annotated[
            str | None, Field(description="Level of detail — tiny/short/long/full/debug/count.")
        ] = None,
        extra_params: Annotated[
            dict[str, object] | None,
            Field(
                description=(
                    "Additional raw query params (id, uuid, startedBy, policyName, "
                    "policyType, resourceName, resourceType, workflowId, "
                    "parentActivityId, resultCode, createdAt, startedAt, completedAt, "
                    "tag, sustainable, allow_deleted)."
                )
            ),
        ] = None,
    ) -> str:
        """Fetch a list of task activities."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        if limit is not None:
            limit = min(limit, _MAX_LIMIT)
        params = {
            "state": state,
            "type": type,
            "taskId": taskId,
            "resourceId": resourceId,
            "policyId": policyId,
            "updatedAt": updatedAt,
            "limit": limit,
            "after": after,
            "order": order,
            "lod": lod,
            **(extra_params or {}),
        }
        try:
            result = await client.get(f"{_BASE}/activities", params=params)
            return dump_json_capped(result)
        except AcronisError as e:
            return e.to_envelope()
