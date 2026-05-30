import sys
import os
# Resolve seeds directory relative to this file (src/)
_ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(_ROOT, 'seeds'))

from rule_parser import RuleParser
from execution_adapter import ClinicalDerivationAdapter
from snapshot_manager import SnapshotManager
from graph_builder import SemanticGraphBuilder
from qc_engine import QCEngine
from define_xml_generator import SubmissionGenerator
from log_parser import SASLogParser
from seed_arm_results import seed_arm_data
from models import init_database
from ingest_protocol import ProtocolIngestor
from seed_clinical_rules import seed_additional_clinical_rules

class PipelineOrchestrator:
    def __init__(self, db_path='metadata.db', duck_path='analytics.duckdb', output_dir='outputs'):
        self.db_path = db_path
        self.duck_path = duck_path
        self.output_dir = output_dir
        
        self.parser = RuleParser(db_path=self.db_path, output_dir=os.path.join(self.output_dir, "sas_programs"))
        self.adapter = ClinicalDerivationAdapter(
            log_dir=os.path.join(self.output_dir, "logs"),
            dataset_dir=os.path.join(self.output_dir, "datasets")
        )
        self.snapshot_mgr = SnapshotManager(db_path=self.db_path, manifest_dir=os.path.join(self.output_dir, "manifests"))
        self.log_parser = SASLogParser(duck_path=self.duck_path)
        
    def run_pipeline(self, run_id="RUN_IMPOWER150_2026_05"):
        import time
        t_start = time.time()
        
        print("="*80)
        print(f"   STARTING ORCHESTRATED REGULATORY PIPELINE RUN: {run_id}")
        print("="*80)
        
        # 0. Initialize & Seed database if fresh or incomplete
        t0 = time.time()
        db_exists = os.path.exists(self.db_path)
        needs_init = not db_exists
        if db_exists:
            import sqlite3
            try:
                conn = sqlite3.connect(self.db_path)
                conn.execute("PRAGMA foreign_keys = ON;")
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM derivation_rules")
                cnt = cur.fetchone()[0]
                if cnt == 0:
                    needs_init = True
                conn.close()
            except Exception:
                needs_init = True
                
        if needs_init:
            print("\n>>> ORCHESTRATOR: Database fresh/incomplete. Initializing and seeding...")
            if os.path.exists(self.db_path):
                try:
                    os.remove(self.db_path)
                except Exception:
                    pass
            init_database(db_path=self.db_path)
            ingestor = ProtocolIngestor(db_path=self.db_path)
            ingestor.ingest()
            seed_additional_clinical_rules(db_path=self.db_path)
        duration_init = time.time() - t0
            
        # 1. Compile Rules (Semantic Gate inside RuleParser)
        t0 = time.time()
        print("\n>>> ORCHESTRATOR: Compiling derivation rules...")
        compiled_count = self.parser.compile_rules()
        print(f"• Successfully compiled {compiled_count} approved rules.")
        duration_compile = time.time() - t0
        
        # 2. Seed ARM Results (GAP-01 & GAP-05 first-class database entity seeding)
        t0 = time.time()
        print("\n>>> ORCHESTRATOR: Seeding ARM Results and Where Clauses...")
        seed_arm_data(db_path=self.db_path)
        duration_seed = time.time() - t0
        
        # 3. Capture Environment Snapshot (drift detection)
        t0 = time.time()
        print("\n>>> ORCHESTRATOR: Capturing reproducibility snapshot...")
        snapshot_id, manifest_path = self.snapshot_mgr.capture(run_id=run_id)
        print(f"• Registered Snapshot: {snapshot_id}")
        duration_snapshot = time.time() - t0
        
        # 4. Execute Compiled Programs
        t0 = time.time()
        print("\n>>> ORCHESTRATOR: Executing compiled rules...")
        programs_dir = self.parser.output_dir
        sas_programs = sorted([f for f in os.listdir(programs_dir) if f.endswith(".sas")])
        
        for prog in sas_programs:
            prog_path = os.path.join(programs_dir, prog)
            print(f"  Executing program: {prog}")
            exec_result = self.adapter.execute(
                program_path=prog_path,
                inputs=self.db_path,
                outputs=os.path.join(self.output_dir, "datasets"),
                run_id=run_id
            )
            # Parse execution logs
            log_path = exec_result["log_path"]
            self.log_parser.parse_log_file(log_path, run_id)
        duration_execute = time.time() - t0
            
        # 5. Build Knowledge Graph
        t0 = time.time()
        print("\n>>> ORCHESTRATOR: Building semantic lineage graph...")
        graph_builder = SemanticGraphBuilder(db_path=self.db_path)
        graph_builder.build_graph()
        graph_builder.export_to_rdf(os.path.join(self.output_dir, "submission", "lineage_ontology.ttl"))
        duration_graph = time.time() - t0
        
        # 6. Run Conformance & QC Engine
        t0 = time.time()
        print("\n>>> ORCHESTRATOR: Running QC conformance suite...")
        qc_engine = QCEngine(db_path=self.db_path, duck_path=self.duck_path, dataset_dir=os.path.join(self.output_dir, "datasets"))
        qc_engine.run_level1_conformance(run_id=run_id)
        qc_engine.run_level2_oncology_checks(run_id=run_id)
        qc_engine.run_level4_cross_dataset_integrity(run_id=run_id)
        qc_engine.run_level5_controlled_terminology_validation(run_id=run_id)
        explained_count = qc_engine.run_level3_explainable_narratives(run_id=run_id)
        print(f"• Level 3 QC analysis complete: explained {explained_count} findings.")
        duration_qc = time.time() - t0
        
        # 7. Generate Submission package (Define.xml, JSON-LD and HTML sdrg)
        t0 = time.time()
        print("\n>>> ORCHESTRATOR: Compiling submission packages (Define.xml & JSON-LD)...")
        sub_generator = SubmissionGenerator(db_path=self.db_path, output_dir=os.path.join(self.output_dir, "submission"))
        define_xml = sub_generator.generate_define_xml()
        sdrg_jsonld = sub_generator.generate_sdrg_json_ld()
        sdrg_html = sub_generator.generate_sdrg_html()
        duration_submission = time.time() - t0
        
        # 8. Generate ARD (CDISC ARS v1.0 Compliant) and M11 Digital Protocol (H5 & H10)
        t0 = time.time()
        print("\n>>> ORCHESTRATOR: Generating ARD and M11 digital protocol exports...")
        from ard_generator import ARDGenerator
        from m11_protocol_exporter import M11ProtocolExporter
        
        ard_gen = ARDGenerator(
            db_path=self.db_path, 
            dataset_dir=os.path.join(self.output_dir, "datasets"),
            output_dir=os.path.join(self.output_dir, "submission")
        )
        ard_json = ard_gen.generate_ard()
        
        m11_exp = M11ProtocolExporter(
            db_path=self.db_path,
            config_path='study_config.yaml',
            output_dir=os.path.join(self.output_dir, "submission")
        )
        m11_protocol = m11_exp.export_protocol()
        duration_ard_m11 = time.time() - t0
        
        total_duration = time.time() - t_start
        
        print("\n" + "="*80)
        print("   ORCHESTRATED REGULATORY PIPELINE TIMING METRICS (M16)")
        print("-"*80)
        print(f"   Stage 0 (DB Init & Seed):       {duration_init:.4f}s")
        print(f"   Stage 1 (Compile Rules):        {duration_compile:.4f}s")
        print(f"   Stage 2 (Seed ARM Results):      {duration_seed:.4f}s")
        print(f"   Stage 3 (Environment Snapshot):  {duration_snapshot:.4f}s")
        print(f"   Stage 4 (Execute Programs):      {duration_execute:.4f}s")
        print(f"   Stage 5 (Build Lineage Graph):   {duration_graph:.4f}s")
        print(f"   Stage 6 (Run QC Engine):         {duration_qc:.4f}s")
        print(f"   Stage 7 (Compile Submissions):   {duration_submission:.4f}s")
        print(f"   Stage 8 (Generate ARD & M11):    {duration_ard_m11:.4f}s")
        print("-"*80)
        print(f"   Total Execution Time:            {total_duration:.4f}s")
        print("="*80)
        
        return {
            "snapshot_id": snapshot_id,
            "compiled_rules": compiled_count,
            "define_xml": define_xml,
            "sdrg_jsonld": sdrg_jsonld,
            "sdrg_html": sdrg_html,
            "ard_json": ard_json,
            "m11_protocol": m11_protocol
        }

if __name__ == '__main__':
    orchestrator = PipelineOrchestrator()
    orchestrator.run_pipeline()
