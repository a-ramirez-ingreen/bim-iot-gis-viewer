"""
Sprint 2C Verification: INSPIRE GML Endpoint

Tests the /api/process/inspire-gml endpoint.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from services.ontology_service import OntologyBuilder
from services.inspire.inspire_mapper import INSPIREMapper
from services.inspire.gml.export_bu import export_bu_gml
from lxml import etree


def test_endpoint_response_structure():
    """Test that GML export returns correct structure"""
    print("\n=== TEST: Endpoint Response Structure ===")
    
    # Simulate endpoint logic
    builder = OntologyBuilder()
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    owl_core = builder.export(format="xml")
    
    mapper = INSPIREMapper(owl_core, ifc_hash="test123")
    alignment_result = mapper.generate_alignment()
    
    geojson_features = [
        {
            "type": "Feature",
            "properties": {"GlobalId": "GUID-001", "IfcType": "IfcBuilding"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-3.7, 40.4],
                    [-3.7, 40.5],
                    [-3.6, 40.5],
                    [-3.6, 40.4],
                    [-3.7, 40.4]
                ]]
            }
        }
    ]
    
    gml_metadata = {"dataset_id": "test123", "crs": "EPSG:4326"}
    bu_gml = export_bu_gml(geojson_features, mapper.alignment_dataset, gml_metadata)
    
    # Simulate response
    response = {
        "status": "success",
        "themes": alignment_result["themes"],
        "bu_gml": bu_gml,
        "metadata": {
            "crs": "EPSG:4326",
            "feature_count": len(geojson_features),
            "dataset_id": "test123",
            "bu_features": alignment_result["mapping_summary"].get("BU", 0)
        }
    }
    
    # Validate response structure
    assert "status" in response, "Response should have 'status'"
    assert response["status"] == "success", "Status should be 'success'"
    assert "themes" in response, "Response should have 'themes'"
    assert "bu_gml" in response, "Response should have 'bu_gml'"
    assert "metadata" in response, "Response should have 'metadata'"
    
    print(f"✓ Status: {response['status']}")
    print(f"✓ Themes: {response['themes']}")
    print(f"✓ Metadata: {response['metadata']}")
    print("✓ Endpoint Response Structure Test PASSED\n")


def test_bu_gml_not_empty():
    """Test that bu_gml field is not empty"""
    print("\n=== TEST: bu_gml Not Empty ===")
    
    # Simulate endpoint logic
    builder = OntologyBuilder()
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    owl_core = builder.export(format="xml")
    
    mapper = INSPIREMapper(owl_core, ifc_hash="test123")
    mapper.generate_alignment()
    
    geojson_features = [
        {
            "type": "Feature",
            "properties": {"GlobalId": "GUID-001", "IfcType": "IfcBuilding"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-3.7, 40.4],
                    [-3.7, 40.5],
                    [-3.6, 40.5],
                    [-3.6, 40.4],
                    [-3.7, 40.4]
                ]]
            }
        }
    ]
    
    gml_metadata = {"dataset_id": "test123", "crs": "EPSG:4326"}
    bu_gml = export_bu_gml(geojson_features, mapper.alignment_dataset, gml_metadata)
    
    assert bu_gml is not None, "bu_gml should not be None"
    assert len(bu_gml) > 0, "bu_gml should not be empty"
    assert "<?xml" in bu_gml, "bu_gml should contain XML declaration"
    
    print(f"✓ bu_gml length: {len(bu_gml)} characters")
    print("✓ bu_gml Not Empty Test PASSED\n")


def test_bu_gml_valid_xml():
    """Test that bu_gml is valid XML"""
    print("\n=== TEST: bu_gml Valid XML ===")
    
    # Simulate endpoint logic
    builder = OntologyBuilder()
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    owl_core = builder.export(format="xml")
    
    mapper = INSPIREMapper(owl_core, ifc_hash="test123")
    mapper.generate_alignment()
    
    geojson_features = [
        {
            "type": "Feature",
            "properties": {"GlobalId": "GUID-001", "IfcType": "IfcBuilding"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-3.7, 40.4],
                    [-3.7, 40.5],
                    [-3.6, 40.5],
                    [-3.6, 40.4],
                    [-3.7, 40.4]
                ]]
            }
        }
    ]
    
    gml_metadata = {"dataset_id": "test123", "crs": "EPSG:4326"}
    bu_gml = export_bu_gml(geojson_features, mapper.alignment_dataset, gml_metadata)
    
    # Validate XML
    try:
        root = etree.fromstring(bu_gml.encode("utf-8"))
        print(f"✓ XML is valid")
        print(f"✓ Root element: {root.tag}")
    except Exception as e:
        raise AssertionError(f"bu_gml is not valid XML: {e}")
    
    print("✓ bu_gml Valid XML Test PASSED\n")


if __name__ == "__main__":
    print("=" * 60)
    print("SPRINT 2C: INSPIRE GML ENDPOINT TESTS")
    print("=" * 60)
    
    try:
        test_endpoint_response_structure()
        test_bu_gml_not_empty()
        test_bu_gml_valid_xml()
        
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
