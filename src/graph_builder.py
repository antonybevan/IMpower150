import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import (
    ProtocolObjective, BiomedicalConcept, EndpointDefinition, 
    Estimand, DerivationRule, Variable, AnalysisResult, Program
)

class SemanticGraphBuilder:
    def __init__(self, db_path='metadata.db'):
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.Session = sessionmaker(bind=self.engine)
        self.graph = nx.DiGraph()

    def build_graph(self):
        """Builds the 8-layer clinical semantic DiGraph from SQLite tables."""
        session = self.Session()
        self.graph.clear()
        
        # ─── LAYER 1: OBJECTIVES ───
        objectives = session.query(ProtocolObjective).all()
        for obj in objectives:
            self.graph.add_node(
                f"OBJ_{obj.obj_id}", 
                type="OBJECTIVE", 
                label=obj.obj_id, 
                text=obj.obj_text, 
                section=obj.m11_section,
                color="#76E4F7"
            )
            
        # ─── LAYER 2: CONCEPTS ───
        concepts = session.query(BiomedicalConcept).all()
        for bc in concepts:
            self.graph.add_node(
                f"CON_{bc.bc_id}", 
                type="CONCEPT", 
                label=bc.bc_name, 
                category=bc.bc_category, 
                cosmos_id=bc.cosmos_bc_id,
                color="#B794F4"
            )
            
        # ─── LAYER 3: ENDPOINTS ───
        endpoints = session.query(EndpointDefinition).all()
        for ep in endpoints:
            self.graph.add_node(
                f"EP_{ep.endpoint_id}", 
                type="ENDPOINT", 
                label=ep.endpoint_id, 
                concept=ep.analysis_concept, 
                criteria=ep.criteria_type,
                color="#F6AD55"
            )
            # Edge: CONCEPT -> ENDPOINT
            if ep.bc_id:
                self.graph.add_edge(f"CON_{ep.bc_id}", f"EP_{ep.endpoint_id}", rel="measures")
            
        # ─── LAYER 4: ESTIMANDS ───
        estimands = session.query(Estimand).all()
        for est in estimands:
            self.graph.add_node(
                f"EST_{est.estimand_id}", 
                type="ESTIMAND", 
                label=est.name, 
                population=est.target_population, 
                summary=est.summary_measure,
                color="#63B3ED"
            )
            
        # Link Objectives and Estimands to Endpoints
        for obj in objectives:
            if obj.endpoint_id:
                self.graph.add_edge(f"OBJ_{obj.obj_id}", f"EP_{obj.endpoint_id}", rel="serves")
                
        for ep in endpoints:
            if ep.estimand_id:
                self.graph.add_edge(f"EP_{ep.endpoint_id}", f"EST_{ep.estimand_id}", rel="quantifies")

        # ─── LAYER 5: RULES ───
        rules = session.query(DerivationRule).all()
        for rule in rules:
            self.graph.add_node(
                f"RULE_{rule.rule_id}", 
                type="RULE", 
                label=rule.rule_id, 
                logic_type=rule.logic_type, 
                assessor=rule.assessor,
                color="#FC8181"
            )
            # Edge: ENDPOINT -> RULE
            if rule.endpoint_id:
                self.graph.add_edge(f"EP_{rule.endpoint_id}", f"RULE_{rule.rule_id}", rel="implemented_by")

        # ─── LAYER 6: VARIABLES ───
        variables = session.query(Variable).all()
        for var in variables:
            var_node_id = f"VAR_{var.dataset}.{var.variable}"
            self.graph.add_node(
                var_node_id, 
                type="VARIABLE", 
                label=f"{var.dataset}.{var.variable}", 
                role=var.role, 
                datatype=var.datatype,
                color="#68D391"
            )
            # Edge: CONCEPT -> VARIABLE
            if var.bc_id:
                self.graph.add_edge(f"CON_{var.bc_id}", var_node_id, rel="realized_by")

        # Link Rules to Variables dynamically
        for rule in rules:
            endpoint = session.query(EndpointDefinition).filter_by(endpoint_id=rule.endpoint_id).first()
            if endpoint:
                matching_vars = session.query(Variable).filter_by(variable=rule.target_variable, bc_id=endpoint.bc_id).all()
                for var in matching_vars:
                    var_node_id = f"VAR_{var.dataset}.{var.variable}"
                    if self.graph.has_node(var_node_id):
                        self.graph.add_edge(f"RULE_{rule.rule_id}", var_node_id, rel="derives")

        # ─── LAYER 7: RESULTS (ARM tables) ───
        results = session.query(AnalysisResult).all()
        for res in results:
            res_node_id = f"RES_{res.analysis_id}"
            self.graph.add_node(
                res_node_id, 
                type="RESULT", 
                label=res.arm_display_label or f"Result {res.analysis_id}",
                color="#9AE6B4"
            )
            if res.endpoint_id:
                self.graph.add_edge(f"EP_{res.endpoint_id}", res_node_id, rel="supports")
            if res.dataset:
                var_node_id = f"VAR_{res.dataset}.AVAL"
                if self.graph.has_node(var_node_id):
                    self.graph.add_edge(var_node_id, res_node_id, rel="populates")

        # ─── LAYER 8: ARTIFACTS (SAS Output files & datasets) ───
        programs = session.query(Program).all()
        for prog in programs:
            sas_art_id = f"ART_SAS_{prog.program_id}"
            self.graph.add_node(
                sas_art_id, 
                type="ARTIFACT", 
                label=prog.name, 
                format="SAS",
                color="#4A5568"
            )
            rule_id = prog.program_id.replace("PROG_", "")
            if self.graph.has_node(f"RULE_{rule_id}"):
                self.graph.add_edge(f"RULE_{rule_id}", sas_art_id, rel="generates")
                rule_obj = session.query(DerivationRule).filter_by(rule_id=rule_id).first()
                if rule_obj:
                    endpoint = session.query(EndpointDefinition).filter_by(endpoint_id=rule_obj.endpoint_id).first()
                    if endpoint:
                        matching_vars = session.query(Variable).filter_by(variable=rule_obj.target_variable, bc_id=endpoint.bc_id).all()
                        for var in matching_vars:
                            var_node_id = f"VAR_{var.dataset}.{var.variable}"
                            if self.graph.has_node(var_node_id):
                                self.graph.add_edge(sas_art_id, var_node_id, rel="outputs")

        # Dynamically link datasets to generated output files
        datasets = ["ados", "adtte", "addor", "adrs"]
        for ds in datasets:
            json_art_id = f"ART_{ds.upper()}_JSON"
            if not self.graph.has_node(json_art_id):
                self.graph.add_node(
                    json_art_id,
                    type="ARTIFACT",
                    label=f"{ds}.json (Dataset-JSON)",
                    format="JSON",
                    color="#4A5568"
                )
            xpt_art_id = f"ART_{ds.upper()}_XPT"
            if not self.graph.has_node(xpt_art_id):
                self.graph.add_node(
                    xpt_art_id,
                    type="ARTIFACT",
                    label=f"{ds}.xpt (SAS Transport)",
                    format="XPT",
                    color="#4A5568"
                )
            for var_node in list(self.graph.nodes()):
                if var_node.startswith(f"VAR_{ds.upper()}."):
                    self.graph.add_edge(var_node, json_art_id, rel="produces_artifact")
                    self.graph.add_edge(var_node, xpt_art_id, rel="produces_artifact")

        session.close()
        print(f"[SemanticGraphBuilder] Graph fully built: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges.")
        return self.graph

    # ─── SEMANTIC LINEAGE QUERIES ───
    def concept_to_artifacts(self, bc_id):
        """Traces the full downstream clinical chain from a COSMoS concept to generated artifacts."""
        start_node = f"CON_{bc_id}"
        if not self.graph.has_node(start_node):
            return []
        
        # Breadth-first search traversal
        visited = list(nx.dfs_preorder_nodes(self.graph, source=start_node))
        return [self.graph.nodes[n] for n in visited]

    def impact_analysis(self, rule_id):
        """Finds downstream variables, results, and artifacts affected by changing a rule."""
        start_node = f"RULE_{rule_id}"
        if not self.graph.has_node(start_node):
            return []
            
        affected_nodes = list(nx.dfs_preorder_nodes(self.graph, source=start_node))
        # Filter for downstream Variables, Results, and Artifacts
        return [self.graph.nodes[n] for n in affected_nodes if self.graph.nodes[n]["type"] in ["VARIABLE", "RESULT", "ARTIFACT"]]

    def semantic_gap_audit(self):
        """Identifies clinical gaps (conceptually unanchored variables or rules without endpoints)."""
        session = self.Session()
        gaps = []
        
        # 1. Audit variables missing bc_id (clinical concept mapping)
        unmapped_vars = session.query(Variable).filter(Variable.bc_id.is_(None)).all()
        for var in unmapped_vars:
            gaps.append({
                "type": "Variable Gap",
                "entity": f"{var.dataset}.{var.variable}",
                "detail": "Variable has no COSMoS Biomedical Concept FK (conceptually unanchored realization)."
            })
            
        # 2. Audit rules missing endpoint_id
        unmapped_rules = session.query(DerivationRule).filter(DerivationRule.endpoint_id.is_(None)).all()
        for rule in unmapped_rules:
            gaps.append({
                "type": "Rule Gap",
                "entity": rule.rule_id,
                "detail": "Rule has no clinical Endpoint Definition FK (semantically unlinked derivation)."
            })
            
        session.close()
        return gaps

if __name__ == '__main__':
    builder = SemanticGraphBuilder()
    g = builder.build_graph()
    
    # Run tests
    pfs_artifacts = builder.concept_to_artifacts("PFS")
    print(f"\n[Linage Query] PFS Downstream Clinical Chain nodes count: {len(pfs_artifacts)}")
    
    gaps = builder.semantic_gap_audit()
    print(f"[Gap Audit] Found {len(gaps)} clinical gaps in metadata repository.")
