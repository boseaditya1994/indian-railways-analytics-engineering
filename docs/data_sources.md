# Data sources and provenance policy

## Approved design constraints

- Do not scrape IRCTC, NTES, or sites whose terms prohibit automated extraction.
- Record source URL, license/terms, retrieval time, checksum, coverage, and known gaps for
  every delivered file/API response.
- Store raw payloads immutably and transform them downstream.

## Candidate source roles

| Domain | Candidate | Status |
| --- | --- | --- |
| Schedule seed | Ministry of Railways timetable via data.gov.in | Official but stale; reference only |
| Historical running/delay | License-reviewed historical dataset | Pending provenance and license audit |
| Current running status | Explicitly authorized third-party API | Optional; not assumed for MVP |
| Weather | Open-Meteo historical/forecast API | Candidate for non-commercial portfolio use with attribution |

No dataset may be added merely because it is publicly downloadable; use requires a clear
license or permission compatible with this portfolio project.
