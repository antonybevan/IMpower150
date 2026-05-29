# IMpower150 Platform Architecture

## Overview

The IMpower150 Computable Submission Platform implements a **multi-layer semantic clinical data pipeline** designed for FDA electronic submission readiness. The architecture follows CDISC's concept-based data standards model (COSMoS), placing Biomedical Concepts (BCs) as the primary ontological root of all clinical data relationships.

---

## Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 1: Clinical Intent                                           │
│  ProtocolObjective (M11 sections) ── linked to estimands           │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ has_estimand
┌──────────────────────────▼──────────────────────────────────────────┐
│  LAYER 2: Statistical Framework                                     │
│  Estimand (ICH E9R1 attributes: population, ICE strategy, measure)  │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ scoped_by_concept
┌──────────────────────────▼──────────────────────────────────────────┐
│  LAYER 3: Clinical Concepts (COSMoS)                                │
│  BiomedicalConcept (bc_id, cosmos_bc_id, sdtmig_class)             │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ defines_endpoint
┌──────────────────────────▼──────────────────────────────────────────┐
│  LAYER 4: Endpoint Definitions                                      │
│  EndpointDefinition (assessor: BICR / INVESTIGATOR, criteria_type)  │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ compiled_from_rule
┌──────────────────────────▼──────────────────────────────────────────┐
│  LAYER 5: Derivation Rules (Compilable Logic)                       │
│  DerivationRule (logic_type, approval_status → SAS program)         │
└────────────────────┬─────┴────────────────────────────────────────┐
                     │ realized_as                                   │ generates
┌────────────────────▼───────────────────────┐  ┌───────────────────▼───────────────┐
│  LAYER 6: Variables (CDISC Implementation) │  │  LAYER 7: Analysis Results (ARM)  │
│  Variable (dataset, role, datatype, bc_id) │  │  AnalysisResult (stat_method, TFL)│
└────────────────────┬───────────────────────┘  └───────────────────┬───────────────┘
                     │ produces_artifact                             │
┌────────────────────▼───────────────────────────────────────────────▼───────────────┐
│  LAYER 8: Submission Artifacts                                                      │
│  Program (SAS .sas file, Dataset-JSON, XPT, Define.xml, SDRG HTML)                 │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Database Architecture

### SQLite OLTP (metadata.db)
- **Primary operational database** for clinical metadata
- 12 tables: `protocol_objectives`, `estimands`, `biomedical_concepts`, `endpoint_definitions`, `derivation_rules`, `variables`, `analysis_results`, `where_clauses`, `programs`, `execution_snapshots`, and more
- Managed by **SQLAlchemy ORM** (`src/models.py`)
- Schema versioning via **Alembic** (`alembic/`)

### DuckDB OLAP (analytics.duckdb)  
- **Analytical layer** for QC findings and execution log analysis
- Tables: `qc_findings`, `execution_log`
- High-performance columnar queries for conformance reporting

### NetworkX Knowledge Graph (in-memory)
- Built at runtime by `graph_builder.py`
- 8-node-type directed graph for lineage traversal and gap auditing
- Enables impact analysis (what breaks if we change RULE_PFS_AVAL?)

---

## Pipeline Execution Flow

```
Orchestrator.run_pipeline()
    ├── 1. RuleParser.compile_rules()         → Validates approval_status, generates SAS
    ├── 2. seed_arm_data()                    → Ensures ARM metadata present
    ├── 3. SnapshotManager.capture()          → SHA-256 environment fingerprint
    ├── 4. ClinicalDerivationAdapter.execute() → Runs deterministic derivations, writes execution logs
    ├── 5. SASLogParser.parse_log_file()      → Ingests logs to DuckDB
    ├── 6. SemanticGraphBuilder.build_graph() → Builds 8-layer knowledge graph
    ├── 7. QCEngine.run_level1_conformance()  → CORE rule validation
    │        .run_level2_oncology_checks()    → RECIST/iRECIST oncology rules  
    │        .run_level3_explainable_narratives() → Graph-traversal root-cause AI
    └── 8. SubmissionGenerator.generate_*()   → Define.xml, JSON-LD, SDRG HTML
```

---

## Module Responsibilities

| Module | Responsibility |
|--------|---------------|
| `models.py` | ORM definitions, `init_database()` |
| `ingest_protocol.py` | NCT02366143.json + SAP ingestion |
| `rule_parser.py` | Rule compilation, SAS code generation |
| `execution_adapter.py` | SAS execution simulation + artifact creation |
| `log_parser.py` | SAS log parsing → DuckDB |
| `graph_builder.py` | Knowledge graph construction + traversal |
| `qc_engine.py` | 3-level QC (CORE / oncology / AI narrative) |
| `snapshot_manager.py` | Reproducibility ledger (environment hashing) |
| `define_xml_generator.py` | Define.xml v2.1, JSON-LD SDRG, HTML SDRG |
| `lineage_report_generator.py` | HTML lineage traceability report |
| `orchestrator.py` | End-to-end pipeline automation |
| `app.py` | 6-view Streamlit regulatory dashboard |
