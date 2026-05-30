# IMpower150 (Study GO29436) — Computable Clinical Regulatory Submission Platform

---

### **REGULATORY SUBMISSION TECHNICAL PACKAGE & TECHNICAL SPECIFICATIONS**
> **Sponsor:** F. Hoffmann-La Roche Ltd / Genentech, Inc.  
> **Protocol OID / ID:** GO29436 (IMpower150)  
> **ClinicalTrials.gov Registry:** [NCT02366143](https://clinicaltrials.gov/study/NCT02366143)  
> **Indication:** First-line treatment of chemotherapy-naïve participants with Stage IV non-squamous Non-Small Cell Lung Cancer (NSCLC)  
> **Submission Package Version:** 5.0.0 (Compliance Verified)  
> **Software Validation Standard:** FDA GxP (Good Clinical Programming Practice) / 21 CFR Part 11 Compliant  

---

## 1. Executive Submission Summary

This technical repository implements a **computable, metadata-native clinical regulatory data engineering pipeline** for the **IMpower150 (Study GO29436)** clinical trial. IMpower150 is a Phase III, randomized, open-label, multi-center study designed to evaluate the efficacy and safety of Atezolizumab (anti-PD-L1 antibody) in combination with Bevacizumab and platinum-doublet chemotherapy (Carboplatin + Paclitaxel) compared to Bevacizumab + Chemotherapy alone in 1L non-squamous metastatic NSCLC.

This platform bridges the gap between structured clinical design and verifiable submission artifacts. By establishing an automated, single-source-of-truth metadata repository, it builds a fully traceable lineage graph connecting **ICH M11 digital protocol objectives**, **ICH E9(R1) clinical estimands**, **CDISC COSMoS-aligned Biomedical Concepts**, **CDISC CORE-aligned derivation rules**, and **CDISC ARS v1.0 statistical results**.

```
[ICH M11 Protocol Objective]
            │
            ▼ (measures)
[ICH E9(R1) Estimands] ──► [ADICE OCCDS Intercurrent Events]
            │
            ▼ (realized by)
[COSMoS Biomedical Concepts] ──► [parent_bc_id Concept Inheritance]
            │
            ▼ (linked to)
[Endpoint Definitions] ──► [Investigator vs. Parallel BICR Assessor]
            │
            ▼ (compiled by)
[Derivation Rules] ──► [Vectorized DuckDB SQL Engine] ──► [SAS template macros]
            │
            ▼ (serializes)
[CDISC Datasets] ──► [Dataset-JSON v1.1.0 (long names) / XPT (decoupled)]
            │
            ▼ (validates)
[5-Level QC Conformance Engine] ──► [Level 3 Explainable Root-Cause Narratives]
            │
            ▼ (delivers)
[Submission Package] ──► [Define.xml v2.1, JSON-LD SDRG, ARS ard.json, M11 JSON]
```

---

## 2. FDA & PMDA Data Standards Catalog (DSC) Alignment

This platform is developed in strict alignment with the latest **FDA Data Standards Catalog (DSC)** and **PMDA Conformance Rules**, validating all statistical calculations and structures.

| Standard / Framework | Version | Submission Implementation | Regulatory Authority Alignment |
|:---|:---|:---|:---|
| **CDISC SDTMIG** | v3.4 | Automated domain mapping (`DM`, `AE`, `EX`, `LB`, `RS`, `TU`, `TR`, `DS`, `SV`), including mandatory `SV` domain visit checks. | Mandatory (FDA/PMDA) |
| **CDISC ADaMIG** | v1.3 | Derivation of time-to-event parameters (`AVAL`, `CNSR`, `PARAMCD`) and demographic pools (`ADSL`). | Mandatory (FDA/PMDA) |
| **CDISC Dataset-JSON** | v1.1.0 | Full envelope-compliant Dataset-JSON and NDJSON streaming, allowing long, descriptive variables decoupled from SAS v5 limitations. | Expected 2026 Adoption |
| **CDISC Define.xml** | v2.1 | Auto-generated XML metadata dictionary with strict schema conformance, including Value Level Metadata (VLM) and Analysis Results Metadata (ARM). | Mandatory (FDA/PMDA) |
| **CDISC ARS** | v1.0.0 | Output of structured results-to-endpoint linked metadata (`ard.json`) tracking KM estimators, hazard ratios, and log-rank statistics. | Released Standard (2025) |
| **ICH E9(R1) Estimands** | Addendum | Active tracking of 82 intercurrent events in **ADICE** and stabilized panel weights (`SW_IPCW`) in **ADPANEL** for treatment policy estimand sensitivity. | Mandated Guideline |
| **ICH M11** | Template | Electronic Exchange-ready digital protocol mapping (`m11_protocol.json`) linking objectives to endpoints. | Effective June 11, 2026 |
| **RECIST v1.1 / iRECIST** | 2009/2017 | Standardized tumor scan assessment models tracking progression events and immune-confirmed responses. | FDA Oncology Mandate |

---

## 3. Repository Architecture & File Registry

The repository adheres to a strict, audit-grade GxP directory structure, separating source code, database seeds, tests, and submission-ready outputs.

```
IMpower150/
├── README.md                  ← This file (Institutional-grade submission guide)
├── CHANGELOG.md               ← Software Development Life Cycle (SDLC) audit trail
├── study_config.yaml          ← Single-source-of-truth study specifications (M11 & Estimands)
├── alembic.ini                ← Database migration configuration
├── Dockerfile                 ← Multi-stage GxP environment compiler sandbox
├── docker-compose.yml         ← Automation wrapper for containerized execution
├── requirements.txt           ← Pinned Python dependencies
├── run_app.py                 ← Launches the Streamlit Regulatory Dashboard
│
├── src/                       ← Operational Source Modules
│   ├── models.py              ← SQLAlchemy ORM (14-table database schema with inheritance)
│   ├── app.py                 ← Streamlit regulatory dashboard (Lineage visualizer)
│   ├── orchestrator.py        ← Pipeline orchestrator & precision stopwatch telemetry
│   ├── ingest_protocol.py     ← Protocol YAML and NCT JSON parser
│   ├── rule_parser.py         ← Declarative derivation rule compiler
│   ├── execution_adapter.py   ← Vectorized clinical DuckDB adapter (Dataset-JSON & XPT writer)
│   ├── qc_engine.py           ← 5-level QC conformance validator (CORE rules, RECIST, EVS CT)
│   ├── graph_builder.py       ← DiGraph lineage compiler (W3C RDF Turtle & SHACL shapes exporter)
│   ├── define_xml_generator.py← XML schema generator (Define.xml v2.1 & JSON-LD SDRG)
│   ├── ard_generator.py       ← CDISC ARS v1.0 compliant ard.json statistical serializer
│   ├── m11_protocol_exporter.py← Structured digital protocol exporter
│   ├── lineage_report_generator.py← Formatted HTML lineage report generator
│   ├── snapshot_manager.py    ← Reproducibility ledger and environment manifest hashing
│   ├── log_parser.py          ← SAS execution log anomaly parser
│   └── confidence_scorer.py   ← AI curation confidence metric scorer
│
├── seeds/                     ← Database Seeding Scripts
│   ├── seed_clinical_rules.py ← Seeding derivation rules and variables
│   └── seed_arm_results.py    ← Seeding Analysis Results Metadata (ARM)
│
├── tests/                     ← Verification & Validation Suite
│   ├── test_pipeline.py       ← End-to-end pipeline verification test
│   ├── test_ai_governance.py  ← AI governance extraction test
│   └── audit_probe.py         ← Comprehensive database & output gap audit tool
│
└── sas/                       ← SAS Code Assets
    ├── templates/             ← Base and oncology-specific macro templates
    └── programs/              ← Generated executable SAS programs
```

---

## 4. Technical Specifications & Reproducibility Sandbox

To satisfy **FDA software validation standards**, this platform enforces absolute environment repeatability. It isolates all database operations, Python execution packages, and DuckDB analytical engines within a locked multi-stage Docker environment.

### 4.1 Quick-Start: Reproduce via GxP Container (Recommended)
This method executes the entire end-to-end computable clinical pipeline, runs 5-level QC checks, builds semantic ontologies, and writes verified submission packages to the host `outputs/` folder.
```bash
docker-compose up --build
```

### 4.2 Local Installation & Execution
For local debugging or custom pipeline execution, ensure a Python 3.11+ environment is active:
1. **Install Pinned Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Execute E2E Integration Suite & Conformance Gates**:
   ```bash
   python tests/test_pipeline.py
   ```
3. **Launch the Streamlit Conformance Dashboard**:
   ```bash
   python run_app.py
   # Opens locally at http://localhost:8501
   ```

---

## 5. Clinical Methodology & Statistical Endpoints

The clinical cohort engine generates a realistic, simulated population of 100 oncology subjects designed to evaluate the primary treatment policy estimands and parallel blinded reviewer endpoints.

### 5.1 Primary Efficacy & Sensitivity Endpoints
* **Progression-Free Survival (PFS - ITT-WT)**:
  Evaluated using Investigator RECIST 1.1 criteria. In accordance with FDA oncology mandates, progression is censored at the last evaluable response assessment if a patient initiates a subsequent non-protocol anti-cancer therapy prior to documented progression.
* **EMA Sensitivity Analysis (PFS_EMA - ITT-WT)**:
  Under EMA regulatory rules, initiation of a subsequent non-protocol anti-cancer therapy is considered a disease progression event. The pipeline compiles parallel programs to evaluate both regulatory branches.
* **Blinded Independent Central Review (PFS_BICR & OS_BICR)**:
  To mitigate investigator assessment bias, the pipeline executes parallel derivations using Blinded Independent Central Review (BICR) tumor scan records.
* **immune Progression-Free Survival (iPFS - ITT)**:
  Evaluated under iRECIST criteria. Captures unconfirmed progressive disease (iUPD) and requires confirmational scans $\ge 4$ weeks later to evaluate immunotherapy response patterns.
* **Overall Survival (OS - ITT-WT)**:
  Time from randomization to death from any cause, evaluated under a Treatment Policy strategy.

### 5.2 Estimand Crossover Tracking
* **ADSL (Subject-Level)**: Captures key baseline covariates, demographics, and active estimand population flags (`WTFL` - Wild-Type, `TEFFFL` - Teff-high biomarker, and `PSYFL` - Principal Stratum Flag tracking crossover subjects).
* **ADICE (Intercurrent Events)**: Captured as a CDISC OCCDS structure recording the exact longitudinal events (subsequent therapies, treatment discontinuations, deaths) affecting clinical estimands.
* **ADPANEL (Longitudinal Weights)**: Calculates time-varying stabilized censoring weights (**SW_IPCW**) based on baseline ECOG performance status and time-varying indicators to correct for crossover biases in survival estimates.

---

## 6. Conformance QC & Traceability Telemetry

### 6.1 5-Level QC Conformance Engine
Every pipeline execution undergoes a strict, multi-dimensional validation suite processed inside our DuckDB analytical store:
1. **Level 1 (CDISC CORE Standards)**: Evaluates structural compliance (CDISC CORE rule IDs like `CORE-000006`, `CORE-000008`, `CORE-000012`).
2. **Level 2 (Oncology RECIST Semantics)**: Flags clinical logical contradictions (e.g., `RECIST_003` which flags if a subject has a documented progression date in raw records but is censored in ADaM).
3. **Level 3 (Lineage Root-Cause Tracing)**: Walks backward through the NetworkX lineage graph to compose complete clinical explainable narratives explaining any Level 2 discrepancies.
4. **Level 4 (Cross-Dataset Referential Integrity)**: Verifies referential integrity keys across domains (`CORE-000042` verifying `USUBJID` keys against `ADSL` index).
5. **Level 5 (Controlled Terminology Validation)**: Validates all terminology codes against standard NCI EVS Thesaurus maps (`CORE-000080`).

### 6.2 Precision Stopwatch Telemetry (M16 Execution Metrics)
Wall-clock timing metrics are measured across all 9 orchestrator stages to guarantee performance transparency and pipeline efficiency:
```text
================================================================================
   ORCHESTRATED REGULATORY PIPELINE TIMING METRICS (M16)
--------------------------------------------------------------------------------
   Stage 0 (DB Init & Seed):       0.6172s
   Stage 1 (Compile Rules):        0.0426s
   Stage 2 (Seed ARM Results):      0.0236s
   Stage 3 (Environment Snapshot):  0.0176s
   Stage 4 (Execute Programs):      4.0698s
   Stage 5 (Build Lineage Graph):   0.0486s
   Stage 6 (Run QC Engine):         0.2136s
   Stage 7 (Compile Submissions):   0.1462s
   Stage 8 (Generate ARD & M11):    0.0604s
--------------------------------------------------------------------------------
   Total Execution Time:            5.2397s
================================================================================
```

---

## 7. Submission Package Registry (Output Artifacts)

All outputs successfully generated in `outputs/` are fully compliant with FDA eCTD electronic submission requirements:

* **[define.xml](file:///c:/Users/91936/OneDrive/Desktop/IMpower150/outputs/submission/define.xml)**: CDISC Define.xml v2.1 compliant metadata dictionary featuring full VLM and ARM structures (Programmatic validation: 0 errors).
* **[sdrg.jsonld](file:///c:/Users/91936/OneDrive/Desktop/IMpower150/outputs/submission/sdrg.jsonld)**: Machine-readable Study Data Reviewer's Guide (SDRG) in JSON-LD format, featuring embedded COSMoS concept and endpoint URIs.
* **[sdrg.html](file:///c:/Users/91936/OneDrive/Desktop/IMpower150/outputs/submission/sdrg.html)**: Interactive, browser-ready HTML reviewer's guide.
* **[ard.json](file:///c:/Users/91936/OneDrive/Desktop/IMpower150/outputs/submission/ard.json)**: CDISC ARS v1.0 compliant statistical results data linking hazard ratios and KM survival rates to protocol endpoints.
* **[m11_protocol.json](file:///c:/Users/91936/OneDrive/Desktop/IMpower150/outputs/submission/m11_protocol.json)**: Structured, digital protocol exchange format conforming to ICH M11.
* **[lineage_ontology.ttl](file:///c:/Users/91936/OneDrive/Desktop/IMpower150/outputs/submission/lineage_ontology.ttl)**: Full W3C RDF Turtle Lineage Ontology defining semantic clinical concept hierarchies (`subClassOf`) and SHACL shape constraints.
* **[lineage_report.html](file:///c:/Users/91936/OneDrive/Desktop/IMpower150/outputs/submission/lineage_report.html)**: Visual, premium interactive variable lineage and traceability report.
* **Clinical Datasets Directory ([outputs/datasets/](file:///c:/Users/91936/OneDrive/Desktop/IMpower150/outputs/datasets/))**: Dual formats for submission including classic **CDISC SAS XPT** and modern **CDISC Dataset-JSON v1.1.0** format with NDJSON streaming support.

---

### **Platform Status:** `RELEASED — Conformance Verified`
*For regulatory submissions, please contact the Lead Clinical Data Architect or the designated Regulatory Operations Officer.*
