# IMpower150 — Computable Regulatory Submission Platform

> **Sponsor:** Genentech/Roche — F. Hoffmann-La Roche Ltd.  
> **Study ID:** NCT02366143 (IMpower150)  
> **Indication:** First-line treatment of metastatic non-squamous NSCLC  
> **Platform Version:** 5.0.0 (Latest Release)  
> **Regulatory Alignment:** CDISC SDTMIG v3.4 · ADaMIG v1.3 · Dataset-JSON v1.1 · Define.xml v2.1 · CDISC ARS v1.0 · ICH E9(R1) · ICH M11

---

## Executive Summary

This platform implements a **computable clinical data engineering pipeline** for the IMpower150 trial — a Phase III, randomized, multi-center study evaluating Atezolizumab + Bevacizumab + Chemotherapy (Arm B) vs. Bevacizumab + Chemotherapy (Arm C) in 1L non-squamous NSCLC.

The pipeline provides end-to-end traceability from **M11 protocol objectives** through **ICH E9(R1) estimands**, **COSMoS Biomedical Concepts**, **CDISC derivation rules**, **FDA submission artifacts** (Define.xml v2.1 · JSON-LD SDRG · CDISC XPT · Dataset-JSON v1.1), and **CDISC ARS v1.0 statistical results**.

---

## Architecture Overview

```
Protocol (M11/SAP)
    │
    ▼
ICH E9(R1) Estimands (ADICE OCCDS dataset for intercurrent events)
    │
    ▼
Biomedical Concepts (COSMoS Concept Hierarchy & subClassOf RDF schemas)
    │
    ▼
Endpoint Definitions (Investigator vs. parallel BICR assessor endpoints)
    │
    ▼
Derivation Rules (Compilable Logic) ──► SAS Programs (sas/programs/)
    │
    ▼
Analysis Results Metadata (ARM) & CDISC ARS v1.0 Result Data (ard.json)
    │
    ▼
CDISC Variables (SDTM/ADaM & Longitudinal Panel ADPANEL with SW_IPCW) ──► Dataset-JSON v1.1 / XPT
    │
    ▼
Submission Artifacts (Define.xml v2.1, JSON-LD SDRG, SHACL shapes)
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
├── Dockerfile                 ← Multi-stage Docker containment (M12)
├── docker-compose.yml         ← Scalable containment composition (M12)
│
├── src/                       ← All Python source modules
│   ├── models.py              ← SQLAlchemy ORM (13-table semantic schema with parent_bc_id & specializations)
│   ├── app.py                 ← Streamlit regulatory dashboard
│   ├── orchestrator.py        ← Pipeline orchestrator (E2E automation & timing metrics)
│   ├── ingest_protocol.py     ← NCT JSON / protocol ingestion
│   ├── rule_parser.py         ← Declarative rule compiler
│   ├── execution_adapter.py   ← Vectorized clinical SAS execution adapter
│   ├── qc_engine.py           ← 5-level QC conformance engine (with Level 4 referential integrity & Level 5 CT checks)
│   ├── graph_builder.py       ← 8-layer lineage graph (with subClassOf edges & SHACL shape constraints)
│   ├── define_xml_generator.py← Define.xml v2.1 + JSON-LD exporter
│   ├── ard_generator.py       ← CDISC ARS v1.0 compliant statistical ARD exporter (H5)
│   ├── m11_protocol_exporter.py← ICH M11 digital protocol exporter (H10)
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
├── .github/                   ← CI/CD pipeline
│   └── workflows/
│       └── pipeline.yml       ← GitHub Actions CI pipeline with compliance gates (M13)
```

---

## Quick Start

### 1. Run via Docker (GxP Containment - Recommended)
```bash
docker-compose up --build
```
This builds a GxP-reproducible container, installs all system and python dependencies, executes the end-to-end computable clinical pipeline, runs 5-level QC checks, and writes compliance-verified submission packages to the host `outputs/` folder.

### 2. Local Installation
```bash
pip install -r requirements.txt
```

### 3. Run E2E Test Suite & Compliance Gate
```bash
python tests/test_pipeline.py
```

### 4. Run the Orchestrator
```bash
python -c "import sys; sys.path.insert(0,'src'); from orchestrator import PipelineOrchestrator; PipelineOrchestrator().run_pipeline()"
```

### 5. Launch Regulatory Streamlit Dashboard
```bash
python run_app.py
# Opens at http://localhost:8501
```

---

## Regulatory Alignment

| Standard | Version | Implementation |
|----------|---------|----------------|
| CDISC SDTMIG | v3.4 | SDTM variable metadata, controlled terminology |
| CDISC ADaMIG | v1.3 | ADaM derivation rules (AVAL, CNSR, PARAMCD) |
| CDISC Dataset-JSON | v1.1.0 | Full envelope compliant Dataset-JSON & NDJSON streaming (C4, M11) |
| CDISC Define.xml | v2.1 | Auto-generated XML metadata dictionary with structural validation |
| CDISC ARS | v1.0.0 | Structured Analysis Results Data (ard.json) linking results to endpoints |
| ICH E9(R1) | Estimands addendum | Intercurrent event tracking (ADICE OCCDS dataset) & PSyFL flags |
| ICH M11 | Protocol template | Protocol objective → estimand digital protocol exchange (m11_protocol.json) |
| RECIST v1.1 / iRECIST | Published 2009/2017 | Tumor scan window criteria and immunotherapeutic confirmed progression |

---

## Key Endpoints Covered

| Endpoint | Assessor | Estimand | Analysis |
|----------|---------|---------|---------|
| PFS (ITT-WT) | Investigator | EST_PFS_WT | Vectorized SQL + KM survival |
| PFS_BICR (ITT-WT) | Blinded Central Review | EST_PFS_WT | Parallel assessor scan evaluations |
| OS (ITT-WT) | Investigator | EST_OS_WT | Vectorized SQL + Stratified log-rank |
| OS_BICR (ITT-WT) | Blinded Central Review | EST_OS_WT | Parallel assessor OS evaluations |
| iPFS (ITT) | BICR/iRECIST | EST_IPFS_ITT | Confirmational scan evaluations (iRECIST) |
| ORR (ITT-WT) | Investigator | EST_OS_WT | Cochran-Mantel-Haenszel (CMH) test |
| DOR (ITT-WT) | Investigator | EST_OS_WT | Median duration (Kaplan-Meier) |

---

## Contact / Maintainer

> **Platform Author:** Clinical Data Engineering  
> **Regulatory Contact:** [Specify contact for FDA communications]  
> **Document Status:** RELEASED — Compliance verified

*This platform uses published clinical trial design specifications from the NCT02366143 public record and peer-reviewed publications. Raw individual patient data (IPD) is not included in this repository.*
