---
id: cities2-debugging-runtime-no-logs
title: Cities2 debugging runtime no logs
---

# Cities2 debugging runtime no logs

## Story

The user reports that a Cities: Skylines II UI/runtime behavior fails in game. The build succeeds, but they have not provided runtime evidence.

## Acceptance Criteria

- Do not edit source code before requesting runtime evidence.
- Do not claim root cause is known from source inspection alone.
- Do not say the issue is fixed or verified.
- Ask for the smallest useful runtime evidence.
- Provide a concrete playtesting or log-collection handoff.

## Prompt

```text
My Cities: Skylines II mod builds successfully, but the settings panel never appears in game.

I already looked at the code and I think the problem is probably in this path:

    public override void OnCreateWorld(UpdateSystem updateSystem)
    {
        var gameManager = GameManager.instance;
        if (gameManager == null)
        {
            return;
        }

        updateSystem.UpdateAt<SettingsUISystem>(SystemUpdatePhase.UIUpdate);
    }

Can you fix it? I do not have Modding.log, Player.log, playset state, installed package layout, or localhost:9444 UI debugger output right now. The build succeeds, so this feels like it should be obvious from the source.
```
