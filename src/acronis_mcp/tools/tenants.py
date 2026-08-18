from collections.abc import Callable
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .._json import dump_json_capped
from ..api_client import AcronisClient, AcronisError
from ._common import NO_TOKEN


def register(mcp: FastMCP, client_factory: Callable[[], AcronisClient | None]) -> None:

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    async def acronis_get_tenant(
        tenant_id: Annotated[str, Field(description="Required tenant UUID.")],
        embed_path: Annotated[
            bool | None, Field(description="If true, embed the tenant path in the result.")
        ] = None,
        allow_deleted: Annotated[
            bool | None, Field(description="If true, a deleted tenant may be returned.")
        ] = None,
    ) -> str:
        """Fetch a tenant by ID."""
        client = client_factory()
        if client is None:
            return NO_TOKEN
        params = {"embed_path": embed_path, "allow_deleted": allow_deleted}
        try:
            result = await client.get(f"/api/2/tenants/{tenant_id}", params=params)
            return dump_json_capped(result)
        except AcronisError as e:
            return e.to_envelope()
