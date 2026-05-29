import os
import yaml
import json
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime, Float, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

Base = declarative_base()

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# 1. Protocol Objective Table
class ProtocolObjective(Base):
    __tablename__ = 'protocol_objectives'
    
    obj_id = Column(String(50), primary_key=True)
    obj_type = Column(String(20)) # primary, secondary, exploratory
    obj_text = Column(Text, nullable=False)
    m11_section = Column(String(50))
    endpoint_id = Column(String(50), ForeignKey('endpoint_definitions.endpoint_id'))

# 2. Biomedical Concept Table
class BiomedicalConcept(Base):
    __tablename__ = 'biomedical_concepts'
    
    bc_id = Column(String(50), primary_key=True) # e.g. OS, PFS, TEAE
    bc_name = Column(String(100), nullable=False)
    bc_category = Column(String(50)) # finding, event, intervention, disposition, special_purpose
    cosmos_bc_id = Column(String(100)) # link to COSMoS
    sdtmig_class = Column(String(50))
    coding_system = Column(String(100))
    bc_definition = Column(Text)

# 3. Endpoint Definition Table
class EndpointDefinition(Base):
    __tablename__ = 'endpoint_definitions'
    
    endpoint_id = Column(String(50), primary_key=True)
    bc_id = Column(String(50), ForeignKey('biomedical_concepts.bc_id'))
    estimand_id = Column(String(50), ForeignKey('estimands.estimand_id'))
    endpoint_type = Column(String(20)) # primary, secondary, exploratory, safety
    analysis_concept = Column(String(50)) # e.g. OS, PFS, iRECIST_BOR
    sap_reference = Column(String(100))
    criteria_type = Column(String(50)) # RECIST_1.1, iRECIST, both

# 4. Estimand Table
class Estimand(Base):
    __tablename__ = 'estimands'
    
    estimand_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    ice_strategy = Column(Text) # intercurrent event strategy
    target_population = Column(Text)
    variable_of_interest = Column(Text)
    summary_measure = Column(Text)

# 5. Derivation Rule Table
class DerivationRule(Base):
    __tablename__ = 'derivation_rules'
    
    rule_id = Column(String(50), primary_key=True)
    endpoint_id = Column(String(50), ForeignKey('endpoint_definitions.endpoint_id'))
    target_variable = Column(String(50), nullable=False)
    logic_type = Column(String(50), nullable=False) # subtraction, event_flag, date_diff, conditional_assign, iupd_confirmation
    assessor = Column(String(20)) # INVESTIGATOR, BICR, both
    criteria_type = Column(String(50)) # RECIST_1.1, iRECIST, both
    approval_status = Column(String(20), default='pending') # pending, approved, rejected
    logic_definition = Column(Text) # code implementation logic description or pseudo-code

# 6. Variable Table
class Variable(Base):
    __tablename__ = 'variables'
    
    variable = Column(String(50), primary_key=True)
    dataset = Column(String(50), primary_key=True)
    role = Column(String(50))
    datatype = Column(String(20))
    bc_id = Column(String(50), ForeignKey('biomedical_concepts.bc_id'))
    origin = Column(String(100))
    controlled_terminology = Column(Text)

# 7. Analysis Result Table (ARM Core)
class AnalysisResult(Base):
    __tablename__ = 'analysis_results'
    
    analysis_id = Column(String(50), primary_key=True)
    endpoint_id = Column(String(50), ForeignKey('endpoint_definitions.endpoint_id'))
    dataset = Column(String(50))
    paramcd = Column(String(8))
    where_clause_id = Column(String(50), ForeignKey('where_clauses.where_clause_id'))
    stat_method = Column(String(100))
    stat_test = Column(String(100))
    tfl_reference = Column(String(50))
    estimand_id = Column(String(50), ForeignKey('estimands.estimand_id'))
    arm_display_label = Column(String(100))

# 8. Where Clause Table
class WhereClause(Base):
    __tablename__ = 'where_clauses'
    
    where_clause_id = Column(String(50), primary_key=True)
    dataset = Column(String(50))
    variable = Column(String(50))
    filter_operator = Column(String(10)) # EQ, NE, IN, etc.
    filter_value = Column(Text)

# 9. Execution Snapshot Table
class ExecutionSnapshot(Base):
    __tablename__ = 'execution_snapshots'
    
    snapshot_id = Column(String(50), primary_key=True)
    run_id = Column(String(50))
    sdtmig_version = Column(String(20))
    adamig_version = Column(String(20))
    python_version = Column(String(20))
    sas_version = Column(String(20))
    rule_hash_manifest = Column(Text) # JSON field
    metadata_db_hash = Column(String(64))
    environment_hash = Column(String(64))
    created_ts = Column(DateTime, default=datetime.datetime.now)

# 10. Program Table
class Program(Base):
    __tablename__ = 'programs'
    
    program_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    generated_path = Column(Text)
    sha256_hash = Column(String(64))
    compiled_ts = Column(DateTime, default=datetime.datetime.now)

# 11. Pending Queue Table
class PendingQueue(Base):
    __tablename__ = 'pending_queue'
    
    queue_id = Column(Integer, primary_key=True, autoincrement=True)
    action_type = Column(String(50))
    payload = Column(Text) # JSON string
    status = Column(String(20), default='pending') # pending, processed, error
    created_ts = Column(DateTime, default=datetime.datetime.now)

# 12. AI Action Table (Audit Trail)
class AIAction(Base):
    __tablename__ = 'ai_actions'
    
    action_id = Column(String(50), primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.now)
    model_version = Column(String(50))
    prompt_hash = Column(String(64))
    input_hash = Column(String(64))
    output_hash = Column(String(64))
    confidence_composite = Column(Float)
    confidence_signals = Column(Text) # JSON field
    human_decision = Column(String(20)) # approved, rejected, edited
    human_id = Column(String(50))
    decision_ts = Column(DateTime)
    rejection_reason = Column(Text)
    endpoint_id_proposed = Column(String(50))
    endpoint_id_approved = Column(String(50))


def init_database(db_path='metadata.db', config_path='study_config.yaml'):
    """Initializes the SQLite database and seeds default data from study_config.yaml"""
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print(f"[Database] SQLite DB initialized at {db_path}")
    
    # 1. Seed Biomedical Concepts (COSMoS Aligned Root Clinical Meanings)
    bc_seeds = [
        BiomedicalConcept(
            bc_id="OS", 
            bc_name="Overall Survival", 
            bc_category="event", 
            cosmos_bc_id="C82515", # NCI Thesaurus Concept OS
            sdtmig_class="EVENTS", 
            coding_system="NCI Thesaurus",
            bc_definition="The length of time from the start of treatment or diagnosis that a patient remains alive."
        ),
        BiomedicalConcept(
            bc_id="PFS", 
            bc_name="Progression-Free Survival", 
            bc_category="event", 
            cosmos_bc_id="C9343", 
            sdtmig_class="EVENTS", 
            coding_system="NCI Thesaurus",
            bc_definition="The length of time during and after treatment that a patient lives with the disease but it does not get worse (RECIST 1.1 based)."
        ),
        BiomedicalConcept(
            bc_id="iPFS", 
            bc_name="immune Progression-Free Survival", 
            bc_category="event", 
            cosmos_bc_id="C128362", 
            sdtmig_class="EVENTS", 
            coding_system="NCI Thesaurus",
            bc_definition="The length of time during and after immunotherapy treatment that a patient lives with the disease but it does not get worse (iRECIST based, confirmed progression required)."
        ),
        BiomedicalConcept(
            bc_id="BOR", 
            bc_name="Best Overall Response", 
            bc_category="finding", 
            cosmos_bc_id="C101284", 
            sdtmig_class="FINDINGS", 
            coding_system="NCI Thesaurus",
            bc_definition="The best response recorded from the start of treatment until disease progression or recurrence (RECIST 1.1 CR, PR, SD, PD)."
        ),
        BiomedicalConcept(
            bc_id="DOR", 
            bc_name="Duration of Response", 
            bc_category="event", 
            cosmos_bc_id="C9342", 
            sdtmig_class="EVENTS", 
            coding_system="NCI Thesaurus",
            bc_definition="The time from the first documented complete or partial response until progressive disease or death."
        ),
        BiomedicalConcept(
            bc_id="ORR", 
            bc_name="Objective Response Rate", 
            bc_category="finding", 
            cosmos_bc_id="C96538", 
            sdtmig_class="FINDINGS", 
            coding_system="NCI Thesaurus",
            bc_definition="The percentage of patients who experience a complete or partial response to therapy (RECIST 1.1 based)."
        ),
        BiomedicalConcept(
            bc_id="PARAMCD", 
            bc_name="Parameter Code", 
            bc_category="special_purpose", 
            cosmos_bc_id="C43582", 
            sdtmig_class="SPECIAL PURPOSE", 
            coding_system="NCI Thesaurus",
            bc_definition="A unique short code representation of the parameter being evaluated (e.g. PFS, OS, iPFS)."
        )
    ]
    
    # Check if seeds already exist to prevent duplicates
    if session.query(BiomedicalConcept).count() == 0:
        session.bulk_save_objects(bc_seeds)
        session.commit()
        print("[Database] Seeded 5 COSMoS Biomedical Concepts.")
        
    # Read study_config.yaml for M11 Protocol Seeds
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            cfg = yaml.safe_load(f)
            
        # Seed Estimands
        if 'm11_protocol' in cfg and 'estimands' in cfg['m11_protocol']:
            for est in cfg['m11_protocol']['estimands']:
                if session.query(Estimand).filter_by(estimand_id=est['estimand_id']).count() == 0:
                    db_est = Estimand(
                        estimand_id=est['estimand_id'],
                        name=est['name'],
                        ice_strategy=est['ice_strategy'],
                        target_population=est['target_population'],
                        variable_of_interest=est['variable_of_interest'],
                        summary_measure=est['summary_measure']
                    )
                    session.add(db_est)
            session.commit()
            print(f"[Database] Seeded Estimands from {config_path}.")

        # Seed Endpoints (linking Biomedical Concepts and Estimands)
        endpoint_seeds = [
            EndpointDefinition(
                endpoint_id="EP_PFS_WT",
                bc_id="PFS",
                estimand_id="EST_PFS_WT",
                endpoint_type="primary",
                analysis_concept="PFS",
                sap_reference="SAP 6.1.1",
                criteria_type="RECIST_1.1"
            ),
            EndpointDefinition(
                endpoint_id="EP_OS_WT",
                bc_id="OS",
                estimand_id="EST_OS_WT",
                endpoint_type="primary",
                analysis_concept="OS",
                sap_reference="SAP 6.1.2",
                criteria_type="both"
            ),
            EndpointDefinition(
                endpoint_id="EP_IPFS_ITT",
                bc_id="iPFS",
                estimand_id="EST_IPFS_ITT",
                endpoint_type="exploratory",
                analysis_concept="iPFS",
                sap_reference="SAP 6.3.1",
                criteria_type="iRECIST"
            ),
            EndpointDefinition(
                endpoint_id="EP_PRM_OS_3",
                bc_id="OS",
                estimand_id="EST_OS_WT",
                endpoint_type="primary",
                analysis_concept="OS",
                sap_reference="SAP 6.1.3",
                criteria_type="both"
            ),
            EndpointDefinition(
                endpoint_id="EP_SEC_BOR_1",
                bc_id="BOR",
                estimand_id="EST_OS_WT",
                endpoint_type="secondary",
                analysis_concept="BOR",
                sap_reference="SAP 6.2.1",
                criteria_type="RECIST_1.1"
            ),
            EndpointDefinition(
                endpoint_id="EP_SEC_DOR_9",
                bc_id="DOR",
                estimand_id="EST_OS_WT",
                endpoint_type="secondary",
                analysis_concept="DOR",
                sap_reference="SAP 6.2.9",
                criteria_type="RECIST_1.1"
            )
        ]
        for ep in endpoint_seeds:
            if session.query(EndpointDefinition).filter_by(endpoint_id=ep.endpoint_id).count() == 0:
                session.add(ep)
        session.commit()
        print("[Database] Seeded Endpoint Definitions (BC-to-Estimand bridges).")

        # Seed Protocol Objectives
        if 'm11_protocol' in cfg and 'objectives' in cfg['m11_protocol']:
            for obj in cfg['m11_protocol']['objectives']:
                if session.query(ProtocolObjective).filter_by(obj_id=obj['obj_id']).count() == 0:
                    # Assign corresponding endpoints based on ID keywords
                    mapped_ep = None
                    if "PFS_WT" in obj['obj_id']:
                        mapped_ep = "EP_PFS_WT"
                    elif "OS_WT" in obj['obj_id']:
                        mapped_ep = "EP_OS_WT"
                    elif "IPFS" in obj['obj_id']:
                        mapped_ep = "EP_IPFS_ITT"
                    elif "OS_ARMA" in obj['obj_id']:
                        mapped_ep = "EP_PRM_OS_3"
                    elif "ORR" in obj['obj_id']:
                        mapped_ep = "EP_SEC_BOR_1"
                    elif "DOR" in obj['obj_id']:
                        mapped_ep = "EP_SEC_DOR_9"
                        
                    db_obj = ProtocolObjective(
                        obj_id=obj['obj_id'],
                        obj_type=obj['type'],
                        obj_text=obj['text'],
                        m11_section=obj['m11_section'],
                        endpoint_id=mapped_ep
                    )
                    session.add(db_obj)
            session.commit()
            print(f"[Database] Seeded Protocol Objectives from {config_path}.")
            
        # Seed Variables (realizations of concepts)
        var_seeds = [
            Variable(variable="AVAL", dataset="ADSL", role="Analysis Value", datatype="float", bc_id="OS", origin="Derived from Rand date and death date", controlled_terminology=None),
            Variable(variable="CNSR", dataset="ADSL", role="Censor Flag", datatype="integer", bc_id="OS", origin="Derived from survival status", controlled_terminology="0 = Event, 1 = Censored"),
            Variable(variable="AVAL", dataset="ADTTE", role="Analysis Value (Days)", datatype="float", bc_id="PFS", origin="Derived", controlled_terminology=None),
            Variable(variable="CNSR", dataset="ADTTE", role="Censor Flag", datatype="integer", bc_id="PFS", origin="Derived based on SAP criteria", controlled_terminology="0 = Event, 1 = Censored"),
            Variable(variable="PARAMCD", dataset="ADTTE", role="Parameter Code", datatype="string", bc_id="PARAMCD", origin="Predefined", controlled_terminology="PFS, OS, iPFS"),
            Variable(variable="RSORRES", dataset="RS", role="Response Result", datatype="string", bc_id="BOR", origin="Investigator Assessment", controlled_terminology="CR, PR, SD, PD, NE")
        ]
        for v in var_seeds:
            if session.query(Variable).filter_by(variable=v.variable, dataset=v.dataset).count() == 0:
                session.add(v)
            
        # Seed Derivation Rules (rules implementing the endpoints)
        rule_seeds = [
            DerivationRule(
                rule_id="RULE_PFS_AVAL",
                endpoint_id="EP_PFS_WT",
                target_variable="AVAL",
                logic_type="date_diff",
                assessor="INVESTIGATOR",
                criteria_type="RECIST_1.1",
                approval_status="approved",
                logic_definition="Time from randomization date (RANDDT) to Investigator-assessed progression date or death date (whichever is earlier) in days."
            ),
            DerivationRule(
                rule_id="RULE_PFS_CNSR",
                endpoint_id="EP_PFS_WT",
                target_variable="CNSR",
                logic_type="event_flag",
                assessor="INVESTIGATOR",
                criteria_type="RECIST_1.1",
                approval_status="approved",
                logic_definition="Set to 0 if patient progressed or died; set to 1 if censored (alive and progression-free at last evaluable response assessment visit)."
            ),
            DerivationRule(
                rule_id="RULE_IPFS_AVAL",
                endpoint_id="EP_IPFS_ITT",
                target_variable="AVAL",
                logic_type="iupd_confirmation",
                assessor="INVESTIGATOR",
                criteria_type="iRECIST",
                approval_status="approved",
                logic_definition="Time from randomization to confirmed iPD (unconfirmed progression iUPD followed by confirmation scan >= 28 days later) or death."
            )
        ]
        for r in rule_seeds:
            if session.query(DerivationRule).filter_by(rule_id=r.rule_id).count() == 0:
                session.add(r)
                
        session.commit()
        print("[Database] Seeded default Derivation Rules and Variables successfully.")

    session.close()

if __name__ == '__main__':
    # Auto-initialize when run directly
    init_database()
