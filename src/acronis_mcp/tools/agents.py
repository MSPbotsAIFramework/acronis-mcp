from collections.abc import Callable
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .._json import dump_json_capped
from ..api_client import AcronisClient, AcronisError
from ._common import NO_TOKEN

_MAX_LIMIT = 200


def register(mcp: FastMCP, client_factory: Callable[[], AcronisClient | None]) -> None:

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def acronis_get_agents(
        hostname: Annotated[
            str | None,
            Field(
                description=(
                    'Filter by host name; supports "hlike(x)"/"like(x)"/"tlike(x)" '
                    "for starts-with/contains/ends-with matching."
                )
            ),
        ] = None,
        online: Annotated[
            bool | None,
            Field(description="If true, only responsive agents; if false, only irresponsive."),
        ] = None,
        os_family: Annotated[
            str | None,
            Field(description="Filter by OS family (UNKNOWN/WINDOWS/LINUX/MACOSX/SOLARIS)."),
        ] = None,
        tenant_id: Annotated[
            str | None, Field(description="Only return agents under this tenant subtree.")
        ] = None,
        up_to_date: Annotated[
            bool | None, Field(description="Filter by whether agent software is current.")
        ] = None,
        limit: Annotated[
            int | None, Field(description="Max number of agents to return (hard cap 200).")
        ] = None,
        after: Annotated[
            str | None, Field(description="Pagination cursor for the next page.")
        ] = None,
        before: Annotated[
            str | None, Field(description="Pagination cursor for the previous page.")
        ] = None,
    ) -> str:
        """Fetch registered Acronis agents."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        if limit is not None:
            limit = min(limit, _MAX_LIMIT)
        params = {
            "hostname": hostname,
            "online": online,
            "os_family": os_family,
            "tenant_id": tenant_id,
            "up_to_date": up_to_date,
            "limit": limit,
            "after": after,
            "before": before,
        }
        try:
            result = await client.get("/api/agent_manager/v2/agents", params=params)
            return dump_json_capped(result)
        except AcronisError as e:
            return e.to_envelope()
