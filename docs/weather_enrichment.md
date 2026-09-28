# Weather enrichment

Weather is optional contextual data, not evidence of causation. When enabled, the
pipeline will request historical daily weather from Open-Meteo using a station latitude,
longitude, and journey date. Requests use bounded timeouts and retries.

Weather joins are permitted only where the station coordinate source and weather API terms
are recorded in provenance. Weather data is excluded from prediction features when it was
not available at the prediction point.
