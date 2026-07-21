from __future__ import annotations

import json

from cities2_mcp import __version__ as VERSION

NAME = "cities2-mcp"
DISPLAY_NAME = "Cities2 MCP and Modding Toolkit"
AUTHOR = {"name": "mayor-modder", "url": "https://github.com/mayor-modder"}
CATALOG_REPO = "mayor-modder/Mayor-Modder-Cities2-Plugins"
CATALOG_NAME = "mayor-modder-cities2-plugins"
CATALOG_DISPLAY_NAME = "Mayor Modder Cities2 Plugins"
REPO_URL = "https://github.com/mayor-modder/Cities2-MCP"
LICENSE = "MIT"
PRIVACY_URL = "https://github.com/mayor-modder/Cities2-MCP/blob/main/PRIVACY.md"
TERMS_URL = "https://github.com/mayor-modder/Cities2-MCP#license"
KEYWORDS = ["cities-skylines-ii", "mcp", "modding", "gameplay", "agent-skills"]

SKILL_NAMES = (
    "cities2-knowledge",
    "cities2-modding",
    "cities2-mod-review",
    "cities2-mod-debugging",
    "cities2-mod-release",
)

PUBLIC_DESCRIPTION = "Cities: Skylines II wiki, encyclopedia, and mod workflow tools for AI agents."
CLAUDE_DESCRIPTION = "Cities: Skylines II wiki, encyclopedia, and mod workflow tools for Claude."
CODEX_DESCRIPTION = "Cities: Skylines II wiki, encyclopedia, and mod workflow tools for Codex."
ANTIGRAVITY_DESCRIPTION = PUBLIC_DESCRIPTION
CLAUDE_MARKETPLACE_DESCRIPTION = "Claude plugin marketplace for Cities2 MCP and Modding Toolkit."

CLAUDE_USER_CONFIG = {
    "trusted_workspace": {
        "type": "directory",
        "title": "Trusted mod projects folder",
        "description": "Optional. Choose the parent folder that contains your mod projects to enable scaffold, edit, analyze, build, and package workflows for projects underneath it.",
        "required": False,
    },
    "mods_dir": {
        "type": "directory",
        "title": "Cities: Skylines II Mods folder",
        "description": "Optional. The plugin normally uses the standard local Mods folder; set this only if your Mods folder is somewhere else.",
        "required": False,
    },
    "game_dir": {
        "type": "directory",
        "title": "Cities: Skylines II install folder",
        "description": "Optional. The plugin normally discovers Steam installs automatically; set this only if encyclopedia search cannot find your game.",
        "required": False,
    },
    "locale_cok": {
        "type": "file",
        "title": "Locale.cok file",
        "description": "Optional. Direct path to Locale.cok; use only when automatic game discovery cannot find the in-game encyclopedia file.",
        "required": False,
    },
}

SERVER_ENVIRONMENT_VARIABLES = [
    {
        "name": "CITIES2_MODS_DIR",
        "description": "Optional path to the Cities: Skylines II Mods directory.",
        "isRequired": False,
        "format": "string",
        "isSecret": False,
    },
    {
        "name": "CITIES2_GAME_DIR",
        "description": "Optional path to the Cities: Skylines II install directory when auto-detection cannot find the game.",
        "isRequired": False,
        "format": "string",
        "isSecret": False,
    },
    {
        "name": "CITIES2_LOCALE_COK",
        "description": "Optional path to Locale.cok when the in-game encyclopedia file should be selected directly.",
        "isRequired": False,
        "format": "string",
        "isSecret": False,
    },
]

CODEX_INTERFACE = {
    "displayName": DISPLAY_NAME,
    "shortDescription": "CS2 wiki, encyclopedia, and mod workflows",
    "longDescription": "Cities2 MCP and Modding Toolkit gives Codex local access to the bundled Cities: Skylines II Wiki corpus and curated research reports, the user's locally extracted in-game encyclopedia when available, five agent skills, and mod project workflow tools for trusted workspaces.",
    "developerName": "mayor-modder",
    "category": "Coding",
    "capabilities": ["Read", "Write"],
    "websiteURL": REPO_URL,
    "privacyPolicyURL": PRIVACY_URL,
    "termsOfServiceURL": TERMS_URL,
    "defaultPrompt": [
        "What changed in the latest Cities: Skylines II patch?",
        "Scaffold a Cities: Skylines II UI mod.",
        "Build and package this Cities: Skylines II mod.",
    ],
    "brandColor": "#1F6F78",
    "screenshots": [],
}

# Verbatim copy of the single-line inline node bootstrap currently in
# plugins/cities2-mcp/mcp_config.json. The pieces below concatenate (no
# separators) into the exact original string. The test in Task 2/Step 3 asserts
# byte-equality with the current file, so any drift here fails fast.
ANTIGRAVITY_BOOTSTRAP_JS = (
    "const fs=require('node:fs');const os=require('node:os');const path=require('node:path');"
    "const home=process.env.USERPROFILE||process.env.HOME||os.homedir();"
    "const installed=[path.join(home,'.gemini','antigravity-cli','plugins','cities2-mcp'),"
    "path.join(home,'.gemini','config','plugins','cities2-mcp')];"
    "const workspaceRoots=process.env.CITIES2_MCP_ALLOW_WORKSPACE_PLUGIN_ROOTS==='1'?"
    "[path.join(process.cwd(),'.agents','plugins','cities2-mcp'),"
    "path.join(process.cwd(),'_agents','plugins','cities2-mcp')]:[];"
    "const candidates=[process.env.CITIES2_MCP_PLUGIN_ROOT,process.env.ANTIGRAVITY_PLUGIN_ROOT,"
    "...installed,...workspaceRoots].filter(Boolean);"
    "const root=candidates.find((candidate)=>fs.existsSync(path.join(candidate,'bin','cities2-mcp-launcher.js')));"
    "if(!root){console.error('Unable to locate the installed Cities2-MCP Antigravity plugin. "
    "Set CITIES2_MCP_PLUGIN_ROOT to the plugin directory. Checked: '+candidates.join('; '));process.exit(1);}"
    "const launcher=path.join(root,'bin','cities2-mcp-launcher.js');process.env.PLUGIN_ROOT=root;"
    "process.argv=[process.argv[0],launcher,...process.argv.slice(1)];require(launcher);"
)

_GENERATED_MARKER = (
    "<!-- Generated by cities2_mcp.plugin_packages; "
    "edit canonical sources in cities2_mcp/plugin_metadata.py, not this file. -->"
)


def _dumps(obj: object) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def server_json() -> str:
    return _dumps(
        {
            "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
            "name": "io.github.mayor-modder/cities2-mcp",
            "title": DISPLAY_NAME,
            "description": PUBLIC_DESCRIPTION,
            "repository": {"url": REPO_URL, "source": "github"},
            "version": VERSION,
            "packages": [
                {
                    "registryType": "pypi",
                    "identifier": "cities2-mcp",
                    "version": VERSION,
                    "transport": {"type": "stdio"},
                    "environmentVariables": SERVER_ENVIRONMENT_VARIABLES,
                }
            ],
        }
    )


def claude_plugin_json() -> str:
    return _dumps(
        {
            "name": NAME,
            "displayName": DISPLAY_NAME,
            "version": VERSION,
            "description": CLAUDE_DESCRIPTION,
            "author": AUTHOR,
            "homepage": REPO_URL,
            "repository": REPO_URL,
            "license": LICENSE,
            "userConfig": CLAUDE_USER_CONFIG,
            "keywords": KEYWORDS,
        }
    )


def claude_mcp_json() -> str:
    return _dumps(
        {
            "mcpServers": {
                "cities2-mcp": {
                    "command": "node",
                    "args": [
                        "${CLAUDE_PLUGIN_ROOT}/bin/cities2-mcp-launcher.js",
                        "--workspace",
                        "${CLAUDE_PROJECT_DIR}",
                    ],
                    "env": {
                        "CITIES2_MCP_WORKSPACE": "${user_config.trusted_workspace}",
                        "CITIES2_MODS_DIR": "${user_config.mods_dir}",
                        "CITIES2_GAME_DIR": "${user_config.game_dir}",
                        "CITIES2_LOCALE_COK": "${user_config.locale_cok}",
                    },
                }
            }
        }
    )


def claude_marketplace_entry() -> dict[str, object]:
    return {
        "name": NAME,
        "source": "./integrations/anthropic/claude-plugin",
        "description": CLAUDE_DESCRIPTION,
        "version": VERSION,
        "author": AUTHOR,
    }


def claude_marketplace_json() -> str:
    return _dumps(
        {
            "name": CATALOG_NAME,
            "description": "Mayor Modder Cities2 Claude plugin marketplace.",
            "owner": AUTHOR,
            "plugins": [claude_marketplace_entry()],
        }
    )


def claude_readme_md() -> str:
    skill_lines = "\n".join(f"- `/{name}`" for name in SKILL_NAMES)
    return f"""{_GENERATED_MARKER}

# Cities2 MCP and Modding Toolkit Claude plugin

This is the Claude plugin package for Cities2 MCP and Modding Toolkit. It bundles five user-facing agent skills, the Cities: Skylines II Wiki corpus, curated research reports, project workflow templates, and a plugin-local MCP server launcher. When the game is installed, it can separately read the user's local game encyclopedia; that extracted content is not bundled.

The plugin gives Claude:

{skill_lines}
- the `cities2-mcp` MCP server, started automatically when the plugin is enabled

The plugin `.mcp.json` points at `bin/cities2-mcp-launcher.js`, which runs the vendored Python package from `vendor/cities2_mcp`. In Claude Code, it automatically sets the MCP workspace to the current project via `${{CLAUDE_PROJECT_DIR}}`.

Validate from the repository root:

```sh
claude plugin validate integrations/anthropic/claude-plugin --strict
```
"""


def codex_plugin_json() -> str:
    return _dumps(
        {
            "name": NAME,
            "version": VERSION,
            "description": CODEX_DESCRIPTION,
            "author": AUTHOR,
            "homepage": REPO_URL,
            "repository": REPO_URL,
            "license": LICENSE,
            "keywords": KEYWORDS,
            "skills": "./skills/",
            "mcpServers": "./.mcp.json",
            "interface": CODEX_INTERFACE,
        }
    )


def codex_mcp_json() -> str:
    return _dumps(
        {
            "mcpServers": {
                "cities2-mcp": {
                    "command": "node",
                    "args": ["./bin/cities2-mcp-launcher.js", "--workspace", "."],
                    "cwd": ".",
                }
            }
        }
    )


def codex_marketplace_entry() -> dict[str, object]:
    return {
        "name": NAME,
        "source": {"source": "local", "path": "./plugins/cities2-mcp"},
        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        "category": "Coding",
    }


def codex_marketplace_json() -> str:
    return _dumps(
        {
            "name": CATALOG_NAME,
            "interface": {"displayName": CATALOG_DISPLAY_NAME},
            "plugins": [codex_marketplace_entry()],
        }
    )


def codex_readme_md() -> str:
    head = ", ".join(f"`{name}`" for name in SKILL_NAMES[:-1])
    included = f"{head}, and `{SKILL_NAMES[-1]}`"
    return f"""{_GENERATED_MARKER}

# Cities2 MCP and Modding Toolkit Codex plugin

This is the Codex plugin package for Cities2 MCP and Modding Toolkit. It bundles five user-facing agent skills, the Cities: Skylines II Wiki corpus, curated research reports, project workflow templates, and a plugin-local MCP server launcher. When the game is installed, it can separately read the user's local game encyclopedia; that extracted content is not bundled.

Included skills: {included}.

The plugin `.mcp.json` points at `bin/cities2-mcp-launcher.js`, which runs the vendored Python package from `vendor/cities2_mcp`. Codex currently launches the server from the installed plugin cache, so bundled wiki and research tools work immediately; local game encyclopedia lookup is available when the game is installed. Direct MCP workflow tools may be allowlist-blocked for the project you opened, and the bundled `cities2-modding` skill includes an explicit template-copy fallback for that case.

Install from this repository marketplace:

```sh
codex plugin marketplace add {CATALOG_REPO}
```
"""


def antigravity_plugin_json() -> str:
    return _dumps(
        {
            "name": NAME,
            "description": ANTIGRAVITY_DESCRIPTION,
            "version": VERSION,
        }
    )


def antigravity_mcp_config_json() -> str:
    return _dumps(
        {
            "mcpServers": {
                "cities2-mcp": {
                    "command": "node",
                    "args": ["-e", ANTIGRAVITY_BOOTSTRAP_JS, "--", "--workspace", "."],
                    "cwd": ".",
                }
            }
        }
    )
