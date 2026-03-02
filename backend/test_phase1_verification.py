"""
Phase 1 Verification Tests: CRS Metadata and Stable URIs

Tests verify:
1. CRS metadata is added to geometry nodes
2. sensorType domain is correctly split
3. Sensor URIs are stable (no GUID suffix)
4. ConfigRun URIs are deterministic (hash-based)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from services.ontology_service import OntologyBuilder
from rdflib import Graph, URIRef, Literal, Namespace, RDF, RDFS, OWL, XSD

# Namespaces
APP = Namespace("http://bim-gis-viewer.local/ontology#")
GEO = Namespace("http://www.opengis.net/ont/geosparql#")


def test_crs_metadata():
    """Test that CRS metadata is added to geometry nodes"""
    print("\n=== TEST: CRS Metadata ===")
    
    builder = OntologyBuilder()
    
    # Create feature with CRS
    crs_uri = URIRef("http://www.opengis.net/def/crs/EPSG/0/4326")
    wkt = "POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))"
    
    builder.add_bim_element("TEST-GUID-001", "IfcWall", "test.ifc")
    builder.add_feature("TEST-GUID-001", wkt, crs_uri=crs_uri)
    
    # Verify CRS triple exists
    geom_uri = URIRef(APP["geom_TEST-GUID-001"])
    crs_triples = list(builder.g.triples((geom_uri, APP.crs, crs_uri)))
    
    assert len(crs_triples) == 1, f"Expected 1 CRS triple, found {len(crs_triples)}"
    print(f"✓ CRS metadata correctly added: {crs_triples[0]}")
    
    # Verify WKT still exists
    wkt_triples = list(builder.g.triples((geom_uri, GEO.asWKT, None)))
    assert len(wkt_triples) == 1, "WKT literal should exist"
    print(f"✓ WKT literal preserved: {wkt_triples[0][2][:50]}...")
    
    print("✓ CRS Metadata Test PASSED\n")


def test_sensortype_domain_split():
    """Test that sensorType and configSensorType have separate domains"""
    print("\n=== TEST: SensorType Domain Split ===")
    
    builder = OntologyBuilder()
    
    # Check T-Box definitions
    # app:sensorType should have domain app:Sensor
    sensor_type_domains = list(builder.g.triples((APP.sensorType, RDFS.domain, None)))
    assert len(sensor_type_domains) == 1, f"Expected 1 domain for sensorType, found {len(sensor_type_domains)}"
    assert sensor_type_domains[0][2] == APP.Sensor, f"Expected domain Sensor, got {sensor_type_domains[0][2]}"
    print(f"✓ app:sensorType domain: {sensor_type_domains[0][2]}")
    
    # app:configSensorType should have domain app:SensorConfig
    config_type_domains = list(builder.g.triples((APP.configSensorType, RDFS.domain, None)))
    assert len(config_type_domains) == 1, f"Expected 1 domain for configSensorType, found {len(config_type_domains)}"
    assert config_type_domains[0][2] == APP.SensorConfig, f"Expected domain SensorConfig, got {config_type_domains[0][2]}"
    print(f"✓ app:configSensorType domain: {config_type_domains[0][2]}")
    
    print("✓ SensorType Domain Split Test PASSED\n")


def test_stable_sensor_uri():
    """Test that Sensor URIs are stable (no GUID suffix)"""
    print("\n=== TEST: Stable Sensor URI ===")
    
    builder = OntologyBuilder()
    
    # Add same sensor to two different BIM elements
    builder.add_bim_element("GUID-001", "IfcWall", "test.ifc")
    builder.add_bim_element("GUID-002", "IfcSlab", "test.ifc")
    
    sensor_data = {
        "sensor_id": "SEN-001",
        "type": "temperature",
        "value": 23.5,
        "status": "OK"
    }
    
    builder.add_sensor("GUID-001", sensor_data)
    builder.add_sensor("GUID-002", sensor_data)
    
    # Expected stable URI
    expected_sensor_uri = URIRef(APP["sensor_SEN-001"])
    
    # Verify sensor exists only once
    sensor_instances = list(builder.g.triples((expected_sensor_uri, RDF.type, APP.Sensor)))
    assert len(sensor_instances) == 1, f"Expected 1 sensor instance, found {len(sensor_instances)}"
    print(f"✓ Stable sensor URI: {expected_sensor_uri}")
    
    # Verify both BIM elements link to same sensor
    bim1_links = list(builder.g.triples((URIRef(APP["bim_GUID-001"]), APP.monitoredBy, expected_sensor_uri)))
    bim2_links = list(builder.g.triples((URIRef(APP["bim_GUID-002"]), APP.monitoredBy, expected_sensor_uri)))
    
    assert len(bim1_links) == 1, "BIM element 1 should link to sensor"
    assert len(bim2_links) == 1, "BIM element 2 should link to sensor"
    print(f"✓ Both BIM elements link to same sensor")
    
    print("✓ Stable Sensor URI Test PASSED\n")


def test_deterministic_configrun_uri():
    """Test that ConfigRun URIs are deterministic (hash-based)"""
    print("\n=== TEST: Deterministic ConfigRun URI ===")
    
    builder1 = OntologyBuilder()
    builder2 = OntologyBuilder()
    
    config_hash = "abc123def456"
    
    # Create ConfigRun in two separate builders with same hash
    run_uri1 = builder1.add_config_run("config.json", config_hash)
    run_uri2 = builder2.add_config_run("config.json", config_hash)
    
    # URIs should be identical
    assert run_uri1 == run_uri2, f"ConfigRun URIs should be identical: {run_uri1} vs {run_uri2}"
    print(f"✓ Deterministic ConfigRun URI: {run_uri1}")
    
    # Verify URI format
    expected_uri = URIRef(APP[f"configRun_{config_hash}"])
    assert run_uri1 == expected_uri, f"Expected {expected_uri}, got {run_uri1}"
    print(f"✓ URI format correct: configRun_{config_hash}")
    
    print("✓ Deterministic ConfigRun URI Test PASSED\n")


def test_app_crs_property_exists():
    """Test that app:crs property is defined in T-Box"""
    print("\n=== TEST: app:crs Property Definition ===")
    
    builder = OntologyBuilder()
    
    # Check that app:crs is defined as ObjectProperty
    crs_type = list(builder.g.triples((APP.crs, RDF.type, OWL.ObjectProperty)))
    assert len(crs_type) == 1, "app:crs should be defined as ObjectProperty"
    print(f"✓ app:crs is ObjectProperty")
    
    # Check domain
    crs_domain = list(builder.g.triples((APP.crs, RDFS.domain, GEO.Geometry)))
    assert len(crs_domain) == 1, "app:crs domain should be geo:Geometry"
    print(f"✓ app:crs domain: geo:Geometry")
    
    # Check range
    crs_range = list(builder.g.triples((APP.crs, RDFS.range, RDFS.Resource)))
    assert len(crs_range) == 1, "app:crs range should be rdfs:Resource"
    print(f"✓ app:crs range: rdfs:Resource")
    
    print("✓ app:crs Property Definition Test PASSED\n")


if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 1 VERIFICATION TESTS")
    print("=" * 60)
    
    try:
        test_app_crs_property_exists()
        test_crs_metadata()
        test_sensortype_domain_split()
        test_stable_sensor_uri()
        test_deterministic_configrun_uri()
        
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
