"""
Sprint 2B Verification: INSPIRE Validation Endpoint

Tests the /api/validate/inspire endpoint.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from services.ontology_service import OntologyBuilder
from services.inspire.inspire_mapper import INSPIREMapper
from services.inspire.validator import INSPIREValidator


def test_endpoint_structure():
    """Test that validation returns correct structure"""
    print("\n=== TEST: Endpoint Structure ===")
    
    # Create core graph
    builder = OntologyBuilder()
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    builder.add_bim_element("GUID-002", "IfcRoad", "test.ifc")
    owl_core = builder.export(format="xml")
    
    # Generate alignment
    mapper = INSPIREMapper(owl_core, ifc_hash="test123")
    alignment_result = mapper.generate_alignment()
    
    # Validate
    validator = INSPIREValidator()
    validation_result = validator.validate_all(
        mapper.alignment_dataset,
        alignment_result["themes"]
    )
    
    # Check structure
    assert "themes_validated" in validation_result, "Expected themes_validated"
    assert "overall_conforms" in validation_result, "Expected overall_conforms"
    assert "total_violations" in validation_result, "Expected total_violations"
    assert "results" in validation_result, "Expected results"
    
    print(f"✓ Themes validated: {validation_result['themes_validated']}")
    print(f"✓ Overall conforms: {validation_result['overall_conforms']}")
    print(f"✓ Total violations: {validation_result['total_violations']}")
    print("✓ Endpoint Structure Test PASSED\n")


def test_multiple_themes_validated():
    """Test that all themes are validated"""
    print("\n=== TEST: Multiple Themes Validated ===")
    
    # Create core graph with multiple themes
    builder = OntologyBuilder()
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    builder.add_bim_element("GUID-002", "IfcRoad", "test.ifc")
    builder.add_bim_element("GUID-003", "IfcPipeSegment", "test.ifc")
    owl_core = builder.export(format="xml")
    
    # Generate alignment
    mapper = INSPIREMapper(owl_core, ifc_hash="test123")
    alignment_result = mapper.generate_alignment()
    
    # Validate
    validator = INSPIREValidator()
    validation_result = validator.validate_all(
        mapper.alignment_dataset,
        alignment_result["themes"]
    )
    
    # Check that BU, TN, US are validated (EMF skipped)
    themes_validated = validation_result["themes_validated"]
    assert "BU" in themes_validated, "Expected BU to be validated"
    assert "TN" in themes_validated, "Expected TN to be validated"
    assert "US" in themes_validated, "Expected US to be validated"
    
    print(f"✓ Themes validated: {themes_validated}")
    print("✓ Multiple Themes Validated Test PASSED\n")


def test_violations_count_correct():
    """Test that violation count is accurate"""
    print("\n=== TEST: Violations Count Correct ===")
    
    # Create valid core graph
    builder = OntologyBuilder()
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    owl_core = builder.export(format="xml")
    
    # Generate alignment
    mapper = INSPIREMapper(owl_core, ifc_hash="test123")
    alignment_result = mapper.generate_alignment()
    
    # Validate
    validator = INSPIREValidator()
    validation_result = validator.validate_all(
        mapper.alignment_dataset,
        alignment_result["themes"]
    )
    
    # Should have 0 violations for valid alignment
    assert validation_result["total_violations"] == 0, \
        f"Expected 0 violations, got {validation_result['total_violations']}"
    assert validation_result["overall_conforms"] == True, \
        "Expected overall conformance"
    
    print(f"✓ Total violations: {validation_result['total_violations']}")
    print(f"✓ Overall conforms: {validation_result['overall_conforms']}")
    print("✓ Violations Count Correct Test PASSED\n")


def test_metadata_checked():
    """Test that metadata graph is checked"""
    print("\n=== TEST: Metadata Checked ===")
    
    # Create core graph
    builder = OntologyBuilder()
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    owl_core = builder.export(format="xml")
    
    # Generate alignment
    mapper = INSPIREMapper(owl_core, ifc_hash="test123", config_hash="abc456")
    alignment_result = mapper.generate_alignment()
    
    # Get metadata graph
    metadata_graph = mapper.get_metadata_graph()
    
    assert len(metadata_graph) > 0, "Expected metadata graph to have triples"
    
    print(f"✓ Metadata graph has {len(metadata_graph)} triples")
    print("✓ Metadata Checked Test PASSED\n")


if __name__ == "__main__":
    print("=" * 60)
    print("SPRINT 2B: INSPIRE VALIDATION ENDPOINT TESTS")
    print("=" * 60)
    
    try:
        test_endpoint_structure()
        test_multiple_themes_validated()
        test_violations_count_correct()
        test_metadata_checked()
        
        print("=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
