---
schema_version: 1
title: Development Diary #11 - Citizen Simulation and Lifepath
slug: citizen-simulation-and-lifepath-developer-diary
source_type: developer_diary
source_url: https://forum.paradoxplaza.com/forum/developer-diary/development-diary-11-citizen-simulation-lifepath.1596988/
published_at: 2023-08-28
publication_date_basis: source_metadata
creators: Colossal Order development team
organizations: Colossal Order; Paradox Interactive
report_created_at: 2026-07-20
report_updated_at: 2026-07-20
event: Cities: Skylines II pre-release developer diary
game_version: pre-release
---

# Development Diary #11 - Citizen Simulation and Lifepath

## Executive summary

This pre-release diary describes citizens as the primary agents that connect traffic, education, employment, consumption, health, crime, leisure, and migration. Its most useful unique detail is that decisions were intended to be preference-weighted rather than uniform: age changes how citizens value time, cost, comfort, walking, and goods; education decisions compare immediate wages with future benefit; and leisure or tourism destinations balance attractiveness against travel cost.

The diary is also a useful warning against reading every visible citizen action as cosmetic. Sickness removes workers from productive capacity, low well-being can contribute to crime, shopping creates goods demand and trips, and a household can leave the city when its needs or finances fail. These are launch-era rules and pathfinding, education, homelessness, pets, and demographic behavior have all received later changes.

## Source context and temporal scope

Colossal Order published the diary on 2023-08-28 before release. It explains the intended launch citizen model and the Lifepath journal used to follow an individual resident.

The report treats age-specific preferences and causal relationships as design evidence, not guaranteed current formulas. Later patch notes and current wiki documentation take precedence for observable behavior in a modern save.

## Findings

### Citizens connect major simulations

Citizens live in households, travel, work or study, consume products, use services, become sick or injured, participate in leisure, and may commit crimes. Their trips create traffic, their work affects company output, and their household decisions contribute to zoning demand and migration.

Happiness was described as a combination of well-being and health. Well-being responds to utilities, sewage, garbage, pollution, crime, services, mail, telecom, housing fit, and consumption. Health responds to environmental conditions and healthcare, while sufficiently sick citizens may require an ambulance and cannot work.

### Age changes preferences

The four launch age groups were children, teens, adults, and seniors. The diary says teens emphasize travel cost and walking and may prefer free parking even when it is farther away; adults emphasize time and are more willing to pay fees; and seniors emphasize comfort and proximity. Age also influences preferred goods.

These preferences explain how identical routes or shops can yield different individual choices. They should not be converted into absolute rules: the source describes relative weighting, and later pathfinding updates may have changed the weights or constraints.

### Education and work involve tradeoffs

Citizens choose whether to pursue further education based on current earning opportunity, the expected income benefit of a higher education level, available places, and inherent preference. Teens and adults may instead enter the workforce.

Jobs have education requirements, and higher-level buildings shift their job mix toward more educated labor. An overqualified worker in a lower-tier position supplies the effectiveness of that position rather than the worker's full education advantage. Happiness, sickness, and workforce composition affect company efficiency.

### Crime and leisure emerge from citizen state

Low well-being increases the chance that a citizen becomes a criminal. The diary describes target selection among buildings with high crime probability, an alarm delay that gives police a chance to catch the offender, imprisonment locally or outside the city, and a reset of criminal status after the sentence.

Leisure destination choice weighs the activity's benefit against path cost. Weather and season affect indoor and outdoor appeal. Tourists consider both attraction value and distance from their hotel, and households can travel outside the city for leisure. These rules connect land use and transport accessibility to recreation outcomes.

### Lifepath and Chirper reflect simulated events

Following a citizen exposes significant life events in a Lifepath journal. Chirper messages were intended to be grounded in events and conditions rather than purely random flavor. This makes individual-citizen observation a useful debugging window, though it is not a statistically representative sample of the city.

The diary described pets as cosmetic companions. Later updates changed dog population and behavior, so that statement is historical rather than a current specification.

## Existing corpus overlap

The wiki corpus covers citizens, households, education, pathfinding, traffic, health, crime, and patches. It is the stronger source for current mechanics. This diary adds the integrated causal story and age-weighted travel preferences, education tradeoff, overqualification behavior, tourist hotel-distance factor, and relationship between agent state and productive capacity.

Economy 2.0, later pathfinding patches, Spring Cleaning, and City Corner reports should outrank the 2023 source where they conflict.

## Implications for Cities2 modding

Citizen-behavior mods should be evaluated across cohorts. A change that appears correct for adults may produce unexpected results for teens or seniors because cost, time, comfort, and walking can be weighted differently.

Diagnostics should separate a citizen's state, available choices, path feasibility, preference weights, and final action. Following one Lifepath can reveal a causal sequence, but aggregate samples are needed before concluding that a citywide system is broken.

Health, education, employment, consumption, crime, and travel are coupled. Mod tests need sufficient simulated time and controlled alternatives to distinguish a direct effect from a downstream response.

## Implications for Cities2-MCP

Cities2-MCP should use this report for explanations of why citizens with apparently similar origins and destinations make different travel choices, why sickness can reduce business efficiency, or why attraction accessibility matters to tourists.

Answers must phrase the age preferences as launch-era weighting and retrieve newer pathfinding sources first. The source should not be used to claim exact percentages, thresholds, or present-day dog behavior.

## Uncertainties and transcript corrections

The diary supplies qualitative factors rather than complete decision formulas. It does not reveal random distributions, utility weights, system order, ECS type names, or present balance.

The archived MHTML's punctuation artifacts were normalized. Community comments were not used as developer evidence.

## Sources

- Colossal Order, Development Diary #11 - Citizen Simulation and Lifepath, published 2023-08-28: https://forum.paradoxplaza.com/forum/developer-diary/development-diary-11-citizen-simulation-lifepath.1596988/
- Cities: Skylines II Wiki, Citizens: https://cs2.paradoxwikis.com/Citizens
- Cities: Skylines II Wiki, Patches: https://cs2.paradoxwikis.com/Patches
