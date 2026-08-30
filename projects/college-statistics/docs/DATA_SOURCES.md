# Data Sources

This document is a planning registry. The current site uses fictional placeholder data only.

## Candidate sources

### IPEDS
Potential use: institution identifiers, enrollment, completions, tuition, graduation, finance, institutional characteristics.

### College Scorecard
Potential use: admissions, cost, completion, debt, earnings, fields of study, institution metadata.

### Bureau of Labor Statistics (BLS)
Potential use: occupation-level wages, employment outlook, labor-market context. BLS data is generally occupation-based rather than university-specific, so mappings must be explicit.

### U.S. Census Bureau
Potential use: demographic, geographic, income, and labor-market context.

### Common Data Set
Potential use: institution-reported admissions, enrollment, financial aid, academic offerings, and student profile data. Availability and formatting vary by university.

### University websites
Potential use: official program availability, degree requirements, deadlines, tuition details, and institutional metadata. Prefer structured official sources where possible.

## Source policy to adopt before production data

1. Record source name and source URL or dataset identifier.
2. Record reporting year versus retrieval date separately.
3. Never infer a missing statistic.
4. Preserve raw imported data outside the browser-ready output when an automated pipeline is introduced.
5. Define transformations and mappings, especially CIP-to-major and occupation-to-major mappings.
6. Document licensing and redistribution constraints for every source.
7. Prefer official government or institution data over secondary aggregators when the same measure exists.

## Open questions

- What defines the initial “top 100” university list?
- Which salary concept should be primary: alumni earnings, occupation wage, early-career, or mid-career?
- What time window defines employment rate?
- How should graduate school enrollment affect employment metrics?
- How should in-state versus out-of-state tuition be represented?
- Which ranking providers permit redistribution?
