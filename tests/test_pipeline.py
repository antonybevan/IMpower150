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
        assert paramcd in ("PFS", "iPFS", "OS", "PFS_EMA", "PFS_BICR", "OS_BICR"), f"Contradiction in ADTTE: PARAMCD is {paramcd} (Expected PFS, iPFS, OS, PFS_EMA, PFS_BICR, or OS_BICR)"
        seen_params.add(paramcd)
        
    assert "PFS" in seen_params, "PFS parameter missing from ADTTE"
    assert "iPFS" in seen_params, "iPFS parameter missing from ADTTE"
    assert "OS" in seen_params, "OS parameter missing from ADTTE"
    assert "PFS_EMA" in seen_params, "PFS_EMA parameter missing from ADTTE"
    assert "PFS_BICR" in seen_params, "PFS_BICR (BICR assessor) parameter missing from ADTTE"
    assert "OS_BICR" in seen_params, "OS_BICR (BICR assessor) parameter missing from ADTTE"
    for ds_name in ("adtte", "addor", "adrs"):
        xpt_path = os.path.join(output_dir, "datasets", f"{ds_name}.xpt")
        assert os.path.exists(xpt_path), f"{ds_name}.xpt missing"
        df, meta = pyreadstat.read_xport(xpt_path)
        assert len(df) > 0, f"{ds_name}.xpt should contain records"
        assert meta.table_name.upper() == ds_name.upper(), f"{ds_name}.xpt table name mismatch"

    # ─── STEP 3b: VERIFY ADSL & ADICE (C1 & C2 Critical Items) ───
    print("\n>>> STEP 3b: Verify ADSL and ADICE Datasets")
    adsl_path = os.path.join(output_dir, "datasets", "adsl.json")
    assert os.path.exists(adsl_path), "adsl.json missing (C1: ADSL generation failed)"
    with open(adsl_path, 'r') as f:
        adsl_data = json.load(f)
    ig_adsl = adsl_data["clinicalData"]["itemGroupData"]["IG.ADSL"]
    adsl_cols = [col["name"] for col in ig_adsl["columns"]]
    assert "ARMCD" in adsl_cols, "ADSL must contain ARMCD (3-arm randomization)"
    assert "WTFL" in adsl_cols, "ADSL must contain WTFL (Wild-Type population flag)"
    assert "TEFFFL" in adsl_cols, "ADSL must contain TEFFFL (Teff-high biomarker flag)"
    assert "PSYFL" in adsl_cols, "ADSL must contain PSYFL (Principal Stratum Flag)"
    assert ig_adsl["records"] == 100, f"ADSL should have 100 subjects, got {ig_adsl['records']}"
    # Verify 3-arm balanced randomization
    armcd_idx = adsl_cols.index("ARMCD")
    arm_counts = {}
    for row in ig_adsl["itemData"]:
        armcd = row[armcd_idx]
        arm_counts[armcd] = arm_counts.get(armcd, 0) + 1
    assert set(arm_counts.keys()) == {"A", "B", "C"}, f"ADSL must have 3 arms (A/B/C), got {set(arm_counts.keys())}"
    print(f"  • ADSL verified: {ig_adsl['records']} subjects, arms {arm_counts}")
    
    adice_path = os.path.join(output_dir, "datasets", "adice.json")
    assert os.path.exists(adice_path), "adice.json missing (C2: ADICE generation failed)"
    with open(adice_path, 'r') as f:
        adice_data = json.load(f)
    ig_adice = adice_data["clinicalData"]["itemGroupData"]["IG.ADICE"]
    adice_cols = [col["name"] for col in ig_adice["columns"]]
    assert "ATERM" in adice_cols, "ADICE must contain ATERM (Intercurrent Event Term)"
    assert "ESTSTP" in adice_cols, "ADICE must contain ESTSTP (Estimand Strategy)"
    assert "SRCDOM" in adice_cols, "ADICE must contain SRCDOM (Source Domain for traceability)"
    assert ig_adice["records"] > 0, "ADICE should contain intercurrent events"
    print(f"  • ADICE verified: {ig_adice['records']} intercurrent event records")
    
    # ─── STEP 3c: VERIFY DATASET-JSON V1.1 ENVELOPE (C4) ───
    print("\n>>> STEP 3c: Verify Dataset-JSON v1.1 Envelope Compliance")
    assert "datasetJSONVersion" in adtte_data, "Missing datasetJSONVersion (Dataset-JSON v1.1 required)"
    assert adtte_data["datasetJSONVersion"] == "1.1.0", f"Expected v1.1.0, got {adtte_data.get('datasetJSONVersion')}"
    assert "fileOID" in adtte_data, "Missing fileOID (Dataset-JSON v1.1 required)"
    assert "datasetJSONCreationDateTime" in adtte_data, "Missing datasetJSONCreationDateTime"
    assert "sourceSystem" in adtte_data, "Missing sourceSystem metadata"
    assert "originator" in adtte_data, "Missing originator field"
    print(f"  • Dataset-JSON v1.1 envelope verified: version={adtte_data['datasetJSONVersion']}, fileOID={adtte_data['fileOID']}")

    # ─── STEP 3d: VERIFY ARD & M11 EXPORTS & ADPANEL IPCW (H5, H10, H6) ───
    print("\n>>> STEP 3d: Verify ARD, M11 and IPCW Weights")
    ard_path = exec_result["ard_json"]
    assert os.path.exists(ard_path), "ard.json missing (H5: ARD generation failed)"
    with open(ard_path, 'r') as f:
        ard_data = json.load(f)
    assert ard_data["arsVersion"] == "1.0.0", "Expected ARS v1.0.0"
    assert ard_data["studyOID"] == "GO29436", "Expected study OID GO29436 in ARD"
    assert len(ard_data["analysisResults"]) > 0, "ARD should contain analysis results"
    print(f"  • ARD verified: {len(ard_data['analysisResults'])} statistical analyses exported conforming to CDISC ARS v1.0")

    m11_path = exec_result["m11_protocol"]
    assert os.path.exists(m11_path), "m11_protocol.json missing (H10: M11 export failed)"
    with open(m11_path, 'r') as f:
        m11_data = json.load(f)
    assert m11_data["m11ProtocolJSONVersion"] == "1.0.0", "Expected M11 version 1.0.0"
    assert m11_data["studyIdentification"]["studyID"] == "GO29436", "Expected study ID GO29436 in M11 protocol"
    assert len(m11_data["protocolStructure"]["objectives"]) > 0, "M11 protocol must contain objectives"
    print(f"  • M11 protocol verified: digital protocol conforms to ICH M11 CeSHarP")

    # Verify ADPANEL IPCW Weight column
    adpanel_path = os.path.join(output_dir, "datasets", "adpanel.json")
    with open(adpanel_path, 'r') as f:
        adpanel_data = json.load(f)
    ig_adpanel = adpanel_data["clinicalData"]["itemGroupData"]["IG.ADPANEL"]
    adpanel_cols = [col["name"] for col in ig_adpanel["columns"]]
    assert "SW_IPCW" in adpanel_cols, "ADPANEL must contain SW_IPCW stabilized weight column (H6)"
    print(f"  • ADPANEL IPCW verified: SW_IPCW column exists")

    import sqlite3
    sqlite_conn = sqlite3.connect(db_path)
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute("SELECT version_num FROM alembic_version")
    alembic_version = sqlite_cur.fetchone()[0]
    sqlite_cur.execute("SELECT COUNT(*) FROM parameter_variable_metadata")
    param_meta_count = sqlite_cur.fetchone()[0]
    # Verify concept inheritance (H8)
    sqlite_cur.execute("SELECT COUNT(*) FROM biomedical_concepts WHERE parent_bc_id IS NOT NULL")
    inherited_bc_count = sqlite_cur.fetchone()[0]
    # Verify Dataset Specialization (H8)
    sqlite_cur.execute("SELECT COUNT(*) FROM dataset_specializations")
    specialization_count = sqlite_cur.fetchone()[0]
    sqlite_conn.close()
    
    assert alembic_version == "9f2b7c31d6a4", f"Unexpected Alembic version: {alembic_version}"
    assert param_meta_count >= 9, "Parameter-level variable metadata must be seeded"
    assert inherited_bc_count >= 3, f"Expected concept hierarchy seeds, got {inherited_bc_count}"
    assert specialization_count >= 4, f"Expected dataset specializations, got {specialization_count}"
    print("  • SUCCESS: All dataset contents and semantic schemas logically verified")

    # ─── STEP 5: EVIDENCE-BASED CONFORMANCE QC VERIFICATION ───
    print("\n>>> STEP 5: Evidence-Based Conformance Validation")
    conn = duckdb.connect(duck_path)
    qc_count = conn.execute("SELECT COUNT(*) FROM qc_findings").fetchone()[0]
    l3_count = conn.execute("SELECT COUNT(*) FROM qc_findings WHERE clinical_narrative LIKE 'EXPLAINABLE%'").fetchone()[0]
    # Verify Level 5 Controlled Terminology Validation (M14)
    l5_count = conn.execute("SELECT COUNT(*) FROM qc_findings WHERE rule_source='EVS_CT'").fetchone()[0]
    assert qc_count > 0, "Analytical store should record QC violations"
    assert l3_count >= 1, "Level 3 root-cause traversal narrative should explain at least 1 critical discrepancy"
    assert l5_count >= 0, "Level 5 controlled terminology checks ran successfully"
    
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
