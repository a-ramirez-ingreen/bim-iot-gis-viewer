"""
Sprint 2B Verification: SHACL Buildings Minimum Compliance

Tests SHACL validation for Buildings theme alignment.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from services.ontology_service import OntologyBuilder
from services.inspire.inspire_mapper import INSPIREMapper
from services.inspire.validator import INSPIREValidator
from rdflib import URIRef


def test_valid_bu_alignment_passes():
    """Test that valid BU alignment passes SHACL validation"""
    print("\n=== TEST: Valid BU Alignment Passes ===")
    
    # Create core graph with Buildings
    builder = OntologyBuilder()
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    builder.add_bim_element("GUID-002", "IfcWall", "test.ifc")
    
    owl_core = builder.export(format="xml")
    
    # Generate alignment
    mapper = INSPIREMapper(owl_core, ifc_hash="test123")
    mapper.generate_alignment()
    
    # Validate
    validator = INSPIREValidator()
    bu_graph = mapper.get_theme_graph("BU")
    result = validator.validate_theme(bu_graph, "BU")
    
    print(f"Conforms: {result['conforms']}")
    print(f"Violations: {result['violations']}")
    
    assert result["conforms"] == True, f"Expected conformance, got violations: {result.get('violations_list', [])}"
    assert result["violations"] == 0, f"Expected 0 violations, got {result['violations']}"
    
    print("✓ Valid BU Alignment Passes Test PASSED\n")


def test_missing_conformsTo_fails():
    """Test that missing dct:conformsTo fails validation"""
    print("\n=== TEST: Missing conformsTo Fails ===")
    
    from rdflib import Graph, RDF
    from services.inspire.namespaces import INSPIRE_BU, SKOS, APP
    
    # Create invalid graph (missing dct:conformsTo)
    invalid_graph = Graph()
    
    inspire_uri = URIRef("urn:inspire:BU:GUID-001")
    bim_uri = URIRef("http://bim-gis-viewer.local/ontology#bim_GUID-001")
    
    # Add type and exactMatch, but NOT conformsTo
    invalid_graph.add((inspire_uri, RDF.type, INSPIRE_BU.Building))
    invalid_graph.add((bim_uri, SKOS.exactMatch, inspire_uri))
    
    # Validate
    validator = INSPIREValidator()
    result = validator.validate_theme(invalid_graph, "BU")
    
    print(f"Conforms: {result['conforms']}")
    print(f"Violations: {result['violations']}")
    
    assert result["conforms"] == False, "Expected validation failure"
    assert result["violations"] > 0, "Expected violations"
    
    print("✓ Missing conformsTo Fails Test PASSED\n")


def test_missing_exactMatch_fails():
    """Test that missing skos:exactMatch fails validation"""
    print("\n=== TEST: Missing exactMatch Fails ===")
    
    from rdflib import Graph, RDF
    from services.inspire.namespaces import INSPIRE_BU, DCT, INSPIRE_TG
    
    # Create invalid graph (missing skos:exactMatch)
    invalid_graph = Graph()
    
    inspire_uri = URIRef("urn:inspire:BU:GUID-001")
    
    # Add type and conformsTo, but NOT exactMatch
    invalid_graph.add((inspire_uri, RDF.type, INSPIRE_BU.Building))
    invalid_graph.add((inspire_uri, DCT.conformsTo, URIRef(INSPIRE_TG["BU"])))
    
    # Validate
    validator = INSPIREValidator()
    result = validator.validate_theme(invalid_graph, "BU")
    
    print(f"Conforms: {result['conforms']}")
    print(f"Violations: {result['violations']}")
    
    assert result["conforms"] == False, "Expected validation failure"
    assert result["violations"] > 0, "Expected violations"
    
    print("✓ Missing exactMatch Fails Test PASSED\n")


def test_violation_messages():
    """Test that violation messages are descriptive"""
    print("\n=== TEST: Violation Messages ===")
    
    from rdflib import Graph, RDF
    from services.inspire.namespaces import INSPIRE_BU
    
    # Create invalid graph (only type, missing everything else)
    invalid_graph = Graph()
    
    inspire_uri = URIRef("urn:inspire:BU:GUID-001")
    invalid_graph.add((inspire_uri, RDF.type, INSPIRE_BU.Building))
    
    # Validate
    validator = INSPIREValidator()
    result = validator.validate_theme(invalid_graph, "BU")
    
    print(f"Violations: {result['violations']}")
    if "violations_list" in result:
        for v in result["violations_list"]:
            print(f"  - {v['message']}")
    
    assert result["violations"] >= 2, "Expected at least 2 violations (conformsTo + exactMatch)"
    assert "violations_list" in result, "Expected violations_list"
    
    print("✓ Violation Messages Test PASSED\n")


if __name__ == "__main__":
    print("=" * 60)
    print("SPRINT 2B: SHACL BUILDINGS MINIMUM COMPLIANCE TESTS")
    print("=" * 60)
    
    try:
        test_valid_bu_alignment_passes()
        test_missing_conformsTo_fails()
        test_missing_exactMatch_fails()
        test_violation_messages()
        
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
