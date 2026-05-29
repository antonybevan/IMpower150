# IMpower150 — Computable Regulatory Submission Platform

> **Sponsor:** Genentech/Roche — F. Hoffmann-La Roche Ltd.  
> **Study ID:** NCT02366143 (IMpower150)  
> **Indication:** First-line treatment of metastatic non-squamous NSCLC  
> **Platform Version:** 3.0.0  
> **Regulatory Alignment:** CDISC SDTMIG v3.3 · ADaMIG v1.3 · Define.xml v2.1 · ICH E9(R1) · ICH M11

---

## Executive Summary

This platform implements a **computable clinical data engineering pipeline** for the IMpower150 trial — a Phase III, randomized, multi-center study evaluating Atezolizumab + Bevacizumab + Chemotherapy (Arm B) vs. Bevacizumab + Chemotherapy (Arm C) in 1L non-squamous NSCLC.

The pipeline provides end-to-end traceability from **M11 protocol objectives** through **ICH E9(R1) estimands**, **CDISC derivation rules**, and **FDA submission artifacts** (Define.xml v2.1 · JSON-LD SDRG · CDISC XPT).

---

## Architecture Overview

```
Protocol (M11/SAP)
    │
    ▼
ICH E9(R1) Estimands
    │
    ▼
Biomedical Concepts (COSMoS)
    │
    ▼
Endpoint Definitions (BICR / Investigator)
    │
    ▼
Derivation Rules (Compilable Logic) ──► SAS Programs (sas/programs/)
    │
    ▼
Analysis Results Metadata (ARM)
    │
    ▼
CDISC Variables (SDTM/ADaM) ──► Dataset-JSON / XPT
    │
    ▼
Submission Artifacts (Define.xml v2.1, JSON-LD SDRG)
```

The semantic lineage graph connects all 8 layers above, enabling downstream impact analysis, root-cause QC narratives, and reproducibility audits.

---

## Repository Structure

```
IMpower150/
├── README.md                  ← This file (executive entry point)
├── CHANGELOG.md               ← Versioned change log (SDLC traceability)
├── run_app.py                 ← Streamlit dashboard launcher
├── study_config.yaml          ← Study-level configuration
├── alembic.ini                ← Database migration config
│
├── src/                       ← All Python source modules
│   ├── models.py              ← SQLAlchemy ORM (12-table semantic schema)
│   ├── app.py                 ← Streamlit regulatory dashboard
│   ├── orchestrator.py        ← Pipeline orchestrator (E2E automation)
│   ├── ingest_protocol.py     ← NCT JSON / protocol ingestion
│   ├── rule_parser.py         ← Declarative rule compiler
│   ├── execution_adapter.py   ← SAS execution adapter
│   ├── qc_engine.py           ← 3-level QC conformance engine
│   ├── graph_builder.py       ← 8-layer lineage knowledge graph
│   ├── define_xml_generator.py← Define.xml v2.1 + JSON-LD exporter
│   ├── lineage_report_generator.py
│   ├── snapshot_manager.py    ← Reproducibility ledger
│   ├── log_parser.py          ← SAS execution log parser
│   └── confidence_scorer.py
│
├── seeds/                     ← One-time database seed scripts
│   ├── seed_arm_results.py    ← ARM + WhereClause seed data
│   └── seed_clinical_rules.py ← Derivation rules + variable seed data
│
├── tests/                     ← Verification suite
│   ├── test_pipeline.py       ← E2E pipeline integration test
│   └── audit_probe.py         ← Metadata integrity audit probe
│
├── sas/                       ← SAS derivation assets
│   ├── templates/             ← Macro/template library (6 macros)
│   └── programs/              ← Compiled rule-specific programs (10 programs)
│
├── references/                ← Clinical & regulatory reference documents
│   ├── NCT02366143_ClinicalTrials.json
│   ├── SAP_IMpower150.pdf
│   ├── NEJM_IMpower150_primary_analysis.pdf
│   ├── NEJM_IMpower150_protocol.pdf
│   ├── RECIST_v1.1.pdf
│   ├── iRECIST_guidelines.pdf
│   ├── ICH_E9_R1_Estimands.pdf
│   ├── Lancet_Resp_Med_IMpower150_2019.pdf
│   └── PIIS_IMpower150_2021.pdf
│
├── alembic/                   ← Database schema migrations (Alembic)
├── docs/                      ← Internal documentation
└── outputs/                   ← Runtime artifacts (gitignored)
    ├── datasets/              ← Generated Dataset-JSON / XPT files
    ├── logs/                  ← SAS execution logs
    ├── manifests/             ← Environment reproducibility manifests
    └── submission/            ← Define.xml, SDRG exports
```

---

## Quick Start

### 1. Install dependencies
```bash
pip install streamlit sqlalchemy duckdb networkx pyyaml pandas
```

### 2. Initialize and seed the database
```bash
python -m pytest tests/test_pipeline.py -v
```

### 3. Launch the regulatory dashboard
```bash
python run_app.py
# Opens at http://localhost:8501
```

### 4. Run the orchestrator (automated E2E pipeline)
```bash
python -c "import sys; sys.path.insert(0,'src'); from orchestrator import PipelineOrchestrator; PipelineOrchestrator().run_pipeline()"
```

---

## Regulatory Alignment

| Standard | Version | Implementation |
|----------|---------|----------------|
| CDISC SDTMIG | v3.3 | SDTM variable metadata, controlled terminology |
| CDISC ADaMIG | v1.3 | ADaM derivation rules (AVAL, CNSR, PARAMCD) |
| CDISC Define.xml | v2.1 | Auto-generated submission metadata dictionary |
| ICH E9(R1) | Estimands addendum | Estimand attributes (population, ICE strategy, summary measure) |
| ICH M11 | Protocol template | Protocol objective → estimand linking |
| RECIST v1.1 | Published 2009 | Tumor assessment criteria (criteria_type field) |
| iRECIST | Published 2017 | Immunotherapy response criteria (iPFS endpoint) |

---

## Key Endpoints Covered

| Endpoint | Assessor | Estimand | Analysis |
|----------|---------|---------|---------|
| PFS (ITT-WT) | Investigator | EST_PFS_WT | Stratified Cox + Log-Rank |
| PFS (ITT-WT) | BICR | EST_PFS_WT | Stratified Cox + Log-Rank |
| OS (ITT-WT) | Investigator | EST_OS_WT | Stratified Cox + Log-Rank |
| iPFS (ITT) | BICR/iRECIST | EST_IPFS_ITT | Unstratified Cox + Log-Rank |
| ORR (ITT-WT) | Investigator | EST_OS_WT | CMH Test |
| DOR (ITT-WT) | Investigator | EST_OS_WT | Kaplan-Meier |

---

## Contact / Maintainer

> **Platform Author:** Clinical Data Engineering  
> **Regulatory Contact:** [Specify contact for FDA communications]  
> **Document Status:** DRAFT — For internal review only

*This platform uses published clinical trial design specifications from the NCT02366143 public record and peer-reviewed publications. Raw individual patient data (IPD) is not included in this repository.*
