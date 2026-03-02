"""
Sprint 2A Verification: INSPIRE Theme Detector Tests

Tests automatic theme detection based on IFC classes present in core graph.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from services.ontology_service import OntologyBuilder
from services.inspire import theme_detector
from rdflib import Graph


def test_detect_buildings_theme():
    """Test detection of Buildings theme (BU)"""
    print("\n=== TEST: Detect Buildings Theme ===")
    
    builder = OntologyBuilder()
    
    # Add IfcBuilding elements
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    builder.add_bim_element("GUID-002", "IfcWall", "test.ifc")
    
    # Detect themes
    themes = theme_detector.detect(builder.g)
    
    assert "BU" in themes, f"Expected 'BU' in themes, got {themes}"
    print(f"✓ Buildings theme detected: {themes}")
    print("✓ Buildings Theme Detection Test PASSED\n")


def test_detect_transport_theme():
    """Test detection of Transport Networks theme (TN)"""
    print("\n=== TEST: Detect Transport Theme ===")
    
    builder = OntologyBuilder()
    
    # Add IfcRoad elements
    builder.add_bim_element("GUID-001", "IfcRoad", "test.ifc")
    builder.add_bim_element("GUID-002", "IfcAlignment", "test.ifc")
    
    # Detect themes
    themes = theme_detector.detect(builder.g)
    
    assert "TN" in themes, f"Expected 'TN' in themes, got {themes}"
    print(f"✓ Transport theme detected: {themes}")
    print("✓ Transport Theme Detection Test PASSED\n")


def test_detect_utility_theme():
    """Test detection of Utility Services theme (US)"""
    print("\n=== TEST: Detect Utility Theme ===")
    
    builder = OntologyBuilder()
    
    # Add IfcPipeSegment elements
    builder.add_bim_element("GUID-001", "IfcPipeSegment", "test.ifc")
    builder.add_bim_element("GUID-002", "IfcValve", "test.ifc")
    
    # Detect themes
    themes = theme_detector.detect(builder.g)
    
    assert "US" in themes, f"Expected 'US' in themes, got {themes}"
    print(f"✓ Utility theme detected: {themes}")
    print("✓ Utility Theme Detection Test PASSED\n")


def test_detect_multiple_themes():
    """Test detection of multiple themes"""
    print("\n=== TEST: Detect Multiple Themes ===")
    
    builder = OntologyBuilder()
    
    # Add elements from different themes
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    builder.add_bim_element("GUID-002", "IfcRoad", "test.ifc")
    builder.add_bim_element("GUID-003", "IfcPipeSegment", "test.ifc")
    
    # Detect themes
    themes = theme_detector.detect(builder.g)
    
    assert "BU" in themes, "Expected BU theme"
    assert "TN" in themes, "Expected TN theme"
    assert "US" in themes, "Expected US theme"
    assert len(themes) == 3, f"Expected 3 themes, got {len(themes)}"
    
    print(f"✓ Multiple themes detected: {themes}")
    print("✓ Multiple Themes Detection Test PASSED\n")


def test_no_themes_detected():
    """Test no themes detected for empty graph"""
    print("\n=== TEST: No Themes Detected ===")
    
    builder = OntologyBuilder()
    
    # Don't add any BIM elements
    
    # Detect themes
    themes = theme_detector.detect(builder.g)
    
    assert len(themes) == 0, f"Expected no themes, got {themes}"
    print(f"✓ No themes detected (as expected): {themes}")
    print("✓ No Themes Detection Test PASSED\n")


def test_get_theme_classes():
    """Test getting specific theme classes"""
    print("\n=== TEST: Get Theme Classes ===")
    
    builder = OntologyBuilder()
    
    # Add multiple building elements
    builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
    builder.add_bim_element("GUID-002", "IfcWall", "test.ifc")
    builder.add_bim_element("GUID-003", "IfcSlab", "test.ifc")
    
    # Get BU theme classes
    bu_classes = theme_detector.get_theme_classes(builder.g, "BU")
    
    assert "IfcBuilding" in bu_classes, "Expected IfcBuilding"
    assert "IfcWall" in bu_classes, "Expected IfcWall"
    assert "IfcSlab" in bu_classes, "Expected IfcSlab"
    
    print(f"✓ BU theme classes found: {bu_classes}")
    print("✓ Get Theme Classes Test PASSED\n")


if __name__ == "__main__":
    print("=" * 60)
    print("SPRINT 2A: INSPIRE THEME DETECTOR TESTS")
    print("=" * 60)
    
    try:
        test_detect_buildings_theme()
        test_detect_transport_theme()
        test_detect_utility_theme()
        test_detect_multiple_themes()
        test_no_themes_detected()
        test_get_theme_classes()
        
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
