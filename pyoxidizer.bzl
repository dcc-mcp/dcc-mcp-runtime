"""PyOxidizer distribution for the shared external-adapter runtime.

Build with `pyoxidizer build --var core_version=0.20.14`. Adapter wheels are
provided through the `DCC_MCP_RUNTIME_ADAPTER_WHEELS` build variable (a
semicolon-separated, operator-supplied allow-list). No network or arbitrary
commands are executed by this file.
"""

def make_exe():
    dist = default_python_distribution()
    policy = dist.make_python_packaging_policy()
    policy.resources_location = "filesystem-relative:lib"
    python_config = dist.make_python_interpreter_config()
    python_config.oxidized_importer = False
    python_config.filesystem_importer = True
    python_config.module_search_paths = ["$ORIGIN/lib/site-packages"]
    python_config.run_module = "dcc_mcp_runtime.cli"
    python_config.parse_argv = True
    exe = dist.to_python_executable(
        name="dcc-mcp-runtime",
        packaging_policy=policy,
        config=python_config,
    )
    wheels = VARS.get("adapter_wheels", "").split(";")
    wheels = [wheel for wheel in wheels if wheel]
    resources = exe.pip_install([".", "dcc-mcp-core=={}".format(VARS["core_version"])])
    if wheels:
        resources += exe.pip_install(wheels)
    exe.add_python_resources(resources)
    return exe

def make_install(exe):
    files = FileManifest()
    files.add_python_resource(".", exe)
    return files

register_target("exe", make_exe)
register_target("install", make_install, depends=["exe"], default=True)
resolve_targets()
