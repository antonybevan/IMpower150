# CHANGELOG

All notable changes to the IMpower150 Computable Submission Platform are documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and 
[Software Development Life Cycle (SDLC) documentation requirements](https://www.fda.gov/media/73141/download) for regulatory submissions.

---

## [3.0.0] — 2026-05-29

### Added
- **Repository Professionalization**: Restructured flat root directory into FDA-grade hierarchy (`src/`, `seeds/`, `tests/`, `sas/`, `references/`, `docs/`, `assets/`)
- **README.md**: Executive-level regulatory submission entry point with architecture overview, quick-start guide, and regulatory alignment table
- **CHANGELOG.md**: This file — SDLC audit trail
- **run_app.py**: Clean root-level launch script for Streamlit dashboard
- **conftest.py**: Pytest path configuration for tests/ directory

### Changed
- Moved all 16 Python source modules to `src/`
- Moved seed scripts to `seeds/`; test and audit scripts to `tests/`
- Moved SAS templates to `sas/templates/`; compiled SAS programs to `sas/programs/`
- Moved all 8 reference PDFs and clinical trial JSON to `references/` with standardized filenames
- Moved `framework_v3.tsx` to `assets/`
- Updated `alembic/env.py` to resolve `models.py` from `src/`
- Updated all cross-module import paths for new directory structure

---

## [2.1.0] — 2026-05-29

### Added
- **Orchestrator** (`orchestrator.py`): End-to-end automated pipeline orchestration
- **SDRG HTML generator** (`define_xml_generator.py`): Human-readable Study Data Reviewer's Guide
- **Lineage Report Generator** (`lineage_report_generator.py`): HTML traceability report

### Fixed
- 13 metadata audit gaps resolved (GAP-01 through GAP-13):
  - GAP-01: ARM first-class entity registration (AnalysisResult table)
  - GAP-02: Protocol objective → endpoint linking
  - GAP-03: BICR parallel rule set (6 BICR-assessor rules added)
  - GAP-04: Where clause entity seeding (WhereClause table)
  - GAP-05: Estimand attribute completeness
  - GAP-06 through GAP-13: Variable metadata, SAS template completeness

---

## [2.0.0] — 2026-05-28

### Added
- **12-table semantic OLTP schema**: Positions `bc_id` (Biomedical Concept) as primary clinical root
- **Alembic migration framework**: Database schema versioning with `alembic.ini` and `env.py`
- **DuckDB analytical store**: Separate OLAP layer for QC findings (Level 1/2/3 conformance)
- **8-layer knowledge graph** (`graph_builder.py`): NetworkX semantic lineage spanning M11 objectives → submission artifacts
- **Level 3 Explainable QC** (`qc_engine.py`): Graph-traversal root-cause narratives
- **Execution snapshot ledger** (`snapshot_manager.py`): SHA-256 environment hashing for reproducibility

### Changed
- `app.py` upgraded to full 6-view Streamlit regulatory dashboard with vis.js network graph
- Define.xml generator upgraded to v2.1 spec compliance

---

## [1.0.0] — 2026-05-27

### Added
- Initial project scaffold
- Protocol ingestion from `NCT02366143.json` (ClinicalTrials.gov public record)
- SAP ingestion (`SAP_000.pdf`)
- Basic SDTM/ADaM metadata model
- Rule parser with SAS program generation
- Mock SAS execution adapter
