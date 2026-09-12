# OBS migration

OBS is an external native/WebSocket bridge. Build `dcc-mcp-obs` as a wheel and
place it in the runtime's `lib/site-packages`; start `adapters/obs_runtime_entry.py`
from the shared runtime. Keep OBS process discovery, WebSocket authentication
and scene operations in that adapter. Do not load the shared runtime into OBS's
own plug-in Python.

Use the existing OBS acceptance and readiness checks after handshake. Upgrade
only after wheel hash/signature verification and a successful loopback health
probe; retain the previous runtime for rollback.
