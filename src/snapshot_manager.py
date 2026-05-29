import os
import sys
import json
import hashlib
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import ExecutionSnapshot, DerivationRule

class SnapshotManager:
    def __init__(self, db_path='metadata.db', manifest_dir='outputs/manifests'):
        self.db_path = db_path
        self.manifest_dir = manifest_dir
        
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.Session = sessionmaker(bind=self.engine)
        
        os.makedirs(self.manifest_dir, exist_ok=True)

    def capture(self, run_id):
        """Captures the exact runtime metadata and generates execution snapshot records."""
        session = self.Session()
        
        # 1. Fetch all active derivation rules and compute rule_hash_manifest
        active_rules = session.query(DerivationRule).filter_by(approval_status='approved').all()
        rule_manifest_list = []
        for rule in active_rules:
            # Create a unique logic hash for each rule
            logic_str = f"{rule.rule_id}:{rule.logic_type}:{rule.target_variable}:{rule.logic_definition}"
            rule_hash = hashlib.sha256(logic_str.encode('utf-8')).hexdigest()
            rule_manifest_list.append({
                "rule_id": rule.rule_id,
                "target_variable": rule.target_variable,
                "logic_type": rule.logic_type,
                "rule_logic_hash": rule_hash
            })
            
        rule_manifest_json = json.dumps(rule_manifest_list, sort_keys=True)
        
        # 2. Get hash of metadata.db itself
        db_hash = "N/A"
        if os.path.exists(self.db_path):
            with open(self.db_path, 'rb') as f:
                db_hash = hashlib.sha256(f.read()).hexdigest()
                
        # 3. Create environment_manifest.json
        def get_package_version(pkg_name):
            try:
                import importlib.metadata
                return importlib.metadata.version(pkg_name)
            except Exception:
                try:
                    import pkg_resources
                    return pkg_resources.get_distribution(pkg_name).version
                except Exception:
                    return "unknown"

        env_manifest = {
            "python_version": sys.version.split()[0],
            "os": os.name,
            "sas_version": "9.4 M7 (ClinicalDerivationAdapter)",
            "execution_ts": datetime.datetime.now().isoformat(),
            "metadata_db_hash": db_hash,
            "rule_hash_manifest": rule_manifest_list,
            "python_packages": {
                "sqlalchemy": get_package_version("sqlalchemy"),
                "pandas": get_package_version("pandas"),
                "networkx": get_package_version("networkx"),
                "duckdb": get_package_version("duckdb")
            }
        }
        
        manifest_filename = f"env_manifest_{run_id}.json"
        manifest_path = os.path.join(self.manifest_dir, manifest_filename)
        with open(manifest_path, 'w') as f:
            json.dump(env_manifest, f, indent=4)
            
        env_hash = hashlib.sha256(json.dumps(env_manifest, sort_keys=True).encode('utf-8')).hexdigest()
        
        # 4. Write to SQLite execution_snapshots table
        snapshot_id = f"SNAP_{run_id}"
        snapshot = ExecutionSnapshot(
            snapshot_id=snapshot_id,
            run_id=run_id,
            sdtmig_version="3.4",
            adamig_version="1.3",
            python_version=sys.version.split()[0],
            sas_version="9.4 M7 (ClinicalDerivationAdapter)",
            rule_hash_manifest=rule_manifest_json,
            metadata_db_hash=db_hash,
            environment_hash=env_hash
        )
        
        session.merge(snapshot)
        session.commit()
        session.close()
        
        print(f"[SnapshotManager] Snapshot {snapshot_id} captured. Environment manifest saved: {manifest_path}")
        return snapshot_id, manifest_path
        
if __name__ == '__main__':
    mgr = SnapshotManager()
    mgr.capture("RUN_INIT_TEST")
