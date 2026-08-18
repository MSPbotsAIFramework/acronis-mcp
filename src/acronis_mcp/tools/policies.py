from collections.abc import Callable
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .._json import dump_json_capped
from ..api_client import AcronisClient, AcronisError
from ._common import NO_TOKEN

_BASE = "/api/policy_management/v4"
_MAX_LIMIT = 200


def register(mcp: FastMCP, client_factory: Callable[[], AcronisClient | None]) -> None:

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def acronis_get_policies(
        tenant_id: Annotated[
            str | None, Field(description="Filter by one or more tenant IDs/UUIDs (max 100).")
        ] = None,
        types: Annotated[
            str | None, Field(description="Filter by one or more policy types (max 10).")
        ] = None,
        enabled: Annotated[
            bool | None, Field(description="Filter only enabled or disabled policies.")
        ] = None,
        policy_id: Annotated[
            str | None, Field(description="Filter by one or more policy IDs (max 100).")
        ] = None,
        search: Annotated[
            str | None, Field(description="SQL-like search by name, type, and tags.")
        ] = None,
        include_settings: Annotated[
            bool | None, Field(description="If true, include policy settings.")
        ] = None,
        templates_only: Annotated[
            bool | None, Field(description="If true, filter out non-template policies.")
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
                    "Additional raw query params (policy_selection_id, parent_ids, "
                    "applicable_to_context_id, applicable_to_context_selection_id, "
                    "dependency_namespace, dependency_path, os_type, "
                    "include_settings_constraints, include_applied_context, "
                    "include_templates, include_temporaries, favorite, default)."
                )
            ),
        ] = None,
    ) -> str:
        """Fetch a list of protection policies."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        if limit is not None:
            limit = min(limit, _MAX_LIMIT)
        params = {
            "tenant_id": tenant_id,
            "types": types,
            "enabled": enabled,
            "policy_id": policy_id,
            "search": search,
            "include_settings": include_settings,
            "templates_only": templates_only,
            "limit": limit,
            "after": after,
            "before": before,
            **(extra_params or {}),
        }
        try:
            result = await client.get(f"{_BASE}/policies", params=params)
            return dump_json_capped(result)
        except AcronisError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def acronis_get_policy_applications(
        tenant_id: Annotated[
            str | None, Field(description="Filter by one or more tenant IDs/UUIDs (max 100).")
        ] = None,
        policy_id: Annotated[
            str | None, Field(description="Filter by one or more policy IDs (max 100).")
        ] = None,
        context_id: Annotated[
            str | None, Field(description="Filter by one or more resource/context IDs (max 100).")
        ] = None,
        context_type: Annotated[
            str | None, Field(description="Filter by one or more resource types (max 10).")
        ] = None,
        status: Annotated[
            str | None, Field(description="Filter by one or more statuses (ExecutionStatus, max 10).")
        ] = None,
        enabled_only: Annotated[
            bool | None, Field(description="If true, only return enabled applications.")
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
                    "Additional raw query params (agent_id, context_selection_id, "
                    "policy_selection_id, policy_type, deployment_state, "
                    "execution_state, issue_types, direct_only, empty_link_only, "
                    "include_deleted, include_temporaries)."
                )
            ),
        ] = None,
    ) -> str:
        """Fetch a list of policy applications (policy-to-resource bindings)."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        if limit is not None:
            limit = min(limit, _MAX_LIMIT)
        params = {
            "tenant_id": tenant_id,
            "policy_id": policy_id,
            "context_id": context_id,
            "context_type": context_type,
            "status": status,
            "enabled_only": enabled_only,
            "limit": limit,
            "after": after,
            "before": before,
            **(extra_params or {}),
        }
        try:
            result = await client.get(f"{_BASE}/applications", params=params)
            return dump_json_capped(result)
        except AcronisError as e:
            return e.to_envelope()
