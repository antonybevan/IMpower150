import sqlite3
import duckdb
import os
import json

print("="*80)
print("  IMPOWER150 EXTENSIVE AUDIT PROBE")
print("="*80)

# ─── SQLite audit ─────────────────────────────────────────────────────────────
conn = sqlite3.connect('metadata.db')
conn.execute("PRAGMA foreign_keys = ON;")
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print("\n[1] SQLITE TABLES PRESENT:")
for t in tables:
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    cnt = cur.fetchone()[0]
    print(f"    {t:<35} {cnt:>5} rows")

print("\n[2] BIOMEDICAL CONCEPTS (COSMoS root):")
cur.execute("SELECT bc_id, bc_name, cosmos_bc_id, sdtmig_class FROM biomedical_concepts")
for r in cur.fetchall():
    print(f"    {r[0]:<10} | {r[1]:<30} | COSMoS: {r[2]} | Class: {r[3]}")

print("\n[3] DERIVATION RULES (logic types & endpoint FKs):")
cur.execute("SELECT rule_id, logic_type, endpoint_id, assessor, criteria_type, approval_status FROM derivation_rules ORDER BY rule_id")
rules = cur.fetchall()
for r in rules:
    ep_missing = "(MISSING ENDPOINT FK)" if not r[2] else ""
    print(f"    {r[0]:<22} | {r[1]:<20} | EP: {r[2] or 'NULL':<22} | {r[5]} {ep_missing}")

print("\n[4] ENDPOINTS (BC to Estimand bridge):")
cur.execute("SELECT endpoint_id, bc_id, estimand_id, endpoint_type, analysis_concept FROM endpoint_definitions ORDER BY endpoint_type, endpoint_id")
eps = cur.fetchall()
primary   = [e for e in eps if e[3] == 'primary']
secondary = [e for e in eps if e[3] == 'secondary']
other     = [e for e in eps if e[3] not in ('primary','secondary')]
print(f"    Total endpoints: {len(eps)} (primary: {len(primary)}, secondary: {len(secondary)}, other: {len(other)})")
for e in primary:
    est_missing = "(NO ESTIMAND)" if not e[2] else ""
    print(f"    [PRIMARY]   {e[0]:<22} | BC: {e[1]:<6} | Estimand: {e[2] or 'NULL'} {est_missing}")

print("\n[5] ESTIMANDS (ICH E9(R1)):")
cur.execute("SELECT estimand_id, name, target_population FROM estimands")
for r in cur.fetchall():
    pop_short = r[2][:60] + "..." if r[2] and len(r[2]) > 60 else r[2]
    print(f"    {r[0]:<25} | {r[1]}")
    print(f"    {'':>25}   Pop: {pop_short}")

print("\n[6] PROTOCOL OBJECTIVES (M11 first-class):")
cur.execute("SELECT obj_id, obj_type, endpoint_id, m11_section FROM protocol_objectives ORDER BY obj_type")
objs = cur.fetchall()
primary_objs = [o for o in objs if o[1]=='primary']
secondary_objs = [o for o in objs if o[1]=='secondary']
print(f"    Total objectives: {len(objs)} (primary: {len(primary_objs)}, secondary: {len(secondary_objs)})")
for o in objs[:8]:
    print(f"    [{o[1].upper():<12}] {o[0]:<25} | Endpoint FK: {o[2] or 'NULL':<22} | {o[3]}")

print("\n[7] EXECUTION SNAPSHOTS (reproducibility):")
cur.execute("SELECT snapshot_id, run_id, python_version, sdtmig_version, adamig_version FROM execution_snapshots")
snaps = cur.fetchall()
if snaps:
    for s in snaps:
        print(f"    {s[0]:<35} | Run: {s[1]} | Py {s[2]} | SDTMIG {s[3]} | ADaM {s[4]}")
else:
    print("    NONE — No snapshots recorded (run test_pipeline.py first)")

print("\n[8] ANALYSIS RESULTS (ARM entities):")
cur.execute("SELECT COUNT(*) FROM analysis_results")
arm_count = cur.fetchone()[0]
if arm_count == 0:
    print("    *** ZERO ARM ROWS — analysis_results table is EMPTY ***")
    print("    AUDIT GAP: Framework specifies analysis_results as Phase 2 first-class entity")
    print("    ACTION REQUIRED: Seed ARM rows from endpoint_definitions")
else:
    cur.execute("SELECT analysis_id, endpoint_id, dataset, stat_method FROM analysis_results")
    for r in cur.fetchall():
        print(f"    {r}")

print("\n[9] AI_ACTIONS AUDIT TABLE:")
cur.execute("SELECT COUNT(*) FROM ai_actions")
ai_count = cur.fetchone()[0]
print(f"    Rows: {ai_count} (Phase 9 AI Governance — empty is expected at this stage)")

print("\n[10] VARIABLES — bc_id FK linkage (gap audit):")
cur.execute("SELECT variable, dataset, bc_id FROM variables WHERE bc_id IS NULL")
unlinked = cur.fetchall()
cur.execute("SELECT COUNT(*) FROM variables")
total_vars = cur.fetchone()[0]
print(f"    Total variables: {total_vars}")
if unlinked:
    print(f"    *** UNLINKED VARIABLES (no bc_id FK): {len(unlinked)} ***")
    for v in unlinked:
        print(f"    UNLINKED: {v[1]}.{v[0]}")
else:
    print("    All variables linked to a Biomedical Concept bc_id FK — CLEAN")

print("\n[11] MISSING SAS TEMPLATES vs FRAMEWORK SPEC:")
required_templates = [
    "derive_date_diff.sas",
    "derive_event_flag.sas",
    "derive_iupd_flag.sas",
    "derive_ipfs_cnsr.sas",         # iRECIST censoring template
    "derive_bor_confirmed.sas",      # BOR confirmation window
    "derive_conditional.sas",        # generic conditional assign
]
present = os.listdir("sas/templates")
for t in required_templates:
    status = "OK" if t in present else "*** MISSING ***"
    print(f"    {status:<18} {t}")

conn.close()

# ─── DuckDB audit ─────────────────────────────────────────────────────────────
print("\n[12] DUCKDB ANALYTICAL STORE (qc_findings):")
if os.path.exists('analytics.duckdb'):
    duck = duckdb.connect('analytics.duckdb')
    try:
        findings = duck.execute("SELECT severity, rule_source, COUNT(*) FROM qc_findings GROUP BY severity, rule_source ORDER BY severity").fetchall()
        total_f = duck.execute("SELECT COUNT(*) FROM qc_findings").fetchone()[0]
        print(f"    Total QC findings: {total_f}")
        for f in findings:
            print(f"    [{f[1]:<20}] Severity: {f[0]:<10} | Count: {f[2]}")

        # Check for Level 3 narratives
        l3 = duck.execute("SELECT COUNT(*) FROM qc_findings WHERE clinical_narrative LIKE 'EXPLAINABLE%'").fetchone()[0]
        print(f"    Level 3 explainable narratives: {l3}")
    except Exception as e:
        print(f"    Error querying DuckDB: {e}")
    duck.close()
else:
    print("    analytics.duckdb not found — run test_pipeline.py first")

# ─── Output artifacts audit ────────────────────────────────────────────────────
print("\n[13] OUTPUT ARTIFACTS:")
artifact_checks = [
    ("outputs/submission/define.xml",   "Define.xml v2.1"),
    ("outputs/submission/sdrg.jsonld",  "JSON-LD SDRG"),
    ("outputs/datasets/adtte.json",     "Dataset-JSON ADTTE"),
    ("outputs/datasets/adtte.xpt",      "SAS XPT ADTTE"),
    ("outputs/manifests/env_manifest_RUN_IMPOWER150_2026_05.json", "Environment Manifest"),
]
for path, label in artifact_checks:
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f"    OK    {label:<35} ({size} bytes)")
    else:
        print(f"    MISSING {label}")

# ─── Generated SAS programs ────────────────────────────────────────────────────
print("\n[14] GENERATED SAS PROGRAMS:")
if os.path.exists("sas/programs"):
    for f in sorted(os.listdir("sas/programs")):
        size = os.path.getsize(os.path.join("sas/programs", f))
        print(f"    {f:<45} ({size} bytes)")
else:
    print("    sas/programs directory not found")

# ─── Framework gaps summary ────────────────────────────────────────────────────
print("\n" + "="*80)
print("  AUDIT GAPS SUMMARY (Framework vs Implementation)")
print("="*80)

gaps = []

# Check ARM
import sqlite3 as _s3
_c = _s3.connect('metadata.db').cursor()
_c.execute("SELECT COUNT(*) FROM analysis_results"); arm_n = _c.fetchone()[0]
if arm_n == 0:
    gaps.append("GAP-01 [HIGH]   analysis_results (ARM) table is EMPTY — Phase 2 first-class entity not seeded")

# Check for missing SAS templates
for t in ["derive_ipfs_cnsr.sas", "derive_bor_confirmed.sas", "derive_conditional.sas"]:
    if t not in present:
        gaps.append(f"GAP-02 [MED]    Missing SAS template: {t}")

# Check Alembic
if not os.path.exists("alembic"):
    gaps.append("GAP-03 [MED]    Alembic schema migration framework not initialized (framework requires day-1 Alembic)")

# Check log_parser / SAS log parsing
if not os.path.exists("src/log_parser.py"):
    gaps.append("GAP-04 [MED]    src/log_parser.py missing — SAS log parsing (ERROR/NOTE/WARNING) not implemented")

# Check orchestrator
if not os.path.exists("src/orchestrator.py"):
    gaps.append("GAP-05 [MED]    src/orchestrator.py missing — rule execution orchestration not formalized")

# Check Phase 9 AI components
for f in ["sap_ingestion.py", "llm_rule_extractor.py", "confidence_scorer.py", "approval_ui.py"]:
    if not os.path.exists(os.path.join("src", f)):
        gaps.append(f"GAP-06 [LOW]    Phase 9 AI component missing: src/{f} (expected per roadmap v4.0)")

# Check SDRG HTML (framework requires HTML + JSON-LD)
if not os.path.exists("outputs/submission/sdrg.html"):
    gaps.append("GAP-07 [LOW]    sdrg.html not generated — framework requires HTML + JSON-LD dual output")

# Check lineage_report_generator
if not os.path.exists("src/lineage_report_generator.py"):
    gaps.append("GAP-08 [LOW]    src/lineage_report_generator.py missing — per-variable HTML lineage reports not implemented")

if gaps:
    for g in gaps:
        print(f"  {g}")
else:
    print("  All checks passed — no gaps found")

print("\n" + "="*80)
print(f"  TOTAL GAPS IDENTIFIED: {len(gaps)}")
print("="*80)
