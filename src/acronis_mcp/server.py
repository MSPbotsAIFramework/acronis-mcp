import contextvars
from collections.abc import Callable

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from .api_client import AcronisClient
from .config import Settings

# Per-request credential isolation via contextvars.
# GatewayTokenMiddleware sets this before the MCP handler runs.
# Python asyncio copies context per task, so concurrent SSE connections are isolated.
# Value is (access_token, datacenter_url) — both required, since Acronis has no
# single default data center (each tenant is provisioned on one of several).
_gateway_creds_var: contextvars.ContextVar[tuple[str, str] | None] = contextvars.ContextVar(
    "acronis_gateway_creds", default=None
)


def get_client_from_context(settings: Settings) -> AcronisClient | None:
    """Resolve the active AcronisClient for the current request context."""
    creds = _gateway_creds_var.get()
    if not creds:
        return None
    token, datacenter_url = creds
    return AcronisClient(token, datacenter_url)


class GatewayTokenMiddleware:
    """ASGI middleware.

    Reads X-Acronis-Token (required) and X-Acronis-Datacenter-Url (required)
    from request headers and stores them in the contextvar. Returns 401 if
    either header is missing on /mcp requests.
    """

    def __init__(self, app: ASGIApp, settings: Settings):
        self.app = app
        self.settings = settings

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if not path.startswith("/mcp"):
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        token = request.headers.get("x-acronis-token")
        datacenter_url = request.headers.get("x-acronis-datacenter-url")
        if not token or not datacenter_url:
            response = JSONResponse(
                {
                    "error": "Missing credentials",
                    "message": (
                        "This server requires the X-Acronis-Token header (OAuth2 "
                        "bearer access token) and the X-Acronis-Datacenter-Url header "
                        "(this tenant's Acronis data center base URL)"
                    ),
                    "required_headers": ["X-Acronis-Token", "X-Acronis-Datacenter-Url"],
                    "optional_headers": [],
                },
                status_code=401,
            )
            await response(scope, receive, send)
            return

        ctx_token = _gateway_creds_var.set((token, datacenter_url))
        try:
            await self.app(scope, receive, send)
        finally:
            _gateway_creds_var.reset(ctx_token)


def create_mcp_server(settings: Settings) -> FastMCP:
    """Build the FastMCP server instance and register all Acronis tools."""
    # DNS-rebinding protection is a browser-oriented safeguard that rejects
    # non-localhost Host headers with 421. Disable it so the server works
    # correctly behind a reverse proxy or docker network.
    mcp = FastMCP(
        name="acronis-mcp",
        instructions=(
            "Acronis Cyber Protect Cloud is a backup/disaster-recovery and "
            "endpoint-protection platform MSPs use to safeguard clients' "
            "workloads (servers, VMs, workstations). This server covers the 6 "
            "read-only areas MSPbots' Acronis integration uses: alerts "
            "(acronis_get_alerts, acronis_get_customer_alerts, "
            "acronis_get_customer_alerts_count, acronis_get_alert_types, "
            "acronis_get_resource_status, acronis_get_alert_status) for "
            "monitoring backup failures/health per customer or resource; tasks "
            "(acronis_get_tasks, acronis_get_task_activities) for backup/"
            "restore job history and progress; agents (acronis_get_agents) for "
            "which protection agents are installed/online per host; resources "
            "(acronis_get_resources, acronis_get_resource_statuses) for the "
            "inventory of protected workloads/devices/groups and their "
            "protection status; policies (acronis_get_policies, "
            "acronis_get_policy_applications) for which protection plans exist "
            "and which resources they apply to; tenants (acronis_get_tenant) "
            "for a customer account's details. All 14 tools are read-only; "
            "there is no write/delete tooling. Typical flow: acronis_get_tenant "
            "or acronis_get_resources to identify a customer/workload, then "
            "acronis_get_alerts or acronis_get_resource_statuses to check "
            "protection health, then acronis_get_tasks for job history if "
            "something looks wrong."
        ),
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )

    client_factory: Callable[[], AcronisClient | None] = lambda: get_client_from_context(settings)

    from .tools import agents, alerts, policies, resources, tasks, tenants

    alerts.register(mcp, client_factory)
    agents.register(mcp, client_factory)
    tasks.register(mcp, client_factory)
    resources.register(mcp, client_factory)
    policies.register(mcp, client_factory)
    tenants.register(mcp, client_factory)

    return mcp
