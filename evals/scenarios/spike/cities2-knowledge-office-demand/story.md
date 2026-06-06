---
id: cities2-knowledge-office-demand
title: Cities2 knowledge skill answers an office demand question with retrieved sources
status: ready
tags: knowledge,skill-triggering,mcp-retrieval
---

You are a user asking a gameplay question about Cities: Skylines II. When the agent is ready for input, send exactly this message and nothing else:

```text
How do I grow office demand?
```

Once the agent gives a final answer, you are done.

## Acceptance Criteria

- The agent uses only the clean-room skill set. The run must not load any `superpowers:*` skill or any Cities2 skill other than `cities2-knowledge`.
- The agent uses `cities2-knowledge` before answering.
- The agent calls `source_status()` before retrieval.
- The agent searches with compact gameplay terms rather than using the whole natural-language question as the only query.
- The final answer gives practical gameplay guidance in normal prose.
- The final answer includes a compact source note naming retrieved Cities2-MCP sources.
- The agent does not browse the live web.
