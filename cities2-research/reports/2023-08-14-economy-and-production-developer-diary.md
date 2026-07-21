---
schema_version: 1
title: Development Diary #9 - Economy and Production
slug: economy-and-production-developer-diary
source_type: developer_diary
source_url: https://forum.paradoxplaza.com/forum/developer-diary/development-diary-9-economy-production.1595744/
published_at: 2023-08-14
publication_date_basis: source_metadata
creators: Colossal Order development team
organizations: Colossal Order; Paradox Interactive
report_created_at: 2026-07-20
report_updated_at: 2026-07-20
event: Cities: Skylines II pre-release developer diary
game_version: pre-release
---

# Development Diary #9 - Economy and Production

## Executive summary

This launch-era diary explains the intended economic graph behind visible zoning and tax controls. Households, companies, city services, and outside connections exchange money and resources; companies choose locations by balancing rent, workforce, suppliers, customers, and transport cost; and resource weight and required storage space shape which production chains benefit most from local supply and cargo infrastructure.

The most reusable insight is that zone demand and company profitability were designed as different layers. Demand may indicate that the simulation wants a category of business, while an individual company can still fail because its input transport, land, wages, taxes, storage, or customer access make the location unprofitable. Economy 2.0 later removed government subsidies and rebalanced prices, wages, demand, production, and rent, so numerical or launch-specific conclusions from this diary are historical.

## Source context and temporal scope

The diary was published on 2023-08-14 before release. It describes design intent for the original economy and includes government subsidies as an automatic stabilizer. That system was explicitly removed by Economy 2.0 in June 2024.

This report preserves the diary's agent and supply-chain model while flagging balance and safeguard behavior as version-sensitive. Only the official first post in the archived forum snapshot is treated as a first-party source.

## Findings

### The economy is a network of flows

Households earn wages, pay rent, and buy goods. Companies buy inputs, pay wages and rent, sell outputs, and pay taxes. City services spend public money and supply enabling infrastructure. Imports and exports connect the local system to an external market. The diary describes most agents as holding money and resources rather than using only global counters.

The original design included scaling government subsidies to keep a young or struggling city solvent. This reduced the consequences of inefficient choices and was later removed, making it a clear example of why source date must be preserved in retrieval.

### Location choice is an economic calculation

Households consider job and school access, leisure, household size, available housing, and travel cost. A shopping trip begins with a desired product and then assigns a household member to obtain it.

Industrial companies weigh land and rent, lot size, suitable workers, supplier and customer distance, and transport cost. Commercial companies need access to both suppliers and consumers, while the product mix must correspond to household consumption. Office businesses consume immaterial or light inputs and sell immaterial products without physical customer trips, making qualified workforce access more important than proximity to shoppers.

### Resource weight and space create geography

Every resource has a price, transport weight, and storage-space requirement. Heavy inputs are expensive to move and favor production near extractors, processors, rail, or ship cargo facilities. Space-intensive businesses favor larger lots and lower land value. A light, valuable product tolerates longer trips better than a bulky low-value input.

The diary's mineral-products example combines stone inputs, wages, power, water, rent, land requirements, customer distance, exports, taxes, and subsidies in one profitability calculation. It demonstrates that production-chain problems can arise from several simultaneous costs rather than a single missing resource.

### Local production is not automatically profitable

Specialized industries extract raw materials and can reduce import dependence. Surplus production may be exported, but export is not a guaranteed profit: the farther goods travel and the heavier they are, the more transport cost erodes the sale. Excess capacity can therefore hurt a producer even when an outside buyer exists.

Resource-specific taxation was intended to influence the chain. Lower or negative taxes on an upstream resource could benefit downstream users through price and availability, while high taxes could suppress the activity. The exact tax response and company balance have since changed, but the cross-chain effect remains a useful investigative hypothesis.

### Offices are part of the production system

The diary characterizes office companies as converting Electronics or Software into immaterial products such as Software, Telecom, Banking, and Media. Their outputs can be delivered without freight, but their productivity still depends on labor and the broader economy. This explains why office demand and profitability should not be analyzed purely as commuter traffic or building occupancy.

## Existing corpus overlap

The current wiki contains resource tables, company descriptions, taxes, zoning, demand, and patch notes. It is better for present balance and terminology. This diary adds the clearest first-party explanation of how weight, storage space, land value, transport distance, workforce education, and downstream customers jointly shape company location and profit.

The Economy 2.0 report must supersede this source on subsidies, price calculation, production work requirements, wages, demand, rent, and service costs.

## Implications for Cities2 modding

Economic mods and diagnostics should separate demand, company spawn, location selection, production, inventory, transport, sales, and profit. A change that raises demand does not guarantee that spawned firms can acquire inputs or remain solvent.

Export and cargo tests should record resource type, weight, amount, storage, trip distance, vehicle availability, and price rather than only total import/export values. For office tests, workforce and education may be more informative than road freight.

The diary exposes concepts, not stable ECS schemas. Installed assemblies and current prefab data are required before mapping these concepts to components, buffers, or systems.

## Implications for Cities2-MCP

Cities2-MCP can use this report to answer causal questions such as why local raw materials matter, why an exporter may still lose money, why industrial firms avoid expensive land, or why commercial variety tracks household consumption.

Advice should retrieve newer economy sources first and use this diary for deeper model explanation. Government subsidies must always be described as removed, not as a current automatic safety net.

## Uncertainties and transcript corrections

This is a pre-release design description. It does not give complete formulas, update intervals, market-clearing rules, or current balance values. Later patches may have retained concepts while changing their implementation.

The MHTML snapshot contains typographic decoding artifacts, which were normalized. Community replies were excluded from findings.

## Sources

- Colossal Order, Development Diary #9 - Economy and Production, published 2023-08-14: https://forum.paradoxplaza.com/forum/developer-diary/development-diary-9-economy-production.1595744/
- Cities: Skylines II Wiki, Economy: https://cs2.paradoxwikis.com/Economy
- Cities: Skylines II Wiki, Patches: https://cs2.paradoxwikis.com/Patches
