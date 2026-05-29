import os
import hashlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import DerivationRule, EndpointDefinition, Estimand, Program

class RuleParser:
    def __init__(self, db_path='metadata.db', template_dir='sas/templates', output_dir='sas/programs'):
        self.db_path = db_path
        self.template_dir = template_dir
        self.output_dir = output_dir
        
        # Connect to DB
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.Session = sessionmaker(bind=self.engine)
        
        # Ensure directories exist
        os.makedirs(self.output_dir, exist_ok=True)

    def compile_rules(self):
        """Processes rules in the database and compiles them into executable SAS programs."""
        session = self.Session()
        
        # Load rules
        rules = session.query(DerivationRule).filter_by(approval_status='approved').all()
        print(f"[RuleParser] Found {len(rules)} approved rules for compilation.")
        
        compiled_count = 0
        
        for rule in rules:
            # ─── SEMANTIC GATE ────────────────────────────────────────────────
            # Load corresponding endpoint
            endpoint = session.query(EndpointDefinition).filter_by(endpoint_id=rule.endpoint_id).first()
            if not endpoint:
                print(f"[RuleParser] [BLOCK] Rule {rule.rule_id} blocked: Endpoint {rule.endpoint_id} not found in database.")
                continue
                
            # Verify Estimand is linked
            if not endpoint.estimand_id:
                print(f"[RuleParser] [BLOCK] Rule {rule.rule_id} blocked: Estimand is missing in endpoint {endpoint.endpoint_id}.")
                continue
                
            estimand = session.query(Estimand).filter_by(estimand_id=endpoint.estimand_id).first()
            if not estimand:
                print(f"[RuleParser] [BLOCK] Rule {rule.rule_id} blocked: Estimand {endpoint.estimand_id} not found in database.")
                continue
            
            # If the gate is passed, compile the rule!
            print(f"[RuleParser] [GATE PASSED] Rule {rule.rule_id} is fully verified. Endpoint: {endpoint.endpoint_id}, Estimand: {estimand.estimand_id}.")
            
            # Map logic to templates
            program_code = self._generate_sas_code(rule, endpoint)
            if not program_code:
                print(f"[RuleParser] Logic type '{rule.logic_type}' is currently not supported for compilation.")
                continue
                
            # Write SAS file
            filename = f"derive_{rule.rule_id.lower()}.sas"
            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, 'w') as f:
                f.write(program_code)
                
            # Compute hash
            code_hash = hashlib.sha256(program_code.encode('utf-8')).hexdigest()
            
            # Register in Programs table
            db_prog = session.query(Program).filter_by(program_id=f"PROG_{rule.rule_id}").first()
            if db_prog:
                db_prog.generated_path = filepath
                db_prog.sha256_hash = code_hash
            else:
                db_prog = Program(
                    program_id=f"PROG_{rule.rule_id}",
                    name=filename,
                    generated_path=filepath,
                    sha256_hash=code_hash
                )
                session.add(db_prog)
                
            compiled_count += 1
            print(f"[RuleParser] Compiled SAS file: {filepath} (SHA256: {code_hash[:10]}...)")
            
        session.commit()
        session.close()
        print(f"[RuleParser] Compilation completed. Successfully compiled {compiled_count} rules.")
        return compiled_count

    def _generate_sas_code(self, rule, endpoint):
        """Translates rule parameters to completed SAS template code blocks."""
        code_block = ""
        
        # Load helper macros
        date_diff_path = os.path.abspath(os.path.join(self.template_dir, 'derive_date_diff.sas'))
        event_flag_path = os.path.abspath(os.path.join(self.template_dir, 'derive_event_flag.sas'))
        iupd_flag_path = os.path.abspath(os.path.join(self.template_dir, 'derive_iupd_flag.sas'))
        conditional_path = os.path.abspath(os.path.join(self.template_dir, 'derive_conditional.sas'))
        
        # Add headers
        code_block += f"/* =====================================================================\n"
        code_block += f"   GENERATED PROGRAM FOR DERIVATION RULE: {rule.rule_id}\n"
        code_block += f"   TARGET VARIABLE: {rule.target_variable}\n"
        code_block += f"   CLINICAL ENDPOINT: {endpoint.endpoint_id} ({endpoint.analysis_concept})\n"
        code_block += f"   ESTIMAND: {endpoint.estimand_id}\n"
        code_block += f"   RECIST CRITERIA: {rule.criteria_type} | ASSESSOR: {rule.assessor}\n"
        code_block += f"   ===================================================================== */\n\n"
        
        if rule.logic_type == 'date_diff':
            code_block += f'%include "{date_diff_path}";\n\n'
            if endpoint.analysis_concept == 'PFS':
                if rule.assessor == 'BICR':
                    code_block += f"%derive_date_diff(outds=work.out_pfs_bicr, inds=work.raw_data, targetvar={rule.target_variable}, startvar=RANDDT, endvar=PFSDT_BICR);\n"
                else:
                    code_block += f"%derive_date_diff(outds=work.out_pfs, inds=work.raw_data, targetvar={rule.target_variable}, startvar=RANDDT, endvar=PFSDT);\n"
            elif endpoint.analysis_concept == 'OS':
                if rule.assessor == 'BICR':
                    code_block += f"%derive_date_diff(outds=work.out_os_bicr, inds=work.raw_data, targetvar={rule.target_variable}, startvar=RANDDT, endvar=DTHDT_BICR);\n"
                else:
                    code_block += f"%derive_date_diff(outds=work.out_os, inds=work.raw_data, targetvar={rule.target_variable}, startvar=RANDDT, endvar=DTHDT);\n"
            elif endpoint.analysis_concept == 'DOR':
                code_block += f"%derive_date_diff(outds=work.out_dor, inds=work.raw_data, targetvar={rule.target_variable}, startvar=RSPDT, endvar=%str(min(PDDT, DTHDT)));\n"
            else:
                code_block += f"%derive_date_diff(outds=work.out_generic, inds=work.raw_data, targetvar={rule.target_variable}, startvar=RANDDT, endvar=DTHDT);\n"
                
        elif rule.logic_type == 'event_flag':
            code_block += f'%include "{event_flag_path}";\n\n'
            if endpoint.analysis_concept == 'PFS':
                if rule.assessor == 'BICR':
                    code_block += f"%derive_event_flag(outds=work.out_pfs_cnsr_bicr, inds=work.raw_data, targetvar={rule.target_variable}, datevar=PFSDT_BICR, censorvar=LSTALVDT_BICR, pdvar=PDDT_BICR, deathvar=DTHDT);\n"
                else:
                    code_block += f"%derive_event_flag(outds=work.out_pfs_cnsr, inds=work.raw_data, targetvar={rule.target_variable}, datevar=PFSDT, censorvar=LSTALVDT, pdvar=PDDT, deathvar=DTHDT);\n"
            else:
                code_block += f"%derive_event_flag(outds=work.out_os_cnsr, inds=work.raw_data, targetvar={rule.target_variable}, datevar=OSDT, censorvar=LSTALVDT, pdvar=., deathvar=DTHDT);\n"
                
        elif rule.logic_type == 'iupd_confirmation':
            # Align logic type compilation to derive actual AVAL progression-free days under iRECIST
            code_block += f'%include "{date_diff_path}";\n\n'
            code_block += f"%derive_date_diff(outds=work.out_ipfs, inds=work.raw_data, targetvar={rule.target_variable}, startvar=RANDDT, endvar=iPFSDT);\n"
            
        elif rule.logic_type == 'conditional_assign':
            code_block += f'%include "{conditional_path}";\n\n'
            code_block += f"%derive_conditional(outds=work.out_orr, inds=work.raw_data, targetvar={rule.target_variable}, condvar=rsorres, condvals=%str('CR', 'PR'), trueval='Y', falseval='N');\n"
            
        else:
            return None
            
        return code_block

if __name__ == '__main__':
    parser = RuleParser()
    parser.compile_rules()
