---
schema_version: 1
title: Cities: Skylines II - Spring Cleaning Livestreams
slug: spring-cleaning-livestreams
source_type: developer_livestream_series
source_url: https://www.youtube.com/watch?v=ydBM34D0SL4
published_at: 2026-04-22
publication_date_basis: source_metadata
creators: Sini; Zoe
organizations: Iceflake Studios; Paradox Interactive
report_created_at: 2026-07-19
report_updated_at: 2026-07-19
event: Cities: Skylines II developer livestream series
game_version: 1.5.7f1 prerelease and release
---

# Cities: Skylines II - Spring Cleaning livestreams

## Executive summary

The April 22 and April 29 Spring Cleaning streams are best treated as one source series. The first previews patch `1.5.7f1` in a new vanilla city; the second resumes that city on release day, recaps the same features, and asks players about their first experience with the patch. Their evidentiary roles differ: April 22 shows intended behavior before release, while April 29 demonstrates the released build but is still an informal livestream rather than a controlled validation.

Most shipped changes are documented more precisely in City Corner #5, the Paradox Mods developer diary, and the final patch notes. The streams add useful practical interpretation. The Historic Building toggle freezes both a building's level and appearance and prevents abandonment, making it a manual tool for preserving lower-level visual variety. Toolbar scaling affects the toolbar and some associated elements rather than serving as a second global text-size control. The dog-population change affects household pet limits and the generation of new households rather than deleting existing pets. Iceflake also presented the benchmark as a common evidence-gathering tool for performance discussions, although the hosts did not run it on stream.

For modding, the written release material supplies the most important operational fact: the Paradox SDK update required script mods to be recompiled. The subsequent `1.5.8f1` hotfix and postmortem materially qualify the optimistic patch-day discussion. The SDK change caused severe startup delays when mods added localization strings, with the cost multiplied across affected mods; Iceflake acknowledged that its roughly 100-mod test set had not caught the problem and committed to broader mod testing.

## Source context and temporal scope

The first official stream was published on 2026-04-22 and runs approximately 92 minutes. Community manager Sini represented Iceflake Studios, while Paradox community ambassador Zoë played a prerelease build and began the city reused in later streams. The second stream was published on 2026-04-29, runs approximately 117 minutes, and explicitly identifies itself as patch day. It continues the same city, revisits features shown the previous week, and discusses the now-released `1.5.7f1` patch.

The two broadcasts are therefore intertwined rather than independent talks. This report combines them while preserving the preview/release boundary. Claims made on April 22 describe a development build and intended patch behavior. April 29 comments describe the release-day state but predate the May 5 hotfix and postmortem. Current behavior must be checked against later patch sources.

Both streams are conversational. The hosts answer live questions, joke about the demonstration city, and often paraphrase patch notes from memory. Exact shipped behavior, version numbers, and compatibility requirements should be taken from the written first-party material. The streams are most valuable for feature semantics, demonstrations, qualifications, and historical context.

## Findings

### Historic Building is a simulation lock as well as an appearance tool

The streams repeatedly demonstrate the new Historic Building toggle on residential, commercial, and industrial buildings. Enabling it preserves the building's current appearance by preventing it from leveling up or being downgraded, and Sini adds that it will not be abandoned. The April 29 stream repeats the same explanation on the release build.

This makes the option more consequential than a cosmetic skin lock. A player can mark selected level-one or level-two buildings as historic so that neighboring buildings continue to level while the district retains visual variation. The tradeoff is that the marked building also gives up future level progression. Near the end of the second stream, the hosts suggest a labor-intensive way to obtain matching buildings on a street: allow buildings to regrow until the desired model appears, then mark each one historic. They correctly frame ploppable-building mods as a more natural solution for exact composition.

The patch notes confirm the two core rules—no leveling and no abandonment—but do not explain this district-design workflow as clearly as the live demonstration.

### Toolbar scaling and transparency are scoped UI controls

The new settings separate toolbar size, existing text scaling, and interface transparency. The April 22 demonstration explicitly notices that reducing toolbar size does not make all text and panels tiny. The final patch notes are more precise: toolbar scaling affects buttons and some other toolbar elements, while transparency affects toolbar and panel backgrounds.

The stream is useful because the settings are shown at both extremes and compared with the preexisting text-size option. Toolkit answers should not describe toolbar scaling as global UI scaling or imply that it replaces accessibility text scaling.

The same patch added a universal mod button in the main interface so mod authors could place their tools in a unified menu. This is documented in the patch notes but receives little substantive technical discussion in the streams.

### The benchmark was introduced as shared performance evidence

The April 22 stream opens the new Benchmark entry under the main-menu options and explains that running it performs an automated camera sequence before reporting CPU, frame-rate, and GPU information. Sini presents it as a way for players to understand their systems and for Iceflake to have more concrete performance discussions with the community.

The hosts deliberately do not execute the benchmark while broadcasting because they are concerned about its resource demands interacting with the streaming setup. The stream therefore documents the feature's location and intended use, not benchmark results or proof of a performance improvement. The written patch notes add the `-benchmark` launch parameter for starting it directly.

Later versions added or corrected benchmark behavior, so `1.5.7f1` screenshots and output fields should not automatically be treated as current. In particular, the `1.5.9f1` known issues later noted that the displayed refresh rate could be fixed at 60 Hz regardless of the monitor's actual refresh rate.

### Taxi move-in traffic and dog population changed prospectively

The preview shows new residents arriving without taxis, and the hosts report seeing no taxi surge. Sini explains that citizens were stopped from moving in and out by taxi to reduce the early traffic jams created by taxi-heavy migration. This is an informal observation in one new city rather than a controlled before-and-after test; it does not prove that early traffic congestion was eliminated.

The dog change is described more carefully than the jokes in the transcript suggest. Iceflake adjusted household pet limits and spawn probabilities so that households with implausibly large numbers of dogs would become unlikely. The patch notes specify that this affects new households, including new households generated in existing saves. It did not delete every dog already present in a save. In the preview city, the hosts later count 21 dogs among just under 1,900 residents, but that snapshot is illustrative rather than a target ratio or balance specification.

### Demand and economy fixes targeted incorrect inputs and stuck states

The streams summarize the office-demand problem as demand no longer rising correctly. The written patch notes identify multiple causes: occupied signature offices were incorrectly treated as available for sale; office demand used incorrect citizen data; and a multiplier workaround caused too many Software companies to spawn. Production statistics were also changed to sample a longer period so time-of-day variation caused less volatility.

Related fixes corrected permanently depressed demand from mixed housing and from a small number of customerless commercial buildings. Commercial demand was changed to consider average shop stock. The specificity matters: the patch did not replace the entire demand model, and a city with low demand after `1.5.7f1` is not necessarily still experiencing one of these resolved bugs.

The patch also rebalanced elementary-versus-high-school demand, fixed leisure participation being restricted to study time, addressed some offices ceasing production or trade, and fixed building upgrades that could stall when delivery processing was skipped on certain update frames. These are primarily patch-note findings; the livestream does not expose the underlying systems or code paths.

### Transport, outside connections, and Bridges & Ports fixes were discrete

On April 29, Sini calls out the fix for public-transport vehicles becoming stuck in a permanent boarding state at busy stops. The final Paradox notes name buses and trams. The patch also fixed non-highway outside connections and port-mail-transfer pathfinding.

For Bridges & Ports, commercial and industrial buildings had failed to use DLC ports for imports even when goods were available there, relying on outside connections instead. The stream paraphrases this as the ports not importing or "not porting," while the written note precisely locates the defect in building selection of port-supplied goods. This should not be generalized into a rewrite of cargo simulation or proof that every port-flow issue was fixed.

### Paradox Mods changed substantially, with an immediate compatibility cost

The associated Paradox Mods diary describes a wider workflow update than the streams cover. Patch `1.5.7f1` updated the Paradox SDK and Mods UI, enabled shared playsets, added up to three parallel downloads, improved progress tracking and responsiveness, allowed browsing and playset management while downloads continued, changed the on-disk folder structure, removed the Beta label, and required a thumbnail for publishing assets.

The release notes warn that script-mod creators had to recompile against the updated SDK. At the beginning of the April 29 stream, the hosts ask players to be patient while volunteer modders update their work. A same-day problem report should therefore begin by checking whether every script mod had a `1.5.7f1`-compatible rebuild rather than assuming the base-game patch alone was at fault.

The release introduced a separate mod-loading regression that the stream could not yet account for. On May 5, hotfix `1.5.8f1` fixed long startup times. Iceflake's postmortem says mods adding localization entries triggered a heavy reinitialization of the Paradox Mods platform, and the cost multiplied with the number of affected code or asset mods. The studio acknowledged that its test set contained only about 100 mods, said it should have caught the problem, and committed to a significantly larger set and improved mod testing. This later first-party account supersedes any impression from the patch-day broadcast that compatibility work ended with recompilation.

### Performance and traffic remained active priorities, not dated promises

Asked on April 29 what Iceflake would work on next, Sini points to previously discussed performance work and traffic improvement as continuing priorities, then says she does not know which item will be next. This is consistent with City Corner #4's performance discussion, but it is not a schedule or commitment to a particular patch.

She also says multiplayer support had not been discussed in her experience. That is an informal, role-limited answer—not a permanent technical ruling or product announcement. Jokes, viewer suggestions, planned stream builds, and comments such as making better tornadoes are not roadmap evidence.

## Existing corpus overlap

The wiki corpus already contains the full `1.5.7f1` patch list in `Patch 1.5.X` and indexes City Corner #5 and Updates for Paradox Mods under developer diaries. Those written sources are the better reference for exhaustive changes, exact component versions, and known issues.

The unique value of the combined livestream report is narrower: it establishes the preview-to-release sequence; demonstrates Historic Building as a way to preserve lower-level district variety; distinguishes toolbar sizing from global text scaling; explains that the dog change applies to newly generated households rather than deleting existing pets; and records the benchmark's intended role in performance conversations. The streams also preserve cautious answers about ongoing performance, traffic, and multiplayer discussions.

The May 5 hotfix postmortem adds information not available during either broadcast and is especially useful to the modding toolkit. It connects the startup regression to localization-triggered SDK reinitialization and documents a concrete gap in Iceflake's mod test coverage.

## Implications for Cities2 modding

Mods interacting with building levels, abandonment, or visual replacement should treat Historic Building as state with gameplay consequences. A marked building is intentionally prevented from progressing and abandoning; tools that toggle or emulate it should not present it as appearance-only.

UI mods should distinguish the game's text scaling, toolbar scaling, transparency controls, and universal mod menu. Authors integrating with the universal menu should not infer from the stream that every mod panel automatically inherits toolbar scaling or transparency behavior; that requires runtime or API verification.

Patch-boundary debugging for `1.5.7f1` should check both recompilation and loading behavior. The official release required script mods to be rebuilt, while the later regression affected any code or asset mod adding localization entries. Reports of a slow launch and reports of an incompatible assembly therefore have different likely causes even though both appeared after the same update.

The hotfix postmortem also suggests a concrete testing lesson for toolkit and mod authors: test with realistic playsets, multiple localization-bearing mods, and cumulative startup conditions. A single-mod smoke test or a relatively small curated set can miss multiplicative integration costs.

The benchmark can support reproducible performance reports, but a useful capture should include game version, city/save, simulation speed, graphics settings, hardware, active playset, and benchmark output. The streams do not establish a cross-version scoring standard or a threshold for acceptable performance.

## Implications for Cities2-MCP

This report should be retrieved for questions about the two Spring Cleaning streams, the practical meaning of Historic Building, the scope of UI scaling and opacity, how the dog reduction applied to existing saves, the intended use of the benchmark, and the `1.5.7f1` mod transition.

For a complete `1.5.7f1` change list, Cities2-MCP should prefer the patch page. For Paradox Mods workflow changes, it should prefer the dedicated developer diary. For startup problems after Spring Cleaning, it should also retrieve the `1.5.8f1` hotfix context and distinguish SDK recompilation from the localization-driven loading regression.

Answers must preserve temporal labels. April 22 is prerelease evidence, April 29 is release-day evidence, and May 5 is the later correction. None of them should be silently presented as current behavior after subsequent patches.

The stream's city-building choices and visual comparisons can support player guidance, but they are demonstrations rather than controlled tests. Assertions such as "the taxi change fixes early traffic" or "21 dogs per 1,900 residents is the intended ratio" would overstate the evidence.

## Uncertainties and transcript corrections

The supplied transcripts are auto-generated and contain recurring errors in names and technical terms. Normalized forms include Iceflake Studios, Sini, Zoë, Historic Building, Paradox Mods, Bridges & Ports, toolbar scaling, UI transparency, benchmark, office demand, and permanent boarding.

The first stream shows a prerelease build, and neither stream performs controlled measurements of taxi traffic, dog generation, demand behavior, port use, or performance. Visual observations in the demonstration city cannot establish global balance outcomes.

The Historic Building panel text quoted on stream says a marked building will not level up or be downgraded, while Sini and the patch notes additionally say it will not be abandoned. This report retains the broader first-party rule but does not infer the exact internal implementation.

The April 29 answers about future work are qualified and sometimes explicitly uncertain. They should not be converted into promises, deadlines, or evidence that an unmentioned feature was rejected. The May 5 hotfix account is later evidence and is intentionally separated from what the hosts knew on patch day.

## Sources

- Iceflake Studios and Paradox Interactive, Cities: Skylines II - Spring Cleaning, published 2026-04-22: https://www.youtube.com/watch?v=ydBM34D0SL4
- Iceflake Studios and Paradox Interactive, Cities: Skylines II - Spring Cleaning (Part Two), published 2026-04-29: https://www.youtube.com/watch?v=v_fWzVfLez0
- Paradox Mods team, Updates for Paradox Mods, published 2026-04-22: https://forum.paradoxplaza.com/forum/developer-diary/dev-diary-updates-for-paradox-mods.1917655/
- Iceflake Studios, City Corner #5 - Spring Cleaning, published 2026-04-24: https://forum.paradoxplaza.com/forum/developer-diary/city-corner-5-spring-cleaning.1918052/
- Iceflake Studios, Spring Cleaning - Patch 1.5.7f1, published 2026-04-29: https://www.paradoxinteractive.com/games/cities-skylines-ii/news/patch-notes-spring-cleaning
- Iceflake Studios, Hotfix - Patch 1.5.8f1 and postmortem, published 2026-05-05: https://steamcommunity.com/games/949230/announcements/detail/666112377194808968
- Cities: Skylines II Wiki, Patch 1.5.X: https://cs2.paradoxwikis.com/Patch_1.5.X
- Cities: Skylines II Wiki, Developer diaries: https://cs2.paradoxwikis.com/Developer_diaries
