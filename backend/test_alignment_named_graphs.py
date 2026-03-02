"""
Sprint 2A Verification: INSPIRE Alignment Named Graphs Tests

Tests that alignment graphs are properly separated using named graphs
and that core graph remains uncontaminated.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from services.ontology_service import OntologyBuilder
from services.inspire.inspire_mapper import INSPIREMapper
from rdflib import URIRef, RDF


def test_named_graph_per_theme():
    """Test that each theme gets its own named graph"""
    print("\n=== TEST: Named Graph Per Theme ===")
    
    # Create core graph with multiple themes
    builder = OntologyBuilder()
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    builder.add_bim_element("GUID-002", "IfcRoad", "test.ifc")
    
    owl_core = builder.export(format="xml")
    
    # Generate alignment
    mapper = INSPIREMapper(owl_core)
    result = mapper.generate_alignment()
    
    # Verify named graphs exist
    assert "BU" in result["themes"], "Expected BU theme"
    assert "TN" in result["themes"], "Expected TN theme"
    
    # Check named graph URIs
    bu_graph_uri = URIRef("urn:inspire:alignment:BU")
    tn_graph_uri = URIRef("urn:inspire:alignment:TN")
    
    bu_graph = mapper.get_theme_graph("BU")
    tn_graph = mapper.get_theme_graph("TN")
    
    assert len(bu_graph) > 0, "BU graph should have triples"
    assert len(tn_graph) > 0, "TN graph should have triples"
    
    print(f"✓ BU graph has {len(bu_graph)} triples")
    print(f"✓ TN graph has {len(tn_graph)} triples")
    print("✓ Named Graph Per Theme Test PASSED\n")


def test_core_graph_not_contaminated():
    """Test that core graph is not modified by alignment generation"""
    print("\n=== TEST: Core Graph Not Contaminated ===")
    
    # Create core graph
    builder = OntologyBuilder()
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    
    owl_core = builder.export(format="xml")
    
    # Count triples before alignment
    triples_before = len(builder.g)
    
    # Generate alignment
    mapper = INSPIREMapper(owl_core)
    mapper.generate_alignment()
    
    # Core graph in mapper should be unchanged
    triples_after = len(mapper.core_graph)
    
    assert triples_before == triples_after, \
        f"Core graph modified: {triples_before} -> {triples_after}"
    
    print(f"✓ Core graph unchanged: {triples_before} triples")
    print("✓ Core Graph Not Contaminated Test PASSED\n")


def test_trig_serialization():
    """Test that TriG serialization works correctly"""
    print("\n=== TEST: TriG Serialization ===")
    
    # Create core graph
    builder = OntologyBuilder()
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    builder.add_bim_element("GUID-002", "IfcRoad", "test.ifc")
    
    owl_core = builder.export(format="xml")
    
    # Generate alignment
    mapper = INSPIREMapper(owl_core)
    mapper.generate_alignment()
    
    # Export as TriG
    trig_output = mapper.export_alignment_trig()
    
    assert len(trig_output) > 0, "TriG output should not be empty"
    assert "urn:inspire:alignment:BU" in trig_output, "BU graph URI should be in TriG"
    assert "urn:inspire:alignment:TN" in trig_output, "TN graph URI should be in TriG"
    
    print(f"✓ TriG output length: {len(trig_output)} chars")
    print("✓ TriG Serialization Test PASSED\n")


def test_alignment_graph_structure():
    """Test that alignment graphs have correct structure"""
    print("\n=== TEST: Alignment Graph Structure ===")
    
    # Create core graph
    builder = OntologyBuilder()
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    
    owl_core = builder.export(format="xml")
    
    # Generate alignment
    mapper = INSPIREMapper(owl_core)
    result = mapper.generate_alignment()
    
    # Get BU graph
    bu_graph = mapper.get_theme_graph("BU")
    
    # Verify structure
    # Should have: INSPIRE URI, type, owl:sameAs, dct:conformsTo
    inspire_uri = URIRef("urn:inspire:BU:GUID-001")
    
    # Check type exists
    type_triples = list(bu_graph.triples((inspire_uri, RDF.type, None)))
    assert len(type_triples) > 0, "INSPIRE URI should have a type"
    
    print(f"✓ INSPIRE URI has type: {type_triples[0][2]}")
    print("✓ Alignment Graph Structure Test PASSED\n")


if __name__ == "__main__":
    print("=" * 60)
    print("SPRINT 2A: INSPIRE ALIGNMENT NAMED GRAPHS TESTS")
    print("=" * 60)
    
    try:
        test_named_graph_per_theme()
        test_core_graph_not_contaminated()
        test_trig_serialization()
        test_alignment_graph_structure()
        
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
