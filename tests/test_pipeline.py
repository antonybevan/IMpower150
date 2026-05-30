import sys
import os
# Resolve src/ and seeds/ relative to this test file
_ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(_ROOT, 'src'))
sys.path.insert(0, os.path.join(_ROOT, 'seeds'))

import json
import duckdb
import pyreadstat
import xml.etree.ElementTree as ET
from models import init_database
from rule_parser import RuleParser
from snapshot_manager import SnapshotManager
from execution_adapter import ClinicalDerivationAdapter
from graph_builder import SemanticGraphBuilder
from qc_engine import QCEngine
from define_xml_generator import SubmissionGenerator
from ingest_protocol import ProtocolIngestor
from seed_clinical_rules import seed_additional_clinical_rules
from seed_arm_results import seed_arm_data
from log_parser import SASLogParser
from lineage_report_generator import LineageReportGenerator

def run_e2e_verification_pipeline():
    print("="*80)
    print("   IMPOWER150 COMPUTE REGULATORY METADATA & DATA PIPELINE E2E TEST")
    print("="*80)
    
    # ─── STEP 1: INITIALIZE CLEAN DB DIRECTLY VIA ORCHESTRATOR ───
    db_path = 'metadata.db'
    duck_path = 'analytics.duckdb'
    output_dir = 'outputs'
    
    if os.path.exists(db_path):
        os.remove(db_path)
    if os.path.exists(duck_path):
        os.remove(duck_path)
        
    # Instantiate PipelineOrchestrator
    from orchestrator import PipelineOrchestrator
    orchestrator = PipelineOrchestrator(db_path=db_path, duck_path=duck_path, output_dir=output_dir)
    
    # Run the full end-to-end pipeline (Database, Rules, Snapshots, Clinical SAS execution adapter, QC, Graph, Exporters)
    run_id = "RUN_IMPOWER150_2026_05"
    exec_result = orchestrator.run_pipeline(run_id=run_id)
    
    # ─── STEP 2: VERIFY EXPORTED SUBMISSION ARTIFACTS ───
    assert os.path.exists(exec_result["define_xml"]), "Define.xml export missing"
    assert os.path.exists(exec_result["sdrg_jsonld"]), "SDRG JSON-LD export missing"
    assert os.path.exists(exec_result["sdrg_html"]), "SDRG HTML export missing"
    
    # Generate Lineage HTML report
    lin_gen = LineageReportGenerator(db_path=db_path, output_dir=os.path.join(output_dir, "submission"))
    lineage_html = lin_gen.generate_report()
    assert os.path.exists(lineage_html), "Lineage HTML export missing"
    
    # ─── STEP 3: STRICT XML COMPLIANCE VALIDATION (XML PARSER GATE) ───
    print("\n>>> STEP 3: Strict XML Compliance Validation")
    try:
        tree = ET.parse(exec_result["define_xml"])
        root = tree.getroot()
        print(f"  • SUCCESS: Define.xml parses cleanly as well-formed XML!")
        print(f"  • Root tag verified: {root.tag}")
        assert "ODM" in root.tag, "XML root tag should be ODM in ODM namespace"
        itemref_methods = {
            elem.get("ItemOID"): elem.get("MethodOID")
            for elem in root.iter()
            if elem.tag.split("}")[-1] == "ItemRef"
        }
        assert itemref_methods.get("IT.ADDOR.AVAL") == "MT.RULE_DOR_AVAL", "ADDOR.AVAL must link to DOR derivation"
        assert itemref_methods.get("IT.ADDOR.CNSR") == "MT.RULE_DOR_CNSR", "ADDOR.CNSR must link to DOR censoring derivation"
        assert itemref_methods.get("IT.ADRS.ORR_FL") == "MT.RULE_ORR_FL", "ADRS.ORR_FL must link to ORR derivation"
        assert itemref_methods.get("IT.ADTTE.AVAL") is None, "ADTTE.AVAL spans multiple PARAMCD-specific methods and must not carry one ambiguous MethodOID"
        assert itemref_methods.get("IT.ADTTE.CNSR") is None, "ADTTE.CNSR spans multiple PARAMCD-specific methods and must not carry one ambiguous MethodOID"
    except Exception as ex:
        assert False, f"CRITICAL Define.xml is structurally invalid or prefix is unbound: {ex}"
        
    # Verify ADTTE (PFS/iPFS/OS)
    adtte_path = os.path.join(output_dir, "datasets", "adtte.json")
    assert os.path.exists(adtte_path), "adtte.json missing"
    with open(adtte_path, 'r') as f:
        adtte_data = json.load(f)
    ig_adtte = adtte_data["clinicalData"]["itemGroupData"]["IG.ADTTE"]
    adtte_records = ig_adtte["itemData"]
    
    seen_params = set()
    for record in adtte_records:
        paramcd = record[2]
        assert paramcd in ("PFS", "iPFS", "OS", "PFS_EMA"), f"Contradiction in ADTTE: PARAMCD is {paramcd} (Expected PFS, iPFS, OS, or PFS_EMA)"
        seen_params.add(paramcd)
        
    assert "PFS" in seen_params, "PFS parameter missing from ADTTE"
    assert "iPFS" in seen_params, "iPFS parameter missing from ADTTE"
    assert "OS" in seen_params, "OS parameter missing from ADTTE"
    assert "PFS_EMA" in seen_params, "PFS_EMA parameter missing from ADTTE"
    for ds_name in ("adtte", "addor", "adrs"):
        xpt_path = os.path.join(output_dir, "datasets", f"{ds_name}.xpt")
        assert os.path.exists(xpt_path), f"{ds_name}.xpt missing"
        df, meta = pyreadstat.read_xport(xpt_path)
        assert len(df) > 0, f"{ds_name}.xpt should contain records"
        assert meta.table_name.upper() == ds_name.upper(), f"{ds_name}.xpt table name mismatch"

    import sqlite3
    sqlite_conn = sqlite3.connect(db_path)
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute("SELECT version_num FROM alembic_version")
    alembic_version = sqlite_cur.fetchone()[0]
    sqlite_cur.execute("SELECT COUNT(*) FROM parameter_variable_metadata")
    param_meta_count = sqlite_cur.fetchone()[0]
    sqlite_conn.close()
    assert alembic_version == "9f2b7c31d6a4", f"Unexpected Alembic version: {alembic_version}"
    assert param_meta_count >= 9, "Parameter-level variable metadata must be seeded"
    print("  • SUCCESS: ADTTE dataset contains logically consistent PARAMCD values ('PFS'/'iPFS'/'OS')")

    # ─── STEP 5: EVIDENCE-BASED CONFORMANCE QC VERIFICATION ───
    print("\n>>> STEP 5: Evidence-Based Conformance Validation")
    conn = duckdb.connect(duck_path)
    qc_count = conn.execute("SELECT COUNT(*) FROM qc_findings").fetchone()[0]
    l3_count = conn.execute("SELECT COUNT(*) FROM qc_findings WHERE clinical_narrative LIKE 'EXPLAINABLE%'").fetchone()[0]
    assert qc_count > 0, "Analytical store should record QC violations"
    assert l3_count >= 1, "Level 3 root-cause traversal narrative should explain at least 1 critical discrepancy"
    
    clinical_review = conn.execute("SELECT clinical_narrative FROM qc_findings WHERE severity='critical'").fetchone()[0]
    print("\n• VERIFIED LEVEL 3 CLINICALLY EXPLAINABLE ROOT-CAUSE NARRATIVE IN DUCKDB:")
    print("-" * 80)
    print(clinical_review)
    print("-" * 80)
    conn.close()

    print("\n" + "="*80)
    print("   ALL PIPELINE RECONSTRUCTION TESTS PASSED SUCCESSFULLY! (100% CORRECT)")
    print("="*80)

if __name__ == '__main__':
    run_e2e_verification_pipeline()
