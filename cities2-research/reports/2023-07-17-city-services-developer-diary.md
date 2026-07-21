---
schema_version: 1
title: Development Diary #5 - City Services
slug: city-services-developer-diary
source_type: developer_diary
source_url: https://forum.paradoxplaza.com/forum/developer-diary/development-diary-5-city-services.1593161/
published_at: 2023-07-17
publication_date_basis: source_metadata
creators: Colossal Order development team
organizations: Colossal Order; Paradox Interactive
report_created_at: 2026-07-20
report_updated_at: 2026-07-20
event: Cities: Skylines II pre-release developer diary
game_version: pre-release
---

# Development Diary #5 - City Services

## Executive summary

This pre-release diary is useful less as a current catalog of service buildings than as an explanation of how services were intended to participate in the simulation. Coverage is not simply a radius to maximize: households and companies have differentiated needs, unmet needs affect happiness or efficiency, and those outcomes influence rent tolerance, building development, employment, and land value. The diary therefore describes services as inputs to feedback loops rather than isolated bonuses.

Several unusually specific mechanics are documented. Road condition changes travel speed and accident risk; sewage treatment returns purified water and converts pollutants into solid waste; education decisions compare near-term earnings with the benefit of further study; telecom capacity is consumed where citizens live, work, and study; and garbage production varies with building characteristics and citizen education. Some operational details have changed since 2023, so current patch and wiki material must outrank this launch-era model.

## Source context and temporal scope

Colossal Order published the diary on 2023-07-17, before the game's PC release. It describes the intended launch simulation, including features and balance that were subsequently revised by patches such as Economy 2.0 and Spring Cleaning.

This report retains the diary's causal explanations while treating exact costs, capacities, radii, eligibility rules, and service behavior as historical unless confirmed by a newer source. The archived MHTML includes forum discussion; only the official opening post is used for developer claims.

## Findings

### Services satisfy agent needs

Households and companies have different service needs, visible through citizen happiness and company efficiency. Satisfying a need improves the corresponding agent outcome, but uniformly saturating the city with every service is expensive and produces diminishing practical value. The intended management problem is to decide which needs matter where and when.

Land value is affected indirectly. A desirable location lets residents or companies tolerate higher rent, which supports building upgrades and raises the value of the surrounding area. Parks, schools, communications, safety, and other services therefore participate in the land-value system through agent willingness to remain and pay rather than through a simple universal value aura.

### Infrastructure condition has downstream effects

Road-maintenance vehicles patrol the network and restore road condition. As condition falls, vehicles travel more slowly and accidents become more likely. This connects maintenance funding to travel time, emergency workload, and network reliability rather than only to road appearance.

Water comes from surface sources or groundwater reservoirs. Reservoirs have finite replenishment rates and can be contaminated. Sewage treatment can return purified water to the freshwater network, while removed pollutants become solid waste that must be transported to garbage facilities. Water, sewage, and waste are consequently coupled systems.

### Health and waste affect productive capacity

Healthcare supplies a local passive health benefit as well as treatment. Sick or injured citizens cannot work while incapacitated, lowering the efficiency of their employers. Service failures can thus surface as labor and production problems rather than only as a health notification.

Garbage generation depends on building type, zone, level, and size, and the diary states that educated citizens and higher-level buildings produce less. Recycling facilities recover usable resources from the waste stream. Exact rates are not supplied, but the intended model connects education and development to waste demand.

### Education is an agent decision

The five education levels are linked to job complexity and company efficiency. A citizen's choice to continue studying considers the income available now, the expected earnings after further education, and an inherent preference. An education mismatch can leave suitable vacancies unfilled even when the city has unemployed citizens.

### Safety, leisure, post, and telecom are simulated services

Fire and rescue respond to fires, accidents, building collapse, forest fires, and disasters; shelters provide disaster protection. Crime probability is related to citizen well-being, police response time affects whether a suspect is caught, and convicted citizens serve sentences in a local or outside prison before their criminal status is reset. The diary also says prisons produce resources through inmate labor, a launch-era detail requiring current verification.

Leisure choices consider path cost and activity value. Weather and season shift the appeal of indoor and outdoor activities, while tourists weigh an attraction against its distance from their hotel. Parks therefore generate trips and indirect desirability effects rather than functioning only as static scenery.

Telecom bandwidth is consumed by citizens at homes, workplaces, and schools, so both range and capacity matter. The diary's original mail-routing description is particularly time-sensitive: it said cities without a local sorting facility sent outgoing mail outside and could distribute only incoming outside mail. Later mail fixes should take precedence.

## Existing corpus overlap

The bundled wiki documents each service and current patch history in greater operational detail. The diary adds a unified explanation of how needs, service provision, agent behavior, building development, and land value were designed to interact.

The later Economy 2.0, Spring Cleaning, and City Corner material supersedes parts of the launch design, especially service import costs, household finances, homelessness, education balance, and service-building behavior. This report should be retrieved as architectural context, not as an unversioned current manual.

## Implications for Cities2 modding

Service mods should be tested through downstream effects, not only whether a building dispatches vehicles or exposes a radius. Useful checks include agent happiness or efficiency, worker availability, building condition, traffic delay, resource conversion, storage, and trip creation.

Systems that alter one service can affect several others. Changing road condition may change accident load; changing sewage processing may change garbage transport; changing health can change workforce participation. ECS queries and test cities should be designed to observe these connected outcomes.

Exact prefab values and component behavior must be verified against the installed game version. This diary provides hypotheses for inspection, not stable API names or balance constants.

## Implications for Cities2-MCP

Cities2-MCP should use this report to explain why a service problem may present as weak company efficiency, unemployment, building decline, congestion, or land-value pressure. Current wiki and patch pages should be retrieved alongside it for concrete advice.

Answers should distinguish service coverage, capacity, dispatch travel time, and the agent's actual need. A colored coverage overlay does not by itself prove that the service is sufficiently staffed, reachable, or delivering the intended outcome.

## Uncertainties and transcript corrections

The source predates release and many later rebalances. It provides no ECS type names, formulas, thresholds, or stable modding APIs. Exact claims about mail sorting, prison production, education decisions, garbage reduction, and passive service effects require current runtime or documentation verification.

The MHTML snapshot contains typographic decoding artifacts, which were normalized without changing substantive meaning.

## Sources

- Colossal Order, Development Diary #5 - City Services, published 2023-07-17: https://forum.paradoxplaza.com/forum/developer-diary/development-diary-5-city-services.1593161/
- Cities: Skylines II Wiki, City services: https://cs2.paradoxwikis.com/City_services
- Cities: Skylines II Wiki, Patches: https://cs2.paradoxwikis.com/Patches
