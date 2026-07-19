# Anthropic distribution

Claude installs use the shared catalog `mayor-modder/Mayor-Modder-Cities2-Plugins` through the Claude plugin marketplace. The generated package snapshot is exported there from `dist/integrations/anthropic/claude-plugin/` during release work.

The Claude plugin vendors the Python MCP server, the bundled Cities: Skylines II Wiki corpus, curated research reports, the skill files, and the local project workflow templates. It can separately read the user's locally extracted game encyclopedia when Cities: Skylines II is installed; that encyclopedia content is not bundled.

The Claude plugin includes five agent skills: `cities2-knowledge`, `cities2-modding`, `cities2-mod-review`, `cities2-mod-debugging`, and `cities2-mod-release`.

For install steps, use [INSTALL.md](../../INSTALL.md#claude).
