class ConfidenceScorer:
    """Phase 9 4-signal composite confidence scorer for Roche Protocol GO29436."""
    def __init__(self):
        self.valid_concepts = {"OS", "PFS", "iPFS", "BOR", "DOR", "ORR", "PARAMCD"}
        self.valid_variables = {"AVAL", "CNSR", "ORR_FL", "PARAMCD"}

    def compute_score(self, rule_candidate, source_chunk):
        """Computes structural and clinical conformance confidence signals for a rule."""
        
        # 1. Syntactic Validity Signal (20% weight)
        # Verify required keys are present and contain valid content
        required_keys = ["rule_id", "endpoint_id", "target_variable", "logic_type", "suggested_concept", "sap_reference", "logic_definition"]
        present_keys = [k for k in required_keys if k in rule_candidate and str(rule_candidate[k]).strip()]
        syntactic_score = len(present_keys) / len(required_keys)
        
        # 2. SAP Coverage Signal (20% weight)
        # Ensure the cited page number or section matches the source chunk's metadata
        coverage_score = 0.50
        cited_ref = str(rule_candidate.get("sap_reference", "")).lower()
        chunk_page = str(source_chunk.get("page_number", ""))
        
        if chunk_page and f"page {chunk_page}" in cited_ref:
            coverage_score = 1.0
        elif "sap" in cited_ref or "section" in cited_ref:
            coverage_score = 0.80
            
        # 3. Concept Overlap Signal (30% weight)
        # Match suggested concept against CDISC / COSMoS seeded concepts
        concept = rule_candidate.get("suggested_concept", "")
        concept_score = 1.0 if concept in self.valid_concepts else 0.20
        
        # 4. Regulatory Compliance Signal (30% weight)
        # Check target variables map correctly to standard CDISC ADaM structures
        var_name = rule_candidate.get("target_variable", "")
        compliance_score = 1.0 if var_name in self.valid_variables else 0.20
        
        # Double check TTE dataset variable assignments (AVAL/CNSR are only for time-to-event)
        logic_type = rule_candidate.get("logic_type", "")
        if logic_type == "date_diff" and var_name not in ["AVAL", "PARAMCD"]:
            compliance_score = max(0.20, compliance_score - 0.50)
        elif logic_type == "event_flag" and var_name not in ["CNSR", "PARAMCD"]:
            compliance_score = max(0.20, compliance_score - 0.50)
            
        # Compute Weighted Composite Score
        composite = (
            0.20 * syntactic_score + 
            0.20 * coverage_score + 
            0.30 * concept_score + 
            0.30 * compliance_score
        )
        
        print(f"[AI Scorer] Calculated composite score for {rule_candidate.get('rule_id', 'unknown')}: {composite:.4f}")
        return {
            "composite": composite,
            "signals": {
                "syntactic_validity": syntactic_score,
                "sap_coverage": coverage_score,
                "concept_overlap": concept_score,
                "regulatory_compliance": compliance_score
            }
        }
