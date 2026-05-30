"""
ICH M11 Compliant Digital Protocol Exporter
Produces a structured, machine-readable JSON protocol export
conforming to the ICH M11 Technical Specification.
"""
import os
import yaml
import json
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import ProtocolObjective, EndpointDefinition, Estimand

class M11ProtocolExporter:
    """Exports structured study metadata to ICH M11 Technical Specification compliant JSON."""
    
    def __init__(self, db_path='metadata.db', config_path='study_config.yaml', output_dir='outputs/submission'):
        self.db_path = db_path
        self.config_path = config_path
        self.output_dir = output_dir
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.Session = sessionmaker(bind=self.engine)
        os.makedirs(self.output_dir, exist_ok=True)

    def export_protocol(self):
        """Generates an ICH M11 compliant digital protocol JSON file."""
        session = self.Session()
        
        # 1. Load config metadata
        study_id = "UNKNOWN"
        acronym = "UNKNOWN"
        sponsor = "UNKNOWN"
        indication = "UNKNOWN"
        protocol_version = "1.0"
        soa_visits = []
        soa_assessments = []
        
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                cfg = yaml.safe_load(f)
            study_id = cfg.get("study_id", study_id)
            acronym = cfg.get("acronym", acronym)
            sponsor = cfg.get("sponsor", sponsor)
            indication = cfg.get("indication", indication)
            protocol_version = cfg.get("protocol_version", protocol_version)
            
            m11_sec = cfg.get("m11_protocol", {})
            soa = m11_sec.get("schedule_of_activities", {})
            soa_visits = soa.get("visits", [])
            soa_assessments = soa.get("assessments", [])

        # 2. Query Objectives from DB
        db_objectives = session.query(ProtocolObjective).all()
        objectives_list = []
        for obj in db_objectives:
            objectives_list.append({
                "objectiveId": obj.obj_id,
                "type": obj.obj_type,
                "text": obj.obj_text,
                "section": obj.m11_section,
                "linkedEndpointId": obj.endpoint_id
            })

        # 3. Query Endpoints from DB
        db_endpoints = session.query(EndpointDefinition).all()
        endpoints_list = []
        for ep in db_endpoints:
            endpoints_list.append({
                "endpointId": ep.endpoint_id,
                "type": ep.endpoint_type,
                "analysisConcept": ep.analysis_concept,
                "criteriaType": ep.criteria_type,
                "sapReference": ep.sap_reference,
                "linkedBiomedicalConceptId": ep.bc_id,
                "linkedEstimandId": ep.estimand_id
            })

        # 4. Query Estimands from DB
        db_estimands = session.query(Estimand).all()
        estimands_list = []
        for est in db_estimands:
            estimands_list.append({
                "estimandId": est.estimand_id,
                "name": est.name,
                "targetPopulation": est.target_population,
                "variableOfInterest": est.variable_of_interest,
                "intercurrentEventStrategy": est.ice_strategy,
                "summaryMeasure": est.summary_measure
            })

        # 5. Build M11 digital protocol schema
        m11_protocol = {
            "m11ProtocolJSONVersion": "1.0.0",
            "metadata": {
                "exportedAt": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "originator": sponsor,
                "conformance": "ICH M11 CeSHarP Digital Protocol Specification v1.0"
            },
            "studyIdentification": {
                "studyID": study_id,
                "acronym": acronym,
                "sponsorName": sponsor,
                "therapeuticIndication": indication,
                "protocolVersion": protocol_version
            },
            "protocolStructure": {
                "objectives": objectives_list,
                "endpoints": endpoints_list,
                "estimands": estimands_list,
                "scheduleOfActivities": {
                    "visits": soa_visits,
                    "assessments": soa_assessments
                }
            }
        }

        output_path = os.path.join(self.output_dir, "m11_protocol.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(m11_protocol, f, indent=4)

        session.close()
        print(f"[M11ProtocolExporter] Successfully exported M11 digital protocol: {output_path}")
        return output_path

if __name__ == '__main__':
    exporter = M11ProtocolExporter()
    exporter.export_protocol()
