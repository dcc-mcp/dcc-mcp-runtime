# Adobe migration

## Selected standalone adapter

The current standalone DCC-MCP bridge is `F:\github\dcc-mcp-aftereffects`: it
contains `DccServerBase`, a CEP bridge broker and MCP server lifecycle. The
`F:\github\dcc-mcp-adobepy` repository is an Adobe SDK/broker and remains a
library/transport dependency; it is not treated as the standalone adapter.

Keep the existing Photoshop/After Effects bridge and host plug-in in Adobe's
native process. Replace only the standalone service launch with the shared
runtime executable and pass the adapter wheel through the operator-owned
`adapter_wheels` allow-list. Do not import the runtime into CEP/UXP or inject
CPython into an Adobe process.

At startup load `runtime/manifests/adobe.json`, call `negotiate`, then register
the resulting `capabilities_fingerprint`. A failed ABI/core/signature check is
reported as not-ready and leaves the previous runtime active.
