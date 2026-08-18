from collections.abc import Callable
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .._json import dump_json_capped
from ..api_client import AcronisClient, AcronisError
from ._common import NO_TOKEN

_BASE = "/api/resource_management/v4"
_MAX_LIMIT = 200


def register(mcp: FastMCP, client_factory: Callable[[], AcronisClient | None]) -> None:

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def acronis_get_resources(
        tenant_id: Annotated[
            str | None, Field(description="Filter by one or more tenant IDs/UUIDs (max 100).")
        ] = None,
        agent_id: Annotated[
            str | None, Field(description="Filter by one or more agent UUIDs (max 100).")
        ] = None,
        parent_id: Annotated[
            str | None, Field(description="Filter by one or more parent UUIDs (max 100).")
        ] = None,
        type: Annotated[
            str | None, Field(description="Filter by resource type (ResourceType or cti.CTI), max 10.")
        ] = None,
        resource_id: Annotated[
            str | None, Field(description="Filter by one or more resource UUIDs (max 100).")
        ] = None,
        search: Annotated[
            str | None, Field(description="SQL-like search by type and tags.")
        ] = None,
        include_attributes: Annotated[
            bool | None, Field(description="If true, include resources' attributes.")
        ] = None,
        include_deleted: Annotated[
            bool | None, Field(description="If true, include deleted resources.")
        ] = None,
        is_group: Annotated[
            bool | None, Field(description="If true, only groups; if false, only non-group resources.")
        ] = None,
        updated_at: Annotated[
            str | None, Field(description="Filter by update timestamp.")
        ] = None,
        limit: Annotated[
            int | None, Field(description="Number of elements per page (hard cap 200).")
        ] = None,
        after: Annotated[
            str | None, Field(description="Pagination cursor after the current page.")
        ] = None,
        before: Annotated[
            str | None, Field(description="Pagination cursor before the current page.")
        ] = None,
        extra_params: Annotated[
            dict[str, object] | None,
            Field(
                description=(
                    "Additional raw query params (has_member_id, "
                    "include_attribute_namespaces, not_applied_only, "
                    "applicable_to_policy_id, applicable_to_policy_selection_id, "
                    "applied_only, applied_to_policy_id, "
                    "applied_to_policy_selection_id, allowed_actions)."
                )
            ),
        ] = None,
    ) -> str:
        """Fetch a list of all resources (managed workloads/devices/groups)."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        if limit is not None:
            limit = min(limit, _MAX_LIMIT)
        params = {
            "tenant_id": tenant_id,
            "agent_id": agent_id,
            "parent_id": parent_id,
            "type": type,
            "resource_id": resource_id,
            "search": search,
            "include_attributes": include_attributes,
            "include_deleted": include_deleted,
            "is_group": is_group,
            "updated_at": updated_at,
            "limit": limit,
            "after": after,
            "before": before,
            **(extra_params or {}),
        }
        try:
            result = await client.get(f"{_BASE}/resources", params=params)
            return dump_json_capped(result)
        except AcronisError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def acronis_get_resource_statuses(
        tenant_id: Annotated[
            str | None, Field(description="Filter by one or more tenant IDs/UUIDs (max 100).")
        ] = None,
        agent_id: Annotated[
            str | None, Field(description="Filter by one or more agent UUIDs (max 100).")
        ] = None,
        resource_id: Annotated[
            str | None, Field(description="Filter by one or more resource UUIDs (max 100).")
        ] = None,
        search: Annotated[
            str | None, Field(description="SQL-like search by type and tags.")
        ] = None,
        include_deleted: Annotated[
            bool | None, Field(description="If true, include deleted resources.")
        ] = None,
        updated_at: Annotated[
            str | None, Field(description="Filter by update timestamp.")
        ] = None,
        order: Annotated[
            str | None, Field(description='e.g. "is_group" or "asc(updated_at)".')
        ] = None,
        limit: Annotated[
            int | None, Field(description="Number of elements per page (hard cap 200).")
        ] = None,
        after: Annotated[
            str | None, Field(description="Pagination cursor after the current page.")
        ] = None,
        before: Annotated[
            str | None, Field(description="Pagination cursor before the current page.")
        ] = None,
        extra_params: Annotated[
            dict[str, object] | None,
            Field(
                description=(
                    "Additional raw query params (parent_id, has_member_id, type, "
                    "selection_id, include_attributes, include_attribute_namespaces)."
                )
            ),
        ] = None,
    ) -> str:
        """Fetch the protection status of resources."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        if limit is not None:
            limit = min(limit, _MAX_LIMIT)
        params = {
            "tenant_id": tenant_id,
            "agent_id": agent_id,
            "resource_id": resource_id,
            "search": search,
            "include_deleted": include_deleted,
            "updated_at": updated_at,
            "order": order,
            "limit": limit,
            "after": after,
            "before": before,
            **(extra_params or {}),
        }
        try:
            result = await client.get(f"{_BASE}/resource_statuses", params=params)
            return dump_json_capped(result)
        except AcronisError as e:
            return e.to_envelope()
