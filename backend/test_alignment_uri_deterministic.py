"""
Sprint 2A Verification: INSPIRE Alignment URI Determinism Tests

Tests that INSPIRE URIs are deterministic and relationships are correct.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from services.ontology_service import OntologyBuilder
from services.inspire.inspire_mapper import INSPIREMapper
from services.inspire.namespaces import OWL, DCT
from rdflib import URIRef


def test_same_guid_same_inspire_uri():
    """Test that same GUID produces same INSPIRE URI"""
    print("\n=== TEST: Same GUID Same INSPIRE URI ===")
    
    # Create two separate core graphs with same GUID
    builder1 = OntologyBuilder()
    builder1.add_bim_element("GUID-STABLE-001", "IfcBuilding", "test1.ifc")
    owl1 = builder1.export(format="xml")
    
    builder2 = OntologyBuilder()
    builder2.add_bim_element("GUID-STABLE-001", "IfcBuilding", "test2.ifc")
    owl2 = builder2.export(format="xml")
    
    # Generate alignments
    mapper1 = INSPIREMapper(owl1)
    mapper1.generate_alignment()
    
    mapper2 = INSPIREMapper(owl2)
    mapper2.generate_alignment()
    
    # Expected INSPIRE URI
    expected_uri = URIRef("urn:inspire:BU:GUID-STABLE-001")
    
    # Check both graphs have same INSPIRE URI
    bu_graph1 = mapper1.get_theme_graph("BU")
    bu_graph2 = mapper2.get_theme_graph("BU")
    
    uri1_exists = (expected_uri, None, None) in bu_graph1
    uri2_exists = (expected_uri, None, None) in bu_graph2
    
    assert uri1_exists, f"Expected URI {expected_uri} in graph 1"
    assert uri2_exists, f"Expected URI {expected_uri} in graph 2"
    
    print(f"✓ Deterministic INSPIRE URI: {expected_uri}")
    print("✓ Same GUID Same INSPIRE URI Test PASSED\n")


def test_owl_sameas_relationship():
    """Test that owl:sameAs relationship is used"""
    print("\n=== TEST: owl:sameAs Relationship ===")
    
    # Create core graph
    builder = OntologyBuilder()
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    owl_core = builder.export(format="xml")
    
    # Generate alignment
    mapper = INSPIREMapper(owl_core)
    mapper.generate_alignment()
    
    # Get BU graph
    bu_graph = mapper.get_theme_graph("BU")
    
    # Expected URIs
    bim_uri = URIRef("http://bim-gis-viewer.local/ontology#bim_GUID-001")
    inspire_uri = URIRef("urn:inspire:BU:GUID-001")
    
    # Check owl:sameAs relationship
    sameas_triples = list(bu_graph.triples((bim_uri, OWL.sameAs, inspire_uri)))
    
    assert len(sameas_triples) == 1, \
        f"Expected 1 owl:sameAs triple, found {len(sameas_triples)}"
    
    print(f"✓ owl:sameAs relationship: {bim_uri} -> {inspire_uri}")
    print("✓ owl:sameAs Relationship Test PASSED\n")


def test_dct_conformsto_present():
    """Test that dct:conformsTo metadata is present"""
    print("\n=== TEST: dct:conformsTo Present ===")
    
    # Create core graph
    builder = OntologyBuilder()
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    owl_core = builder.export(format="xml")
    
    # Generate alignment
    mapper = INSPIREMapper(owl_core)
    mapper.generate_alignment()
    
    # Get BU graph
    bu_graph = mapper.get_theme_graph("BU")
    
    # Expected URIs
    inspire_uri = URIRef("urn:inspire:BU:GUID-001")
    tg_uri = URIRef("http://inspire.ec.europa.eu/id/document/tg/bu")
    
    # Check dct:conformsTo
    conformsto_triples = list(bu_graph.triples((inspire_uri, DCT.conformsTo, tg_uri)))
    
    assert len(conformsto_triples) == 1, \
        f"Expected 1 dct:conformsTo triple, found {len(conformsto_triples)}"
    
    print(f"✓ dct:conformsTo: {inspire_uri} -> {tg_uri}")
    print("✓ dct:conformsTo Present Test PASSED\n")


def test_uri_format_consistency():
    """Test that URI format is consistent across themes"""
    print("\n=== TEST: URI Format Consistency ===")
    
    # Create core graph with multiple themes
    builder = OntologyBuilder()
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    builder.add_bim_element("GUID-002", "IfcRoad", "test.ifc")
    builder.add_bim_element("GUID-003", "IfcPipeSegment", "test.ifc")
    
    owl_core = builder.export(format="xml")
    
    # Generate alignment
    mapper = INSPIREMapper(owl_core)
    mapper.generate_alignment()
    
    # Expected URIs
    bu_uri = URIRef("urn:inspire:BU:GUID-001")
    tn_uri = URIRef("urn:inspire:TN:GUID-002")
    us_uri = URIRef("urn:inspire:US:GUID-003")
    
    # Check all URIs exist
    bu_graph = mapper.get_theme_graph("BU")
    tn_graph = mapper.get_theme_graph("TN")
    us_graph = mapper.get_theme_graph("US")
    
    assert (bu_uri, None, None) in bu_graph, "BU URI should exist"
    assert (tn_uri, None, None) in tn_graph, "TN URI should exist"
    assert (us_uri, None, None) in us_graph, "US URI should exist"
    
    # Verify format: urn:inspire:{THEME}:{GUID}
    assert str(bu_uri).startswith("urn:inspire:BU:"), "BU URI format incorrect"
    assert str(tn_uri).startswith("urn:inspire:TN:"), "TN URI format incorrect"
    assert str(us_uri).startswith("urn:inspire:US:"), "US URI format incorrect"
    
    print(f"✓ BU URI: {bu_uri}")
    print(f"✓ TN URI: {tn_uri}")
    print(f"✓ US URI: {us_uri}")
    print("✓ URI Format Consistency Test PASSED\n")


if __name__ == "__main__":
    print("=" * 60)
    print("SPRINT 2A: INSPIRE ALIGNMENT URI DETERMINISM TESTS")
    print("=" * 60)
    
    try:
        test_same_guid_same_inspire_uri()
        test_owl_sameas_relationship()
        test_dct_conformsto_present()
        test_uri_format_consistency()
        
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
