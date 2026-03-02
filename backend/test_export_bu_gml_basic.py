"""
Sprint 2C Verification: Basic GML Export

Tests GML generation for INSPIRE Buildings theme.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from services.ontology_service import OntologyBuilder
from services.inspire.inspire_mapper import INSPIREMapper
from services.inspire.gml.export_bu import export_bu_gml
from lxml import etree


def test_gml_structure_valid():
    """Test that generated GML is valid XML"""
    print("\n=== TEST: GML Structure Valid ===")
    
    # Create core graph with Buildings
    builder = OntologyBuilder()
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    owl_core = builder.export(format="xml")
    
    # Generate alignment
    mapper = INSPIREMapper(owl_core, ifc_hash="test123")
    mapper.generate_alignment()
    
    # Create mock GeoJSON features
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
    
    # Generate GML
    gml_metadata = {"dataset_id": "test123", "crs": "EPSG:4326"}
    gml_string = export_bu_gml(geojson_features, mapper.alignment_dataset, gml_metadata)
    
    # Validate XML
    try:
        root = etree.fromstring(gml_string.encode("utf-8"))
        print(f"✓ GML is valid XML")
    except Exception as e:
        raise AssertionError(f"GML is not valid XML: {e}")
    
    print("✓ GML Structure Valid Test PASSED\n")


def test_gml_has_gml_id():
    """Test that GML features have gml:id"""
    print("\n=== TEST: GML Has gml:id ===")
    
    # Create core graph
    builder = OntologyBuilder()
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    owl_core = builder.export(format="xml")
    
    # Generate alignment
    mapper = INSPIREMapper(owl_core, ifc_hash="test123")
    mapper.generate_alignment()
    
    # Create mock GeoJSON
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
    
    # Generate GML
    gml_metadata = {"dataset_id": "test123", "crs": "EPSG:4326"}
    gml_string = export_bu_gml(geojson_features, mapper.alignment_dataset, gml_metadata)
    
    # Parse and check for gml:id
    root = etree.fromstring(gml_string.encode("utf-8"))
    
    # Check dataset gml:id
    dataset_id = root.get("{http://www.opengis.net/gml/3.2}id")
    assert dataset_id is not None, "Dataset should have gml:id"
    assert "BU_DATASET_" in dataset_id, f"Dataset gml:id should contain 'BU_DATASET_', got {dataset_id}"
    
    # Check Building gml:id
    namespaces = {
        "gml": "http://www.opengis.net/gml/3.2",
        "bu-core2d": "http://inspire.ec.europa.eu/schemas/bu-core2d/4.0"
    }
    
    buildings = root.xpath("//bu-core2d:Building", namespaces=namespaces)
    assert len(buildings) > 0, "Should have at least one Building"
    
    building_id = buildings[0].get("{http://www.opengis.net/gml/3.2}id")
    assert building_id is not None, "Building should have gml:id"
    assert "BU_" in building_id, f"Building gml:id should contain 'BU_', got {building_id}"
    
    print(f"✓ Dataset gml:id: {dataset_id}")
    print(f"✓ Building gml:id: {building_id}")
    print("✓ GML Has gml:id Test PASSED\n")


def test_gml_has_srsname():
    """Test that GML geometries have srsName"""
    print("\n=== TEST: GML Has srsName ===")
    
    # Create core graph
    builder = OntologyBuilder()
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    owl_core = builder.export(format="xml")
    
    # Generate alignment
    mapper = INSPIREMapper(owl_core, ifc_hash="test123")
    mapper.generate_alignment()
    
    # Create mock GeoJSON
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
    
    # Generate GML
    gml_metadata = {"dataset_id": "test123", "crs": "EPSG:4326"}
    gml_string = export_bu_gml(geojson_features, mapper.alignment_dataset, gml_metadata)
    
    # Parse and check for srsName
    root = etree.fromstring(gml_string.encode("utf-8"))
    
    namespaces = {
        "gml": "http://www.opengis.net/gml/3.2",
        "bu-core2d": "http://inspire.ec.europa.eu/schemas/bu-core2d/4.0"
    }
    
    polygons = root.xpath("//gml:Polygon", namespaces=namespaces)
    assert len(polygons) > 0, "Should have at least one Polygon"
    
    srs_name = polygons[0].get("srsName")
    assert srs_name is not None, "Polygon should have srsName"
    assert "EPSG" in srs_name, f"srsName should contain 'EPSG', got {srs_name}"
    assert "4326" in srs_name, f"srsName should contain '4326', got {srs_name}"
    
    print(f"✓ srsName: {srs_name}")
    print("✓ GML Has srsName Test PASSED\n")


def test_gml_has_building_element():
    """Test that GML contains bu:Building element"""
    print("\n=== TEST: GML Has Building Element ===")
    
    # Create core graph
    builder = OntologyBuilder()
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    owl_core = builder.export(format="xml")
    
    # Generate alignment
    mapper = INSPIREMapper(owl_core, ifc_hash="test123")
    mapper.generate_alignment()
    
    # Create mock GeoJSON
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
    
    # Generate GML
    gml_metadata = {"dataset_id": "test123", "crs": "EPSG:4326"}
    gml_string = export_bu_gml(geojson_features, mapper.alignment_dataset, gml_metadata)
    
    # Parse and check for bu:Building
    root = etree.fromstring(gml_string.encode("utf-8"))
    
    namespaces = {
        "gml": "http://www.opengis.net/gml/3.2",
        "bu-core2d": "http://inspire.ec.europa.eu/schemas/bu-core2d/4.0"
    }
    
    buildings = root.xpath("//bu-core2d:Building", namespaces=namespaces)
    assert len(buildings) > 0, "Should have at least one bu-core2d:Building"
    
    # Sprint 2E: Check INSPIRE BU 2D geometry structure
    bu_base_ns = {
        "gml": "http://www.opengis.net/gml/3.2",
        "bu-core2d": "http://inspire.ec.europa.eu/schemas/bu-core2d/4.0",
        "bu-base": "http://inspire.ec.europa.eu/schemas/bu-base/4.0"
    }
    geom2d = root.xpath("//bu-base:geometry2D", namespaces=bu_base_ns)
    assert len(geom2d) > 0, "Building should have bu-base:geometry2D"
    
    bldg_geom = root.xpath("//bu-base:BuildingGeometry2D", namespaces=bu_base_ns)
    assert len(bldg_geom) > 0, "Should have bu-base:BuildingGeometry2D"
    
    geom_inner = root.xpath("//bu-base:BuildingGeometry2D/bu-base:geometry", namespaces=bu_base_ns)
    assert len(geom_inner) > 0, "BuildingGeometry2D should have bu-base:geometry"
    
    print(f"✓ Found {len(buildings)} bu-core2d:Building element(s)")
    print(f"✓ Found {len(geom2d)} bu-base:geometry2D element(s)")
    print(f"✓ Found {len(bldg_geom)} bu-base:BuildingGeometry2D element(s)")
    print(f"✓ Found {len(geom_inner)} bu-base:geometry element(s)")
    print("✓ GML Has Building Element Test PASSED\n")


def test_gml_coordinate_order():
    """Test that coordinates are in correct order (lon lat)"""
    print("\n=== TEST: GML Coordinate Order ===")
    
    # Create core graph
    builder = OntologyBuilder()
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    owl_core = builder.export(format="xml")
    
    # Generate alignment
    mapper = INSPIREMapper(owl_core, ifc_hash="test123")
    mapper.generate_alignment()
    
    # Create mock GeoJSON with known coordinates
    geojson_features = [
        {
            "type": "Feature",
            "properties": {"GlobalId": "GUID-001", "IfcType": "IfcBuilding"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-3.7, 40.4],  # lon, lat
                    [-3.7, 40.5],
                    [-3.6, 40.5],
                    [-3.6, 40.4],
                    [-3.7, 40.4]
                ]]
            }
        }
    ]
    
    # Generate GML
    gml_metadata = {"dataset_id": "test123", "crs": "EPSG:4326"}
    gml_string = export_bu_gml(geojson_features, mapper.alignment_dataset, gml_metadata)
    
    # Parse and check coordinates
    root = etree.fromstring(gml_string.encode("utf-8"))
    
    namespaces = {
        "gml": "http://www.opengis.net/gml/3.2"
    }
    
    pos_lists = root.xpath("//gml:posList", namespaces=namespaces)
    assert len(pos_lists) > 0, "Should have at least one posList"
    
    pos_list_text = pos_lists[0].text.strip()
    coords = pos_list_text.split()
    
    # First coordinate should be -3.7 40.4 (lon lat order)
    assert coords[0] == "-3.7", f"First coordinate should be -3.7 (lon), got {coords[0]}"
    assert coords[1] == "40.4", f"Second coordinate should be 40.4 (lat), got {coords[1]}"
    
    print(f"✓ Coordinates: {' '.join(coords[:4])}...")
    print("✓ GML Coordinate Order Test PASSED\n")


def test_gml_has_schema_location():
    """Test that GML have xsi:schemaLocation"""
    print("\n=== TEST: GML Has schemaLocation ===")
    
    builder = OntologyBuilder()
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    owl_core = builder.export(format="xml")
    mapper = INSPIREMapper(owl_core, ifc_hash="test123")
    mapper.generate_alignment()
    
    geojson_features = [{"type":"Feature","properties":{"GlobalId":"GUID-001"},"geometry":{"type":"Point","coordinates":[0,0]}}]
    gml_string = export_bu_gml(geojson_features, mapper.alignment_dataset, {"dataset_id":"test123"})
    
    root = etree.fromstring(gml_string.encode("utf-8"))
    
    xsi_ns = "http://www.w3.org/2001/XMLSchema-instance"
    schema_loc = root.get(f"{{{xsi_ns}}}schemaLocation")
    
    assert schema_loc is not None, "GML should have xsi:schemaLocation"
    assert "bu-core2d" in schema_loc, "schemaLocation should contain bu-core2d"
    assert "BuildingsCore2D.xsd" in schema_loc, "schemaLocation should point to BuildingsCore2D.xsd"
    
    print(f"✓ schemaLocation: {schema_loc[:80]}...")
    print("✓ GML Has schemaLocation Test PASSED\n")


if __name__ == "__main__":
    print("=" * 60)
    print("SPRINT 2C: BASIC GML EXPORT TESTS")
    print("=" * 60)
    
    try:
        test_gml_structure_valid()
        test_gml_has_gml_id()
        test_gml_has_srsname()
        test_gml_has_building_element()
        test_gml_coordinate_order()
        test_gml_has_schema_location()
        
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
