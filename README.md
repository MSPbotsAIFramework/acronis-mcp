# acronis-mcp

**Acronis** MCP server — exposes the Acronis Cyber Protect Cloud platform APIs as MCP tools.

> **Naming note:** app.mspbots.ai calls this integration **"Acronis"** (`sys_integration.subject_code = ACRONIS`, type "BackUp Disaster Recovery Software"). The underlying vendor product is **Acronis Cyber Protect Cloud**, and its public API surface is officially named the **"Acronis Cyber Platform APIs"** (`developer.acronis.com`).

<div align="center">

## MSPbots Connector

**The MCP Gateway built for MSPs: visible, controlled, and your data stays where it belongs.**

[**Get started at connect.mspbots.ai →**](https://connect.mspbots.ai)

</div>

---

MSPbots Connector gives your AI clients one MCP URL to reach your entire MSP stack (RMM, PSA, documentation, security, finance), and gives you control over who can call which tool and a record of everything that was called.

**Hosted service: [connect.mspbots.ai](https://connect.mspbots.ai)** · Free to use.

### Why Connector

![MSPbots Connector](https://stgoss.mspbots.ai/files/mcp/mspbots-mcp.png)

| | |
|---|---|
| **Visible** | Every tool call is logged: who, which vendor, when. Usage dashboard, CSV export, SIEM streaming. |
| **Controlled** | Role-based, per-tool allowlist. Deny by default. |
| **Protected** | Credentials encrypted per record. AI clients never see your vendor passwords or tokens. |
| **MSP-native** | Built for the MSP stack only: RMM, PSA, documentation, security, finance. |

### Quick start

1. **Sign up** at [connect.mspbots.ai](https://connect.mspbots.ai).
2. **Connect your vendors.** Pick from 150+ connectors and authorize each one on the vendor's own page, or bring your own API keys. No extra vendor accounts needed.
3. **Set access.** Create roles and decide which tools each role may call. Nothing is allowed until you allow it.
4. **Add your MCP URL to your AI client.** Copy the URL from your Connector dashboard into Claude, ChatGPT, Cursor, VS Code, Gemini, Codex, or any MCP-capable client.
5. **Ask your AI to do real work**, and watch every call appear in the audit log.

### Features

**Unified gateway**
- One MCP URL for all your AI clients
- 150+ connectors across the MSP stack
- Custom MCP servers supported, free
- Authorization happens on each vendor's own page; the AI never sees passwords or tokens
- Bring your own credentials: use the vendor API keys you already have
- Multiple accounts per app; connect once, reuse across AI clients
- Tool search: finds the right action for the task
- One sign-in; vendor credentials are injected behind the scenes and OAuth tokens refresh automatically

**Visibility**
- Audit log for every tool call (who, which vendor, when)
- Usage dashboard: call volume, top vendors, error rate, per-user activity
- Export audit logs to CSV, or stream to Loki, Graylog, or LogScale (SIEM)
- Optional recording of tool arguments and result summaries (off by default, enabled per organization)

**Control**
- Per-role, per-tool allowlist, deny by default
- owner / admin / member roles
- SCIM provisioning with Entra ID, Okta, JumpCloud, and Google Workspace

**Security**
- Credentials encrypted one record at a time (AES-256-GCM, per-record key)
- AI clients authenticate with OAuth 2.1 + PKCE
- Vendor responses are scanned for prompt-injection patterns and returned as structured data. This is one layer of defense, not a guarantee against every attack.
- Static egress IP for customer firewall and API allowlisting

### Pricing

**Free.**

Links: [connect.mspbots.ai](https://connect.mspbots.ai) · [mspbots.ai](https://mspbots.ai)

---

## Overview

This server implements the [Model Context Protocol](https://modelcontextprotocol.io/) (Streamable HTTP/SSE transport) and covers the **14 read-only interfaces** that MSPbots' own Acronis integration actually uses across 5 Acronis sub-APIs, matching the interface scope configured in MSPbots' `sys_integration`/`sys_integration_api` tables:

| Sub-API | Tools |
|---|---|
| Alert Manager v1 | 6 |
| Task Manager v2 | 2 |
| Agent Manager v2 | 1 |
| Resource Management v4 | 2 |
| Policy Management v4 | 2 |
| Account Management v2 (tenants) | 1 |

It follows the MSPbots **Vendor MCP Service SOP**: stateless, no stored credentials, per-request header authentication.

The underlying API authenticates via **OAuth2 Client Credentials** (`POST <datacenter-url>/api/2/idp/token` with `client_id` + `client_secret`, matching the "Data Center URL / Client ID / Client Secret" fields configured in MSPbots' own Acronis integration). This server does not perform the token exchange itself — it receives an already-obtained bearer access token per request, the same pattern used for other real-OAuth2 vendors in this MCP fleet (e.g. BizRatings, ConnectWise Asio): the gateway mints/refreshes the token from `client_id`/`client_secret`, and only the resulting token — plus the tenant's data center URL — reaches this server.

## Quick Start

### Docker (recommended)

```bash
docker compose up --build
```

The server starts on `http://localhost:8080`.

### Local (uv)

```bash
uv sync
python -m acronis_mcp
```

## Health Check

```bash
curl http://localhost:8080/health
# {"status": "ok", "service": "acronis-mcp", "transport": "http"}
```

No credentials are required for the health endpoint.

## 授权参数说明 (Authentication)

Every request to `/mcp` must include the following HTTP headers:

| Header | 类型 | 是否必填 | 默认值 | 枚举值 | 字段描述 | Example |
|---|---|---|---|---|---|---|
| `X-Acronis-Token` | string | 必填 | 无 | 无(自由文本) | OAuth2 bearer access token,由调用方(Agent Platform / 上游网关)通过 `POST <datacenter-url>/api/2/idp/token`(client_credentials grant,需 client_id + client_secret)预先换取并负责刷新。本服务从不接触 client_id/client_secret,只转发已获取的 token。 | `X-Acronis-Token: <access_token>` |
| `X-Acronis-Datacenter-Url` | string | 必填 | 无 | 无(不同租户对应不同数据中心域名,以该租户在 Acronis 管理控制台 / MSPbots 集成配置里的 Data Center URL 为准,例如 `https://us5-cloud.acronis.com`、`https://eu2-cloud.acronis.com`) | Acronis Cyber Protect Cloud 每个租户被分配在某一个数据中心,没有统一默认地址,必须显式传入。 | `X-Acronis-Datacenter-Url: https://us5-cloud.acronis.com` |

Missing either header returns `401 Unauthorized`.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MCP_HTTP_PORT` | `8080` | Listening port |
| `MCP_HTTP_HOST` | `0.0.0.0` | Listening host |

## MCP Endpoint

```
POST http://localhost:8080/mcp
```

Connect your MCP client with:
- Transport: `http` (Streamable HTTP / SSE)
- Headers: `X-Acronis-Token: <access_token>` (required), `X-Acronis-Datacenter-Url: <datacenter_url>` (required)

## Tool List

**14 tools**, matching the exact interface count MSPbots' own Acronis integration uses.

### Alert Manager (6)

| Tool | 功能 | 参数 |
|---|---|---|
| `acronis_get_alerts` | 按条件查全部告警 | `limit?`, `severity?`, `type?`, `category?`, `tenant?`, `query?`, `show_deleted?`, `order?`, `updated_at?`, `created_at?`, `extra_params?` |
| `acronis_get_customer_alerts` | 按客户分组查告警 | `customer_id`(必填,列表), `severity?`, `type?`, `category?`, `query?`, `show_deleted?`, `extra_params?` |
| `acronis_get_customer_alerts_count` | 查每个客户的告警计数 | `severity?`, `type?`, `category?`, `show_deleted?`, `extra_params?` |
| `acronis_get_alert_types` | 查全部已注册告警类型 | `os_type`(必填,列表), `category?`, `order?` |
| `acronis_get_resource_status` | 查含最高严重告警的资源 | `id?`(列表), `embed_alert?` |
| `acronis_get_alert_status` | 按 scope 分组查最新最高严重告警 | `scope_key`(必填), `scope_value?`(列表) |

### Task Manager (2)

| Tool | 功能 | 参数 |
|---|---|---|
| `acronis_get_tasks` | 查任务列表 | `state?`, `type?`, `priority?`, `resourceId?`, `policyId?`, `updatedAt?`, `limit?`, `after?`, `order?`, `lod?`, `extra_params?` |
| `acronis_get_task_activities` | 查任务活动列表 | `state?`, `type?`, `taskId?`, `resourceId?`, `policyId?`, `updatedAt?`, `limit?`, `after?`, `order?`, `lod?`, `extra_params?` |

### Agent Manager (1)

| Tool | 功能 | 参数 |
|---|---|---|
| `acronis_get_agents` | 查已注册 agent 列表 | `hostname?`, `online?`, `os_family?`, `tenant_id?`, `up_to_date?`, `limit?`, `after?`, `before?` |

### Resource Management (2)

| Tool | 功能 | 参数 |
|---|---|---|
| `acronis_get_resources` | 查全部受管资源(workload/设备/分组) | `tenant_id?`, `agent_id?`, `parent_id?`, `type?`, `resource_id?`, `search?`, `include_attributes?`, `include_deleted?`, `is_group?`, `updated_at?`, `limit?`, `after?`, `before?`, `extra_params?` |
| `acronis_get_resource_statuses` | 查资源防护状态 | `tenant_id?`, `agent_id?`, `resource_id?`, `search?`, `include_deleted?`, `updated_at?`, `order?`, `limit?`, `after?`, `before?`, `extra_params?` |

### Policy Management (2)

| Tool | 功能 | 参数 |
|---|---|---|
| `acronis_get_policies` | 查防护策略列表 | `tenant_id?`, `types?`, `enabled?`, `policy_id?`, `search?`, `include_settings?`, `templates_only?`, `limit?`, `after?`, `before?`, `extra_params?` |
| `acronis_get_policy_applications` | 查策略应用(策略与资源的绑定关系) | `tenant_id?`, `policy_id?`, `context_id?`, `context_type?`, `status?`, `enabled_only?`, `limit?`, `after?`, `before?`, `extra_params?` |

### Account Management (1)

| Tool | 功能 | 参数 |
|---|---|---|
| `acronis_get_tenant` | 按 ID 查租户信息 | `tenant_id`(必填), `embed_path?`, `allow_deleted?` |

## 测试示例 (Test Example)

Fetch alerts:

```json
{
  "method": "tools/call",
  "params": { "name": "acronis_get_alerts", "arguments": { "limit": 10, "show_deleted": false } }
}
```

Equivalent `curl` against the running server (streamable HTTP MCP endpoint):

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "X-Acronis-Token: <access_token>" \
  -H "X-Acronis-Datacenter-Url: https://us5-cloud.acronis.com" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": { "name": "acronis_get_alerts", "arguments": { "limit": 10 } }
  }'
```

A parameterized call:

```json
{
  "method": "tools/call",
  "params": {
    "name": "acronis_get_tenant",
    "arguments": { "tenant_id": "890f6ce1-918d-43c8-9f9c-8febb5bec432" }
  }
}
```

## API Reference

- API library: `https://developer.acronis.com/doc/outbound/apis/index.html`
- Alert Manager v1: `https://developer.acronis.com/doc/alerts/v1/reference/index.html`
- Task Manager v2: `https://developer.acronis.com/doc/tasks/v2/reference/index.html`
- Agent Manager v2: `https://developer.acronis.com/doc/agents/v2/reference/index.html`
- Resource & Policy Management v4: `https://developer.acronis.com/doc/resource-policy-management/v4/reference/index.html`
- Account Management v2: `https://developer.acronis.com/doc/account-management/v2/reference/index.html`

## Known Gaps / Implementation Notes

- Scope is intentionally bounded to the 14 interfaces MSPbots' own Acronis integration is configured to use, not the full Acronis Cyber Platform API surface (which also includes PSA, Event Manager, Disaster Recovery, EDR, Vaults Management, File Sync & Share, and write/management endpoints across every sub-API) — per this task's requirement that interface count stay consistent with MSPbots.
- Endpoints with a large filter surface (e.g. `acronis_get_alerts`, `acronis_get_customer_alerts`, `acronis_get_tasks`, `acronis_get_resources`, `acronis_get_policies`) expose the most commonly-used filters as named parameters plus a generic `extra_params: dict` for the remaining, less-common query filters documented in the vendor API reference.
- `X-Acronis-Datacenter-Url` has no default — Acronis Cyber Protect Cloud tenants are provisioned on one of several regional data centers with no single fallback, so the caller must always supply it (matches the "Data Center URL" field being a required field in MSPbots' own Acronis integration config).
- Not yet tested against a live Acronis account — only protocol-level verification (health check, 401 on missing headers, `tools/list` returning all 14 tools) has been done so far.
