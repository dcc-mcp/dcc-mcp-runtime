# CapCut migration

CapCut is an external bridge: package `dcc-mcp-capcut` as a wheel and install it
under `lib/site-packages` of the shared runtime. Keep CapCut Desktop UI control,
token bridge and installation lifecycle in the adapter. The runtime only owns
process startup, MCP/gateway registration and typed handshake.

Use the exact install plan from `dcc_mcp_runtime.lifecycle.plan_install`; route
execution through `ui_control__system_operation` with an operator grant. Never
add a PowerShell or arbitrary Python fallback. Preserve side-by-side rollback
when CapCut or the runtime fails readiness.
