# Data-Type Routing

Use this file after the package readiness check. Route conservatively when the same dataset could support several analyses.

## Camera Trap

Typical inputs: station ID, date/time, species, independent-event rule, camera days, deployment dates, coordinates or site covariates, camera model/settings, detection/non-detection matrix if available.

Good manuscript routes:

- Species inventory and monitoring baseline.
- Occupancy and habitat association when repeated sampling periods are defensible.
- Activity rhythm and temporal overlap when timestamps are reliable.
- Community response to disturbance when sampling is balanced across gradients.
- Density or abundance only when design supports SCR, distance sampling, REM, REST, time-to-event, space-to-event, or similar assumptions.

Boundaries:

- Photo rate is not density.
- Independent events are not always independent biological observations.
- Co-occurrence is not species interaction.
- Camera data alone do not measure full forest habitat integrity.

## Acoustic Monitoring

Typical inputs: recorder ID, recording schedule, timestamps, species/call labels, classifier confidence, validation set, detection threshold, sampling effort.

Good routes:

- Calling activity and seasonal/diel patterns.
- Occupancy or distribution with detection probability.
- Automated classifier performance linked to ecological inference.
- Long-term trend when recording design is consistent.

Boundaries:

- Calls are not individual counts unless individually identifiable or model assumptions justify the link.
- Classifier accuracy must not be treated as ecological truth.
- Absence of calls is not absence of species without detection modeling or careful caveats.

## Transect, Point Count, and Direct Survey

Typical inputs: transect or point ID, length/area/time, observer, date/time, species, distance bands if relevant, effort, environmental covariates.

Good routes:

- Encounter-rate baseline or trend.
- Distance sampling for density when detection distances and assumptions are valid.
- Occupancy or GLM/GLMM for occurrence or count response.
- Survey-design evaluation.

Boundaries:

- Encounter rate is not population size.
- Unmodeled observer, weather, access, and habitat effects can bias comparisons.

## Occupancy, Distribution, and Habitat Suitability

Typical inputs: detection histories, sites, repeat visits or periods, covariates, background/absence/pseudoabsence rules, spatial resolution.

Good routes:

- Occupancy probability and detection probability.
- Habitat association.
- Suitability maps and conservation gap analysis.
- Dynamic occupancy when colonization/extinction is estimable.

Boundaries:

- Suitability is not confirmed presence.
- Non-detection is not true absence unless the design supports that interpretation.
- Maps need resolution, uncertainty, and validation details.

## Remote Sensing and Habitat

Typical inputs: raster/vector layers, dates, resolution, classification method, validation accuracy, habitat definitions, landscape metrics.

Good routes:

- Habitat change and fragmentation.
- Connectivity and corridor prioritization.
- Protected-area gap analysis.
- Integration with species records or monitoring outputs.

Boundaries:

- Forest cover is not habitat quality by itself.
- Habitat integrity should not be inferred from one proxy without acknowledging missing dimensions.

## Patrol, Threat, and Management Data

Typical inputs: patrol routes, effort, threat records, date/time, intervention timing, treatment/control areas, costs, accessibility.

Good routes:

- Threat hotspots.
- Patrol prioritization.
- Intervention evaluation when design supports it.
- Decision model with cost, uncertainty, and error consequences.

Boundaries:

- Before-after change is not automatically an intervention effect.
- More patrol records can mean more effort, not more threats.

## Multi-Source Data

Typical inputs: source-specific detection process, shared state variable, time/space alignment, uncertainty from each source.

Good routes:

- Integrated occupancy or abundance.
- State-space trend modeling.
- Multi-evidence conservation assessment.

Boundaries:

- Agreement across sources is stronger evidence, but still not automatic causality.
- Each source's observation error must be described.

## Plant Community / Vegetation Survey

Typical inputs: plot/quadrat ID, species list, abundance/cover/frequency, trait measurements, environmental covariates, sampling date, plot size, coordinate.

Good manuscript routes:

- Species diversity and composition baseline.
- Functional diversity and trait-environment relationships.
- Community classification and ordination.
- Succession or restoration trajectory.
- Phenological response to climate or disturbance.

Boundaries:

- Species richness alone is not biodiversity quality.
- Presence/absence does not capture abundance change.
- Plot-scale patterns do not automatically scale to landscape.
- Functional trait selection must be justified.

See also:
- `references/domain/objections/plant-vegetation.md`
- `references/domain/overclaims/plant-vegetation.md`

## Population Ecology (Mark-Recapture, Matrix Models)

Typical inputs: capture histories, individual covariates, time intervals, life-stage transitions, fecundity/survival estimates, population counts, environmental drivers.

Good routes:

- Abundance and survival estimation (CJS, POPAN, robust design).
- Population growth rate and viability analysis (matrix models, IPM, PVA).
- Density dependence and carrying capacity.
- Movement and dispersal estimation (multi-state models).
- Harvest or management impact assessment.

Boundaries:

- Apparent survival is not true survival without dead recovery or telemetry data.
- Population trend is not population viability without uncertainty propagation.
- Extrapolation beyond sampled sites or years requires explicit caveats.
- Detection probability must be modeled or its absence justified.

See also:
- `references/domain/objections/population-ecology.md`
- `references/domain/overclaims/population-ecology.md`

## Ecosystem Function (Productivity, Nutrient Cycling)

Typical inputs: biomass measurements, primary productivity (NPP/GPP), decomposition rates, soil nutrients, carbon stocks, flux measurements, climate variables, land-use history.

Good routes:

- Carbon stock and sequestration estimation.
- Nutrient cycling rates and budgets.
- Productivity drivers across environmental gradients.
- Land-use or restoration effects on ecosystem function.
- Soil health and quality indices.

Boundaries:

- Point measurements do not represent landscape-scale function without spatial sampling design.
- Correlation with environmental variables is not mechanistic understanding.
- Short-term measurements do not capture interannual variability.
- Proxy indicators (e.g., NDVI) require ground validation.

## Landscape Ecology (Fragmentation, Connectivity)

Typical inputs: land-cover/land-use maps, patch metrics, resistance surfaces, movement data (optional), graph/network metrics, time-series maps for change detection.

Good routes:

- Fragmentation and patch dynamics analysis.
- Connectivity modeling (circuit theory, least-cost path, graph theory).
- Landscape change and land-use legacy effects.
- Corridor and protected-area network design.
- Multi-scale habitat selection.

Boundaries:

- Structural connectivity is not functional connectivity without movement validation.
- Patch metrics are scale-dependent and sensitive to classification.
- Map resolution must match ecological process scale.
- Landscape pattern does not prove ecological process.

See also:
- `references/domain/objections/landscape-ecology.md`

## Freshwater Ecology

Typical inputs: water quality parameters, benthic macroinvertebrate/fish/diatom samples, habitat assessment scores, flow data, catchment land use, longitudinal position.

Good routes:

- Biotic indices (IBI, BMWP, EPT) and water quality assessment.
- Community composition along longitudinal or land-use gradients.
- Occupancy or abundance of indicator taxa.
- Flow-ecology relationships.
- Restoration or impact assessment (BACI design).

Boundaries:

- Biotic index thresholds are region-specific and require calibration.
- Single-season sampling may miss seasonal or flow-driven dynamics.
- Upstream-downstream comparisons need spatial autocorrelation handling.
- Abundance estimates require effort standardization.

See also:
- `references/domain/objections/freshwater.md`

## Soil Ecology

Typical inputs: soil fauna/microbial abundance and diversity, enzyme activity, soil physicochemical properties, land-use history, depth profiles, sampling date.

Good routes:

- Soil biodiversity patterns across land-use or environmental gradients.
- Decomposition and nutrient turnover rates.
- Soil health indicators and indices.
- Microbial community composition and function.
- Belowground-aboveground linkage analysis.

Boundaries:

- Soil heterogeneity requires adequate within-plot replication.
- Seasonal variation can exceed treatment effects without repeated sampling.
- DNA-based methods detect presence, not activity or viability.
- Functional gene abundance is not necessarily functional gene expression.

See also:
- `references/domain/objections/soil-ecology.md`

## Behavioral Ecology

Typical inputs: behavioral sequences, activity budgets, social interaction records, movement tracks, environmental context, individual and group covariates.

Good routes:

- Time budget and activity pattern analysis.
- Social network structure and dynamics.
- Foraging or habitat selection behavior.
- Response to anthropogenic disturbance or environmental change.
- Behavioral plasticity or repeatability.

Boundaries:

- Observed behavior is context-specific and may not represent full repertoire.
- Correlation between behavior and fitness is not causation.
- Short observation windows may miss rare but important behaviors.
- Observer presence may alter behavior (habituation or disturbance).

See also:
- `references/domain/objections/behavioral-ecology.md`

## Disease Ecology

Typical inputs: pathogen detection data (PCR/serology/visual), host population data, environmental covariates, transmission network data, spatial coordinates, temporal sampling.

Good routes:

- Occupancy or prevalence estimation with imperfect detection.
- Risk factor and environmental driver analysis.
- Transmission network reconstruction.
- Spillover or cross-species transmission assessment.
- Intervention or management evaluation.

Boundaries:

- Detection method sensitivity/specificity affects prevalence estimates.
- Apparent prevalence is not true prevalence unless detection is modeled.
- Correlation with environmental variables is not transmission mechanism.
- Sampling design must match the scale of transmission process.

See also:
- `references/domain/objections/disease-ecology.md`

## Molecular Ecology (eDNA, Metabarcoding)

Typical inputs: sequence reads, OTU/ASV tables, taxonomic assignments, sample metadata, PCR replicates, negative/positive controls, reference databases.

Good routes:

- Species detection and distribution via eDNA.
- Community composition and diversity via metabarcoding.
- Diet analysis via DNA metabarcoding.
- Population genetics and gene flow.
- Environmental DNA as a monitoring tool.

Boundaries:

- DNA detection is not organism presence without considering transport/degradation.
- Primer bias affects taxonomic coverage and relative abundance.
- Database completeness limits taxonomic resolution.
- Contamination requires negative controls and replication.
- Sequence read count is not organism abundance without careful calibration.

See also:
- `references/domain/objections/molecular-ecology.md`

## Urban Ecology

Typical inputs: urbanization gradients, socioeconomic variables, biodiversity surveys, land-cover maps, temperature/humidity records, citizen science data.

Good routes:

- Biodiversity patterns along urban-rural gradients.
- Urban heat island and species response.
- Ecosystem services in urban landscapes.
- Citizen science data validation and integration.
- Socio-ecological system analysis.

Boundaries:

- Urban gradient definitions vary and affect comparability.
- Socioeconomic variables are proxies and may confound with other factors.
- Citizen science data have spatial and taxonomic biases.
- Urban habitat quality is multidimensional and may not be captured by single metrics.

See also:
- `references/domain/objections/urban-ecology.md`

## Paleoecology

Typical inputs: sediment/peat/ice cores, fossil pollen, charcoal, diatom, or macrofossil counts, radiometric dates, age-depth models, modern calibration datasets.

Good routes:

- Long-term vegetation and disturbance history reconstruction.
- Climate-vegetation-fire relationships over centuries to millennia.
- Baseline conditions for restoration and conservation.
- Rate-of-change and resilience analysis.
- Human land-use legacies.

Boundaries:

- Age models carry uncertainty that propagates to all interpretations.
- Pollen representation varies by taxon (differential production, dispersal, preservation).
- Temporal resolution limits detection of short-lived events.
- Modern analog methods assume stationarity of species-environment relationships.

See also:
- `references/domain/objections/paleoecology.md`

## Agroecology

Typical inputs: crop yield, management practices, soil properties, biodiversity surveys (pollinators, natural enemies, weeds), input use, economic data, field trial design.

Good routes:

- Biodiversity-ecosystem service relationships in agricultural systems.
- Pest and natural enemy dynamics.
- Soil health and management practice effects.
- Yield gaps and sustainable intensification assessment.
- Pollinator diversity and crop pollination services.

Boundaries:

- On-farm trials may lack replication and randomization of controlled experiments.
- Yield is influenced by multiple interacting factors beyond measured variables.
- Biodiversity metrics at field scale may not capture landscape-level processes.
- Economic outcomes require cost and labor data, not only yield.

See also:
- `references/domain/objections/agroecology.md`
