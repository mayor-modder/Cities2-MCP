---
schema_version: 1
title: Economy 2.0 Developer Diaries
slug: economy-2-0-developer-diaries
source_type: developer_diary_series
source_url: https://forum.paradoxplaza.com/forum/developer-diary/economy-2-0-dev-diary-1.1682626/
published_at: 2024-06-03
publication_date_basis: source_metadata
creators: Colossal Order development team
organizations: Colossal Order; Paradox Interactive
report_created_at: 2026-07-20
report_updated_at: 2026-07-20
event: Economy 2.0 developer diary series
game_version: 1.1.5f1 prerelease
---

# Economy 2.0 Developer Diaries

## Executive summary

These two linked diaries explain the June 2024 Economy 2.0 redesign. Colossal Order deliberately removed hidden safeguards and made economic outcomes more responsive: government subsidies disappeared, imported services gained a population-scaled fee and opt-in policy, service upkeep rose, household and zone demand changed, production and prices were rebalanced, and rent became a shared tenant expense based on land, zone, level, lot, and space.

The reports' most useful diagnostic lesson is that several visible complaints became income- and flow-based. A household temporarily short of cash should reduce consumption before reporting high rent; unemployment can eventually force move-out; residential density demand depends on household size and wealth; commercial demand follows household consumption; and companies need time to recompute staff and production after a major patch or save load.

## Source context and temporal scope

Part one was published on 2024-06-03 and part two on 2024-06-10. Both describe the changes that shipped in patch `1.1.5f1`. Their sequence is intentionally intertwined: the first covers finance, demand, education, employment, production, wages, and prices; the second covers rent, removable service upgrades, and migration of existing saves.

Later patches continued to rebalance the economy, demand, homelessness, education, services, and companies. These diaries are authoritative for the intent and initial `1.1.5f1` model, not every current result.

## Findings

### The redesign traded safeguards for legibility

Government subsidies were removed because their scaling with expenses concealed poor finances and reduced consequences. City-service upkeep increased, and importing ambulances, hearses, fire engines, police, or garbage service from outside gained a fee that scaled with population.

The new `Import City Services` policy was disabled by default and initially controlled imports as one all-or-nothing toggle. This source therefore dates any advice that assumes free automatic outside assistance.

### Demand follows household composition and consumption

Residential density demand was tied more closely to household size and wealth. Low density is generally more expensive because one household bears the building's rent and upkeep; medium and high density share those expenses. Wealthier households and families prefer more space, while lower-wealth and single households support denser housing demand.

The mix of households spawning was described as dependent on average happiness, homelessness, residential taxes, school capacity, and open jobs. Commercial demand was tied to household consumption after rent and garbage fees, and company selection was adjusted to better match the products residents consume. Industry and office demand were brought closer to the scale of other zones, while industry received more workplaces.

### Education, sickness, and unemployment affect labor supply

Children attend elementary school when a place exists, teens became more likely to attend and graduate high school, and adults without a diploma gained a small chance to return. Teens and adults can work, but sick or injured citizens do not count as employable until they recover.

Unemployed citizens receive support only temporarily. If suitable work remains unavailable, they eventually cannot afford rent and leave. Work at an outside connection remained possible but became less desirable.

### Production and prices were made more tunable

Work required per product changed from a start-of-game calculation to configured values, allowing direct balance tuning. Overall work and production were adjusted, reducing profits and tax receipts. Resource pricing was split so industrial users buy production inputs at a discounted price while commercial companies pay the normal price; consumer pricing combines stages of the chain. Wages increased to support rent and consumption.

### Rent and building condition became tenant driven

The virtual landlord was removed. Renters share building upkeep equally, and the diary gives the formula `Rent = (LandValue + (ZoneType * Building Level)) * LotSize * SpaceMultiplier`. High-rent notifications became based on income rather than current cash balance. A temporarily cash-poor household reduces consumption; a structurally underpaid household complains, seeks cheaper housing, or moves out.

Full upkeep payments increase building condition toward the next level. Failure to pay decreases condition by the same progression and can eventually cause collapse.

### Service upgrades became individually editable

Extensions can be deactivated or deleted. Sub-buildings can be removed, relocated, or switched off and no longer need to touch the main building, provided they remain within their allowed radius and have the required pedestrian or road connection. This is a general composition rule useful beyond the economy itself.

### Existing saves require a settling period

The diaries warned that old saves would experience an adjustment: lost subsidies and higher service costs can create an immediate deficit; demand bars can swing; industry can hire more workers; companies can reduce staff to become profitable; unemployment can rise; and households can change density or move.

The recommendation to let calculations catch up is not a claim that every long-running problem self-corrects. Persistent deficits, unemployment, or rent stress still require diagnosis.

## Existing corpus overlap

The wiki contains the released patch notes and current economy, demand, rent, education, and service pages. Those sources are stronger for present behavior. This report adds a connected causal explanation and preserves the exact initial rent formula, save-transition expectations, and rationale for removing subsidies.

The earlier Economy and Production diary is useful for the underlying supply-chain model but is superseded here on subsidies, production work, pricing, wages, and demand.

## Implications for Cities2 modding

Economy mods must be tested against income, cash balance, consumption, rent, building condition, workforce, production, and taxes as separate variables. Reproducing a high-rent icon from pre-`1.1.5f1` logic can be incorrect even if household cash looks low.

Migration tests should use both new and mature saves and allow controlled settling time. Simulation mods are especially likely to need updates across economic overhauls.

Service-upgrade tools should preserve radius and access rules when relocating sub-buildings. A visually valid placement can remain functionally disconnected.

## Implications for Cities2-MCP

Cities2-MCP should retrieve this report for questions about the Economy 2.0 transition, removal of subsidies, service-import fees, density demand, high rent, building condition, or suddenly changed unemployment after loading an old save.

Newer patch material must rank above this report for current tuning. The useful answer pattern is to explain the `1.1.5f1` causal model, then state any later change.

## Uncertainties and transcript corrections

The diaries do not expose every coefficient, update interval, configured production value, wage, or import fee. The printed rent formula may have been revised later and should not be treated as a stable API contract.

The MHTML punctuation was normalized. Forum replies were excluded except that no reply is required to understand the official posts.

## Sources

- Colossal Order, Economy 2.0 Dev Diary #1, published 2024-06-03: https://forum.paradoxplaza.com/forum/developer-diary/economy-2-0-dev-diary-1.1682626/
- Colossal Order, Economy 2.0 Dev Diary #2, published 2024-06-10: https://forum.paradoxplaza.com/forum/developer-diary/economy-2-0-dev-diary-2.1682628/
- Cities: Skylines II Wiki, Patch `1.1.X`: https://cs2.paradoxwikis.com/Patch_1.1.X
- Cities: Skylines II Wiki, Economy: https://cs2.paradoxwikis.com/Economy
