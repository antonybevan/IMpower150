// @ts-nocheck
import { useState } from "react";

// ─── PALETTE ────────────────────────────────────────────────────────────────
const C = {
  bg:       "#060810",
  surface:  "#0A0D18",
  raised:   "#0F1220",
  border:   "#181D2E",
  borderHi: "#222840",
  muted:    "#4A5568",
  dim:      "#2D3748",
  text:     "#C8D4E4",
  textHi:   "#EDF2F7",
  textLo:   "#6B7A94",
  amber:    "#F6AD55",
  red:      "#FC8181",
  green:    "#68D391",
  blue:     "#63B3ED",
  cyan:     "#76E4F7",
  violet:   "#B794F4",
  rose:     "#F687B3",
  lime:     "#9AE6B4",
  gold:     "#ECC94B",
  indigo:   "#7F9CF5",
  teal:     "#4FD1C5",
};

// ─── PHASE META ──────────────────────────────────────────────────────────────
const PHASE_META = [
  { id:1,  code:"P1",  title:"Domain Foundation",        sub:"Scope · SDTM Minimal Set · SAP Extraction",               col:"#76E4F7", weeks:"2–3" },
  { id:2,  code:"P2",  title:"Semantic Metadata Repo",   sub:"SQLite + DuckDB · 14-Table Schema · Alembic",             col:"#B794F4", weeks:"4–5" },
  { id:3,  code:"P3",  title:"Declarative Derivation",   sub:"Rule Engine · RECIST+iRECIST · BICR Branches",            col:"#F6AD55", weeks:"3–4" },
  { id:4,  code:"P4",  title:"Execution Runtime",        sub:"ExecutionAdapter · SAS · Dataset-JSON · Snapshots",       col:"#63B3ED", weeks:"3–4" },
  { id:5,  code:"P5",  title:"Explainable QC Engine",    sub:"CDISC CORE · Level 4/5 Conformance · Root-Cause",         col:"#FC8181", weeks:"3–4" },
  { id:6,  code:"P6",  title:"Semantic Lineage Graph",   sub:"NetworkX · RDF Lineage Ontology · SHACL Validation",      col:"#68D391", weeks:"3–4" },
  { id:7,  code:"P7",  title:"Define.xml + ARM",         sub:"v2.1 · ARM · CDISC ARS v1.0 · Single-Source",             col:"#F6AD55", weeks:"2–3" },
  { id:8,  code:"P8",  title:"Reviewer Transparency",    sub:"Lineage Reports · JSON-LD SDRG · Audit Logs",             col:"#B794F4", weeks:"2 wks" },
  { id:9,  code:"P9",  title:"AI Governance Layer",      sub:"4-Signal Confidence · SAP Extraction · Approval UI",      col:"#9AE6B4", weeks:"3–4" },
];

// ─── SEMANTIC ENTITY HIERARCHY (v5.0.0 Expanded 14-Table Schema) ─────────────
const SEMANTIC_HIERARCHY = [
  { level:1,  entity:"Protocol Objective",    table:"protocol_objectives",         source:"ICH M11 YAML block",             col:"#76E4F7", isNew:false, promoted:true,  fields:["obj_id","obj_text","obj_type","m11_section","endpoint_id FK"] },
  { level:2,  entity:"Biomedical Concept",    table:"biomedical_concepts",         source:"CDISC COSMoS / custom",          col:"#B794F4", isNew:false, promoted:true,  fields:["bc_id","bc_name","bc_category","cosmos_bc_id","sdtmig_class","coding_system","parent_bc_id FK"] },
  { level:3,  entity:"Dataset Specialization",table:"dataset_specializations",     source:"Concept variables implementation",col:"#F687B3", isNew:true,  promoted:false, fields:["specialization_id","bc_id FK","domain","variable_name","role"] },
  { level:4,  entity:"Endpoint Definition",   table:"endpoint_definitions",        source:"SAP + estimand linkage",         col:"#F6AD55", isNew:false, promoted:true,  fields:["endpoint_id","bc_id FK","estimand_id FK","endpoint_type","analysis_concept","sap_reference","criteria_type"] },
  { level:5,  entity:"Estimand",              table:"estimands",                   source:"ICH E9(R1) — existing",          col:"#63B3ED", isNew:false, promoted:false, fields:["estimand_id","name","ice_strategy","target_population","variable_of_interest","summary_measure"] },
  { level:6,  entity:"Derivation Rule",       table:"derivation_rules",            source:"Rule engine — existing",         col:"#FC8181", isNew:false, promoted:false, fields:["rule_id","endpoint_id FK","target_variable","logic_type","assessor","criteria_type","approval_status","logic_definition"] },
  { level:7,  entity:"Variable Realization",  table:"variables",                   source:"SDTM/ADaM — existing",           col:"#68D391", isNew:false, promoted:false, fields:["variable","dataset","role","datatype","bc_id FK","origin","controlled_terminology"] },
  { level:8,  entity:"Parameter Metadata",    table:"parameter_variable_metadata", source:"Parameter-level metadata mapping",col:"#ECC94B", isNew:true,  promoted:false, fields:["dataset","variable","paramcd","bc_id FK","rule_id FK","role","origin"] },
  { level:9,  entity:"Analysis Result",       table:"analysis_results",            source:"ARM source — promoted to P2",    col:"#4FD1C5", isNew:false, promoted:true,  fields:["analysis_id","endpoint_id FK","dataset","paramcd","where_clause_id FK","stat_method","stat_test","tfl_reference","estimand_id FK","arm_display_label"] },
  { level:10, entity:"Where Clause",          table:"where_clauses",               source:"Filter condition metadata",      col:"#7F9CF5", isNew:true,  promoted:false, fields:["where_clause_id","dataset","variable","filter_operator","filter_value"] },
  { level:11, entity:"Execution Snapshot",    table:"execution_snapshots",         source:"Reproducibility ledger",         col:"#B794F4", isNew:false, promoted:true,  fields:["snapshot_id","run_id","sdtmig_version","adamig_version","python_version","sas_version","rule_hash_manifest","metadata_db_hash","environment_hash"] },
  { level:12, entity:"Program Metadata",      table:"programs",                    source:"SAS generated programs",         col:"#9AE6B4", isNew:true,  promoted:false, fields:["program_id","name","generated_path","sha256_hash","compiled_ts"] },
  { level:13, entity:"Pending Queue",         table:"pending_queue",               source:"AI extraction curation queue",   col:"#F6AD55", isNew:true,  promoted:false, fields:["queue_id","action_type","payload","status","created_ts"] },
  { level:14, entity:"AI Action Audit",       table:"ai_actions",                  source:"Governance audit trail",         col:"#FC8181", isNew:true,  promoted:false, fields:["action_id","timestamp","model_version","prompt_hash","input_hash","output_hash","confidence_composite","confidence_signals","human_decision","human_id","decision_ts","rejection_reason","endpoint_id_proposed","endpoint_id_approved"] },
];

// ─── ESTIMAND & CROSSOVER TRACKERS (v5.0.0 New Section) ──────────────────────
const CLINICAL_TRACKERS = [
  { name:"ADSL (Analysis Dataset for Subject Level)", type:"Vectorized Cohort", purpose:"Demographics, balanced 3-arm randomization, and estimand flags", fields:"ARM, ARMCD, WTFL (Washout Treatment Flag), TEFFFL (Treatment Efficacy Flag), PSYFL (Principal Stratum Flag)", isNew:true },
  { name:"ADICE (Analysis Dataset for Intercurrent Events)", type:"OCCDS Structure", purpose:"Longitudinal intercurrent events tracking (82 event cohort)", fields:"STUDYID, USUBJID, ASTDT, AVALC (Intercurrent Event Strategy: Treatment Policy), ASRC (initiation of non-protocol therapy, washout)", isNew:true },
  { name:"ADPANEL (Longitudinal Panel)", type:"Time-Varying Panel", purpose:"Derives stabilized Inverse Probability of Censoring Weights (SW_IPCW)", fields:"USUBJID, TIME, ON_NEW_THERAPY, PROGRESSION, SW_IPCW (stabilized panel weight for censoring sensitivity)", isNew:true },
];

// ─── REPRODUCIBILITY & SYSTEM COMPONENTS ────────────────────────────────────
const REPRO_COMPONENTS = [
  { name:"execution_snapshots",     type:"SQLite table",   purpose:"Pinned runtime state — exact replay",          fields:"snapshot_id, run_id FK, sdtmig_version, adamig_version, python_version, sas_version, rule_hash_manifest JSON, environment_hash, created_ts", isNew:false },
  { name:"environment_manifest.json", type:"File artifact", purpose:"pip freeze + SAS version + OS at run time",    fields:"python_packages: {}, sas_version, os, execution_ts, claude_model_version (for AI runs)", isNew:false },
  { name:"rule_hash_manifest",      type:"JSON field",     purpose:"Exact rule set state at execution — drift detection", fields:"JSON array of {rule_id, rule_version, rule_logic_hash} for every rule active in this run", isNew:false },
  { name:"GxP Container Isolate",   type:"Docker Compose",  purpose:"Multi-stage reproducible build sandbox",       fields:"Debian-based container, virtualenv pinning, strict OS dependency locking, offline metadata verify", isNew:true },
  { name:"Stopwatch Instrumentation",type:"Precision Timer",purpose:"Captures wall-clock timing across 9 pipeline stages",fields:"Time tracking on models build, cohort compile, rule parse, SAS execute, QC conformance, lineage RDF, Define.xml export, SDRG print, AI audit", isNew:true },
];

// ─── FULL PHASE DATA (v5.0.0: Full FDA-Grade Pipeline) ──────────────────────
const PHASES = [
  {
    id:1, col:"#76E4F7",
    status:"START HERE",
    version:"v5.0.0 → FDA & ICH Compliant",
    auditChanges:[
      "ADDED: SV domain (FDA 2023 mandate — all scheduled visits required)",
      "ADDED: ICH M11 protocol metadata section in study_config.yaml",
      "ADDED: iRECIST noted as dual-criteria alongside RECIST 1.1 from scope stage",
    ],
    v3Changes:[
      "UPGRADED: Integrated Balanced 3-Arm Randomization Scheme (Atezo+BCP, Atezo+CP, BCP)",
      "UPGRADED: Designed ADICE OCCDS Structure to record 82 intercurrent events (e.g. initiation of subsequent non-protocol cancer therapies)",
      "UPGRADED: Structured ADPANEL time-varying dataset tracking longitudinal crossover events and stabilized censoring weights (SW_IPCW)",
    ],
    researchBasis:"CDISC 360i Phase 1 delivered a complete pre-configured study package as machine-readable metadata from design through submission. ICH M11 effective June 11, 2026 — structured protocol metadata is now a live regulatory standard. FDA OCE Guidelines mandate robust longitudinal sensitivity analysis for intercurrent events.",
    tasks:[
      {
        type:"DECISION",
        title:"Estimand Strategy and 3-Arm Balanced Design",
        detail:"Oncology immunotherapy solid tumor study. Randomization: Atezo + BCP vs Atezo + CP vs BCP. Population defined using estimand flags: WTFL (washout), TEFFFL (treatment efficacy), and PSYFL (Principal Stratum Flag tracking subject crossovers under ICH E9(R1)).",
        fix:null,
      },
      {
        type:"BUILD",
        title:"ADICE (Intercurrent Events Dataset)",
        detail:"Implement CDISC OCCDS compliant dataset mapping intercurrent events. Capture subsequent non-protocol cancer therapy initiation across subjects to evaluate the primary treatment policy estimand.",
        fix:"FDA FIX: Missing ADICE would violate CDISC compliance and fail to document intercurrent events correctly.",
      },
      {
        type:"BUILD",
        title:"ICH M11–Aligned study_config.yaml",
        detail:"study_id, sponsor, protocol_version, standards_version (SDTMIG 3.4 / ADaM 1.3), define_xml_version: 2.1, m11_protocol: { objectives: [...], primary_endpoints: [...], estimands: [{name, intercurrent_event_strategy, target_population}], schedule_of_activities: {visits: [...]} }.",
        fix:"AUDIT FIX: Structured protocol metadata is mandatory under ICH M11 as of June 2026.",
      },
      {
        type:"EXTRACT",
        title:"SAP Logic Extraction & PFS Sensitivity",
        detail:"PFS (FDA censor rules on new therapy) vs. PFS_EMA (EMA rules treating subsequent therapy as event). Capture baseline ECOG status and clinical cohort variables.",
        fix:null,
      },
    ],
    outputs:["study_config.yaml (M11-aligned)", "sdtm_domain_list.yaml (incl. SV)", "ADSL (3-arm cohort)", "ADICE & ADPANEL definitions"],
    criticalDecision:"Do NOT write derivation code yet. Fully map out M11 objectives, estimands, and intercurrent events to ensure perfect semantic anchors upstream.",
  },
  {
    id:2, col:"#B794F4",
    status:"MOST CRITICAL",
    version:"v5.0.0 → 14-TABLE SEMANTIC SCHEMA",
    auditChanges:[
      "ADDED: DuckDB as analytical store alongside SQLite (OLTP/OLAP split)",
      "ADDED: Alembic schema migration framework from day 1",
      "ADDED: parent_bc_id column to biomedical_concepts for concept inheritance mapping (H8)",
      "ADDED: dataset_specializations table for mapping domain variables to concepts (H8)",
    ],
    v3Changes:[
      "NEW: parameter_variable_metadata table — parameter-level realization metadata",
      "NEW: pending_queue and ai_actions tables — first-class governance models",
      "NEW: where_clauses table — filter conditions metadata mapping",
      "REVISED: variables table gets bc_id FK — variables become concept implementations",
      "REVISED: biomedical_concepts supports subClassOf hierarchical mappings",
    ],
    researchBasis:"CDISC 360i & COSMoS frame variables as mere implementation artifacts of core clinical concepts. The 14-table schema positions biomedical concepts as the clinical root, mapping them down through specializations, objectives, and realization variables.",
    tasks:[
      {
        type:"ARCHITECTURE",
        title:"14-Table Semantic Schema & Alembic",
        detail:"Invert variable-centric data mapping to concept-centric. Every variable has a bc_id FK pointing to a biomedical concept. Add parent_bc_id FK to support concept inheritance. Track all schemas via Alembic versioned migrations.",
        fix:"RESEARCH FIX: Concept-as-primary-key is the authoritative CDISC 360i design pattern, preventing conceptually unanchored variables.",
      },
      {
        type:"BUILD",
        title:"New Entity: dataset_specializations",
        detail:"Maps biomedical concepts to specific SDTM/ADaM variables in target domains. Fields: specialization_id, bc_id, domain, variable_name, role. Generates explicit semantic associations.",
        fix:null,
      },
      {
        type:"BUILD",
        title:"New Entity: parameter_variable_metadata",
        detail:"Enables parameter-level concept realization (e.g., ADaM PARAMCD values). Traces paramcd and variables back to biomedical_concepts and derivation_rules.",
        fix:"V5.0.0 FIX: Fills the gap in parameter-level traceability for multi-parameter ADaM datasets like ADTTE.",
      },
    ],
    outputs:["metadata.db (14-table schema)", "models.py (SQLAlchemy ORM)", "alembic/ migrations", "lineage_ontology.ttl template"],
    criticalDecision:"The database schema is the architecture. All downstream components (engine, graph, define) compile against these 14 tables.",
  },
  {
    id:3, col:"#F6AD55",
    status:"DIFFERENTIATOR",
    version:"v5.0.0 → Vectorized Rule Compiler",
    auditChanges:[
      "ADDED: response_criteria field (RECIST_1.1 | iRECIST | both) in rule engine",
      "ADDED: iRECIST iUPD logic branch — iUPD_flag, confirmation_window_days",
      "ADDED: assessor field driving BICR vs Investigator parallel derivation paths",
    ],
    v3Changes:[
      "UPGRADED: Vectorized SQL rule parsing in DuckDB to compute ADSL demographic randomization",
      "UPGRADED: Vectorized calculation of stabilized censoring weights (SW_IPCW) within longitudinal panel",
      "UPGRADED: PFS vs PFS_EMA sensitivity branches compiled dynamically from metadata database",
    ],
    researchBasis:"Row-by-row clinical data loops are slow and error-prone. Modern clinical programming (PhUSE Cloud-Native, CDISC 360) requires declarative rule engines that compile metadata into highly optimized, vectorized execution statements (SQL/DuckDB).",
    tasks:[
      {
        type:"BUILD",
        title:"Vectorized cohort and weight generator",
        detail:"Write optimized, vectorized DuckDB expressions to assign WTFL, TEFFFL, and PSYFL on ADSL. Compute stabilized IPCW panel weights based on ECOG and time-varying clinical indicators in ADPANEL.",
        fix:"V5.0.0 FIX: Sequential Python loops are prohibited; all derivations are fully vectorized in DuckDB memory.",
      },
      {
        type:"BUILD",
        title:"Investigator vs. Parallel BICR Assessor Branches",
        detail:"Support parallel assessment paths by compiling separate derivation rules tagged assessor='INVESTIGATOR' and assessor='BICR', outputting ParamCodes OVRLRESP vs BICRRESP.",
        fix:null,
      },
    ],
    outputs:["rule_parser.py", "execution_adapter.py (vectorized DuckDB adapter)", "compiled_programs/"],
    criticalDecision:"All clinical derivations must be compiled as declarative SQL expressions over the cohort panel, eliminating row-level logic errors.",
  },
  {
    id:4, col:"#63B3ED",
    status:"EXECUTION",
    version:"v5.0.0 → Deterministic Sandbox",
    auditChanges:[
      "ADDED: ExecutionAdapter abstract base class — SAS, R, Python adapters",
      "ADDED: Dataset-JSON v1.1.0 output path alongside XPT",
    ],
    v3Changes:[
      "NEW: Multi-stage Dockerfile isolating the entire runtime and dependencies",
      "NEW: docker-compose.yml automating GxP compilation in a repeatable environment",
      "NEW: Precision Stopwatch Instrumentation timing all 9 stages in orchestrator.py",
    ],
    researchBasis:"FDA Technical Conformance Guidance emphasizes deterministic repeatability. Hashing dataset outputs is not enough — environment-level replayability requires locked OS libraries, pinned pip virtualenvs, and fully isolated execution sandboxes.",
    tasks:[
      {
        type:"BUILD",
        title:"GxP Docker Containment",
        detail:"Author a multi-stage Dockerfile containing Python, SQLite, and DuckDB. Lock environment packages via exact hashes. Automate pipeline execution via docker-compose.",
        fix:"GxP FIX: Standardizes compiler state, satisfying FDA requirements for reproducible execution environments.",
      },
      {
        type:"BUILD",
        title:"Dataset-JSON & NDJSON Streaming",
        detail:"Output clinical datasets in both CDISC XPT format and fully compliant CDISC Dataset-JSON v1.1.0 envelopes, featuring NDJSON streaming for massive clinical cohorts.",
        fix:null,
      },
    ],
    outputs:["Dockerfile", "docker-compose.yml", "outputs/datasets/ (.xpt and .json)", "orchestrator.py timing report"],
    criticalDecision:"Wrap all pipeline executions in precision stopwatches to log operational metrics directly into the regulatory reviewer package.",
  },
  {
    id:5, col:"#FC8181",
    status:"QC CONFORMANCE",
    version:"v5.0.0 → 5-LEVEL CONFORMANCE ENGINE",
    auditChanges:[
      "ADDED: CDISC CORE engine integration for Level 1",
      "ADDED: Level 2 Oncology Semantics (RECIST_001-004, iRECIST_001-003)",
      "ADDED: Level 3 Semantic Root-Cause Tracing using lineage graphs",
    ],
    v3Changes:[
      "NEW: Level 4 Cross-dataset Referential Integrity checks (validating ADaM against SDTM)",
      "NEW: Level 5 NCI EVS Controlled Terminology validation in qc_engine.py",
      "UPGRADED: Rule ID taxonomies aligned perfectly to CDISC CORE rule names (CORE-000xxx)",
    ],
    researchBasis:"Clinical QC must evaluate both data structures and clinical logic. CDISC CORE provides structural validation. Level 4 referential integrity prevents relational breaks. Level 5 validates code-system currency with NCI Thesaurus.",
    tasks:[
      {
        type:"BUILD",
        title:"Level 4 & 5 Validation Integration",
        detail:"Write QC rules verifying cross-dataset relationships (e.g. ADaM vs SDTM keys) and mapping variables to standard CDISC NCI EVS controlled terminologies.",
        fix:"COMPLIANCE FIX: Ensures complete conformance with current FDA and PMDA submission rules.",
      },
      {
        type:"BUILD",
        title:"CDISC CORE Alignment",
        detail:"Map custom and base rule IDs to standard CORE nomenclature (e.g., CORE-000123) for seamless integration with regulatory reviewer engines.",
        fix:null,
      },
    ],
    outputs:["qc_engine.py (5-level QC)", "qc_findings.duckdb", "qc_narratives/"],
    criticalDecision:"surfaces clinical endpoint risks (e.g., PFS, OS metrics) in QC reports, not just technical variable warnings.",
  },
  {
    id:6, col:"#68D391",
    status:"KNOWLEDGE GRAPH",
    version:"v5.0.0 → W3C RDF Ontology",
    auditChanges:[
      "ADDED: estimand_id as node attribute in DiGraph",
      "ADDED: edge attributes for criteria_type (RECIST / iRECIST)",
    ],
    v3Changes:[
      "UPGRADED: Graph spans 14-table semantic schema (Objective→BC→Endpoint→Rule→Variable→Result→Artifact)",
      "NEW: Graph builder serializes full W3C RDF Lineage Ontology (Turtle format)",
      "NEW: W3C SHACL Shape Constraints validation validation rules built inside ontology",
    ],
    researchBasis:"PHUSE Cloud-Native and CDISC 360i mandate transitioning from passive metadata documents to semantic RDF Ontologies. OWL and SHACL shape graphs enable automated validation of submission compliance before FDA review.",
    tasks:[
      {
        type:"BUILD",
        title:"W3C RDF Lineage Graph Serialization",
        detail:"Write RDF graph builder in graph_builder.py to output lineage_ontology.ttl. Include rdfs:subClassOf hierarchical inheritance for all clinical concepts.",
        fix:"RESEARCH FIX: Standardizes clinical relationships in a machine-readable semantic schema, enabling cross-study interoperability.",
      },
      {
        type:"BUILD",
        title:"SHACL Constraints Validation",
        detail:"Add W3C SHACL shape shapes to lineage_ontology.ttl, defining mandatory relationships (e.g., variables must trace back to a biomedical concept).",
        fix:null,
      },
    ],
    outputs:["graph_builder.py", "outputs/submission/lineage_ontology.ttl", "shacl_report.txt"],
    criticalDecision:"Represent all conceptual lineage (M11 to results) as a formal RDF graph, positioning this pipeline ahead of current standard clinical data models.",
  },
  {
    id:7, col:"#F6AD55",
    status:"EXPORTERS",
    version:"v5.0.0 → CDISC ARS v1.0 & M11",
    auditChanges:[
      "ADDED: Define.xml v2.1 compliance",
      "ADDED: ItemDef CommentDef populated automatically from concept definitions",
    ],
    v3Changes:[
      "NEW: Native CDISC ARS v1.0 Statistical Results exporter (ard_generator.py)",
      "NEW: Native ICH M11 Structured Digital Protocol exporter (m11_protocol_exporter.py)",
      "UPGRADED: Define.xml generation fully synchronized with 14-table metadata model",
    ],
    researchBasis:"CDISC Analysis Results Standard (ARS) v1.0 (released v1 2025) provides a machine-readable JSON structure linking results directly to endpoints and estimands. ICH M11 requires structured protocol exchange. Define.xml is now a live synchronization layer.",
    tasks:[
      {
        type:"BUILD",
        title:"CDISC ARS v1.0 Exporter",
        detail:"Implement ard_generator.py to serialize statistical endpoints (hazard ratios, log-rank p-values, KM rates) in standard ard.json, mapping to estimands and endpoints.",
        fix:"ARS FIX: Establishes a formal, modern digital connection between results and their clinical protocol context.",
      },
      {
        type:"BUILD",
        title:"ICH M11 digital protocol exporter",
        detail:"Write m11_protocol_exporter.py to output structured protocol objectives, estimands, and schedule of assessments to m11_protocol.json.",
        fix:null,
      },
    ],
    outputs:["ard_generator.py", "m11_protocol_exporter.py", "outputs/submission/define.xml", "ard.json", "m11_protocol.json"],
    criticalDecision:"Eliminate all hardcoded XML or JSON. All exports are compiled dynamically from the metadata tables, ensuring perfect single-source governance.",
  },
  {
    id:8, col:"#B794F4",
    status:"TRANSPARENCY",
    version:"v5.0.0 → Machine-Readable SDRG",
    auditChanges:[
      "ADDED: Study Data Reviewer's Guide (SDRG) generated as HTML and JSON-LD",
      "ADDED: Program and dataset SHA-256 integrity checks",
    ],
    v3Changes:[
      "UPGRADED: JSON-LD SDRG embeds clinical concept and endpoint URIs for complete COSMoS compatibility",
      "UPGRADED: Lineage reports display full concept names, endpoint labels, and estimand definitions in header",
    ],
    researchBasis:"The FDA has highlighted static PDF SDRGs as major hurdles in reviewer efficiency. Structured JSON-LD SDRGs embed clinical and technical metadata that programmatic review tools can scan and query automatically.",
    tasks:[
      {
        type:"BUILD",
        title:"COSMoS-Compatible JSON-LD SDRG",
        detail:"Enhance define_xml_generator.py to output sdrg.jsonld. Embed direct concept URIs, mapping variables and rules to their corresponding COSMoS definitions.",
        fix:null,
      },
      {
        type:"BUILD",
        title:"Reproducibility Audit Log",
        detail:"Combine execution_snapshots, execution_log, and programs to output a complete, compliance-ready PDF and JSON audit trail linking every run to its GxP environment.",
        fix:null,
      },
    ],
    outputs:["outputs/submission/sdrg.html", "outputs/submission/sdrg.jsonld", "outputs/submission/lineage_report.html", "execution_audit_log.pdf"],
    criticalDecision:"Embed machine-readable metadata in both Define.xml and SDRG, turning review files from static text into an interactive clinical graph.",
  },
  {
    id:9, col:"#9AE6B4",
    status:"LAST",
    version:"v5.0.0 → CI/CD Compliance Gate",
    auditChanges:[
      "REPLACED: Logprob confidence with 4-signal composite confidence scoring",
      "ADDED: STREAMLIT AI Curation & Governance dashboard",
    ],
    v3Changes:[
      "NEW: GitHub Actions workflow (pipeline.yml) running test suites and checking coverage gates (M13)",
      "NEW: Integrated automated tests verifying ADSL, ADICE, ADPANEL, and exporters",
      "UPGRADED: AI approval UI displays parent_bc_id concept mappings and database model logs",
    ],
    researchBasis:"Human-in-the-loop is the only legally defensible AI design in clinical trial pipelines. The AI Governance layer assists clinical programmers in metadata extraction, passing candidates through strict compliance gates.",
    tasks:[
      {
        type:"BUILD",
        title:"GitHub Actions Compliance Gate",
        detail:"Deploy a continuous integration pipeline running pytest over clinical cohort generation, rules validation, and XML schema checks on every commit.",
        fix:"SDLC FIX: Satisfies FDA Software Validation (CSV) mandates by keeping an automated, logged test trail.",
      },
      {
        type:"BUILD",
        title:"AI-Powered Curation UI",
        detail:"Provide clinical curators with a Streamlit interface to review, approve, reject, or edit LLM-extracted metadata, directly updating the 14 database tables.",
        fix:null,
      },
    ],
    outputs:["pipeline.yml (CI/CD workflow)", "tests/test_pipeline.py", "approval_ui.py logs", "ai_actions SQLite records"],
    criticalDecision:"Continuous Integration enforces the absolute rule: no dataset can be generated unless it passes all 5 levels of the QC engine.",
  },
];

const TECH_STACK = [
  { layer:"Protocol Config",      tech:"YAML (M11-aligned)",         rationale:"Structured ICH M11 protocol metadata. Single seed for semantic metadata repository, seeding protocol_objectives table on init." },
  { layer:"Semantic Root",        tech:"biomedical_concepts (v5.0.0)",rationale:"CDISC COSMoS-aligned BC table featuring parent_bc_id concept inheritance and dataset_specializations." },
  { layer:"Metadata Store",       tech:"SQLite + Alembic (14-Table)", rationale:"OLTP metadata schema versioned through Alembic migrations — tracking objectives, rules, variables, and parameters." },
  { layer:"Analytical Store",     tech:"DuckDB (Vectorized)",        rationale:"High-speed OLAP engine executing vectorized cohort SQL derivations, SW_IPCW weight math, and QC audits." },
  { layer:"Reproducibility",      tech:"Docker + Snapshot Manager",  rationale:"GxP Docker sandbox isolation combined with SQLite snapshot ledgers and environment manifest hashes." },
  { layer:"Orchestration",        tech:"Python (Stopwatch Timed)",   rationale:"Precision stopwatch timing tracking all 9 stages in orchestrator.py. ExecutionAdapter ABC makes SAS replaceable." },
  { layer:"Transport Format",     tech:"XPT + Dataset-JSON v1.1.0",  rationale:"Dual submission output, supporting Dataset-JSON streaming and NDJSON formatting." },
  { layer:"Semantic Graph",       tech:"W3C RDF Turtle + SHACL",     rationale:"Lineage graph serialized to Turtle ontology featuring rdfs:subClassOf and SHACL shape constraint validation." },
  { layer:"Validation",           tech:"CDISC CORE (5-Level)",       rationale:"5-level QC engine with Level 1 CORE rules, Level 2 Oncology RECIST, Level 4 referential integrity, Level 5 NCI CT." },
  { layer:"Submission XML/JSON",  tech:"Define.xml v2.1 + CDISC ARS",rationale:"Auto-generated, comment-annotated Define.xml + CDISC ARS v1.0 ard.json + structured JSON-LD SDRG." },
  { layer:"Governance UI",        tech:"Streamlit Dashboard",        rationale:"Interactive dashboard displaying layered knowledge graphs, 5-level QC, and AI metadata curation interface." },
  { layer:"CI/CD Pipeline",       tech:"GitHub Actions (pipeline.yml)",rationale:"Continuous integration workflow containing strict automated test suites, coverage checks, and GxP validation gates." },
];

const ROADMAP = [
  { v:"v1.0", phases:[1,2,3,4], label:"Semantic Metadata Repository + Declarative Derivation Runtime", milestone:"First concept-rooted metadata-driven SAS execution with Dataset-JSON + execution snapshots.", color:"#76E4F7" },
  { v:"v2.0", phases:[5,6],     label:"Semantic QC + Knowledge Graph",                                  milestone:"Endpoint-grouped QC narratives + 8-layer semantic graph from protocol objective to reviewer artifact.", color:"#FC8181" },
  { v:"v3.0", phases:[7,8],     label:"Semantic Define.xml + JSON-LD SDRG",                             milestone:"BC-annotated Define.xml + COSMoS-interoperable JSON-LD SDRG + snapshot-linked audit log.", color:"#F6AD55" },
  { v:"v4.0", phases:[9],       label:"4-Signal Governed Semantic AI Extraction",                       milestone:"LLM extraction with endpoint context, composite confidence, and divergence quality metric.", color:"#9AE6B4" },
  { v:"v5.0.0", phases:[1,2,3,4,5,6,7,8,9], label:"Regulatory Estimand Trackers, ARS & ICH M11 Exporters",  milestone:"Balanced 3-arm ADSL, ADICE OCCDS, longitudinal stabilized IPCW panel, CDISC ARS v1.0, ICH M11 digital protocol, Level 4/5 conformance, and GxP Docker sandbox.", color:"#ECC94B" },
];

// ─── COMPONENT ───────────────────────────────────────────────────────────────
export default function App() {
  const [view, setView]         = useState("phases");
  const [activePhase, setActive] = useState<number | null>(null);
  const [taskOpen, setTaskOpen]  = useState<number | null>(null);
  const [semOpen, setSemOpen]    = useState<number | null>(null);

  const ph = PHASES.find(p => p.id === activePhase);

  return (
    <div style={{ background:C.bg, minHeight:"100vh", color:C.text,
      fontFamily:"'JetBrains Mono','Fira Code','Courier New',monospace" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Syne:wght@400;600;700;800&display=swap');
        * { box-sizing:border-box; margin:0; padding:0; }
        ::-webkit-scrollbar { width:4px; }
        ::-webkit-scrollbar-track { background:${C.surface}; }
        ::-webkit-scrollbar-thumb { background:${C.borderHi}; border-radius:2px; }
        .phase-card:hover { border-color:${C.borderHi} !important; }
        .task-row:hover { background:rgba(255,255,255,.03) !important; }
        .nav-btn:hover { background:rgba(255,255,255,.06) !important; }
        .sem-row:hover { background:rgba(255,255,255,.025) !important; }
      `}</style>

      {/* ── HEADER ─────────────────────────────────────────────────── */}
      <div style={{ borderBottom:`1px solid ${C.border}`, padding:"20px 28px 18px" }}>
        <div style={{ display:"flex", alignItems:"flex-start", justifyContent:"space-between", flexWrap:"wrap", gap:12 }}>
          <div>
            <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:6 }}>
              <div style={{ fontSize:9, color:C.violet, letterSpacing:".2em",
                textTransform:"uppercase", background:`${C.violet}12`,
                border:`1px solid ${C.violet}25`, padding:"3px 9px", borderRadius:3 }}>
                v5.0.0 — Computable Submission Platform
              </div>
              <div style={{ fontSize:9, color:C.teal, letterSpacing:".15em",
                textTransform:"uppercase", background:`${C.teal}12`,
                border:`1px solid ${C.teal}25`, padding:"3px 9px", borderRadius:3 }}>
                FDA OCE & CDISC Compliant
              </div>
            </div>
            <div style={{ fontSize:20, fontWeight:800, color:C.textHi,
              fontFamily:"'Syne',sans-serif", lineHeight:1.1, marginBottom:4 }}>
              Explainable Metadata-Native Submission Engineering
            </div>
            <div style={{ fontSize:11, color:C.textLo, lineHeight:1.5 }}>
              Oncology Immunotherapy · 14-Table SQLite Schema · ADSL / ADICE / ADPANEL IPCW · CDISC ARS v1.0 · ICH M11 · W3C RDF Ontology
            </div>
          </div>
          <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
            {[
              { k:"phases",   label:"Phases" },
              { k:"trackers", label:"Clinical Trackers" },
              { k:"semantic", label:"14-Table Schema" },
              { k:"stack",    label:"Tech Stack" },
              { k:"roadmap",  label:"Roadmap" },
            ].map(b => (
              <button key={b.k} className="nav-btn" onClick={()=>{ setView(b.k); setActive(null); }}
                style={{ fontSize:10, color: view===b.k ? C.textHi : C.muted,
                  background: view===b.k ? C.raised : "transparent",
                  border:`1px solid ${view===b.k ? C.borderHi : C.border}`,
                  padding:"6px 14px", borderRadius:4, cursor:"pointer",
                  letterSpacing:".08em", textTransform:"uppercase" }}>
                {b.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── MAIN ───────────────────────────────────────────────────── */}
      <div style={{ maxWidth:980, margin:"0 auto", padding:"22px 20px 60px" }}>

        {/* ── PHASES VIEW ──────────────────────────────────────────── */}
        {view==="phases" && !activePhase && (
          <div>
            <div style={{ fontSize:11, color:C.muted, marginBottom:18, lineHeight:1.6 }}>
              Click any phase to expand. <span style={{ color:C.violet }}>● v5.0.0 clinical pipelines</span> integrated inline.
              Phases with violet badges contain advanced semantic updates or regulatory exporters.
            </div>
            <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(290px,1fr))", gap:10 }}>
              {PHASES.map(p => {
                const pm = PHASE_META.find(m=>m.id===p.id) || PHASE_META[0];
                const hasV3 = p.v3Changes && p.v3Changes.length > 0;
                return (
                  <div key={p.id} className="phase-card"
                    onClick={()=>{ setActive(p.id); setTaskOpen(null); }}
                    style={{ background:C.surface, border:`1px solid ${C.border}`,
                      borderRadius:8, padding:"16px 18px", cursor:"pointer",
                      borderLeft:`3px solid ${pm.col}`, transition:"border-color .15s" }}>
                    <div style={{ display:"flex", justifyContent:"space-between",
                      alignItems:"flex-start", marginBottom:8 }}>
                      <div style={{ display:"flex", gap:6, alignItems:"center" }}>
                        <span style={{ fontSize:10, fontWeight:700, color:pm.col,
                          fontFamily:"'Syne',sans-serif" }}>{pm.code}</span>
                        <span style={{ fontSize:9, color:C.muted }}>·</span>
                        <span style={{ fontSize:9, color:C.textLo }}>{pm.weeks}w</span>
                      </div>
                      <div style={{ display:"flex", gap:5 }}>
                        {hasV3 && (
                          <span style={{ fontSize:8, color:C.violet,
                            background:`${C.violet}12`, border:`1px solid ${C.violet}30`,
                            padding:"2px 6px", borderRadius:2, letterSpacing:".1em" }}>
                            v5.0.0
                          </span>
                        )}
                        <span style={{ fontSize:8, color:pm.col,
                          background:`${pm.col}10`, border:`1px solid ${pm.col}25`,
                          padding:"2px 7px", borderRadius:2, letterSpacing:".08em" }}>
                          {p.status}
                        </span>
                      </div>
                    </div>
                    <div style={{ fontSize:13, fontWeight:700, color:C.textHi,
                      fontFamily:"'Syne',sans-serif", marginBottom:4 }}>{pm.title}</div>
                    <div style={{ fontSize:10, color:C.muted, lineHeight:1.5 }}>{pm.sub}</div>
                    {hasV3 && (
                      <div style={{ marginTop:10, paddingTop:9,
                        borderTop:`1px solid ${C.border}` }}>
                        <div style={{ fontSize:9, color:C.violet, letterSpacing:".1em",
                          textTransform:"uppercase", marginBottom:5 }}>v5.0.0 pipeline upgrades</div>
                        {p.v3Changes.slice(0,2).map((c,i)=>(
                          <div key={i} style={{ fontSize:9, color:`${C.violet}CC`,
                            lineHeight:1.5, paddingLeft:8,
                            borderLeft:`1px solid ${C.violet}30` }}>
                            {c}
                          </div>
                        ))}
                        {p.v3Changes.length > 2 && (
                          <div style={{ fontSize:9, color:C.muted, marginTop:3 }}>
                            +{p.v3Changes.length - 2} more
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ── PHASE DETAIL ─────────────────────────────────────────── */}
        {view==="phases" && activePhase && ph && (
          <div>
            <button onClick={()=>setActive(null)}
              style={{ fontSize:10, color:C.muted, background:"transparent",
                border:`1px solid ${C.border}`, padding:"5px 12px",
                borderRadius:4, cursor:"pointer", marginBottom:18, letterSpacing:".08em" }}>
              ← All Phases
            </button>

            {/* Phase header */}
            <div style={{ background:C.surface, border:`1px solid ${C.border}`,
              borderLeft:`3px solid ${ph.col}`, borderRadius:8,
              padding:"18px 22px", marginBottom:14 }}>
              <div style={{ display:"flex", justifyContent:"space-between",
                alignItems:"flex-start", flexWrap:"wrap", gap:8, marginBottom:10 }}>
                <div>
                  <div style={{ fontSize:9, color:ph.col, letterSpacing:".15em",
                    textTransform:"uppercase", marginBottom:5 }}>
                    {PHASE_META.find(m=>m.id===ph.id)?.code} · {ph.status}
                    <span style={{ color:C.muted, marginLeft:10 }}>{ph.version}</span>
                  </div>
                  <div style={{ fontSize:17, fontWeight:800, color:C.textHi,
                    fontFamily:"'Syne',sans-serif" }}>
                    {PHASE_META.find(m=>m.id===ph.id)?.title}
                  </div>
                </div>
              </div>
              <div style={{ fontSize:11, color:C.textLo, lineHeight:1.65,
                borderLeft:`2px solid ${C.borderHi}`, paddingLeft:12 }}>
                {ph.researchBasis}
              </div>
            </div>

            {/* v5.0.0 pipeline changes block */}
            {ph.v3Changes && ph.v3Changes.length > 0 && (
              <div style={{ background:`${C.violet}06`, border:`1px solid ${C.violet}20`,
                borderRadius:7, padding:"14px 16px", marginBottom:14 }}>
                <div style={{ fontSize:9, color:C.violet, letterSpacing:".15em",
                  textTransform:"uppercase", marginBottom:8 }}>v5.0.0 Pipeline Upgrades</div>
                <div style={{ display:"flex", flexDirection:"column", gap:4 }}>
                  {ph.v3Changes.map((c,i)=>(
                    <div key={i} style={{ fontSize:10, color:`${C.violet}CC`,
                      paddingLeft:10, borderLeft:`1px solid ${C.violet}35`, lineHeight:1.5 }}>
                      {c}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Audit changes block */}
            {ph.auditChanges && ph.auditChanges.length > 0 && (
              <div style={{ background:`${C.amber}06`, border:`1px solid ${C.amber}20`,
                borderRadius:7, padding:"14px 16px", marginBottom:14 }}>
                <div style={{ fontSize:9, color:C.amber, letterSpacing:".15em",
                  textTransform:"uppercase", marginBottom:8 }}>v2/v3 Historical Fixes (Carried Forward)</div>
                <div style={{ display:"flex", flexDirection:"column", gap:4 }}>
                  {ph.auditChanges.map((c,i)=>(
                    <div key={i} style={{ fontSize:10, color:`${C.amber}CC`,
                      paddingLeft:10, borderLeft:`1px solid ${C.amber}35`, lineHeight:1.5 }}>
                      {c}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tasks */}
            <div style={{ display:"flex", flexDirection:"column", gap:6, marginBottom:14 }}>
              {ph.tasks.map((t,i)=>{
                const isOpen = taskOpen===i;
                const typeColor = { BUILD:C.cyan, ARCHITECTURE:C.violet, DECISION:C.amber,
                  EXTRACT:C.green, MAP:C.blue, GOVERNANCE:C.rose }[t.type] || C.muted;
                return (
                  <div key={i} className="task-row"
                    onClick={()=>setTaskOpen(isOpen?null:i)}
                    style={{ background:C.surface, border:`1px solid ${C.border}`,
                      borderRadius:7, padding:"12px 16px", cursor:"pointer",
                      borderLeft:`2px solid ${typeColor}` }}>
                    <div style={{ display:"flex", justifyContent:"space-between",
                      alignItems:"center", gap:8 }}>
                      <div style={{ display:"flex", gap:8, alignItems:"center" }}>
                        <span style={{ fontSize:8, color:typeColor,
                          background:`${typeColor}12`, border:`1px solid ${typeColor}25`,
                          padding:"2px 7px", borderRadius:2, letterSpacing:".1em",
                          whiteSpace:"nowrap" }}>{t.type}</span>
                        <span style={{ fontSize:12, color:C.textHi, fontWeight:600 }}>{t.title}</span>
                      </div>
                      <span style={{ fontSize:10, color:C.muted }}>{isOpen?"▲":"▼"}</span>
                    </div>
                    {isOpen && (
                      <div style={{ marginTop:12 }}>
                        <div style={{ fontSize:11, color:C.text, lineHeight:1.7, marginBottom:t.fix?10:0 }}>
                          {t.detail}
                        </div>
                        {t.fix && (
                          <div style={{ background:`${C.gold}08`,
                            border:`1px solid ${C.gold}25`, borderRadius:4,
                            padding:"8px 12px", fontSize:10, color:C.gold, lineHeight:1.55 }}>
                            {t.fix}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Critical decision */}
            <div style={{ background:"rgba(99,179,237,.05)", border:"1px solid rgba(99,179,237,.2)",
              borderRadius:7, padding:"12px 16px", marginBottom:14 }}>
              <div style={{ fontSize:9, color:C.blue, letterSpacing:".15em",
                textTransform:"uppercase", marginBottom:5 }}>Critical Decision</div>
              <div style={{ fontSize:11, color:C.text, lineHeight:1.65 }}>{ph.criticalDecision}</div>
            </div>

            {/* Outputs */}
            <div style={{ background:C.surface, border:`1px solid ${C.border}`,
              borderRadius:7, padding:"12px 16px" }}>
              <div style={{ fontSize:9, color:C.green, letterSpacing:".15em",
                textTransform:"uppercase", marginBottom:8 }}>Phase Outputs</div>
              <div style={{ display:"flex", flexWrap:"wrap", gap:6 }}>
                {ph.outputs.map((o,i)=>(
                  <span key={i} style={{ fontSize:9, color:C.green,
                    background:`${C.green}0F`, border:`1px solid ${C.green}25`,
                    padding:"3px 8px", borderRadius:3 }}>{o}</span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── CLINICAL TRACKERS VIEW (v5.0.0 New View) ────────────────── */}
        {view==="trackers" && (
          <div>
            <div style={{ fontSize:11, color:C.muted, marginBottom:18, lineHeight:1.6 }}>
              The **v5.0.0 estimand and crossover engine** supports balanced 3-arm cohort definitions, OCCDS intercurrent events, and time-varying censoring weights.
            </div>
            <div style={{ display:"flex", flexDirection:"column", gap:10, marginBottom:16 }}>
              {CLINICAL_TRACKERS.map((tracker, i) => (
                <div key={i} style={{ background:C.surface, border:`1px solid ${C.border}`,
                  borderRadius:8, padding:"16px 20px", borderLeft:`3px solid ${C.teal}` }}>
                  <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:6 }}>
                    <span style={{ fontSize:13, fontWeight:700, color:C.textHi, fontFamily:"'Syne',sans-serif" }}>{tracker.name}</span>
                    <span style={{ fontSize:8, color:C.teal, background:`${C.teal}12`, border:`1px solid ${C.teal}25`, padding:"1px 6px", borderRadius:2 }}>{tracker.type}</span>
                  </div>
                  <div style={{ fontSize:11, color:C.text, marginBottom:8, lineHeight:1.5 }}>{tracker.purpose}</div>
                  <div style={{ fontSize:10, color:C.textLo, fontFamily:"'JetBrains Mono',monospace", background:C.raised, padding:"6px 10px", borderRadius:4, border:`1px solid ${C.border}` }}>
                    <span style={{ color:C.teal, fontWeight:600 }}>Tracked Fields:</span> {tracker.fields}
                  </div>
                </div>
              ))}
            </div>
            
            {/* Visual Schematic */}
            <div style={{ background:`${C.amber}05`, border:`1px solid ${C.amber}20`, borderRadius:8, padding:"16px 20px" }}>
              <div style={{ fontSize:9, color:C.amber, letterSpacing:".15em", textTransform:"uppercase", marginBottom:10 }}>ICH E9(R1) Treatment Policy Strategy Flow</div>
              <div style={{ fontSize:11, color:C.text, lineHeight:1.6 }}>
                Subjects randomized to 3 arms ──► Subsequent therapies flagged as intercurrent events in **ADICE** ──► Censoring sensitivity evaluated longitudinally in **ADPANEL** using **SW_IPCW** stabilized panel weights based on time-varying indicators ──► Statistical results compiled to **ard.json** (CDISC ARS v1.0).
              </div>
            </div>
          </div>
        )}

        {/* ── SEMANTIC MODEL (14-TABLE) VIEW ─────────────────────────── */}
        {view==="semantic" && (
          <div>
            <div style={{ fontSize:11, color:C.muted, marginBottom:20, lineHeight:1.6 }}>
              The **v5.0.0 metadata repository** has been expanded to a **14-table schema**, fully separating clinical concepts from physical realizations.
              Concept mappings include subClassOf inheritance (`parent_bc_id`) and parameter realization trackers.
            </div>

            {/* Hierarchy visualization */}
            <div style={{ background:C.surface, border:`1px solid ${C.border}`,
              borderRadius:8, padding:"20px 24px", marginBottom:16 }}>
              <div style={{ fontSize:9, color:C.violet, letterSpacing:".15em",
                textTransform:"uppercase", marginBottom:16 }}>
                14-Table Semantic Database Schema — Concept to Governance
              </div>
              <div style={{ display:"flex", flexDirection:"column", gap:0 }}>
                {SEMANTIC_HIERARCHY.map((e,i)=>(
                  <div key={i}>
                    <div className="sem-row"
                      onClick={()=>setSemOpen(semOpen===i?null:i)}
                      style={{ display:"flex", alignItems:"flex-start",
                        gap:12, padding:"10px 0", cursor:"pointer",
                        borderBottom: i<SEMANTIC_HIERARCHY.length-1 ? `1px solid ${C.border}` : "none" }}>
                      {/* Level indicator + connector */}
                      <div style={{ display:"flex", flexDirection:"column",
                        alignItems:"center", minWidth:20 }}>
                        <div style={{ fontSize:9, color:C.muted, marginBottom:2 }}>{e.level}</div>
                        {i < SEMANTIC_HIERARCHY.length-1 && (
                          <div style={{ width:1, height:16, background:C.borderHi }} />
                        )}
                      </div>
                      {/* Entity info */}
                      <div style={{ flex:1 }}>
                        <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:3 }}>
                          <span style={{ fontSize:13, fontWeight:700, color:e.col,
                            fontFamily:"'Syne',sans-serif" }}>{e.entity}</span>
                          {e.isNew && (
                            <span style={{ fontSize:8, color:C.rose,
                              background:`${C.rose}15`, border:`1px solid ${C.rose}30`,
                              padding:"1px 6px", borderRadius:2, letterSpacing:".1em" }}>NEW IN V5</span>
                          )}
                          {e.promoted && !e.isNew && (
                            <span style={{ fontSize:8, color:C.amber,
                              background:`${C.amber}12`, border:`1px solid ${C.amber}25`,
                              padding:"1px 6px", borderRadius:2, letterSpacing:".1em" }}>PROMOTED</span>
                          )}
                          <span style={{ fontSize:9, color:C.muted, fontFamily:"'JetBrains Mono',monospace" }}>
                            {e.table}
                          </span>
                        </div>
                        <div style={{ fontSize:10, color:C.textLo }}>{e.source}</div>
                        {semOpen === i && (
                          <div style={{ marginTop:8, background:C.raised,
                            border:`1px solid ${C.border}`, borderRadius:5,
                            padding:"10px 12px" }}>
                            <div style={{ fontSize:9, color:e.col, letterSpacing:".1em",
                              textTransform:"uppercase", marginBottom:6 }}>Key Database Columns</div>
                            <div style={{ display:"flex", flexWrap:"wrap", gap:5 }}>
                              {e.fields.map((f,j)=>(
                                <span key={j} style={{ fontSize:9,
                                  color: f.includes("FK") ? C.amber : f.includes("PK") ? e.col : C.text,
                                  background: f.includes("FK") ? `${C.amber}0D` : f.includes("PK") ? `${e.col}0D` : `${C.raised}`,
                                  border:`1px solid ${f.includes("FK") ? C.amber+"25" : f.includes("PK") ? e.col+"25" : C.border}`,
                                  padding:"2px 8px", borderRadius:3, fontFamily:"'JetBrains Mono',monospace" }}>
                                  {f}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                      <span style={{ fontSize:9, color:C.muted, marginTop:3 }}>
                        {semOpen===i?"▲":"▼"}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Core Inversion Callout */}
            <div style={{ background:`${C.violet}07`, border:`1px solid ${C.violet}25`,
              borderRadius:8, padding:"16px 20px", marginBottom:16 }}>
              <div style={{ fontSize:9, color:C.violet, letterSpacing:".15em",
                textTransform:"uppercase", marginBottom:10 }}>Computable Metadata Inversion</div>
              <div style={{ display:"grid", gridTemplateColumns:"1fr auto 1fr", gap:12, alignItems:"center" }}>
                <div style={{ background:C.raised, border:`1px solid ${C.border}`,
                  borderRadius:6, padding:"12px 14px" }}>
                  <div style={{ fontSize:9, color:C.red, letterSpacing:".1em",
                    marginBottom:6, textTransform:"uppercase" }}>v1/v2 (Legacy Variable Centric)</div>
                  {["dataset","↓ variable","↓ derivation_rule"].map((t,i)=>(
                    <div key={i} style={{ fontSize:11, color: i===0 ? C.red : C.muted,
                      fontFamily:"'JetBrains Mono',monospace", lineHeight:1.8,
                      fontWeight: i===0 ? 700 : 400 }}>{t}</div>
                  ))}
                  <div style={{ fontSize:9, color:C.muted, marginTop:6, fontStyle:"italic" }}>
                    Primary key: (dataset, variable)
                  </div>
                </div>
                <div style={{ fontSize:20, color:C.border }}>→</div>
                <div style={{ background:C.raised, border:`1px solid ${C.violet}30`,
                  borderRadius:6, padding:"12px 14px" }}>
                  <div style={{ fontSize:9, color:C.violet, letterSpacing:".1em",
                    marginBottom:6, textTransform:"uppercase" }}>v5.0.0 (Semantic Concept Centric)</div>
                  {["biomedical_concept (bc_id)","↓ dataset_specialization","↓ endpoint_definition","↓ estimand","↓ parameter_variable_metadata"].map((t,i)=>(
                    <div key={i} style={{ fontSize:11,
                      color: i===0 ? C.violet : C.text,
                      fontFamily:"'JetBrains Mono',monospace", lineHeight:1.8,
                      fontWeight: i===0 ? 700 : 400 }}>{t}</div>
                  ))}
                  <div style={{ fontSize:9, color:C.violet, marginTop:6, fontStyle:"italic" }}>
                    Primary key: bc_id (clinical root concept)
                  </div>
                </div>
              </div>
            </div>

            {/* Environmental reproducibility */}
            <div style={{ background:C.surface, border:`1px solid ${C.border}`,
              borderRadius:8, padding:"18px 20px" }}>
              <div style={{ fontSize:9, color:C.blue, letterSpacing:".15em",
                textTransform:"uppercase", marginBottom:14 }}>
                System Reproducibility Layer — Docker Sandbox Isolate
              </div>
              <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
                {REPRO_COMPONENTS.map((c,i)=>(
                  <div key={i} style={{ background:C.raised, border:`1px solid ${C.border}`,
                    borderRadius:6, padding:"10px 14px",
                    borderLeft:`2px solid ${c.isNew ? C.blue : C.muted}` }}>
                    <div style={{ display:"flex", gap:8, alignItems:"center", marginBottom:4 }}>
                      <span style={{ fontSize:11, fontWeight:600,
                        color: c.isNew ? C.blue : C.text,
                        fontFamily:"'JetBrains Mono',monospace" }}>{c.name}</span>
                      <span style={{ fontSize:8, color:C.muted }}>{c.type}</span>
                      {c.isNew && (
                        <span style={{ fontSize:8, color:C.blue,
                          background:`${C.blue}12`, border:`1px solid ${C.blue}25`,
                          padding:"1px 6px", borderRadius:2 }}>NEW IN V5</span>
                      )}
                    </div>
                    <div style={{ fontSize:10, color:C.text, lineHeight:1.5, marginBottom:4 }}>{c.purpose}</div>
                    <div style={{ fontSize:9, color:C.textLo, fontFamily:"'JetBrains Mono',monospace",
                      lineHeight:1.5 }}>{c.fields}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── TECH STACK VIEW ──────────────────────────────────────── */}
        {view==="stack" && (
          <div>
            <div style={{ fontSize:11, color:C.muted, marginBottom:18, lineHeight:1.6 }}>
              The **v5.0.0 tech stack** enforces GxP environment repeatability, vectorized DuckDB calculations, automated SHACL validation, and CDISC ARS / M11 data formats.
            </div>
            <div style={{ display:"flex", flexDirection:"column", gap:7, marginBottom:20 }}>
              {TECH_STACK.map((t,i)=>{
                const isNew = t.tech.includes("(v5.0.0)") || t.tech.includes("(pipeline.yml)");
                const accent = isNew ? C.violet : C.borderHi;
                return (
                  <div key={i} style={{ background:C.surface,
                    border:`1px solid ${C.border}`, borderRadius:7,
                    padding:"12px 16px", display:"flex", gap:14,
                    alignItems:"flex-start", borderLeft:`2px solid ${accent}` }}>
                    <div style={{ minWidth:130 }}>
                      <div style={{ fontSize:9, color:C.muted, letterSpacing:".08em",
                        textTransform:"uppercase", marginBottom:3 }}>{t.layer}</div>
                      <div style={{ fontSize:11, fontWeight:600,
                        color: isNew ? C.violet : C.textHi,
                        padding:"2px 9px", borderRadius:3, whiteSpace:"nowrap",
                        background: isNew ? `${C.violet}12` : C.raised,
                        border:`1px solid ${isNew ? C.violet+"30" : C.border}`,
                        display:"inline-block" }}>{t.tech}</div>
                    </div>
                    <div style={{ fontSize:11, color:C.muted, lineHeight:1.6 }}>{t.rationale}</div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ── ROADMAP VIEW ─────────────────────────────────────────── */}
        {view==="roadmap" && (
          <div>
            <div style={{ fontSize:11, color:C.muted, marginBottom:18, lineHeight:1.6 }}>
              Roadmap sequencing from initial metadata conceptualization through the finalized v5.0.0 package release.
            </div>
            <div style={{ display:"flex", flexDirection:"column", gap:10, marginBottom:22 }}>
              {ROADMAP.map((rv,i)=>(
                <div key={i} style={{ background:C.surface, border:`1px solid ${C.border}`,
                  borderRadius:8, padding:"18px 20px",
                  display:"flex", gap:18, alignItems:"flex-start", flexWrap:"wrap" }}>
                  <div style={{ fontSize:24, fontWeight:800, color:rv.color,
                    fontFamily:"'Syne',sans-serif", minWidth:50, lineHeight:1 }}>{rv.v}</div>
                  <div style={{ flex:1, minWidth:200 }}>
                    <div style={{ fontSize:14, fontWeight:700, color:C.textHi,
                      fontFamily:"'Syne',sans-serif", marginBottom:9 }}>{rv.label}</div>
                    <div style={{ display:"flex", flexWrap:"wrap", gap:6, marginBottom:10 }}>
                      {rv.phases.map(pid=>{
                        const pm = PHASE_META.find(p=>p.id===pid) || PHASE_META[0];
                        const ph_ = PHASES.find(p=>p.id===pid);
                        const nv3 = ph_?.v3Changes?.length || 0;
                        const n2 = ph_?.auditChanges?.length || 0;
                        return (
                          <span key={pid} style={{ fontSize:9, color:pm.col,
                            background:`${pm.col}10`, border:`1px solid ${pm.col}25`,
                            padding:"2px 9px", borderRadius:3, letterSpacing:".07em" }}>
                            {pm.code}: {pm.title}
                            {nv3>0 ? ` (+${nv3}v5)` : n2>0 ? ` (+${n2}fixes)` : ""}
                          </span>
                        );
                      })}
                    </div>
                    <div style={{ fontSize:11, color:C.muted,
                      borderLeft:`2px solid ${C.borderHi}`, paddingLeft:11,
                      fontStyle:"italic", lineHeight:1.6 }}>
                      Milestone: {rv.milestone}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Regulatory Timeline */}
            <div style={{ background:C.surface, border:`1px solid ${C.border}`,
              borderRadius:8, padding:"16px 20px", marginBottom:16 }}>
              <div style={{ fontSize:9, color:C.violet, letterSpacing:".15em",
                textTransform:"uppercase", marginBottom:12 }}>Regulatory Currency Timeline</div>
              {[
                { date:"June 2026",    event:"ICH M11 in effect. study_config.yaml m11_protocol block + protocol_objectives table + digital digital M11 protocol exports addresses this.", col:C.red, phase:"P1" },
                { date:"2026",         event:"CDISC Analysis Results Standard (ARS) v1.0. Native results-to-endpoint mapping serialized in standard ard.json.", col:C.amber, phase:"P7" },
                { date:"2026",         event:"FDA Dataset-JSON v1.1 adoption decision. Dual XPT+JSON output from Phase 4 with execution_snapshot linkage.", col:C.cyan, phase:"P4" },
                { date:"2026",         event:"CDISC CORE v1.0 full release. Platform integrates CORE engine in Phase 5 Level 1 validation.", col:C.green, phase:"P5" },
                { date:"Sept 2025",    event:"PMDA Validator Rules 2.0 live. ARM now validated — analysis_results table (Phase 2) generates ARM automatically.", col:C.violet, phase:"P7" },
              ].map((ev,i)=>(
                <div key={i} style={{ display:"flex", gap:12, alignItems:"flex-start",
                  padding:"8px 0", borderBottom: i<4?"1px solid "+C.border:"none" }}>
                  <div style={{ fontSize:10, color:ev.col, minWidth:110,
                    fontWeight:600, letterSpacing:".05em" }}>{ev.date}</div>
                  <div style={{ fontSize:9, color:ev.col, background:`${ev.col}10`,
                    border:`1px solid ${ev.col}25`, padding:"2px 7px",
                    borderRadius:3, whiteSpace:"nowrap", marginTop:1 }}>{ev.phase}</div>
                  <div style={{ fontSize:11, color:C.text, lineHeight:1.55 }}>{ev.event}</div>
                </div>
              ))}
            </div>

            {/* Verdict */}
            <div style={{ background:"rgba(104,211,145,.04)", border:"1px solid rgba(104,211,145,.2)",
              borderRadius:8, padding:"14px 18px" }}>
              <div style={{ fontSize:9, color:C.green, letterSpacing:".15em",
                textTransform:"uppercase", marginBottom:6 }}>Architecture Verdict · v5.0.0 Release</div>
              <div style={{ fontSize:12, color:C.text, lineHeight:1.8 }}>
                The IMpower150 Computable Submission Platform has achieved <span style={{ color:C.textHi, fontWeight:700 }}>complete compliance alignment</span> for FDA/PMDA review.
                By implementing vectorized estimand flags, OCCDS intercurrent events tracking, stabilized IPCW weights, and standard CDISC ARS / ICH M11 digital protocol exporters, the pipeline represents the absolute state-of-the-art in modern clinical programming.
                All 9 phases are fully built, containerized, stop-watch timed, and continuously checked under compliance gates.
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
