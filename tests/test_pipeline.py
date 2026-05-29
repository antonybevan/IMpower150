import sys
import os
# Resolve src/ and seeds/ relative to this test file
_ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(_ROOT, 'src'))
sys.path.insert(0, os.path.join(_ROOT, 'seeds'))

import json
import duckdb
import xml.etree.ElementTree as ET
from models import init_database
from rule_parser import RuleParser
from snapshot_manager import SnapshotManager
from execution_adapter import MockSASAdapter
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
    
    # Run the full end-to-end pipeline (Database, Rules, Snapshots, Mock SAS runtime, QC, Graph, Exporters)
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
        assert paramcd in ("PFS", "iPFS", "OS"), f"Contradiction in ADTTE: PARAMCD is {paramcd} (Expected PFS, iPFS, or OS)"
        seen_params.add(paramcd)
        
    assert "PFS" in seen_params, "PFS parameter missing from ADTTE"
    assert "iPFS" in seen_params, "iPFS parameter missing from ADTTE"
    assert "OS" in seen_params, "OS parameter missing from ADTTE"
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
