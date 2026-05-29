import os
import sys
# Make sure src path is imported correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sap_ingestion import SAPIngestionModule
from llm_rule_extractor import LLMRuleExtractor
from confidence_scorer import ConfidenceScorer

def test_ai_governance_pipeline():
    # 1. Verify Ingestion Engine
    ingestor = SAPIngestionModule()
    chunks = ingestor.extract_chunks()
    
    assert len(chunks) > 0, "No chunks extracted from SAP PDF"
    first_chunk = chunks[0]
    assert "chunk_id" in first_chunk
    assert "text" in first_chunk
    assert "page_number" in first_chunk
    assert len(first_chunk["matched_keywords"]) > 0
    
    # Verify spacing cleaning heuristic works on test pattern
    test_pattern = "o v er all s ur vi v al is P F S and O S under R E CI S T v 1. 1."
    cleaned = ingestor.clean_text(test_pattern)
    assert "overall survival" in cleaned.lower()
    assert "PFS" in cleaned
    assert "OS" in cleaned
    assert "RECIST" in cleaned

    # 2. Verify AI Semantic Rule Extractor
    extractor = LLMRuleExtractor()
    extraction_res = extractor.extract_declarative_rules(first_chunk)
    
    assert "proposed_rules" in extraction_res
    assert len(extraction_res["proposed_rules"]) > 0
    
    first_proposed = extraction_res["proposed_rules"][0]
    required_keys = ["rule_id", "endpoint_id", "target_variable", "logic_type", "suggested_concept", "logic_definition"]
    for k in required_keys:
        assert k in first_proposed, f"Required key '{k}' missing from proposed rule"
        
    # 3. Verify Composite Scorer calculations
    scorer = ConfidenceScorer()
    scoring_res = scorer.compute_score(first_proposed, first_chunk)
    
    assert "composite" in scoring_res
    composite = scoring_res["composite"]
    assert 0.0 <= composite <= 1.0, "Composite score out of bounds"
    
    signals = scoring_res["signals"]
    required_signals = ["syntactic_validity", "sap_coverage", "concept_overlap", "regulatory_compliance"]
    for sig in required_signals:
        assert sig in signals, f"Confidence signal '{sig}' missing from scoring response"
        assert 0.0 <= signals[sig] <= 1.0, f"Signal '{sig}' value out of bounds"

    print("\n[PASSED] Automated AI Governance & Conformance tests passed successfully!")

if __name__ == '__main__':
    test_ai_governance_pipeline()
