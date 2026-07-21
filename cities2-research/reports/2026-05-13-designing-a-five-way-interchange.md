---
schema_version: 1
title: Cities: Skylines II - Designing a Five-Way Interchange
slug: designing-a-five-way-interchange
source_type: developer_livestream
source_url: https://www.youtube.com/watch?v=liuqwdHj720
published_at: 2026-05-13
publication_date_basis: source_metadata
creators: Sini; Zoe
organizations: Iceflake Studios; Paradox Interactive
report_created_at: 2026-07-19
report_updated_at: 2026-07-19
event: Cities: Skylines II developer livestream
---

# Cities: Skylines II - Designing a Five-Way Interchange

## Executive summary

This May 2026 livestream combines an informal five-way-interchange build by Paradox community ambassador Zoë with community manager Sini's summaries of answers from Iceflake Studios' Reddit AMA. It is valuable primarily as a secondary source and as evidence of a few topics not clearly present in the written AMA: a possible accessibility review, discussion of undo support with particular interest in terrain editing, and hopes to expand recoloring or historical-building functionality.

For technical questions about logistics, traffic, performance, citizen models, or mod integration, the written AMA is the stronger source because it preserves direct answers from Iceflake's lead programmer, producer, QA representative, game designer, and community manager. The stream should not be used to turn tentative discussion into a roadmap commitment.

## Source context and temporal scope

The video was streamed on the official Cities: Skylines channel on 2026-05-13. Sini represented Iceflake Studios as community manager, while Zoë built the interchange and discussed community questions. Sini repeatedly explained that she was recalling or paraphrasing the May 8 AMA, was not the team's technical authority, and recommended consulting the written answers for exact details.

The stream occurred five days after the formal AMA and captures the team's public messaging at that moment. Later City Corners and patches supersede its statements about work in progress. The road-building portion is a live player demonstration rather than an engineering explanation from a traffic or tools programmer.

## Findings

### Interchange-building method

Zoë approached the five-way junction iteratively: connect the highway approaches, create ramps by adding or separating lanes, check that every origin can reach every destination, and adjust terrain where geometry prevents a clean connection. This is practical build-along advice, not a statement about the simulation's internal lane or pathfinding implementation.

The exercise nevertheless illustrates why interchange design is difficult in the current toolset. Many connections must be created and checked manually, terrain mistakes are easy to make, and late lane changes can undermine a geometrically valid design. Those observations help explain the community interest in stronger road controls, terrain undo, and traffic-behavior improvements.

### Accessibility review

In response to requests involving control rebinding, head-mouse use, color-vision support, and a dyslexia-friendly font, Sini said the team had discussed accessibility and wanted the game to be reviewed or tested, with improvements guided by the results. She did not announce a scheduled audit, supported feature list, or delivery date. This is evidence of intent to evaluate accessibility, not confirmation of any particular accommodation.

### Undo and terrain editing

Sini said undo functionality had been discussed and was badly needed in her view. Terrain editing was singled out because a small mistake can leave a deep hole or large mound that is difficult to restore precisely. The wording indicates a recognized usability gap and internal discussion, but not an implementation commitment.

### Recoloring and historical buildings

The stream expressed hope that the recoloring tool and historical-building option could be expanded. No concrete scope or timing was given. The related AMA answer about broader city history and character was also explicitly speculative and described as potentially time-consuming.

### Traffic work

Sini described traffic, traffic AI, and vehicle behavior as active work and specifically referred to lane changes between road nodes. She also stressed that simulation changes affect many other systems and must be made carefully. These statements align with direct AMA answers about late lane changes, U-turns, pathfinding weights, and incremental traffic changes; the AMA should be cited for the precise technical claim.

### Topics repeated from the AMA

Most other substantive material repeats the written AMA in abbreviated form: making hidden simulation information understandable, considering more player control over production and trade, improving farms and specialized industries, adding citizen activity animations, retaining Popul8, treating pathfinding rather than citizen models as the main performance problem, learning from popular mods, and releasing smaller changes that are easier to diagnose and hotfix.

The stream also repeated that macOS was not on the roadmap at that time and that deep traffic-signal micromanagement might remain better suited to mods. Because these statements are time-sensitive and paraphrased, the written AMA and later official posts should be preferred.

### Material excluded as evidence

Suggestions for creator packs, disasters, historical-era play, scenarios, offices, and other additions were often community ideas or personal wishes. They are not development commitments. A vague tease that the biggest improvement since launch was still to come contained no verifiable detail and is not useful as a factual finding.

## Existing corpus overlap

The wiki corpus's `Developer diaries` page briefly indexes the City Corner series but does not preserve this stream, the full AMA, or the stream-only accessibility and undo discussion. The new AMA research report contains the stronger version of nearly all technical subjects repeated here.

The existing ECS conference report covers internal architecture at a much deeper level than this stream. The livestream adds product-direction and usability signals rather than public APIs or new ECS implementation details.

## Implications for Cities2 modding

The stream identifies feature gaps that may attract mod experimentation, especially terrain recovery, accessibility, road-building assistance, historical-building controls, and richer information displays. It does not establish that the necessary internal hooks are stable or that a vanilla implementation will appear.

Traffic mods should not interpret the hosts' lane-change discussion as a complete model of the problem. The direct AMA describes many interacting cases and performance constraints, so any intervention should be validated against current assemblies, large-city behavior, and later patches.

The distinction between community wishes, a community manager's preferences, internal discussion, active work, and confirmed delivery is especially important for mod authors deciding whether to invest in a feature. Only active or shipped behavior should affect compatibility decisions; tentative developer interest is useful context but not a dependency.

## Implications for Cities2-MCP

The toolkit should retrieve this report for questions specifically about the May 13 livestream, its five-way-interchange demonstration, the accessibility-review statement, terrain undo discussion, and tentative expansion of recoloring or historical-building controls.

For logistics, performance, citizen models, traffic internals, engine constraints, or mod-integration policy, retrieval should prefer the May 2026 AMA report and use this livestream only as corroboration. Results should link the original YouTube video and identify the 2026-05-13 date.

Current feature or roadmap answers require later sources. If a later patch implements or rejects a topic discussed here, the later primary source should supersede this report while the report remains useful as historical context.

## Uncertainties and transcript corrections

The supplied transcript is auto-generated and contains frequent name and terminology errors. Normalized forms include Iceflake Studios, Sini, Zoë, Timo, Reddit AMA, Linux, pathfinding, lanes, and road nodes. Some sentences are incomplete or merge unrelated speakers.

Sini explicitly qualified her technical recollection and directed viewers to the AMA. Consequently, this report uses the written AMA to resolve duplicated claims and retains the stream as the authority only for statements made uniquely during the broadcast.

The visual state of the interchange, lane arrows, terrain, and UI cannot be reconstructed fully from text. The report does not infer road geometry or traffic-tool behavior that the transcript alone cannot establish.

## Sources

- Iceflake Studios and Paradox Interactive, original livestream, streamed 2026-05-13: https://www.youtube.com/watch?v=liuqwdHj720
- Iceflake Studios, Reddit AMA announcement and full discussion, published 2026-05-06: https://www.reddit.com/r/CitiesSkylines/comments/1t59nyo/were_iceflake_studios_the_new_development_team/
- Iceflake Studios, City Corner #4 - A Peek into Performance, published 2026-04-09: https://steamcommunity.com/games/949230/announcements/detail/532128384944178048
- Colossal Order, Behind the Scenes #5: Citizen Characters, published 2023-10-21: https://colossalorder.fi/news/behind-the-scenes-5-citizen-characters/
- Cities: Skylines II Wiki, Developer diaries: https://cs2.paradoxwikis.com/Developer_diaries
