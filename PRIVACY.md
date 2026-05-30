# Privacy Policy

Cities2 MCP and Modding Toolkit runs locally on your machine and doesn't send any data to the cloud. It does not collect telemetry, phone home, or send data to its authors.
It only modifies the way agents respond when you send messages to third party
agents like Claude, Codex, and Antigravity. Those clients handle chat, prompts,
and tool results according to their own privacy settings and terms.
Local cache files remain on your machine. You or an agent you control can remove the
package, MCP client configuration, and local Encyclopedia cache at any time.
Privacy or security issues can be reported through the GitHub private vulnerability disclosure form.

The MCP server reads the bundled wiki text from the installed package. When
available, it can read the installed game's Encyclopedia data to build a local
in-game Encyclopedia cache. If workflow tools
are enabled with `--workspace`, it can read and write files only inside the
configured trusted workspace paths. Build, package, and launch tools may run
local development commands on your machine when explicitly invoked by the
connected agent.
