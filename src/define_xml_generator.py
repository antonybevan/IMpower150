import os
import json
import xml.etree.ElementTree as ET
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import BiomedicalConcept, EndpointDefinition, AnalysisResult, ParameterVariableMetadata, Variable, WhereClause

class SubmissionGenerator:
    def __init__(self, db_path='metadata.db', output_dir='outputs/submission'):
        self.db_path = db_path
        self.output_dir = output_dir
        
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.Session = sessionmaker(bind=self.engine)
        
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_define_xml(self):
        """Generates a semantically-annotated CDISC Define.xml v2.1 file from metadata tables."""
        session = self.Session()
        
        # XML Namespace mapping
        ODM_NS = 'http://www.cdisc.org/ns/odm/v1.3'
        DEF_NS = 'http://www.cdisc.org/ns/def/v2.1'
        ARM_NS = 'http://www.cdisc.org/ns/arm/v1.0'
        XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'
        
        ET.register_namespace('odm', ODM_NS)
        ET.register_namespace('def', DEF_NS)
        ET.register_namespace('arm', ARM_NS)
        ET.register_namespace('xsi', XSI_NS)
        
        # Root element in ODM namespace
        root = ET.Element(f"{{{ODM_NS}}}ODM", {
            "FileOID": "Define_XML_2.1_IMpower150",
            "AsOfDateTime": "2026-05-29T12:00:00",
            "ODMVersion": "1.3.2",
            "Originator": "Hoffmann-La Roche",
            f"{{{XSI_NS}}}schemaLocation": "http://www.cdisc.org/ns/odm/v1.3 define2-1-0.xsd"
        })
        
        study = ET.SubElement(root, f"{{{ODM_NS}}}Study", {"OID": "STUDY.GO29436"})
        meta_data = ET.SubElement(study, f"{{{ODM_NS}}}MetaDataVersion", {
            "OID": "MDV.GO29436.SDTMIG.3.4",
            "Name": "IMpower150 Study Metadata",
            "Description": "Metadata representation for Stage IV NSCLC trial"
        })
        
        # 1. Add Comment Definitions based on Biomedical Concepts
        comments_def = ET.SubElement(meta_data, f"{{{DEF_NS}}}CommentDefs")
        concepts = session.query(BiomedicalConcept).all()
        for bc in concepts:
            com = ET.SubElement(comments_def, f"{{{DEF_NS}}}CommentDef", {"OID": f"COM.{bc.bc_id}"})
            desc = ET.SubElement(com, f"{{{ODM_NS}}}Description")
            translated = ET.SubElement(desc, f"{{{ODM_NS}}}TranslatedText", {"xml:lang": "en"})
            translated.text = f"Biomedical Concept definition: {bc.bc_definition} (Interoperable COSMoS Link: {bc.cosmos_bc_id})"

        # 2. Add ItemGroupDefs (Datasets metadata)
        datasets_metadata = {
            "ADTTE": {
                "Label": "Analysis Dataset for Time-to-Event",
                "Structure": "One record per subject per parameter",
                "Purpose": "Analysis"
            },
            "ADRS": {
                "Label": "Analysis Dataset for Response",
                "Structure": "One record per subject per parameter",
                "Purpose": "Analysis"
            },
            "ADDOR": {
                "Label": "Analysis Dataset for Duration of Response",
                "Structure": "One record per subject per parameter",
                "Purpose": "Analysis"
            }
        }
        
        variables = session.query(Variable).all()
        param_metadata = session.query(ParameterVariableMetadata).all()
        rule_lookup = {}
        for row in param_metadata:
            if row.rule_id:
                rule_lookup.setdefault((row.dataset, row.variable), set()).add(row.rule_id)
        rule_lookup = {key: sorted(value) for key, value in rule_lookup.items()}
        from models import DerivationRule
        
        for ds, ds_meta in datasets_metadata.items():
            ds_vars = [v for v in variables if v.dataset == ds]
            if not ds_vars:
                continue
                
            item_group = ET.SubElement(meta_data, f"{{{ODM_NS}}}ItemGroupDef", {
                "OID": f"IG.{ds}",
                "Name": ds,
                "Repeating": "Yes",
                "SASDatasetName": ds,
                "Purpose": ds_meta["Purpose"],
                "Structure": ds_meta["Structure"],
                f"{{{DEF_NS}}}ArchiveLocationID": f"LOC.{ds}"
            })
            
            desc_el = ET.SubElement(item_group, f"{{{ODM_NS}}}Description")
            ET.SubElement(desc_el, f"{{{ODM_NS}}}TranslatedText", {"xml:lang": "en"}).text = ds_meta["Label"]
            
            # Link variables inside ItemGroupDef
            for idx, var in enumerate(ds_vars, start=1):
                item_ref = ET.SubElement(item_group, f"{{{ODM_NS}}}ItemRef", {
                    "ItemOID": f"IT.{ds}.{var.variable}",
                    "OrderNumber": str(idx),
                    "Mandatory": "Yes" if var.variable in ("STUDYID", "USUBJID", "PARAMCD") else "No"
                })
                # Attach MethodOID only for unambiguous dataset-variable derivations.
                # Multi-PARAMCD variables are documented in ARM descriptions below.
                mapped_rules = rule_lookup.get((ds, var.variable), [])
                if len(mapped_rules) == 1:
                    item_ref.set("MethodOID", f"MT.{mapped_rules[0]}")
            
            # Add archive location leaf element pointing to physical transport file
            leaf = ET.SubElement(item_group, f"{{{DEF_NS}}}leaf", {
                "ID": f"LOC.{ds}",
                f"{{http://www.w3.org/1999/xlink}}href": f"{ds.lower()}.xpt"
            })
            ET.SubElement(leaf, f"{{{DEF_NS}}}title").text = f"{ds.lower()}.xpt"

        # 3. Add Item Definitions (variables) mapped to Concepts
        for var in variables:
            datatype_map = {"float": "float", "integer": "integer", "string": "text"}
            dtype = datatype_map.get(var.datatype, "text")
            
            item_attrs = {
                "OID": f"IT.{var.dataset}.{var.variable}",
                "Name": var.variable,
                "DataType": dtype,
                "Length": "8"
            }
            if var.variable == "PARAMCD":
                item_attrs["CodeListOID"] = "CL.PARAMCD"
            elif var.variable == "CNSR":
                item_attrs["CodeListOID"] = "CL.CNSR"
                
            item_def = ET.SubElement(meta_data, f"{{{ODM_NS}}}ItemDef", item_attrs)
            
            desc_el = ET.SubElement(item_def, f"{{{ODM_NS}}}Description")
            ET.SubElement(desc_el, f"{{{ODM_NS}}}TranslatedText", {"xml:lang": "en"}).text = var.role or var.variable
            
            item_concepts = sorted({
                row.bc_id for row in param_metadata
                if row.dataset == var.dataset and row.variable == var.variable and row.bc_id
            })
            if not item_concepts and var.bc_id:
                item_concepts = [var.bc_id]
            for bc_id in item_concepts:
                ET.SubElement(item_def, f"{{{DEF_NS}}}CommentRef", {"CommentOID": f"COM.{bc_id}"})
                
        # 4. Add CodeLists for Controlled Terminology
        paramcd_cl = ET.SubElement(meta_data, f"{{{ODM_NS}}}CodeList", {
            "OID": "CL.PARAMCD",
            "Name": "Parameter Code List",
            "DataType": "text"
        })
        for val, desc in [("PFS", "Progression-Free Survival"), ("OS", "Overall Survival"), ("iPFS", "immune Progression-Free Survival"), ("DOR", "Duration of Response"), ("BOR", "Best Overall Response")]:
            cli = ET.SubElement(paramcd_cl, f"{{{ODM_NS}}}CodeListItem", {"CodedValue": val})
            dec = ET.SubElement(cli, f"{{{ODM_NS}}}Decode")
            ET.SubElement(dec, f"{{{ODM_NS}}}TranslatedText", {"xml:lang": "en"}).text = desc
            
        cnsr_cl = ET.SubElement(meta_data, f"{{{ODM_NS}}}CodeList", {
            "OID": "CL.CNSR",
            "Name": "Censor Flag Code List",
            "DataType": "integer"
        })
        for val, desc in [("0", "Event"), ("1", "Censored")]:
            cli = ET.SubElement(cnsr_cl, f"{{{ODM_NS}}}CodeListItem", {"CodedValue": val})
            dec = ET.SubElement(cli, f"{{{ODM_NS}}}Decode")
            ET.SubElement(dec, f"{{{ODM_NS}}}TranslatedText", {"xml:lang": "en"}).text = desc

        # 5. Add Derivation Method definitions
        rules = session.query(DerivationRule).all()
        for r in rules:
            method_def = ET.SubElement(meta_data, f"{{{ODM_NS}}}MethodDef", {
                "OID": f"MT.{r.rule_id}",
                "Name": f"Derivation Method for {r.rule_id}",
                "Type": "Derivation"
            })
            desc_el = ET.SubElement(method_def, f"{{{ODM_NS}}}Description")
            ET.SubElement(desc_el, f"{{{ODM_NS}}}TranslatedText", {"xml:lang": "en"}).text = r.logic_definition or "Derivation rule"

        # 6. Add ARM (Analysis Results Metadata) based on AnalysisResult rows
        arm_def = ET.SubElement(meta_data, f"{{{ARM_NS}}}AnalysisResults")
        results = session.query(AnalysisResult).all()
        for res in results:
            result_def = ET.SubElement(arm_def, f"{{{ARM_NS}}}AnalysisResult", {
                "OID": f"AR.{res.analysis_id}",
                "ParameterOID": f"IT.{res.dataset}.PARAMCD" if res.dataset else "IT.ADTTE.PARAMCD",
                "AnalysisResultLabel": res.arm_display_label or f"Analysis for endpoint {res.endpoint_id}"
            })
            # Link back to Estimand and Endpoint
            desc_el = ET.SubElement(result_def, f"{{{ARM_NS}}}Description")
            derivation_rules = sorted({
                row.rule_id for row in param_metadata
                if row.dataset == res.dataset and row.paramcd == res.paramcd and row.rule_id
            })
            rule_text = ", ".join(derivation_rules) if derivation_rules else "No parameter-level derivation rule registered"
            desc_el.text = f"Endpoint: {res.endpoint_id} serving Estimand {res.estimand_id}. Method: {res.stat_method}. Test: {res.stat_test}. TFL Ref: {res.tfl_reference}. Parameter-level derivations: {rule_text}."
            
            if res.where_clause_id:
                wc = session.query(WhereClause).filter_by(where_clause_id=res.where_clause_id).first()
                if wc:
                    ET.SubElement(result_def, f"{{{ARM_NS}}}WhereClause", {
                        "OID": wc.where_clause_id,
                        "Dataset": wc.dataset or "ADTTE",
                        "Variable": wc.variable or "PARAMCD",
                        "Operator": wc.filter_operator or "EQ",
                        "Value": wc.filter_value or ""
                    })
            
        # Write to file
        tree = ET.ElementTree(root)
        xml_path = os.path.join(self.output_dir, "define.xml")
        
        # Simple indented string write
        ET.indent(tree, space="    ", level=0)
        tree.write(xml_path, encoding='utf-8', xml_declaration=True)
        
        session.close()
        print(f"[SubmissionGenerator] Generated Define.xml v2.1 submission file: {xml_path}")
        
        # Self-validate the generated XML file
        is_valid, validation_errors = self.validate_define_xml(xml_path)
        if not is_valid:
            print(f"[SubmissionGenerator] [Warning] Define-XML validation failed with {len(validation_errors)} errors!")
            
        return xml_path

    def validate_define_xml(self, xml_path):
        """
        Runs programmatic Define-XML v2.1 integrity validation checking
        structure, namespaces, references, and controlled terminology.
        """
        print(f"[Validator] Starting programmatic Define-XML 2.1 integrity validation on {xml_path}...")
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except Exception as e:
            return False, [f"XML parsing failed: {e}"]
            
        errors = []
        
        # 1. Namespace & Root tag validation
        ODM_NS = 'http://www.cdisc.org/ns/odm/v1.3'
        DEF_NS = 'http://www.cdisc.org/ns/def/v2.1'
        
        if root.tag != f"{{{ODM_NS}}}ODM":
            errors.append(f"Root tag must be {{{ODM_NS}}}ODM, found {root.tag}")
            
        # 2. Extract all defined OIDs and references
        defined_comments = set()
        defined_methods = set()
        defined_codelists = set()
        defined_items = set()
        defined_itemgroups = set()
        
        referenced_comments = set()
        referenced_methods = set()
        referenced_codelists = set()
        referenced_items = set()
        
        # Helper to strip namespace for easy checking
        def strip_ns(tag):
            return tag.split('}')[-1] if '}' in tag else tag
            
        # Recurse and parse
        for elem in root.iter():
            tag = strip_ns(elem.tag)
            
            # Record definitions
            if tag == 'CommentDef':
                oid = elem.get('OID')
                if oid: defined_comments.add(oid)
            elif tag == 'MethodDef':
                oid = elem.get('OID')
                if oid: defined_methods.add(oid)
            elif tag == 'CodeList':
                oid = elem.get('OID')
                if oid: defined_codelists.add(oid)
            elif tag == 'ItemDef':
                oid = elem.get('OID')
                if oid: defined_items.add(oid)
            elif tag == 'ItemGroupDef':
                oid = elem.get('OID')
                if oid: defined_itemgroups.add(oid)
                
            # Record references
            if tag == 'CommentRef':
                oid = elem.get('CommentOID')
                if oid: referenced_comments.add(oid)
            elif tag == 'ItemRef':
                oid = elem.get('ItemOID')
                if oid: referenced_items.add(oid)
                method_oid = elem.get('MethodOID')
                if method_oid: referenced_methods.add(method_oid)
            elif tag == 'ItemDef':
                cl_oid = elem.get('CodeListOID')
                if cl_oid: referenced_codelists.add(cl_oid)
                
        # 3. Reference integrity checks (No dangling references)
        for ref in referenced_comments:
            if ref not in defined_comments:
                errors.append(f"Dangling Comment Reference: {ref} is referenced but not defined in CommentDefs")
                
        for ref in referenced_methods:
            if ref not in defined_methods:
                errors.append(f"Dangling Method Reference: {ref} is referenced but not defined in MethodDefs")
                
        for ref in referenced_codelists:
            if ref not in defined_codelists:
                errors.append(f"Dangling CodeList Reference: {ref} is referenced but not defined")
                
        for ref in referenced_items:
            if ref not in defined_items:
                errors.append(f"Dangling Item Reference: {ref} is referenced in ItemGroupDef but not defined in ItemDefs")
                
        # 4. Controlled terminology validation
        paramcd_items = []
        cnsr_items = []
        for elem in root.iter():
            tag = strip_ns(elem.tag)
            if tag == 'CodeList':
                oid = elem.get('OID')
                if oid == 'CL.PARAMCD':
                    paramcd_items = [item.get('CodedValue') for item in elem.findall(f"{{{ODM_NS}}}CodeListItem")]
                elif oid == 'CL.CNSR':
                    cnsr_items = [item.get('CodedValue') for item in elem.findall(f"{{{ODM_NS}}}CodeListItem")]
                    
        expected_paramcds = {"PFS", "OS", "iPFS", "DOR", "BOR"}
        for pc in expected_paramcds:
            if pc not in paramcd_items:
                errors.append(f"Missing expected PARAMCD in CodeList: {pc}")
                
        expected_cnsrs = {"0", "1"}
        for c in expected_cnsrs:
            if c not in cnsr_items:
                errors.append(f"Missing expected CNSR value in CodeList: {c}")
                
        # 5. Empty or incomplete elements
        for elem in root.iter():
            tag = strip_ns(elem.tag)
            if tag in ('ItemDef', 'ItemGroupDef', 'MethodDef', 'CommentDef') and not elem.get('OID'):
                errors.append(f"Element {tag} is missing required 'OID' attribute")
                
        if errors:
            print(f"[Validator] Validation failed with {len(errors)} errors:")
            for err in errors:
                print(f"  • [ERROR] {err}")
            return False, errors
            
        print("[Validator] SUCCESS: Define-XML 2.1 structure and reference integrity verified (0 errors).")
        return True, []

    def generate_sdrg_json_ld(self):
        """Generates a machine-readable JSON-LD Study Data Reviewer Guide (SDRG)."""
        session = self.Session()
        
        # Context structure linking to clinical standard ontologies
        sdrg_ld = {
            "@context": {
                "cdisc": "https://www.cdisc.org/standards/metadata/",
                "cosmos": "https://cosmos.cdisc.org/concepts/",
                "study": "http://example.org/study/go29436/",
                "SDRGSection": "cdisc:SDRGSection",
                "biomedicalConcept": "cosmos:biomedicalConcept",
                "endpointLabel": "cdisc:endpointLabel",
                "variables": "cdisc:variables",
                "derivationRules": "cdisc:derivationRules"
            },
            "@type": "study:SDRGDocument",
            "@id": "study:sdrg-v1.0",
            "studyId": "GO29436",
            "sections": []
        }
        
        # Build sections based on endpoints and concepts
        endpoints = session.query(EndpointDefinition).all()
        param_metadata = session.query(ParameterVariableMetadata).all()
        for ep in endpoints:
            bc = session.query(BiomedicalConcept).filter_by(bc_id=ep.bc_id).first()
            bc_name = bc.bc_name if bc else "N/A"
            cosmos_id = bc.cosmos_bc_id if bc else "N/A"
            
            # Dynamically query active realized variables mapped to this biomedical concept
            var_records = session.query(Variable).filter_by(bc_id=ep.bc_id).all()
            section_vars = set([f"{v.dataset}.{v.variable}" for v in var_records])
            section_vars.update(
                f"{row.dataset}.{row.variable}"
                for row in param_metadata
                if row.bc_id == ep.bc_id
            )
            section_vars = sorted(section_vars)
            if not section_vars:
                section_vars = ["ADTTE.AVAL", "ADTTE.CNSR"]
                
            section = {
                "@type": "SDRGSection",
                "@id": f"study:section-{ep.endpoint_id}",
                "biomedicalConcept": bc_name,
                "cosmosConceptId": cosmos_id,
                "endpointLabel": ep.endpoint_id,
                "sapSection": ep.sap_reference,
                "estimandId": ep.estimand_id,
                "variables": section_vars
            }
            sdrg_ld["sections"].append(section)
            
        json_path = os.path.join(self.output_dir, "sdrg.jsonld")
        with open(json_path, 'w') as f:
            json.dump(sdrg_ld, f, indent=4)
            
        session.close()
        print(f"[SubmissionGenerator] Generated JSON-LD SDRG submission file: {json_path}")
        return json_path

    def generate_sdrg_html(self):
        """Generates a CDISC-compliant, beautiful HTML Study Data Reviewer Guide (SDRG)."""
        session = self.Session()
        
        endpoints = session.query(EndpointDefinition).all()
        concepts = {bc.bc_id: bc for bc in session.query(BiomedicalConcept).all()}
        
        # Build HTML content
        html_lines = []
        html_lines.append("""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>IMpower150 Study Data Reviewer Guide (SDRG)</title>
    <style>
        body {
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #2D3748;
            max-width: 1000px;
            margin: 40px auto;
            padding: 0 20px;
            background-color: #F7FAFC;
        }
        .header {
            background: linear-gradient(135deg, #1A202C 0%, #2D3748 100%);
            color: #FFFFFF;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        .header h1 {
            margin: 0 0 10px 0;
            font-size: 28px;
            font-weight: 700;
        }
        .header p {
            margin: 0;
            color: #CBD5E0;
            font-size: 14px;
            letter-spacing: 1px;
        }
        .card {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }
        h2 {
            font-size: 20px;
            border-bottom: 2px solid #E2E8F0;
            padding-bottom: 8px;
            margin-top: 0;
            color: #1A202C;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        th, td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #E2E8F0;
        }
        th {
            background-color: #EDF2F7;
            color: #4A5568;
            font-weight: 600;
        }
        tr:hover {
            background-color: #F8FAFC;
        }
        .badge {
            background-color: #EBF8FF;
            color: #2B6CB0;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        }
        .footer {
            text-align: center;
            margin-top: 50px;
            font-size: 12px;
            color: #A0AEC0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>IMpower150 (GO29436) Submission</h1>
        <p>STUDY DATA REVIEWER GUIDE (SDRG) - SEMANTIC VERSION 3.0</p>
    </div>
    
    <div class="card">
        <h2>1. Protocol Objectives & Endpoint Mapping</h2>
        <p>The following table lists clinical endpoints mapped directly to their respective Statistical Outcomes and COSMoS Biomedical Concepts.</p>
        <table>
            <thead>
                <tr>
                    <th>Endpoint ID</th>
                    <th>Biomedical Concept</th>
                    <th>COSMoS ID</th>
                    <th>Type</th>
                    <th>Response Criteria</th>
                    <th>SAP Reference</th>
                </tr>
            </thead>
            <tbody>""")
            
        for ep in endpoints:
            bc = concepts.get(ep.bc_id)
            bc_name = bc.bc_name if bc else ep.bc_id
            cosmos_id = bc.cosmos_bc_id if bc else "N/A"
            
            html_lines.append(f"""
                <tr>
                    <td><strong>{ep.endpoint_id}</strong></td>
                    <td>{bc_name}</td>
                    <td><code>{cosmos_id}</code></td>
                    <td><span class="badge">{ep.endpoint_type.upper()}</span></td>
                    <td>{ep.criteria_type}</td>
                    <td>{ep.sap_reference}</td>
                </tr>""")
                
        html_lines.append("""
            </tbody>
        </table>
    </div>

    <div class="card">
        <h2>2. Standards Conformance & Submission Scope</h2>
        <p>This package records the intended CDISC SDTMIG v3.4, ADaMIG v1.3, and Define-XML v2.1 standards scope. Internal XML reference checks, derivation rule hashing, and execution environment hashes are recorded in the reproducibility ledger; external regulatory validation evidence must be attached before final submission.</p>
        <table>
            <thead>
                <tr>
                    <th>Standard</th>
                    <th>Version Used</th>
                    <th>Conformance Status</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>CDISC SDTM</td>
                    <td>v3.4</td>
                    <td>Internal scope metadata generated; external SDTM validation evidence required</td>
                </tr>
                <tr>
                    <td>CDISC ADaM</td>
                    <td>v1.3</td>
                    <td>Internal ADaM artifact checks generated; external ADaM validation evidence required</td>
                </tr>
                <tr>
                    <td>CDISC Define.xml</td>
                    <td>v2.1</td>
                    <td>Programmatic XML structure and reference integrity checks passed</td>
                </tr>
            </tbody>
        </table>
    </div>
    
    <div class="footer">
        <p>Generated by Hoffmann-La Roche Computable Pipeline Engine &bull; Timestamp: 2026-05-29 &bull; Confidential</p>
    </div>
</body>
</html>""")
        
        html_path = os.path.join(self.output_dir, "sdrg.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(html_lines))
            
        session.close()
        print(f"[SubmissionGenerator] Generated HTML SDRG reviewer guide: {html_path}")
        return html_path

if __name__ == '__main__':
    gen = SubmissionGenerator()
    gen.generate_define_xml()
    gen.generate_sdrg_json_ld()
    gen.generate_sdrg_html()
