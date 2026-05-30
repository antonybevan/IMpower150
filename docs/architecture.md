# IMpower150 Computable Submission Platform — Architecture Specifications

This document defines the **computable, metadata-native architectural specifications** for the IMpower150 (Study GO29436) submission platform. The architecture follows a strict semantic metadata pattern that decouples the clinical design intent (defined in protocol objectives and estimands) from physical implementations (such as datasets, variables, and transport formats).

---

## 1. 8-Layer Semantic Lineage Architecture

The platform organizes clinical trial metadata into a cohesive, **8-layer directed acyclic lineage graph**. Every physical clinical observation or statistical result is anchored upstream to a core clinical concept and protocol objective.

```
┌────────────────────────────────────────────────────────────────────────┐
│  LAYER 1: Clinical Protocol Intent                                     │
│  ProtocolObjective (ICH M11 text, section & endpoint links)            │
└──────────────────────────┬─────────────────────────────────────────────┘
                           │ serves
┌──────────────────────────▼─────────────────────────────────────────────┐
│  LAYER 2: Statistical Estimand Framework                               │
│  Estimand (ICH E9(R1) population, ICE strategy, summary measure)       │
└──────────────────────────┬─────────────────────────────────────────────┘
                           │ quantifies
┌──────────────────────────▼─────────────────────────────────────────────┐
│  LAYER 3: Clinical Biomedical Concepts                                 │
│  BiomedicalConcept (COSMoS-aligned bc_id, inheritance & hierarchies)   │
└──────────────────────────┬─────────────────────────────────────────────┘
                           │ measured_by
┌──────────────────────────▼─────────────────────────────────────────────┐
│  LAYER 4: Clinical Endpoint Definitions                                │
│  EndpointDefinition (Endpoint type, analysis concepts, criteria, assessor)│
└──────────────────────────┬─────────────────────────────────────────────┘
                           │ implemented_by
┌──────────────────────────▼─────────────────────────────────────────────┐
│  LAYER 5: Compilable Derivation Rules                                  │
│  DerivationRule (declarative SQL parser, SAS template macros)          │
└────────────────────┬─────┴─────────────────────────────────────────────┘
                     │ realized_as                                 │ generates
┌────────────────────▼───────────────────────┐  ┌───────────────────▼────────────────┐
│  LAYER 6: Variables & Realizations         │  │  LAYER 7: Analysis Results (ARM)   │
│  Variable / ParameterVariableMetadata      │  │  AnalysisResult (stat_method, TFL) │
└────────────────────┬───────────────────────┘  └───────────────────┬────────────────┘
                     │ produces_artifact                             │ populates
┌────────────────────▼───────────────────────────────────────────────▼────────────────┐
│  LAYER 8: submission-ready Reviewer Artifacts                                      │
│  Define.xml v2.1, Dataset-JSON v1.1.0, CDISC ARS, JSON-LD SDRG, Ontologies         │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Multi-Database Storage Architecture

The platform separates transactional metadata configurations from fast analytical auditing and in-memory graphing by implementing a **hybrid multi-database storage architecture**.

```
                           ┌─────────────────────────┐
                           │   study_config.yaml     │
                           └────────────┬────────────┘
                                        │ seed
                                        ▼
┌───────────────────────────────────────┴───────────────────────────────────────┐
│                     SQLite OLTP METADATA STORE (metadata.db)                  │
│  - Tracks all transactional configurations & single-source-of-truth metadata.  │
│  - Schema managed by SQLAlchemy ORM with day-1 Alembic migrations.            │
│  - Features 14 structured tables representing the complete semantic clinical core.│
└───────────────────────────────────────┬───────────────────────────────────────┘
                                        │ query
                                        ▼
┌───────────────────────────────────────┴───────────────────────────────────────┐
│                     DUCKDB OLAP ANALYTICAL ENGINE (analytics.duckdb)          │
│  - High-performance, columnar store executing vectorized cohort derivations.  │
│  - Resolves time-varying stabilized IPCW weights over panel datasets.          │
│  - Ingests and aggregates CDISC CORE and Level 2 RECIST QC findings.          │
└───────────────────────────────────────┬───────────────────────────────────────┘
                                        │ build
                                        ▼
┌───────────────────────────────────────┴───────────────────────────────────────┐
│                     NETWORKX IN-MEMORY KNOWLEDGE GRAPH                        │
│  - Constructs complete directed lineage graph at runtime.                      │
│  - Drives Level 3 Explainable Root-Cause QC traversals.                       │
│  - Serializes compliant W3C RDF Turtle linege ontologies & SHACL shapes.      │
└───────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 SQLite 14-Table OLTP Schema (`metadata.db`)
Transactional tables represent the complete clinical metadata lifecycle:
1. `protocol_objectives`: Digital M11 objectives mapping to endpoints.
2. `biomedical_concepts`: Standard CDISC COSMoS concepts with parent inheritance.
3. `dataset_specializations`: Concepts variable realizations in target domains.
4. `endpoint_definitions`: Scoped clinical measurements linking concepts to estimands.
5. `estimands`: ICH E9(R1) population and strategy definitions.
6. `derivation_rules`: Compilable SQL derivation statements and templates.
7. `variables`: SDTM/ADaM physical variable descriptions.
8. `parameter_variable_metadata`: Parameter-level variable mappings (e.g. PARAMCD).
9. `analysis_results`: Analysis Results Metadata (ARM) for Define.xml.
10. `where_clauses`: Value level metadata filtering criteria.
11. `execution_snapshots`: Ledger storing rule hashes and GxP environment states.
12. `programs`: Metadata tracking generated compilable SAS files.
13. `pending_queue`: Candidate rules for human curation.
14. `ai_actions`: Complete governance audit trail for AI extraction.

### 2.2 DuckDB OLAP Columnar Store (`analytics.duckdb`)
Optimized for high-speed clinical aggregation and compliance checking:
* `qc_findings`: Structural and logical violations generated by the Conformance Engine.
* `execution_log`: Log anomalies parsed from SAS batch runs.

---

## 3. Vectorized Pipeline Execution Flow

Orchestrated end-to-end via `src/orchestrator.py`, the pipeline executes across **9 precision-timed stages**, recording comprehensive stopwatch telemetry for submission reviewers.

```
PipelineOrchestrator.run_pipeline()
  │
  ├── STAGE 0: DB Init & Seed
  │     Initializes metadata.db, runs Alembic migrations, seeds concepts & rules.
  │
  ├── STAGE 1: Compile Rules
  │     RuleParser compiles active derivation rules into standalone programs.
  │
  ├── STAGE 2: Seed ARM Results
  │     Seeds analysis results metadata mapping endpoints to tables/listings (TFLs).
  │
  ├── STAGE 3: Environment Snapshot
  │     SnapshotManager hashes rule logic, DB state, and packages to snapshot ledger.
  │
  ├── STAGE 4: Execute Programs
  │     ClinicalDerivationAdapter runs vectorized SQL cohorts in DuckDB, generates 
  │     Dataset-JSON v1.1.0/XPT outputs, and logs execution files.
  │
  ├── STAGE 5: Build Lineage Graph
  │     SemanticGraphBuilder builds directed knowledge graph and serializes RDF Turtle.
  │
  ├── STAGE 6: Run QC Engine
  │     QCEngine runs 5-level checks, traversing the lineage graph for L3 narratives.
  │
  ├── STAGE 7: Compile Submissions
  │     SubmissionGenerator outputs schema-verified Define.xml v2.1 & JSON-LD SDRG.
  │
  └── STAGE 8: Generate ARD & M11
        Exports CDISC ARS compliant ard.json and ICH M11 digital protocol JSON.
```

---

## 4. Conformance Engine Architecture

To ensure the clinical database matches the highest standards of logical integrity, the engine executes a **5-level conformance validation suite** processed inside our DuckDB analytical store:

* **Level 1 (CORE Conformance)**: Checks structural data conventions mapped directly to CDISC CORE rule IDs (`CORE-000006`, `CORE-000008`, `CORE-000012`).
* **Level 2 (RECIST/iRECIST Semantics)**: Runs clinical oncology rule audits, comparing dataset realization states against raw patient history (e.g. flagging a patient progression censored mismatch `RECIST_003`).
* **Level 3 (Lineage Root-Cause Tracing composition)**: Walks backward from physical variable nodes to rules, endpoints, and protocol objectives inside the NetworkX graph to construct complete, explainable clinical narratives for all Level 2 discrepancies.
* **Level 4 (Cross-Dataset Referential Integrity)**: Validates referential keys and identifiers across SDTM and ADaM boundaries (`CORE-000042` verifying `USUBJID` matches `ADSL` index).
* **Level 5 (Controlled Terminology Validation)**: Matches code definitions against standard NCI EVS Thesaurus maps (`CORE-000080`).

---

## 5. Functional Module Directory

| Operational Module | Regulatory Responsibility |
|:---|:---|
| `src/models.py` | Declares ORM structures for the 14-table database schema with parent inheritance. |
| `src/ingest_protocol.py` | Ingests NCT public registry specifications and structured clinical study criteria. |
| `src/rule_parser.py` | Compiles declarative database rules into executable SAS programs and SQL. |
| `src/execution_adapter.py` | Simulates clinical SAS runs, computes vectorized IPCW weights, and outputs Dataset-JSON v1.1.0/XPT. |
| `src/log_parser.py` | Parses SAS batch execution logs and registers anomalies (warnings, zero observations). |
| `src/graph_builder.py` | Constructs the NetworkX Directed Lineage Graph, exporting W3C RDF Turtle ontologies. |
| `src/qc_engine.py` | Executes the 5-level conformance validation and writes explainable clinical narratives. |
| `src/snapshot_manager.py` | Fingerprints environment manifest hashes to secure absolute 21 CFR Part 11 repeatability. |
| `src/define_xml_generator.py` | Generates schema-validated Define.xml v2.1 and structured JSON-LD SDRGs. |
| `src/ard_generator.py` | Serializes statistical endpoints (HR, p-values, KM rates) to CDISC ARS `ard.json`. |
| `src/m11_protocol_exporter.py` | Serializes objectives, estimands, and visit schedules to ICH M11 structured JSON. |
| `src/lineage_report_generator.py` | Exports visual, premium interactive variable lineage reports. |
| `src/orchestrator.py` | Coordinates all pipeline execution stages and logs stopwatch metrics. |
| `src/app.py` | Hosts the Streamlit Conformance Dashboard and AI Governance metadata queue. |
