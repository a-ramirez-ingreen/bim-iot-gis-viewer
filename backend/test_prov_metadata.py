"""
Sprint 2B Verification: PROV-O Metadata Presence

Tests that PROV-O and DCAT metadata are correctly added to alignment dataset.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from services.ontology_service import OntologyBuilder
from services.inspire.inspire_mapper import INSPIREMapper
from services.inspire.namespaces import PROV, DCT
from rdflib import URIRef, Namespace


def test_prov_wasDerivedFrom_present():
    """Test that prov:wasDerivedFrom is present in metadata"""
    print("\n=== TEST: prov:wasDerivedFrom Present ===")
    
    # Create core graph
    builder = OntologyBuilder()
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    owl_core = builder.export(format="xml")
    
    # Generate alignment with provenance
    mapper = INSPIREMapper(owl_core, ifc_hash="abc123", config_hash="def456")
    mapper.generate_alignment()
    
    # Get metadata graph
    metadata_graph = mapper.get_metadata_graph()
    
    # Check for prov:wasDerivedFrom
    wasDerivedFrom_triples = list(metadata_graph.triples((None, PROV.wasDerivedFrom, None)))
    
    assert len(wasDerivedFrom_triples) > 0, "Expected prov:wasDerivedFrom triple"
    
    print(f"✓ Found prov:wasDerivedFrom: {wasDerivedFrom_triples[0]}")
    print("✓ prov:wasDerivedFrom Present Test PASSED\n")


def test_dct_created_timestamp():
    """Test that dct:created timestamp is present"""
    print("\n=== TEST: dct:created Timestamp ===")
    
    # Create core graph
    builder = OntologyBuilder()
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    owl_core = builder.export(format="xml")
    
    # Generate alignment
    mapper = INSPIREMapper(owl_core, ifc_hash="abc123")
    mapper.generate_alignment()
    
    # Get metadata graph
    metadata_graph = mapper.get_metadata_graph()
    
    # Check for dct:created
    created_triples = list(metadata_graph.triples((None, DCT.created, None)))
    
    assert len(created_triples) > 0, "Expected dct:created triple"
    
    timestamp = str(created_triples[0][2])
    assert "T" in timestamp, "Expected ISO 8601 timestamp format"
    
    print(f"✓ Found dct:created: {timestamp}")
    print("✓ dct:created Timestamp Test PASSED\n")


def test_dct_creator():
    """Test that dct:creator is present"""
    print("\n=== TEST: dct:creator ===")
    
    # Create core graph
    builder = OntologyBuilder()
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    owl_core = builder.export(format="xml")
    
    # Generate alignment
    mapper = INSPIREMapper(owl_core, ifc_hash="abc123")
    mapper.generate_alignment()
    
    # Get metadata graph
    metadata_graph = mapper.get_metadata_graph()
    
    # Check for dct:creator
    creator_triples = list(metadata_graph.triples((None, DCT.creator, None)))
    
    assert len(creator_triples) > 0, "Expected dct:creator triple"
    
    creator = str(creator_triples[0][2])
    assert "BIM-GIS Viewer" in creator, f"Expected 'BIM-GIS Viewer' in creator, got {creator}"
    
    print(f"✓ Found dct:creator: {creator}")
    print("✓ dct:creator Test PASSED\n")


def test_dct_identifier_deterministic():
    """Test that dct:identifier is deterministic based on hashes"""
    print("\n=== TEST: dct:identifier Deterministic ===")
    
    # Create core graph
    builder = OntologyBuilder()
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    owl_core = builder.export(format="xml")
    
    # Generate alignment twice with same hashes
    mapper1 = INSPIREMapper(owl_core, ifc_hash="abc123", config_hash="def456")
    mapper1.generate_alignment()
    
    mapper2 = INSPIREMapper(owl_core, ifc_hash="abc123", config_hash="def456")
    mapper2.generate_alignment()
    
    # Get identifiers
    metadata1 = mapper1.get_metadata_graph()
    metadata2 = mapper2.get_metadata_graph()
    
    id1_triples = list(metadata1.triples((None, DCT.identifier, None)))
    id2_triples = list(metadata2.triples((None, DCT.identifier, None)))
    
    assert len(id1_triples) > 0, "Expected dct:identifier in mapper1"
    assert len(id2_triples) > 0, "Expected dct:identifier in mapper2"
    
    id1 = str(id1_triples[0][2])
    id2 = str(id2_triples[0][2])
    
    assert id1 == id2, f"Expected same identifier, got {id1} vs {id2}"
    assert "abc123_def456" in id1, f"Expected hash in identifier, got {id1}"
    
    print(f"✓ Deterministic identifier: {id1}")
    print("✓ dct:identifier Deterministic Test PASSED\n")


def test_metadata_graph_separate():
    """Test that metadata is in separate named graph"""
    print("\n=== TEST: Metadata Graph Separate ===")
    
    # Create core graph
    builder = OntologyBuilder()
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    owl_core = builder.export(format="xml")
    
    # Generate alignment
    mapper = INSPIREMapper(owl_core, ifc_hash="abc123")
    mapper.generate_alignment()
    
    # Get metadata graph
    metadata_graph = mapper.get_metadata_graph()
    
    # Get BU theme graph
    bu_graph = mapper.get_theme_graph("BU")
    
    # Metadata should not be in BU graph
    prov_in_bu = list(bu_graph.triples((None, PROV.wasDerivedFrom, None)))
    assert len(prov_in_bu) == 0, "PROV metadata should not be in BU graph"
    
    # Metadata should be in metadata graph
    prov_in_metadata = list(metadata_graph.triples((None, PROV.wasDerivedFrom, None)))
    assert len(prov_in_metadata) > 0, "PROV metadata should be in metadata graph"
    
    print(f"✓ Metadata graph has {len(metadata_graph)} triples")
    print(f"✓ BU graph has {len(bu_graph)} triples (no metadata)")
    print("✓ Metadata Graph Separate Test PASSED\n")


if __name__ == "__main__":
    print("=" * 60)
    print("SPRINT 2B: PROV-O METADATA PRESENCE TESTS")
    print("=" * 60)
    
    try:
        test_prov_wasDerivedFrom_present()
        test_dct_created_timestamp()
        test_dct_creator()
        test_dct_identifier_deterministic()
        test_metadata_graph_separate()
        
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
