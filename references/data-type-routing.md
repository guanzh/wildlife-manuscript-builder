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
