from collections.abc import Callable
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .._json import dump_json_capped
from ..api_client import AcronisClient, AcronisError
from ._common import NO_TOKEN

_BASE = "/api/alert_manager/v1"
_MAX_LIMIT = 200


def register(mcp: FastMCP, client_factory: Callable[[], AcronisClient | None]) -> None:

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def acronis_get_alerts(
        limit: Annotated[
            int | None, Field(description="Max number of alerts to return (hard cap 200).")
        ] = None,
        severity: Annotated[
            str | None,
            Field(
                description=(
                    "Filter by severity (ok/information/warning/error/critical). "
                    'Supports operators, e.g. "eq(warning)", "or(warning,critical)".'
                )
            ),
        ] = None,
        type: Annotated[str | None, Field(description="Filter by alert type.")] = None,
        category: Annotated[
            str | None, Field(description='Filter by alert category (e.g. "Backup", "Monitoring").')
        ] = None,
        tenant: Annotated[str | None, Field(description="Filter by alert tenant ID.")] = None,
        query: Annotated[
            str | None, Field(description="Free-text search within planName/resourceName fields.")
        ] = None,
        show_deleted: Annotated[
            bool | None, Field(description="If true, include dismissed alerts.")
        ] = None,
        order: Annotated[
            str | None, Field(description='Order results, e.g. "asc(updated_at)" or "desc(created_at)".')
        ] = None,
        updated_at: Annotated[
            str | None,
            Field(
                description=(
                    'Filter by update timestamp (Unix ns). Supports operators like "ge(1711687981)".'
                )
            ),
        ] = None,
        created_at: Annotated[
            str | None, Field(description="Filter by creation timestamp (Unix ns), same operator syntax.")
        ] = None,
        extra_params: Annotated[
            dict[str, object] | None,
            Field(
                description=(
                    "Additional raw query params (e.g. id, skip, deleted_at, source, "
                    "source_time_stamp, planId, resourceId, planName, resourceName, "
                    "show_deleted_only)."
                )
            ),
        ] = None,
    ) -> str:
        """Fetch all alerts by optional filtering parameters."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        if limit is not None:
            limit = min(limit, _MAX_LIMIT)
        params = {
            "limit": limit,
            "severity": severity,
            "type": type,
            "category": category,
            "tenant": tenant,
            "query": query,
            "show_deleted": show_deleted,
            "order": order,
            "updated_at": updated_at,
            "created_at": created_at,
            **(extra_params or {}),
        }
        try:
            result = await client.get(f"{_BASE}/alerts", params=params)
            return dump_json_capped(result)
        except AcronisError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def acronis_get_customer_alerts(
        customer_id: Annotated[
            list[str],
            Field(
                description=(
                    "Required list of customer (tenant) UUIDs whose alerts to return "
                    "— not company display names. Resolve a name to its ID via "
                    "acronis_get_tenant or acronis_get_resources first."
                )
            ),
        ],
        severity: Annotated[
            str | None, Field(description="Filter by severity (ok/information/warning/error/critical).")
        ] = None,
        type: Annotated[str | None, Field(description="Filter by alert type.")] = None,
        category: Annotated[str | None, Field(description="Filter by alert category.")] = None,
        query: Annotated[
            str | None, Field(description="Free-text search within planName/resourceName fields.")
        ] = None,
        show_deleted: Annotated[
            bool | None, Field(description="If true, include dismissed alerts.")
        ] = None,
        extra_params: Annotated[
            dict[str, object] | None,
            Field(
                description=(
                    "Additional raw query params (id, source, updated_at, created_at, "
                    "planId, resourceId, planName, resourceName, deleted_at, "
                    "source_time_stamp, show_deleted_only)."
                )
            ),
        ] = None,
    ) -> str:
        """Fetch alerts grouped per customer."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        params = {
            "customer_id": customer_id,
            "severity": severity,
            "type": type,
            "category": category,
            "query": query,
            "show_deleted": show_deleted,
            **(extra_params or {}),
        }
        try:
            result = await client.get(f"{_BASE}/customer_alerts", params=params)
            return dump_json_capped(result)
        except AcronisError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def acronis_get_customer_alerts_count(
        severity: Annotated[
            str | None, Field(description="Filter by severity (ok/information/warning/error/critical).")
        ] = None,
        type: Annotated[str | None, Field(description="Filter by alert type.")] = None,
        category: Annotated[str | None, Field(description="Filter by alert category.")] = None,
        show_deleted: Annotated[
            bool | None, Field(description="If true, include dismissed alerts.")
        ] = None,
        extra_params: Annotated[
            dict[str, object] | None,
            Field(
                description=(
                    "Additional raw query params (id, query, source, updated_at, "
                    "created_at, planId, resourceId, planName, resourceName, "
                    "deleted_at, source_time_stamp, show_deleted_only)."
                )
            ),
        ] = None,
    ) -> str:
        """Fetch aggregate alert COUNTS per customer, not the alert list itself
        (customers with no alerts are omitted). Use acronis_get_customer_alerts
        for the actual alert rows.
        """
        client = client_factory()
        if client is None:
            return NO_TOKEN
        params = {
            "severity": severity,
            "type": type,
            "category": category,
            "show_deleted": show_deleted,
            **(extra_params or {}),
        }
        try:
            result = await client.get(f"{_BASE}/customer_alerts_count", params=params)
            return dump_json_capped(result)
        except AcronisError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def acronis_get_alert_types(
        os_type: Annotated[
            list[str],
            Field(
                description=(
                    "Required list of OS filters (ios/linux/macos/windows) — the "
                    "vendor API has no \"all\" option. If the user hasn't specified "
                    'a target OS, pass all four: ["ios","linux","macos","windows"].'
                )
            ),
        ],
        category: Annotated[
            str | None, Field(description="Filter by list of type categories.")
        ] = None,
        order: Annotated[
            str | None, Field(description='Order by column (id/severity/category), e.g. "desc(severity)".')
        ] = None,
    ) -> str:
        """Fetch all registered alert types."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        params = {"os_type": os_type, "category": category, "order": order}
        try:
            result = await client.get(f"{_BASE}/types", params=params)
            return dump_json_capped(result)
        except AcronisError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def acronis_get_resource_status(
        id: Annotated[
            list[str] | None,
            Field(
                description=(
                    "Optional list of resource UUIDs to filter by — not hostnames, "
                    "resolve via acronis_get_resources first. If omitted, returns "
                    "statuses for all resources that have alerts."
                )
            ),
        ] = None,
        embed_alert: Annotated[
            bool | None, Field(description="If true, include the full alert object in the response.")
        ] = None,
    ) -> str:
        """Fetch the resources containing the highest-severity alerts found for them."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        params = {"id": id, "embed_alert": embed_alert}
        try:
            result = await client.get(f"{_BASE}/resource_status", params=params)
            return dump_json_capped(result)
        except AcronisError as e:
            return e.to_envelope()

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def acronis_get_alert_status(
        scope_key: Annotated[
            str,
            Field(
                description=(
                    "Required context key or searchable detail to group by (see "
                    "registered alert types for available keys)."
                )
            ),
        ],
        scope_value: Annotated[
            list[str] | None,
            Field(
                description=(
                    "Optional list of scope values to filter by; if omitted, returns "
                    "the last most-critical status among available alerts."
                )
            ),
        ] = None,
    ) -> str:
        """Fetch the last, most critical alerts grouped by the selected scope."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        params = {"scope_key": scope_key, "scope_value": scope_value}
        try:
            result = await client.get(f"{_BASE}/status", params=params)
            return dump_json_capped(result)
        except AcronisError as e:
            return e.to_envelope()
