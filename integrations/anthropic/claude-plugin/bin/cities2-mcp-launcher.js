#!/usr/bin/env node

const fs = require("node:fs");
const { spawn, spawnSync } = require("node:child_process");
const path = require("node:path");

const selfRoot = path.resolve(__dirname, "..");

function candidates() {
  const configured = process.env.CITIES2_MCP_PYTHON;
  const values = [];
  if (configured) {
    values.push({ command: configured, args: [] });
  }
  if (process.platform === "win32") {
    values.push({ command: "py", args: ["-3"] });
  }
  values.push({ command: "python3", args: [] });
  values.push({ command: "python", args: [] });
  return values;
}

function findPython() {
  for (const candidate of candidates()) {
    const result = spawnSync(candidate.command, [...candidate.args, "-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"], {
      stdio: "ignore",
      windowsHide: true,
    });
    if (result.status === 0) {
      return candidate;
    }
  }
  return null;
}

function uniquePaths(values) {
  const seen = new Set();
  const paths = [];
  for (const value of values) {
    if (!value) {
      continue;
    }
    const resolved = path.resolve(value);
    const key = process.platform === "win32" ? resolved.toLowerCase() : resolved;
    if (!seen.has(key)) {
      seen.add(key);
      paths.push(resolved);
    }
  }
  return paths;
}

function invocationForRoot(pluginRoot) {
  const vendoredScript = path.join(pluginRoot, "vendor", "run_server.py");
  if (fs.existsSync(vendoredScript)) {
    return { args: [vendoredScript], env: process.env };
  }

  const vendoredPackageServer = path.join(pluginRoot, "vendor", "cities2_mcp", "mcp_server.py");
  if (fs.existsSync(vendoredPackageServer)) {
    const env = { ...process.env };
    env.PYTHONPATH = [path.join(pluginRoot, "vendor"), env.PYTHONPATH].filter(Boolean).join(path.delimiter);
    return { args: ["-m", "cities2_mcp.mcp_server"], env };
  }

  const sourceServer = path.join(pluginRoot, "cities2_mcp", "mcp_server.py");
  if (fs.existsSync(sourceServer)) {
    const env = { ...process.env };
    env.PYTHONPATH = [pluginRoot, env.PYTHONPATH].filter(Boolean).join(path.delimiter);
    return { args: ["-m", "cities2_mcp.mcp_server"], env };
  }

  return null;
}

function serverInvocation() {
  const checkedRoots = uniquePaths([selfRoot, process.env.PLUGIN_ROOT, process.env.CLAUDE_PLUGIN_ROOT]);
  for (const root of checkedRoots) {
    const invocation = invocationForRoot(root);
    if (invocation) {
      return invocation;
    }
  }

  console.error(`Unable to locate Cities2-MCP server files. Checked: ${checkedRoots.join("; ")}.`);
  process.exit(1);
}

const python = findPython();
if (!python) {
  console.error("Cities2-MCP requires Python 3.10 or newer. Set CITIES2_MCP_PYTHON to a Python interpreter if it is not on PATH.");
  process.exit(127);
}

const invocation = serverInvocation();
const child = spawn(python.command, [...python.args, ...invocation.args, ...process.argv.slice(2)], {
  env: invocation.env,
  stdio: ["inherit", "inherit", "inherit"],
  windowsHide: true,
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 1);
});

child.on("error", (error) => {
  console.error(`Unable to start Cities2-MCP: ${error.message}`);
  process.exit(1);
});
