import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import DerivationRule, Variable

def seed_additional_clinical_rules(db_path='metadata.db'):
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()

    var_seeds = [
        Variable(variable="AVAL", dataset="ADTTE", role="Analysis Value (Days)", datatype="float", bc_id="OS", origin="Derived from Rand date and death date", controlled_terminology=None),
        Variable(variable="CNSR", dataset="ADTTE", role="Censor Flag", datatype="integer", bc_id="OS", origin="Derived from survival status", controlled_terminology="0 = Event, 1 = Censored"),
        Variable(variable="PARAMCD", dataset="ADTTE", role="Parameter Code", datatype="string", bc_id="PARAMCD", origin="Assigned parameter code", controlled_terminology=None),
        Variable(variable="ORR_FL", dataset="ADRS", role="Objective Response Flag", datatype="string", bc_id="BOR", origin="Derived from Best Overall Response", controlled_terminology="Y = Responder, N = Non-responder"),
        Variable(variable="PARAMCD", dataset="ADRS", role="Parameter Code", datatype="string", bc_id="PARAMCD", origin="Assigned parameter code", controlled_terminology=None),
        Variable(variable="AVAL", dataset="ADDOR", role="Analysis Value (DOR)", datatype="float", bc_id="DOR", origin="Derived based on response timeline", controlled_terminology=None),
        Variable(variable="CNSR", dataset="ADDOR", role="Censor Flag (DOR)", datatype="integer", bc_id="DOR", origin="Derived based on progression post-response", controlled_terminology="0 = Event, 1 = Censored"),
        Variable(variable="PARAMCD", dataset="ADDOR", role="Parameter Code", datatype="string", bc_id="PARAMCD", origin="Assigned parameter code", controlled_terminology=None)
    ]
    
    for v in var_seeds:
        session.merge(v)
        
    # 2. Seed Derivation Rules matching the new M11/SAP endpoints
    rule_seeds = [
        # Overall Survival
        DerivationRule(
            rule_id="RULE_OS_AVAL",
            endpoint_id="EP_OS_WT", # Unified primary OS endpoint
            target_variable="AVAL",
            logic_type="date_diff",
            assessor="INVESTIGATOR",
            criteria_type="RECIST_1.1",
            approval_status="approved",
            logic_definition="Survival time in days, calculated as Death Date (DTHDT) - Randomization Date (RANDDT) + 1."
        ),
        DerivationRule(
            rule_id="RULE_OS_CNSR",
            endpoint_id="EP_OS_WT",
            target_variable="CNSR",
            logic_type="event_flag",
            assessor="INVESTIGATOR",
            criteria_type="RECIST_1.1",
            approval_status="approved",
            logic_definition="Set to 0 if patient died (event); set to 1 if patient is alive/censored (last alive date LSTALVDT)."
        ),
        # Objective Response Rate (ORR)
        DerivationRule(
            rule_id="RULE_ORR_FL",
            endpoint_id="EP_SEC_BOR_1", # Ingested secondary ORR
            target_variable="ORR_FL",
            logic_type="conditional_assign",
            assessor="INVESTIGATOR",
            criteria_type="RECIST_1.1",
            approval_status="approved",
            logic_definition="Set to 'Y' (Responder) if Best Overall Response (BOR) is 'CR' or 'PR'; set to 'N' if BOR is 'SD', 'PD', or 'NE'."
        ),
        # Duration of Response (DOR)
        DerivationRule(
            rule_id="RULE_DOR_AVAL",
            endpoint_id="EP_SEC_DOR_9", # Ingested secondary DOR
            target_variable="AVAL",
            logic_type="date_diff",
            assessor="INVESTIGATOR",
            criteria_type="RECIST_1.1",
            approval_status="approved",
            logic_definition="Time in days from first documented objective response (CR or PR) to progressive disease (PD) or death."
        ),
        # BICR (Blinded Independent Central Review) Parallel Rules
        DerivationRule(
            rule_id="RULE_PFS_AVAL_BICR",
            endpoint_id="EP_PFS_WT",
            target_variable="AVAL",
            logic_type="date_diff",
            assessor="BICR",
            criteria_type="RECIST_1.1",
            approval_status="approved",
            logic_definition="Time from randomization date (RANDDT) to BICR-assessed progression date or death date (whichever is earlier) in days."
        ),
        DerivationRule(
            rule_id="RULE_PFS_CNSR_BICR",
            endpoint_id="EP_PFS_WT",
            target_variable="CNSR",
            logic_type="event_flag",
            assessor="BICR",
            criteria_type="RECIST_1.1",
            approval_status="approved",
            logic_definition="Set to 0 if patient progressed under BICR or died; set to 1 if censored (alive and progression-free at last evaluable BICR response assessment visit)."
        ),
        DerivationRule(
            rule_id="RULE_OS_AVAL_BICR",
            endpoint_id="EP_OS_WT",
            target_variable="AVAL",
            logic_type="date_diff",
            assessor="BICR",
            criteria_type="RECIST_1.1",
            approval_status="approved",
            logic_definition="BICR-assessed survival time in days, calculated as Death Date (DTHDT) - Randomization Date (RANDDT) + 1."
        )
    ]
    
    for r in rule_seeds:
        session.merge(r)
        
    session.commit()
    
    # 3. Explicitly link objectives to endpoints (GAP-02)
    objective_mappings = {
        "OBJ_PFS_WT": "EP_PFS_WT",
        "OBJ_OS_WT": "EP_OS_WT",
        "OBJ_OS_ARMA": "EP_PRM_OS_3",
        "OBJ_ORR": "EP_SEC_BOR_1",
        "OBJ_DOR": "EP_SEC_DOR_9",
        "OBJ_IPFS": "EP_IPFS_ITT"
    }
    
    for obj_id, ep_id in objective_mappings.items():
        session.execute(
            text("UPDATE protocol_objectives SET endpoint_id = :ep_id WHERE obj_id = :obj_id"),
            {"ep_id": ep_id, "obj_id": obj_id}
        )
    session.commit()
    session.close()
    print(f"[seed_clinical_rules] Successfully registered 5 clinical variables, 7 SAP oncology rules, and updated objectives mapping.")

if __name__ == '__main__':
    seed_additional_clinical_rules()
