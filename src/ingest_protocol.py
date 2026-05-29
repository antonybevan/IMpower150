import os
import json
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import ProtocolObjective, EndpointDefinition, Estimand, BiomedicalConcept

class ProtocolIngestor:
    def __init__(self, json_path=None, db_path='metadata.db'):
        # Resolve NCT JSON: check references/ first, then current dir
        if json_path is None:
            _here = os.path.dirname(os.path.abspath(__file__))
            _root = os.path.join(_here, '..')
            candidates = [
                os.path.join(_root, 'references', 'NCT02366143_ClinicalTrials.json'),
                os.path.join(_root, 'NCT02366143.json'),
                'NCT02366143.json',
            ]
            json_path = next((p for p in candidates if os.path.exists(p)), candidates[0])
        self.json_path = json_path
        self.db_path = db_path
        
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.Session = sessionmaker(bind=self.engine)

    def ingest(self):
        """Parses the ClinicalTrials.gov NCT02366143.json file and populates M11 trial objectives and endpoints."""
        if not os.path.exists(self.json_path):
            print(f"[ProtocolIngestor] Error: Registry file {self.json_path} not found.")
            return False
            
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        protocol = data.get("protocolSection", {})
        id_module = protocol.get("identificationModule", {})
        outcomes_module = protocol.get("outcomesModule", {})
        
        study_id = id_module.get("nctId", "N/A")
        brief_title = id_module.get("briefTitle", "N/A")
        official_title = id_module.get("officialTitle", "N/A")
        
        print("="*80)
        print(f"[ProtocolIngestor] Ingesting registry entry for Study OID: {study_id}")
        print(f"• Title: {brief_title}")
        print("="*80)
        
        session = self.Session()
        
        # 1. Parse Primary Outcomes (Primary M11 Objectives)
        primary_outcomes = outcomes_module.get("primaryOutcomes", [])
        print(f"\n[ProtocolIngestor] Parsing {len(primary_outcomes)} primary outcomes...")
        
        for i, out in enumerate(primary_outcomes, start=1):
            measure = out.get("measure", "")
            desc = out.get("description", "")
            time_frame = out.get("timeFrame", "")
            
            # Fuzzy match to COSMoS Biomedical Concepts
            bc_id = "PFS"
            if "overall survival" in measure.lower() or "os" in measure.lower():
                bc_id = "OS"
                
            obj_id = f"OBJ_PRM_{bc_id}_{i}"
            endpoint_id = f"EP_PRM_{bc_id}_{i}"
            estimand_id = f"EST_PFS_WT" if bc_id == "PFS" else "EST_OS_WT"
            
            # Ensure Endpoint Definition exists
            ep = session.query(EndpointDefinition).filter_by(endpoint_id=endpoint_id).first()
            if not ep:
                ep = EndpointDefinition(
                    endpoint_id=endpoint_id,
                    bc_id=bc_id,
                    estimand_id=estimand_id,
                    endpoint_type="primary",
                    analysis_concept=bc_id,
                    sap_reference=f"SAP Section 6.1.{i}",
                    criteria_type="RECIST_1.1"
                )
                session.add(ep)
                
            # Create Protocol Objective
            obj = session.query(ProtocolObjective).filter_by(obj_id=obj_id).first()
            if not obj:
                obj = ProtocolObjective(
                    obj_id=obj_id,
                    obj_type="primary",
                    obj_text=f"{measure}. {desc} (Timeline: {time_frame})",
                    m11_section="Section 3.1",
                    endpoint_id=endpoint_id
                )
                session.add(obj)
                print(f"• Ingested Primary Objective: {obj_id} -> Endpoint: {endpoint_id} [{bc_id}]")
                
        # 2. Parse Secondary Outcomes (Secondary Objectives & Endpoints)
        secondary_outcomes = outcomes_module.get("secondaryOutcomes", [])
        print(f"\n[ProtocolIngestor] Parsing {len(secondary_outcomes)} secondary outcomes...")
        
        # Limit to key secondary oncology outcomes (DOR, ORR, PK) to keep schema clean
        key_index = 1
        for out in secondary_outcomes:
            measure = out.get("measure", "")
            desc = out.get("description", "")
            time_frame = out.get("timeFrame", "")
            
            bc_id = None
            if "duration of response" in measure.lower() or "dor" in measure.lower():
                bc_id = "DOR"
            elif "objective response" in measure.lower() or "orr" in measure.lower() or "best overall response" in measure.lower() or "bor" in measure.lower():
                bc_id = "BOR"
            elif "overall survival" in measure.lower() or "os" in measure.lower():
                bc_id = "OS"
                
            if bc_id:
                obj_id = f"OBJ_SEC_{bc_id}_{key_index}"
                endpoint_id = f"EP_SEC_{bc_id}_{key_index}"
                estimand_id = "EST_OS_WT" # Fallback estimand linkage
                
                ep = session.query(EndpointDefinition).filter_by(endpoint_id=endpoint_id).first()
                if not ep:
                    ep = EndpointDefinition(
                        endpoint_id=endpoint_id,
                        bc_id=bc_id,
                        estimand_id=estimand_id,
                        endpoint_type="secondary",
                        analysis_concept=bc_id,
                        sap_reference=f"SAP Section 6.2.{key_index}",
                        criteria_type="RECIST_1.1"
                    )
                    session.add(ep)
                    
                obj = session.query(ProtocolObjective).filter_by(obj_id=obj_id).first()
                if not obj:
                    obj = ProtocolObjective(
                        obj_id=obj_id,
                        obj_type="secondary",
                        obj_text=f"{measure}. {desc} (Timeline: {time_frame})",
                        m11_section="Section 3.2",
                        endpoint_id=endpoint_id
                    )
                    session.add(obj)
                    print(f"• Ingested Secondary Objective: {obj_id} -> Endpoint: {endpoint_id} [{bc_id}]")
                key_index += 1
                
        session.commit()
        session.close()
        print("\n[ProtocolIngestor] Ingestion completed successfully.")
        return True

if __name__ == '__main__':
    ingestor = ProtocolIngestor()
    ingestor.ingest()
