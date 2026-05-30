# CHANGELOG

All notable changes to the IMpower150 Computable Submission Platform are documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and 
[Software Development Life Cycle (SDLC) documentation requirements](https://www.fda.gov/media/73141/download) for regulatory submissions.

---

## [5.0.0] — 2026-05-30

### Added
- **FDA-Grade Crossover & Estimand Trackers (🔴 Critical & 🟡 High)**:
  - Implemented standard **ADSL** (Analysis Dataset for Subject Level) with demographics, 3-arm balanced randomization, `WTFL`, `TEFFFL` and `PSYFL` (Principal Stratum Flag) estimand population flags.
  - Implemented **ADICE** (Analysis Dataset for Intercurrent Events) OCCDS structure to record 82 intercurrent events (e.g. initiation of subsequent non-protocol cancer therapies) across subjects, supporting E9(R1) Treatment Policy estimand strategy alignment.
  - Implemented stabilized Inverse Probability of Censoring Weighting (`SW_IPCW`) columns in **ADPANEL** (Longitudinal Panel) using baseline demographics (ECOG) and time-varying indicators (`ON_NEW_THERAPY`, `PROGRESSION`).
- **Standard Exporters & Statistical Tracing (🟡 High & 🟢 Medium)**:
  - Created compliant **CDISC ARS v1.0 Statistical Results** (`ard.json`) capturing hazard ratios, log-rank p-values, Kaplan-Meier survival rates, and median survival.
  - Created **ICH M11 digital protocol** (`m11_protocol.json`) serializing objectives, estimands, scan frequencies, and visits.
  - Added concept inheritance mapping (`parent_bc_id`) to **Biomedical Concepts** in `models.py` and exported concept relationships (`rdfs:subClassOf`) with W3C SHACL shape validation constraints in the RDF ontology.
  - Aligned QC rule IDs to standard CDISC CORE rules taxonomy (`CORE-000xxx`).
  - Added Level 4 Cross-dataset Referential Integrity checks and Level 5 NCI EVS Controlled Terminology Validation directly within the `QCEngine`.
- **Reproducibility & Timing Instrumentation (🟢 Medium)**:
  - Authored a multi-stage `Dockerfile`, `docker-compose.yml`, and a GitHub Actions workflow (`pipeline.yml`) incorporating compliance quality gates.
  - Integrated precision stopwatches around each pipeline stage, printing a comprehensive, human-readable execution timing summary.

---

## [4.0.0] — 2026-05-30

### Added
- **Phase 9 High-Fidelity AI Governance Layer**:
  - Upgraded Ingestion Engine (`src/sap_ingestion.py`) to parse the actual 10MB `references/SAP_IMpower150.pdf` using `pypdf` with space-insensitive cleaning normalization.
  - Upgraded Semantic Rules Extractor (`src/llm_rule_extractor.py`) and Confidence Scorer (`src/confidence_scorer.py`) with 4-signal composite scoring.
  - Added dedicated **AI Governance & Curation** tab in Streamlit dashboard (`src/app.py`) with a curation pending queue, gauge visualizations, and Approve/Reject controls.
  - Implemented W3C RDF Turtle lineage ontology serialization (`outputs/submission/lineage_ontology.ttl`) in `src/graph_builder.py`.
- **Efficacy Censoring Sensitivity Analysis Engine**:
  - Implemented parallel time-to-event parameters: `PFS` (FDA rules with censor-on-new-therapy) and `PFS_EMA` (EMA rules treating new therapy as progression event) in `src/execution_adapter.py`.
  - Added deterministic new anti-cancer therapy (`NT_DT`) and last assessment (`LAST_ASSESS_DT`) generation to clinical cohort engine.
  - Integrated `PFS_EMA` into database schema, seeds (`seeds/seed_clinical_rules.py`, `seeds/seed_arm_results.py`, `src/models.py`), Define-XML CodeList generator (`src/define_xml_generator.py`), and Level 2 oncology QC engine (`src/qc_engine.py`).

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
