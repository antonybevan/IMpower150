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
  { id:2,  code:"P2",  title:"Semantic Metadata Repo",   sub:"SQLite + DuckDB · Semantic Entities · Alembic",           col:"#B794F4", weeks:"4–5" },
  { id:3,  code:"P3",  title:"Declarative Derivation",   sub:"Rule Engine · RECIST+iRECIST · BICR Branches",            col:"#F6AD55", weeks:"3–4" },
  { id:4,  code:"P4",  title:"Execution Runtime",        sub:"ExecutionAdapter · SAS · Dataset-JSON · Snapshots",       col:"#63B3ED", weeks:"3–4" },
  { id:5,  code:"P5",  title:"Explainable QC Engine",    sub:"CDISC CORE · Root-Cause · RECIST Rules",                  col:"#FC8181", weeks:"3–4" },
  { id:6,  code:"P6",  title:"Semantic Lineage Graph",   sub:"NetworkX · Concept-to-Result · Estimand-Aware",           col:"#68D391", weeks:"3–4" },
  { id:7,  code:"P7",  title:"Define.xml + ARM",         sub:"v2.1 · ARM · VLM · Single-Source · JSON-LD",              col:"#F6AD55", weeks:"2–3" },
  { id:8,  code:"P8",  title:"Reviewer Transparency",    sub:"Lineage Reports · JSON-LD SDRG · Audit Logs",             col:"#B794F4", weeks:"2 wks" },
  { id:9,  code:"P9",  title:"AI Governance Layer",      sub:"4-Signal Confidence · SAP Extraction · Approval UI",      col:"#9AE6B4", weeks:"3–4" },
];

// ─── SEMANTIC ENTITY HIERARCHY (new v3 section) ──────────────────────────────
const SEMANTIC_HIERARCHY = [
  { level:1, entity:"Protocol Objective",    table:"protocol_objectives",    source:"ICH M11 YAML block",             col:"#76E4F7", isNew:false, promoted:true,  fields:["obj_id","obj_text","obj_type","m11_section"] },
  { level:2, entity:"Biomedical Concept",    table:"biomedical_concepts",    source:"CDISC COSMoS / custom",          col:"#B794F4", isNew:true,  promoted:false, fields:["bc_id","bc_name","bc_category","cosmos_bc_id","sdtmig_class","coding_system"] },
  { level:3, entity:"Endpoint Definition",  table:"endpoint_definitions",   source:"SAP + estimand linkage",         col:"#F6AD55", isNew:true,  promoted:false, fields:["endpoint_id","bc_id FK","estimand_id FK","endpoint_type","analysis_concept","sap_reference"] },
  { level:4, entity:"Estimand",             table:"estimands",              source:"ICH E9(R1) — existing",          col:"#63B3ED", isNew:false, promoted:false, fields:["estimand_id","name","ice_strategy","target_population","variable_of_interest","summary_measure"] },
  { level:5, entity:"Derivation Rule",      table:"derivation_rules",       source:"Rule engine — existing",         col:"#FC8181", isNew:false, promoted:false, fields:["rule_id","endpoint_id FK","target_variable","logic_type","assessor","criteria_type","approval_status"] },
  { level:6, entity:"Variable Realization", table:"variables",              source:"SDTM/ADaM — existing",           col:"#68D391", isNew:false, promoted:false, fields:["variable","dataset","role","datatype","bc_id FK","origin","controlled_terminology"] },
  { level:7, entity:"Analysis Result",      table:"analysis_results",       source:"ARM source — promoted to P2",    col:"#F6AD55", isNew:false, promoted:true,  fields:["analysis_id","endpoint_id FK","dataset","paramcd","where_clause_id FK","stat_method","tfl_reference","estimand_id FK"] },
  { level:8, entity:"Reviewer Artifact",    table:"artifacts",              source:"Execution output — existing",    col:"#9AE6B4", isNew:false, promoted:false, fields:["artifact_id","dataset_name","transport_format","file_hash_sha256","execution_snapshot_id FK"] },
];

// ─── REPRODUCIBILITY COMPONENTS (new v3 section) ────────────────────────────
const REPRO_COMPONENTS = [
  { name:"execution_snapshots",     type:"SQLite table",   purpose:"Pinned runtime state — exact replay",          fields:"snapshot_id, run_id FK, sdtmig_version, adamig_version, python_version, sas_version, rule_hash_manifest JSON, metadata_db_hash, environment_hash, created_ts", isNew:true },
  { name:"environment_manifest.json", type:"File artifact", purpose:"pip freeze + SAS version + OS at run time",    fields:"python_packages: {}, sas_version, os, execution_ts, claude_model_version (for AI runs)", isNew:true },
  { name:"rule_hash_manifest",      type:"JSON field",     purpose:"Exact rule set state at execution — drift detection", fields:"JSON array of {rule_id, rule_version, rule_logic_hash} for every rule active in this run", isNew:true },
  { name:"file_hash_sha256",        type:"Existing field", purpose:"Dataset content fingerprint — cross-run integrity", fields:"SHA-256 of source dataset — transport-format-independent", isNew:false },
  { name:"program_sha256",          type:"Existing field", purpose:"Detects manual code alterations between runs",  fields:"SHA-256 of generated SAS program at execution time", isNew:false },
  { name:"alembic_version",         type:"Existing table", purpose:"Schema state tracking — 21 CFR Part 11 trail",  fields:"Current migration revision — every schema change is versioned and Git-committed", isNew:false },
];

// ─── FULL PHASE DATA (v3: semantic upgrades integrated) ──────────────────────
const PHASES = [
  {
    id:1, col:"#76E4F7",
    status:"START HERE",
    version:"v1 → unchanged",
    auditChanges:[
      "ADDED: SV domain (FDA 2023 mandate — all scheduled visits required)",
      "ADDED: ICH M11 protocol metadata section in study_config.yaml",
      "ADDED: iRECIST noted as dual-criteria alongside RECIST 1.1 from scope stage",
    ],
    v3Changes:[],
    researchBasis:"CDISC 360i Phase 1 delivered a complete pre-configured study package as machine-readable metadata from design through submission. ICH M11 effective June 11 2026 — structured protocol metadata is now a live regulatory standard, not aspirational.",
    tasks:[
      {
        type:"DECISION",
        title:"Trial Type & Response Criteria",
        detail:"Immunotherapy solid tumor study. RECIST 1.1 as primary response criteria. iRECIST as parallel IO-specific criteria (mandatory for immunotherapy — FDA reviewers expect both documented). Endpoints: BOR, ORR, PFS (RECIST), iPFS (iRECIST), OS, DOR, TEAEs.",
        fix:null,
      },
      {
        type:"BUILD",
        title:"SDTM Minimal Domain Set — Revised",
        detail:"DM · AE · EX · LB · RS · TU · TR · DS · SV. SV is now mandatory: FDA 2023 catalog update requires all scheduled visits regardless of occurrence, and SVREASOC / SVEPCHGI / SVCNTMOD variables. SV feeds ADSL.LSTALVDT censoring chain in traceability graph.",
        fix:"AUDIT FIX: SV added — omission would trigger FDA information request.",
      },
      {
        type:"BUILD",
        title:"ICH M11–Aligned study_config.yaml",
        detail:"study_id, sponsor, indication, protocol_version, standards_version (SDTMIG 3.4 / ADaM 1.3), define_xml_version: 2.1, transport_format: [xpt, json], m11_protocol: { objectives: [...], primary_endpoints: [...], secondary_endpoints: [...], estimands: [{name, intercurrent_event_strategy, target_population}], schedule_of_activities: {visits: [...], assessments: [...]} }. This config is the single source that seeds the metadata repository.",
        fix:"AUDIT FIX: ICH M11 effective June 2026 — protocol metadata must be structured, not free-text.",
      },
      {
        type:"EXTRACT",
        title:"SAP Logic Extraction",
        detail:"Extract: endpoint definitions, censoring rules (PFS: PD or death; OS: death; iPFS: confirmed iPD), baseline definitions, RECIST 1.1 precedence, iRECIST iUPD confirmation window (next assessment ≥ 4 weeks), TEAE definition. Tag every extracted rule with sap_section, page_ref, and criteria_type (RECIST | iRECIST).",
        fix:null,
      },
      {
        type:"MAP",
        title:"RECIST + iRECIST Dependency Maps",
        detail:"RECIST chain: TU→TR→RS→ADTR→ADRS→ADINTEV→ADEFFSUM→ADTTE. iRECIST parallel chain: RS(iUPD flag)→ADRS(iUPD_FL)→ADTTE(iPFS). Both chains share TU/TR source but branch at RS domain (RSSPONID + response criteria parameter). Each arrow becomes a lineage_edge record with criteria_type attribute.",
        fix:null,
      },
    ],
    outputs:["study_config.yaml (M11-aligned)", "sdtm_domain_list.yaml (incl. SV)", "sap_rules_extracted.md", "recist_ireq_dependency_maps.json"],
    criticalDecision:"Do NOT write derivation code yet. Only metadata representation. ICH M11 protocol section in study_config.yaml must be designed before Phase 2 schema — it is the upstream seed of the metadata repository.",
  },
  {
    id:2, col:"#B794F4",
    status:"MOST CRITICAL",
    version:"v2 → MAJOR SEMANTIC UPGRADE",
    auditChanges:[
      "ADDED: DuckDB as analytical store alongside SQLite (OLTP/OLAP split)",
      "ADDED: Alembic schema migration framework from day 1",
      "ADDED: estimands table + estimand_id FK in derivation_rules",
      "ADDED: assessor field (BICR | INVESTIGATOR | both) in derivation_rules",
      "ADDED: cdisc_rule_id field in qc_findings (for CORE integration)",
    ],
    v3Changes:[
      "NEW: biomedical_concepts table — semantic root, primary key of architecture",
      "NEW: endpoint_definitions table — explicit BC→estimand→analysis linkage",
      "NEW: execution_snapshots table — deterministic reproducibility layer",
      "PROMOTED: analysis_results from Phase 7 artifact to Phase 2 first-class entity",
      "PROMOTED: protocol_objectives from YAML block to database table",
      "REVISED: variables table gets bc_id FK — variables become concept implementations",
      "REVISED: derivation_rules gets endpoint_id FK — rules trace to semantic endpoints",
    ],
    researchBasis:"CDISC 360i: 'two-dimensional standards are insufficient — future requires entities, semantics, relationships, lifecycle rules.' COSMoS exposes machine-readable YAML schemas with LinkML semantic models and generated Python object models. BRIDG defines computable semantic interoperability with relationship-aware biomedical entities. Variables are implementation artifacts; concepts are primary entities.",
    tasks:[
      {
        type:"ARCHITECTURE",
        title:"Semantic-First Schema Design",
        detail:"The v3 schema inversion: primary key is concept_id, not (dataset, variable). Every variable row has a bc_id FK pointing up to a biomedical concept. Every derivation rule has an endpoint_id FK tracing to a semantic endpoint definition. This is the CDISC 360i / COSMoS architectural pattern — concepts at root, variables as realization artifacts. The schema change is additive (Alembic migration) but the conceptual shift is foundational.",
        fix:"RESEARCH FIX: Variable-centric schema is architecturally obsolete per CDISC 360i direction. Concept-as-primary-key is the correct enterprise pattern.",
      },
      {
        type:"BUILD",
        title:"New Entity: biomedical_concepts",
        detail:"biomedical_concepts SQLite table: bc_id (PK), bc_name (e.g. 'Overall Survival', 'Tumor Response'), bc_category (finding|event|intervention|disposition|special_purpose), cosmos_bc_id (nullable — links to CDISC COSMoS published BC for interoperability), sdtmig_class, coding_system (NCI Thesaurus | MedDRA | SNOMED), bc_definition (plain text), created_ts. This table is the semantic root. All variables FK to this table. BC rows can be seeded from COSMoS YAML API or authored manually.",
        fix:"RESEARCH FIX: Biomedical Concepts are CDISC's explicit semantic abstraction layer — standards-agnostic entities that connect to SDTM/ADaM implementations. Without this table, the schema cannot represent conceptual meaning.",
      },
      {
        type:"BUILD",
        title:"New Entity: endpoint_definitions",
        detail:"endpoint_definitions SQLite table: endpoint_id (PK), bc_id FK (the clinical concept this endpoint measures), estimand_id FK (ICH E9(R1) estimand this endpoint serves), endpoint_type (primary|secondary|exploratory|safety), analysis_concept (RECIST_BOR | OS | PFS | iPFS | ORR | DOR | TEAE), endpoint_label (display name), sap_reference, sap_section, criteria_type (RECIST_1.1 | iRECIST | both). This table fills the gap between protocol objectives and derivation rules — previously implicit in sap_reference strings, now computable.",
        fix:"RESEARCH FIX: Endpoint definitions are the missing layer in BC→estimand→derivation chain. Without this table, the semantic graph has no bridge between clinical concepts and executable derivations.",
      },
      {
        type:"BUILD",
        title:"Promoted Entity: protocol_objectives",
        detail:"protocol_objectives SQLite table: obj_id (PK), obj_type (primary|secondary|exploratory), obj_text, m11_section (maps back to study_config.yaml m11_protocol.objectives), endpoint_id FK. Seeded from study_config.yaml m11_protocol block at repo initialization. This promotes objectives from YAML documentation to first-class database entities with FK relationships — enables objective→endpoint→estimand→derivation traversal in the semantic graph.",
        fix:"RESEARCH FIX: ICH M11 protocol objectives must be machine-readable database entities, not YAML documentation. Promotes the existing M11 block to queryable rows.",
      },
      {
        type:"BUILD",
        title:"Promoted Entity: analysis_results (from Phase 7)",
        detail:"analysis_results SQLite table (previously only in Phase 7 Define.xml generation): analysis_id (PK), endpoint_id FK, dataset, paramcd, where_clause_id FK, stat_method, stat_test, tfl_reference, sap_reference, estimand_id FK, arm_display_label. Seeding this table in Phase 2 means ARM generation in Phase 7 becomes a metadata query, not a post-processing construction. Analyst authors analysis metadata alongside derivation rules — not after the fact.",
        fix:"RESEARCH FIX: PMDA Validator Rules 2.0 now validates ARM — it must be first-class metadata from day 1, not a Phase 7 afterthought.",
      },
      {
        type:"BUILD",
        title:"New Entity: execution_snapshots (Reproducibility Layer)",
        detail:"execution_snapshots SQLite table: snapshot_id (PK), run_id FK, sdtmig_version, adamig_version, define_xml_version, python_version, sas_version, rule_hash_manifest (JSON array of {rule_id, rule_version, rule_logic_hash} for every active rule), metadata_db_hash (SHA-256 of metadata.db at run start), environment_hash (SHA-256 of environment_manifest.json), created_ts. Paired with environment_manifest.json (pip freeze + SAS version + OS emitted each run). Given same snapshot_id: exact reruns are deterministic. This is what separates 'automation' from 'submission engineering.'",
        fix:"RESEARCH FIX: FDA technical conformance guidance emphasizes deterministic reproducibility. Hashing outputs is insufficient — environment-level replayability requires the full snapshot.",
      },
      {
        type:"BUILD",
        title:"Dual-Database Storage + Revised Variable Schema",
        detail:"SQLite OLTP: all semantic entities (biomedical_concepts, protocol_objectives, endpoint_definitions, estimands, derivation_rules, variables, analysis_results, where_clauses, execution_snapshots, programs, pending_queue, ai_actions). variables table gains bc_id FK — variables become concept implementations, not root entities. DuckDB OLAP: qc_findings, lineage_edges, execution_log, artifacts. All SQLAlchemy ORM models in models.py. Alembic tracks every schema change.",
        fix:null,
      },
    ],
    outputs:["metadata.db (SQLite — 12-table semantic schema)", "analytics.duckdb (DuckDB — OLAP)", "models.py (SQLAlchemy ORM — all entities)", "alembic/ (migration scripts)", "study_config.yaml (M11-aligned)", "environment_manifest.json (per run)"],
    criticalDecision:"The schema is the architecture. Invest 60% of Phase 2 time on getting the semantic entity relationships correct — biomedical_concepts as root, endpoint_definitions as the BC-to-derivation bridge, execution_snapshots for reproducibility. Everything downstream compiles against these tables.",
  },
  {
    id:3, col:"#F6AD55",
    status:"DIFFERENTIATOR",
    version:"v2 → minor additions",
    auditChanges:[
      "ADDED: response_criteria field (RECIST_1.1 | iRECIST | both) in rule engine",
      "ADDED: iRECIST iUPD logic branch — iUPD_flag, confirmation_window_days",
      "ADDED: assessor field driving BICR vs Investigator parallel derivation paths",
      "ADDED: confirmation_required boolean for BOR/CR/PR protocol requirement",
    ],
    v3Changes:[
      "REVISED: Rule parser now reads endpoint_id FK — each rule traces to semantic endpoint",
      "REVISED: iRECIST rules seed with endpoint_id pointing to iPFS endpoint_definition row",
      "REVISED: Estimand gate now validates endpoint_id AND estimand_id both populated",
    ],
    researchBasis:"PharmaSUG 2025: IO trials require iRECIST alongside RECIST 1.1. Eli Lilly: metadata IS the engine, macros are execution adapters. The rule engine is an execution compiler — rules are semantic metadata rows, code is output.",
    tasks:[
      {
        type:"BUILD",
        title:"Python Rule Parser — Endpoint-Aware",
        detail:"Reads derivation_rules (including endpoint_id FK) from SQLite. Maps logic_type → SAS template. Supported types: subtraction (CHG), event_flag (CNSR), date_diff (AVAL TTE), conditional_assign, iupd_confirmation (iRECIST iUPD). For rules with assessor ≠ 'both': parser inserts WHERE clause filter. For rules with criteria_type='iRECIST': parser selects iRECIST template variant. For confirmation_required=TRUE: parser inserts confirmation window check. V3 addition: parser logs endpoint_id→rule_id mapping to execution_snapshots.rule_hash_manifest.",
        fix:"V3 FIX: Endpoint-awareness means the parser can group rules by clinical endpoint — provides semantic context for QC narratives.",
      },
      {
        type:"BUILD",
        title:"SAS Template Library — IO Complete",
        detail:"Base templates: %derive_diff, %derive_event_flag, %derive_date_diff, %derive_conditional. IO templates: %derive_iupd_flag (sets iUPD_FL based on RS response and confirmation window), %derive_ipfs_cnsr (iRECIST censoring), %derive_bor_confirmed (BOR with confirmation window). Each template accepts macro params populated by Python parser from derivation_rules fields.",
        fix:null,
      },
      {
        type:"BUILD",
        title:"iRECIST + BICR Metadata Rules",
        detail:"Seed derivation_rules with iRECIST-specific records tagged criteria_type='iRECIST', each with endpoint_id FK pointing to iPFS endpoint_definition row. iUPD_FL, iUPD_CONFIRM_FL, iPFS_CNSR, iPFS_AVAL. Dual-assessment BICR: two derivation_rules records per RECIST endpoint (assessor='INVESTIGATOR', assessor='BICR'), both FK to same endpoint_id. PARAMCD distinguishes output: OVRLRESP vs BICRRESP.",
        fix:null,
      },
      {
        type:"GOVERNANCE",
        title:"Semantic Approval Gate",
        detail:"Before execution: check (1) approval_status='approved', (2) estimand_id IS NOT NULL, (3) endpoint_id IS NOT NULL for all analysis rules. Rules without endpoint_id → blocked: 'semantic endpoint not assigned.' This forces explicit BC→endpoint→estimand→rule chain — prevents executing derivations where clinical meaning is ambiguous. PFS (ITT) and PFS (mITT) share source but have different endpoint_ids — ambiguity is impossible.",
        fix:"V3 FIX: endpoint_id gate added — previously only estimand_id was required. Now the full semantic chain must be populated.",
      },
    ],
    outputs:["rule_parser.py (endpoint-aware)", "orchestrator.py", "sas_templates/ (incl. iRECIST)", "generated_programs/", "execution_log.duckdb"],
    criticalDecision:"Rules are semantic data rows, not code files. The endpoint_id FK means every generated SAS program is traceable back through: variable → rule → endpoint → BC → protocol objective. That chain is the differentiator.",
  },
  {
    id:4, col:"#63B3ED",
    status:"EXECUTION",
    version:"v2 → snapshot integration",
    auditChanges:[
      "ADDED: ExecutionAdapter abstract base class — SAS, R, Python adapters",
      "ADDED: Dataset-JSON output path alongside XPT",
      "ADDED: file_hash_sha256 for 21 CFR Part 11 integrity",
    ],
    v3Changes:[
      "NEW: execution_snapshots written at every run start — full state capture",
      "NEW: environment_manifest.json emitted alongside each run",
      "REVISED: artifact_capture writes execution_snapshot_id FK to artifacts table",
    ],
    researchBasis:"R Consortium submitted ADaM in Dataset-JSON to FDA fall 2025. FDA Dataset-JSON decision expected 2026. Enterprise pattern: externalize metadata, internalize orchestration, isolate execution engines. SAS is replaceable — but only if the adapter interface is a real code contract.",
    tasks:[
      {
        type:"BUILD",
        title:"ExecutionAdapter + Snapshot Capture",
        detail:"Python ABC: class ExecutionAdapter: def execute(program, inputs, outputs, run_id) → ExecutionResult. V3 addition: before execute(), orchestrator calls snapshot_manager.capture(run_id) → writes execution_snapshots row: python_version, sas_version, sdtmig_version, adamig_version, rule_hash_manifest (iterate active rules, hash each logic field), metadata_db_hash, environment_hash. environment_manifest.json emitted to /outputs/manifests/. After run: artifacts table gets execution_snapshot_id FK.",
        fix:"V3 FIX: Reproducibility was the biggest missing enterprise-grade component. Snapshot capture at run start closes the environment-level replayability gap.",
      },
      {
        type:"BUILD",
        title:"SAS Batch Harness + Log Parser",
        detail:"SASAdapter.execute(): subprocess.run(['sas', '-sysin', program_path, '-log', log_path]). Parse log: ERROR → severity=critical, WARNING → severity=warning, NOTE.*obs=0 → severity=major. Write to execution_log DuckDB. If rc != 0 AND error_count > 0: mark run_status=failed, do NOT write to artifacts.",
        fix:null,
      },
      {
        type:"BUILD",
        title:"Dataset-JSON Output + Dual Artifact Registry",
        detail:"Post-execution: generate BOTH XPT and Dataset-JSON (cdisc-dataset-json library or pyreadstat serializer). artifacts DuckDB: transport_format=['xpt','json'], xpt_path, json_path, file_hash_sha256, obs_count, var_count, execution_snapshot_id FK. SHA-256 computed on source data content — transport-format-independent. Phase 7 define.xml generator references Dataset-JSON metadata natively via def:leaf elements.",
        fix:null,
      },
    ],
    outputs:["execution_adapter.py (ABC + SASAdapter)", "snapshot_manager.py", "log_parser.py", "artifact_capture.py", "dataset_json_serializer.py", "environment_manifest.json (per run)"],
    criticalDecision:"SAS is the current execution adapter. The ABC makes replacement cost one class implementation. The snapshot manager makes every run reproducible — given a snapshot_id, the exact execution state is known.",
  },
  {
    id:5, col:"#FC8181",
    status:"BIGGEST DIFFERENTIATOR",
    version:"v2 → semantic QC narratives",
    auditChanges:[
      "ADDED: CDISC CORE engine integration for Level 1",
      "ADDED: cdisc_rule_id in qc_findings (links to CORE rule ID)",
      "ADDED: RECIST_001–004 + iRECIST_001–003 custom rules",
    ],
    v3Changes:[
      "REVISED: Root-cause narratives now include endpoint and BC context from semantic tables",
      "REVISED: QC summary groups findings by endpoint (not just variable) — clinical meaning surfaced",
    ],
    researchBasis:"CDISC CORE (MIT, Python 3.12): ~220 of 336 SDTMIG 3.4 conformance rules published. PMDA Validator Rules 2.0 (Sept 2025) adds ARM conformance rules. Root-cause explainability is the differentiator — no commercial tool does Level 3.",
    tasks:[
      {
        type:"BUILD",
        title:"Level 1: CDISC CORE Integration",
        detail:"Install cdisc-rules-engine. Run against SDTM XPT/JSON. Parse violation report. Ingest into qc_findings DuckDB: rule_source='CORE', cdisc_rule_id=violation.rule_id (e.g. SDTMIG.CG0001), severity mapped from CORE. Replaces ~220 custom structural checks with regulatory-grade citable rule IDs.",
        fix:null,
      },
      {
        type:"BUILD",
        title:"Level 2: Custom RECIST/iRECIST Validation",
        detail:"RECIST_001 (RS.RSORRES must trace to ≥1 TR record for same VISIT + RSSPONID), RECIST_002 (ADTR.DTYPE=BASELINE requires TU screening record), RECIST_003 (BOR=CR/PR satisfies confirmation window if protocol requires), RECIST_004 (ORR denominator = subjects with ≥1 evaluable post-baseline). iRECIST_001 (iUPD must have subsequent assessment within confirmation_window_days), iRECIST_002 (iPFS CNSR=0 requires confirmed iPD or death), iRECIST_003 (iRECIST and RECIST BOR must not conflict without documented basis).",
        fix:null,
      },
      {
        type:"BUILD",
        title:"Level 3: Semantic Root-Cause + Endpoint Context",
        detail:"For every qc_finding: traverse lineage_edges backward to root cause. V3 addition: also join to endpoint_definitions via rule_id→derivation_rules.endpoint_id. QC narrative now includes: 'Subject 001-001: CNSR derivation error. Endpoint: PFS (ITT). Biomedical Concept: Progression-Free Survival. Root cause traced to LBBLFL not populated at screening. RECIST rule: RECIST_003. SAP 8.4.2.' The endpoint and BC context makes narratives clinically meaningful — not just variable-level flags.",
        fix:"V3 FIX: Semantic context from endpoint_definitions and biomedical_concepts elevates QC narratives from variable diagnostics to clinical endpoint diagnostics.",
      },
      {
        type:"BUILD",
        title:"QC Summary by Endpoint (v3)",
        detail:"DuckDB analytical query: JOIN qc_findings → derivation_rules → endpoint_definitions → biomedical_concepts. Group findings by endpoint_type, analysis_concept, bc_name. Executive summary: 'PFS (ITT) endpoint: 3 findings. Biomedical concept: Progression-Free Survival. Highest severity: critical (RECIST_001 RS-TR linkage). Affected subjects: 4 of 120.' This is clinically meaningful QC — not just a variable-level error count.",
        fix:"V3 FIX: Endpoint-grouped QC surfaces clinical risk, not just technical errors.",
      },
    ],
    outputs:["qc_engine.py", "core_integrator.py", "validation_rules (DuckDB)", "qc_findings (DuckDB)", "trace_root_cause.py (endpoint-aware)", "qc_narratives/ (semantic)"],
    criticalDecision:"CORE owns Level 1. Custom rules own Level 2 oncology semantics. Root-cause + endpoint context owns Level 3. The moat is not the checks — it's the clinical meaning in the narrative output.",
  },
  {
    id:6, col:"#68D391",
    status:"EXTRAORDINARY",
    version:"v2 → semantic graph upgrade",
    auditChanges:[
      "ADDED: estimand_id as node attribute",
      "ADDED: Estimand-aware traversal functions",
      "ADDED: criteria_type on edges (RECIST | iRECIST)",
      "ADDED: Neo4j migration trigger criteria documented",
    ],
    v3Changes:[
      "UPGRADED: Graph now spans full semantic hierarchy: protocol_objective → BC → endpoint → estimand → derivation_rule → variable → analysis_result → reviewer_artifact",
      "NEW: Concept node type — BC rows become graph nodes with SDTMIG class attributes",
      "NEW: Endpoint node type — endpoint_definition rows become graph nodes",
      "REVISED: graph_builder reads all 8 semantic entity tables",
    ],
    researchBasis:"CDISC 360i technical roadmap is explicitly graph-oriented — endpoints to SOA to SDTM specs to analysis concepts as connected metadata. BRIDG explicitly defines computable semantic interoperability and relationship-aware biomedical entities. OpenStudyBuilder uses Neo4j at ~300 users for cross-study metadata. The graph must evolve from variable lineage to semantic relationship graph.",
    tasks:[
      {
        type:"BUILD",
        title:"Semantic Graph Builder — Full Hierarchy",
        detail:"NetworkX DiGraph. Node types: OBJECTIVE (protocol_objectives), CONCEPT (biomedical_concepts), ENDPOINT (endpoint_definitions), ESTIMAND (estimands), RULE (derivation_rules), VARIABLE (variables), RESULT (analysis_results), ARTIFACT (artifacts). Node attributes vary by type: CONCEPT nodes carry bc_category, cosmos_bc_id; ENDPOINT nodes carry analysis_concept, criteria_type; RULE nodes carry assessor, approval_status. Edges typed by relationship: OBJECTIVE→ENDPOINT (serves), CONCEPT→ENDPOINT (measures), ENDPOINT→ESTIMAND (quantifies), ENDPOINT→RULE (implemented_by), RULE→VARIABLE (derives), VARIABLE→RESULT (populates), RESULT→ARTIFACT (generates). This is the BRIDG-aligned semantic relationship graph.",
        fix:"V3 FIX: Variable-to-variable lineage is insufficient. BRIDG and CDISC 360i require semantic relationship graph spanning from protocol objectives to reviewer artifacts.",
      },
      {
        type:"BUILD",
        title:"Semantic Traversal Functions",
        detail:"concept_to_artifacts(bc_id): full downstream chain from BC to all generated artifacts. objective_coverage(obj_id): which endpoints, estimands, variables, and TLFs serve this protocol objective — coverage audit. endpoint_lineage(endpoint_id, criteria_type=None): all variables and results for this endpoint. cross_estimand_impact(rule_id): does changing this rule affect multiple estimands? (flags shared-source risk). semantic_gap_audit(): find variables with no bc_id FK (conceptually unanchored), rules with no endpoint_id (semantically unlinked).",
        fix:"V3 FIX: semantic_gap_audit() enforces the concept-as-root invariant — surfaces any variable that slipped through without a BC linkage.",
      },
      {
        type:"BUILD",
        title:"Estimand-Aware Impact Analysis",
        detail:"impact_analysis(sap_section, estimand_id=None): find rules referencing that section → endpoint_ids affected → variables derived → downstream results and artifacts — grouped by estimand and criteria_type. cross_estimand_impact(variable): does a change affect multiple estimands? V3 addition: impact report now names endpoint labels and BC names — 'Changes to SAP 8.4.2 affect: PFS (ITT) endpoint [Progression-Free Survival concept], 4 variables, 3 TLFs.'",
        fix:null,
      },
      {
        type:"BUILD",
        title:"Graph Visualization — Layered Semantic View",
        detail:"Streamlit + pyvis. Layer filter: show/hide OBJECTIVE, CONCEPT, ENDPOINT, ESTIMAND, RULE, VARIABLE, RESULT, ARTIFACT layers. Default view: ENDPOINT→RULE→VARIABLE (operational). Semantic view: full 8-layer hierarchy. Node color: OBJECTIVE=cyan, CONCEPT=violet, ENDPOINT=amber, ESTIMAND=blue, RULE=red, VARIABLE=green, RESULT=lime, ARTIFACT=muted. Edge style: RECIST=solid, iRECIST=dashed. Click CONCEPT node → expand to all variables implementing that BC.",
        fix:"V3 FIX: Layered semantic view enables switching between clinical perspective (BC/endpoint) and operational perspective (rule/variable).",
      },
    ],
    outputs:["graph_builder.py (8-layer semantic)", "lineage_queries.py (semantic-aware)", "impact_analysis.py (endpoint-context)", "graph_viz.py (Streamlit+pyvis — layered)"],
    criticalDecision:"The graph is the semantic nervous system of the submission. Full 8-layer hierarchy from protocol objective to reviewer artifact is what makes this a knowledge graph, not a lineage tracker.",
  },
  {
    id:7, col:"#F6AD55",
    status:"SUBMISSION CRITICAL",
    version:"v2 → BC-driven VLM + semantic Define",
    auditChanges:[
      "ADDED: analysis_results table + where_clauses for ARM generation",
      "ADDED: define_xml_version locked to 2.1",
      "ADDED: Dataset-JSON metadata integration",
      "ADDED: ARM conformance for PMDA Validator Rules 2.0",
    ],
    v3Changes:[
      "REVISED: ItemDef CommentDef now references bc_name from biomedical_concepts — semantic annotations",
      "REVISED: VLM generation joins endpoint_definitions for semantic labels",
      "REVISED: ARM AnalysisResultsDef traces to endpoint_id — Define.xml is semantically annotated",
    ],
    researchBasis:"CDISC Biomedical Concepts documentation explicitly states BCs can generate Define.xml metadata, drive Value Level Metadata, and support metadata-driven automation. Define.xml is evolving from documentation layer to semantic synchronization layer. PMDA Validator Rules 2.0: ARM is now validated.",
    tasks:[
      {
        type:"BUILD",
        title:"Semantic Define.xml Generator",
        detail:"ODM root → MetaDataVersion. V3 addition: ItemDef elements now include def:CommentDef from biomedical_concepts.bc_definition — every variable annotated with its clinical concept meaning. ItemDef label derived from bc_name where bc_id FK is populated. ARM AnalysisResultsDef generated from analysis_results table with endpoint_definitions.endpoint_label as display text. Define.xml is semantically annotated, not just structurally complete.",
        fix:"V3 FIX: CDISC BCs can drive Define.xml annotations — bc_definition and bc_name populate CommentDef and ItemDef labels automatically.",
      },
      {
        type:"BUILD",
        title:"BC-Driven VLM Generation",
        detail:"For ADTTE PARAMCD-driven VLM: JOIN derivation_rules × where_clauses × endpoint_definitions × biomedical_concepts. Generate ItemRef → WhereClauseDef pairs with endpoint_label from endpoint_definitions as the VLM context label. Example: CNSR for PARAMCD=PFS with EndpointLabel='PFS (ITT) — RECIST 1.1' → semantically labeled VLM section. The clinical meaning of each VLM entry is now explicit in the Define.xml.",
        fix:"V3 FIX: VLM entries were previously labeled by PARAMCD strings alone. endpoint_definitions provide clinical endpoint context.",
      },
      {
        type:"BUILD",
        title:"ARM + Single-Source Governance",
        detail:"ARM AnalysisResultsDef generated from analysis_results × where_clauses × endpoint_definitions join. analysis_results.arm_display_label used as display text. analysis_results.endpoint_id FK creates bidirectional traceability: Define.xml ARM → endpoint definition → derivation rules → variables. Git pre-commit hook regenerates define.xml on every metadata change. Never manually edit — every element traces to a table row.",
        fix:null,
      },
    ],
    outputs:["define_xml_generator.py (semantic v2.1)", "arm_generator.py (endpoint-linked)", "analysis_results table (Phase 2 origin)", "where_clauses table", "define.xml (auto-generated, semantically annotated)"],
    criticalDecision:"Define.xml is not documentation — it is semantic synchronization. BC annotations in CommentDef make the submission self-explaining. Reviewers see clinical concept context alongside variable definitions.",
  },
  {
    id:8, col:"#B794F4",
    status:"DELIVERY",
    version:"v2 → semantic SDRG",
    auditChanges:[
      "ADDED: Machine-readable JSON-LD SDRG",
      "ADDED: JSON-LD embeds variable URIs from metadata repository",
      "ADDED: Execution audit log with program SHA-256 hash",
    ],
    v3Changes:[
      "REVISED: JSON-LD SDRG now embeds bc_id and endpoint_id URIs — semantic IRIs, not just variable names",
      "REVISED: Lineage reports include BC name and endpoint label in header",
    ],
    researchBasis:"2024 CDISC Data Standards White Paper: explicit call to transition from static PDF-based SDRGs to structured machine-readable formats. JSON-LD is forward-compatible with future reviewer tooling — embeds semantic metadata queryable by programmatic reviewers.",
    tasks:[
      {
        type:"BUILD",
        title:"Semantic JSON-LD SDRG",
        detail:"Generate SDRG as both HTML and JSON-LD. V3: JSON-LD @context maps CDISC variable URIs AND biomedical concept URIs (cosmos_bc_id where available). Each SDRG section node includes: @type, @id, bc_name, endpoint_label, endpoint_type, variables[], derivationRules[], sapSection, estimandId. Example: {'@type':'SDRGSection','@id':'section-CNSR','biomedicalConcept':'Progression-Free Survival','endpointLabel':'PFS (ITT)','variables':['ADTTE.CNSR'],'derivationRule':'DER001','sapSection':'8.4.2'}. Fully queryable by future FDA tooling.",
        fix:"V3 FIX: BC and endpoint URIs in JSON-LD SDRG make the document semantically interoperable with COSMoS and future CDISC infrastructure.",
      },
      {
        type:"BUILD",
        title:"Lineage Reports — Semantic Header",
        detail:"Per-variable HTML lineage reports. V3 addition: report header now shows BC name and endpoint label. Example: 'ADTTE.CNSR — Biomedical Concept: Progression-Free Survival — Endpoint: PFS (ITT) — Criteria: RECIST 1.1 — Estimand: ITT.' Dual RECIST/iRECIST chains shown as parallel branches with criteria labels. Export HTML + PDF.",
        fix:null,
      },
      {
        type:"BUILD",
        title:"Execution Audit Log (21 CFR Part 11)",
        detail:"From execution_log + programs + execution_snapshots tables: full audit of what ran, when, with what rules and snapshot. Each log entry: program_id, program_sha256, run_id, snapshot_id FK, timestamp, rule_ids_used, rule_versions, dataset_output, obs_count, transport_formats, adapter_used, sdtmig_version (from snapshot), python_version (from snapshot). Exportable PDF for submission. Snapshot FK means the exact reproducibility state is traceable for every audit entry.",
        fix:"V3 FIX: snapshot_id FK in audit log links every run to its full reproducibility state — execution_snapshots + environment_manifest.json.",
      },
    ],
    outputs:["lineage_report_generator.py (semantic headers)", "sdrg_json_ld.py (BC/endpoint URIs)", "sdrg.html + sdrg.jsonld", "derivation_dictionary.html", "audit_log_exporter.py (snapshot-linked)"],
    criticalDecision:"The JSON-LD SDRG with BC and endpoint URIs is the feature that positions this platform ahead of the current CDISC standard. It costs zero new derivation — the data is already in the semantic tables.",
  },
  {
    id:9, col:"#9AE6B4",
    status:"LAST",
    version:"v2 → endpoint-context extraction",
    auditChanges:[
      "REPLACED: logprob confidence with 4-signal composite scoring",
      "ADDED: schema_compliance, sap_coverage, cross_run_consistency, source_grounding scores",
      "ADDED: model_version and prompt_hash to ai_actions audit table",
    ],
    v3Changes:[
      "REVISED: LLM extraction prompt now requests endpoint_id suggestion alongside rule fields",
      "REVISED: Approval UI shows BC and endpoint context for each proposed rule — reviewer sees clinical meaning",
      "REVISED: ai_actions audit includes endpoint_id assigned (approved vs proposed) for semantic audit trail",
    ],
    researchBasis:"CDISC AI + Biomedical Concepts Challenge: CDISC frames AI as assisting BC development, accelerating metadata curation, supporting semantic interoperability — not autonomous derivation execution. JMIR AI 2026: LLM capability bounded by hallucination and brittle reasoning. Human-in-loop is the only defensible architecture.",
    tasks:[
      {
        type:"BUILD",
        title:"SAP Ingestion + Endpoint-Aware Extraction",
        detail:"PDF/DOCX SAP → chunked by section. Each chunk tagged: section_id, page_ref, section_type. Feed to LLM with v3 extraction prompt: 'Extract derivation rules. Output ONLY valid YAML matching derivation_rules schema. Include: target_variable, source_variables, logic_type, condition, sap_reference, criteria_type, assessor, estimand context. Also suggest: endpoint_concept (plain text name of clinical endpoint this rule serves).' The endpoint_concept suggestion is human-verified against endpoint_definitions table in approval UI.",
        fix:"V3 FIX: LLM suggests endpoint context — reviewer maps it to endpoint_id FK, not the LLM. Semantic assignment stays human-controlled.",
      },
      {
        type:"BUILD",
        title:"4-Signal Composite Confidence Scoring",
        detail:"For each LLM-extracted candidate: (1) schema_compliance_score: YAML parses to derivation_rules schema (0 or 1). (2) sap_coverage_score: cited sap_reference findable in document index (0 or 1). (3) cross_run_consistency_score: Jaccard similarity across 3 runs at temperature=0.2 (0.0–1.0). (4) source_grounding_score: logic traceable to specific SAP chunk via second LLM call (0 or 1). Composite = weighted mean [0.2, 0.2, 0.3, 0.3]. Auto-approval threshold: all 4 ≥ 0.8 AND composite ≥ 0.85 — even then, human review recommended for estimand-sensitive rules.",
        fix:null,
      },
      {
        type:"BUILD",
        title:"Approval UI — Semantic Context Panel",
        detail:"Streamlit review UI. V3 addition: right panel shows proposed rule YAML + source SAP chunk + suggested endpoint_concept + matching endpoint_definitions rows (fuzzy name match). Reviewer actions: APPROVE (assigns endpoint_id FK, commits to derivation_rules, logs to ai_actions with endpoint_id_approved), REJECT (rejection_reason required), EDIT (modify YAML + endpoint_id inline). The semantic context panel is the key upgrade — reviewer approves both the rule logic AND the clinical endpoint linkage in one action.",
        fix:"V3 FIX: Approval UI now surfaces BC and endpoint context — reviewer is not just approving YAML, they're confirming semantic classification.",
      },
      {
        type:"GOVERNANCE",
        title:"Full Semantic AI Audit Trail",
        detail:"ai_actions table: action_id, timestamp, model_version, prompt_hash, input_hash, output_hash, confidence_composite, confidence_signals JSON, human_decision, human_id, decision_ts, rejection_reason, endpoint_id_proposed (LLM suggestion), endpoint_id_approved (human assignment). Divergence between proposed and approved endpoint_id is auditable signal of extraction quality. Exportable for regulatory audit.",
        fix:"V3 FIX: endpoint_id_proposed vs endpoint_id_approved comparison makes LLM semantic accuracy measurable over time.",
      },
    ],
    outputs:["sap_ingestion.py", "llm_rule_extractor.py (endpoint-aware)", "confidence_scorer.py (4-signal)", "pending_queue (SQLite)", "approval_ui.py (semantic panel)", "ai_actions (SQLite — semantic audit)"],
    criticalDecision:"AI assists semantic metadata authoring. The endpoint_id_proposed vs endpoint_id_approved divergence metric is a quality signal for the extraction pipeline — measurable, improvable, auditable.",
  },
];

const TECH_STACK = [
  { layer:"Protocol Config",      tech:"YAML (M11-aligned)",         rationale:"Structured ICH M11 protocol metadata. Single seed for semantic metadata repository. Promotes to protocol_objectives table on init." },
  { layer:"Semantic Root",        tech:"biomedical_concepts (new)",   rationale:"CDISC COSMoS-aligned BC table. Primary key of architecture — all variables FK here. cosmos_bc_id enables COSMoS interoperability." },
  { layer:"Metadata Store",       tech:"SQLite + Alembic",           rationale:"OLTP 12-table semantic schema. Alembic versioned migrations — every schema change tracked, reversible, Git-committed." },
  { layer:"Analytical Store",     tech:"DuckDB",                     rationale:"OLAP columnar engine. 10–100× SQLite for QC aggregations and lineage scans. MIT-licensed, embedded, zero infrastructure." },
  { layer:"Reproducibility",      tech:"execution_snapshots (new)",  rationale:"Snapshot captures full runtime state per run: standards versions, rule hashes, env manifest. Environment-level replayability." },
  { layer:"Orchestration",        tech:"Python 3.12+",               rationale:"Rule parser, orchestrator, snapshot manager. ExecutionAdapter ABC makes SAS swappable without refactoring." },
  { layer:"Execution",            tech:"SAS (via ExecutionAdapter)",  rationale:"Adapter pattern — SAS is one implementation. R and Python adapters substitutable." },
  { layer:"Transport Format",     tech:"XPT + Dataset-JSON v1.1",    rationale:"Dual output. FDA Dataset-JSON adoption decision expected 2026. Python handles JSON natively." },
  { layer:"Semantic Graph",       tech:"NetworkX → Neo4j",           rationale:"Full 8-layer hierarchy: Objective→BC→Endpoint→Estimand→Rule→Variable→Result→Artifact. Neo4j triggers documented." },
  { layer:"Validation",           tech:"CDISC CORE + Custom Rules",   rationale:"CORE Level 1 structural compliance. Custom RECIST/iRECIST Level 2. Endpoint-context Level 3 narratives." },
  { layer:"Define.xml",           tech:"Python lxml (v2.1)",         rationale:"Semantic single-source: BC definitions in CommentDef, endpoint labels in ARM. Never manually authored." },
  { layer:"SDRG Output",          tech:"HTML + JSON-LD",             rationale:"JSON-LD embeds BC and endpoint URIs — semantically interoperable with COSMoS and future FDA tooling." },
  { layer:"Dashboard/UI",         tech:"Streamlit",                  rationale:"Graph visualization (pyvis), semantic AI approval workflow, endpoint-grouped QC. Zero frontend stack." },
  { layer:"AI Extraction",        tech:"Claude/GPT-4o + 4-Signal",   rationale:"4-signal composite confidence. endpoint_id_proposed vs approved divergence is quality metric. Human gate unconditional." },
];

const ROADMAP = [
  { v:"v1.0", phases:[1,2,3,4], label:"Semantic Metadata Repository + Declarative Derivation Runtime", milestone:"First concept-rooted metadata-driven SAS execution with Dataset-JSON + execution snapshots.", color:"#76E4F7" },
  { v:"v2.0", phases:[5,6],     label:"Semantic QC + Knowledge Graph",                                  milestone:"Endpoint-grouped QC narratives + 8-layer semantic graph from protocol objective to reviewer artifact.", color:"#FC8181" },
  { v:"v3.0", phases:[7,8],     label:"Semantic Define.xml + JSON-LD SDRG",                             milestone:"BC-annotated Define.xml + COSMoS-interoperable JSON-LD SDRG + snapshot-linked audit log.", color:"#F6AD55" },
  { v:"v4.0", phases:[9],       label:"4-Signal Governed Semantic AI Extraction",                       milestone:"LLM extraction with endpoint context, composite confidence, and divergence quality metric.", color:"#9AE6B4" },
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
                v3.0 — Semantic Architecture
              </div>
              <div style={{ fontSize:9, color:C.teal, letterSpacing:".15em",
                textTransform:"uppercase", background:`${C.teal}12`,
                border:`1px solid ${C.teal}25`, padding:"3px 9px", borderRadius:3 }}>
                CDISC 360i Aligned
              </div>
            </div>
            <div style={{ fontSize:20, fontWeight:800, color:C.textHi,
              fontFamily:"'Syne',sans-serif", lineHeight:1.1, marginBottom:4 }}>
              Explainable Metadata-Native Submission Engineering
            </div>
            <div style={{ fontSize:11, color:C.textLo, lineHeight:1.5 }}>
              Oncology Immunotherapy · SDTMIG 3.4 / ADaM 1.3 · ICH M11 · RECIST 1.1 + iRECIST · Define.xml v2.1
            </div>
          </div>
          <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
            {[
              { k:"phases",   label:"Phases" },
              { k:"semantic", label:"Semantic Model" },
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
              Click any phase to expand. <span style={{ color:C.violet }}>● v3 semantic upgrades</span> shown inline.
              Phases with violet badges contain new semantic entity additions.
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
                            v3
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
                          textTransform:"uppercase", marginBottom:5 }}>v3 additions</div>
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

            {/* v3 Changes block */}
            {ph.v3Changes && ph.v3Changes.length > 0 && (
              <div style={{ background:`${C.violet}06`, border:`1px solid ${C.violet}20`,
                borderRadius:7, padding:"14px 16px", marginBottom:14 }}>
                <div style={{ fontSize:9, color:C.violet, letterSpacing:".15em",
                  textTransform:"uppercase", marginBottom:8 }}>v3 Semantic Upgrades</div>
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
                  textTransform:"uppercase", marginBottom:8 }}>v2 Audit Fixes (carried forward)</div>
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

        {/* ── SEMANTIC MODEL VIEW ───────────────────────────────────── */}
        {view==="semantic" && (
          <div>
            <div style={{ fontSize:11, color:C.muted, marginBottom:20, lineHeight:1.6 }}>
              The v3 semantic architecture inverts the primary key from <span style={{ color:C.amber }}>(dataset, variable)</span> to{" "}
              <span style={{ color:C.violet }}>concept_id</span>. Variables become implementation artifacts.
              Concepts are the root. This is the CDISC 360i / COSMoS / BRIDG architectural pattern.
            </div>

            {/* Hierarchy visualization */}
            <div style={{ background:C.surface, border:`1px solid ${C.border}`,
              borderRadius:8, padding:"20px 24px", marginBottom:16 }}>
              <div style={{ fontSize:9, color:C.violet, letterSpacing:".15em",
                textTransform:"uppercase", marginBottom:16 }}>
                Semantic Entity Hierarchy — Concept to Artifact
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
                            <span style={{ fontSize:8, color:C.violet,
                              background:`${C.violet}15`, border:`1px solid ${C.violet}30`,
                              padding:"1px 6px", borderRadius:2, letterSpacing:".1em" }}>NEW</span>
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
                              textTransform:"uppercase", marginBottom:6 }}>Key Fields</div>
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

            {/* Key inversion callout */}
            <div style={{ background:`${C.violet}07`, border:`1px solid ${C.violet}25`,
              borderRadius:8, padding:"16px 20px", marginBottom:16 }}>
              <div style={{ fontSize:9, color:C.violet, letterSpacing:".15em",
                textTransform:"uppercase", marginBottom:10 }}>The Core Architectural Inversion</div>
              <div style={{ display:"grid", gridTemplateColumns:"1fr auto 1fr", gap:12, alignItems:"center" }}>
                <div style={{ background:C.raised, border:`1px solid ${C.border}`,
                  borderRadius:6, padding:"12px 14px" }}>
                  <div style={{ fontSize:9, color:C.red, letterSpacing:".1em",
                    marginBottom:6, textTransform:"uppercase" }}>v1/v2 (obsolete)</div>
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
                    marginBottom:6, textTransform:"uppercase" }}>v3 (semantic)</div>
                  {["biomedical_concept","↓ endpoint_definition","↓ estimand","↓ derivation_rule","↓ variable (realization)"].map((t,i)=>(
                    <div key={i} style={{ fontSize:11,
                      color: i===0 ? C.violet : i===4 ? C.muted : C.text,
                      fontFamily:"'JetBrains Mono',monospace", lineHeight:1.8,
                      fontWeight: i===0 ? 700 : 400 }}>{t}</div>
                  ))}
                  <div style={{ fontSize:9, color:C.violet, marginTop:6, fontStyle:"italic" }}>
                    Primary key: bc_id (concept_id)
                  </div>
                </div>
              </div>
            </div>

            {/* Reproducibility components */}
            <div style={{ background:C.surface, border:`1px solid ${C.border}`,
              borderRadius:8, padding:"18px 20px" }}>
              <div style={{ fontSize:9, color:C.blue, letterSpacing:".15em",
                textTransform:"uppercase", marginBottom:14 }}>
                Reproducibility Layer — Environment-Level Replayability
              </div>
              <div style={{ fontSize:10, color:C.muted, marginBottom:14, lineHeight:1.55 }}>
                Hashing outputs is insufficient. Enterprise reproducibility requires: same metadata + same standards + same runtime + same dependencies + same orchestration state = identical submission.
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
                          padding:"1px 6px", borderRadius:2 }}>NEW</span>
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
              v3 additions: <span style={{ color:C.violet }}>biomedical_concepts</span> as semantic root,{" "}
              <span style={{ color:C.blue }}>execution_snapshots</span> for reproducibility.
              All other choices unchanged from v2.
            </div>
            <div style={{ display:"flex", flexDirection:"column", gap:7, marginBottom:20 }}>
              {TECH_STACK.map((t,i)=>{
                const isNew = t.tech.includes("(new)");
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
            <div style={{ background:"rgba(118,228,247,.04)",
              border:"1px solid rgba(118,228,247,.15)", borderRadius:7,
              padding:"14px 16px" }}>
              <div style={{ fontSize:9, color:C.cyan, letterSpacing:".15em",
                textTransform:"uppercase", marginBottom:6 }}>v3 Architecture Principle</div>
              <div style={{ fontSize:12, color:C.text, lineHeight:1.7 }}>
                <span style={{ color:C.violet, fontWeight:600 }}>biomedical_concepts</span> = semantic root (concept_id is the primary key).
                {" "}<span style={{ color:C.amber, fontWeight:600 }}>endpoint_definitions</span> = BC-to-derivation bridge (the previously implicit layer).
                {" "}<span style={{ color:C.blue, fontWeight:600 }}>execution_snapshots</span> = environment-level reproducibility (not just output hashes).
                {" "}<span style={{ color:C.teal, fontWeight:600 }}>analysis_results</span> = ARM source from Phase 2 (first-class, not Phase 7 afterthought).
                {" "}Variables are implementation artifacts of concepts — not root entities.
              </div>
            </div>
          </div>
        )}

        {/* ── ROADMAP VIEW ─────────────────────────────────────────── */}
        {view==="roadmap" && (
          <div>
            <div style={{ fontSize:11, color:C.muted, marginBottom:18, lineHeight:1.6 }}>
              Version sequencing unchanged — metadata first, semantic model second, explainability third, AI last.
              v3 semantic additions are distributed across all phases but concentrate in v1.0 (Phase 2 schema).
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
                            {nv3>0 ? ` (+${nv3}v3)` : n2>0 ? ` (+${n2}fixes)` : ""}
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

            {/* Regulatory timeline */}
            <div style={{ background:C.surface, border:`1px solid ${C.border}`,
              borderRadius:8, padding:"16px 20px", marginBottom:16 }}>
              <div style={{ fontSize:9, color:C.violet, letterSpacing:".15em",
                textTransform:"uppercase", marginBottom:12 }}>Regulatory Currency Timeline</div>
              {[
                { date:"June 2026",    event:"ICH M11 in effect. study_config.yaml m11_protocol block + protocol_objectives table addresses this.",          col:C.red,    phase:"P1" },
                { date:"2026",         event:"FDA Dataset-JSON v1.1 adoption decision. Dual XPT+JSON output from Phase 4 with execution_snapshot linkage.", col:C.amber,  phase:"P4" },
                { date:"2026",         event:"CDISC CORE v1.0 full release. Platform integrates CORE engine in Phase 5 Level 1 validation.",               col:C.cyan,   phase:"P5" },
                { date:"Sept 2025",    event:"PMDA Validator Rules 2.0 live. ARM now validated — analysis_results table (Phase 2) generates ARM automatically.", col:C.green,  phase:"P7" },
                { date:"2026 (active)","event":"COSMoS OpenAPI + LinkML BCs publicly available. biomedical_concepts.cosmos_bc_id enables direct interoperability.", col:C.violet, phase:"P2" },
                { date:"Ongoing",      event:"SDTM v3.0 / ADaM v3.0 in development. Alembic + execution_snapshots.standards_version pinning handles evolution.", col:C.muted,  phase:"P2" },
              ].map((ev,i)=>(
                <div key={i} style={{ display:"flex", gap:12, alignItems:"flex-start",
                  padding:"8px 0", borderBottom: i<5?"1px solid "+C.border:"none" }}>
                  <div style={{ fontSize:10, color:ev.col, minWidth:110,
                    fontWeight:600, letterSpacing:".05em" }}>{ev.date}</div>
                  <div style={{ fontSize:9, color:ev.col, background:`${ev.col}10`,
                    border:`1px solid ${ev.col}25`, padding:"2px 7px",
                    borderRadius:3, whiteSpace:"nowrap", marginTop:1 }}>{ev.phase}</div>
                  <div style={{ fontSize:11, color:C.text, lineHeight:1.55 }}>{ev.event}</div>
                </div>
              ))}
            </div>

            {/* Final verdict */}
            <div style={{ background:"rgba(104,211,145,.04)", border:"1px solid rgba(104,211,145,.2)",
              borderRadius:8, padding:"14px 18px" }}>
              <div style={{ fontSize:9, color:C.green, letterSpacing:".15em",
                textTransform:"uppercase", marginBottom:6 }}>Architecture Verdict · v3.0</div>
              <div style={{ fontSize:12, color:C.text, lineHeight:1.8 }}>
                Core architecture remains <span style={{ color:C.textHi, fontWeight:700 }}>structurally sound</span> — no redesign required.
                The v3 semantic layer adds 3 new tables and 2 promotions:{" "}
                <span style={{ color:C.violet }}>biomedical_concepts</span> (semantic root),{" "}
                <span style={{ color:C.amber }}>endpoint_definitions</span> (BC-to-derivation bridge),{" "}
                <span style={{ color:C.blue }}>execution_snapshots</span> (reproducibility), plus{" "}
                <span style={{ color:C.lime }}>analysis_results</span> and{" "}
                <span style={{ color:C.cyan }}>protocol_objectives</span> promoted to Phase 2.{" "}
                The result is <span style={{ color:C.violet }}>CDISC 360i / COSMoS / BRIDG aligned</span> semantic submission infrastructure — not metadata-driven automation.
                Goal: <span style={{ color:C.textHi, fontWeight:700 }}>Computable Regulatory Metadata Architecture</span>.
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
