"""
INSPIRE Theme Detector

Automatically detects which INSPIRE themes are present in a BIM-GIS core graph
based on IFC class types.
"""

from rdflib import Graph, RDF
from .namespaces import APP


# Theme detection rules: theme_code -> list of IFC class names
THEME_RULES = {
    "BU": [
        "IfcBuilding", "IfcWall", "IfcSlab", "IfcRoof", "IfcColumn",
        "IfcBeam", "IfcDoor", "IfcWindow", "IfcStair", "IfcRailing"
    ],
    "TN": [
        "IfcRoad", "IfcRail", "IfcAlignment", "IfcRailway",
        "IfcBridge", "IfcTunnel"
    ],
    "US": [
        "IfcPipeSegment", "IfcValve", "IfcFlowSegment", "IfcCableSegment",
        "IfcPipeFitting", "IfcFlowController", "IfcDistributionElement"
    ],
    "EMF": [
        "Sensor"  # Non-IFC class for monitoring facilities
    ]
}


def detect(core_graph: Graph) -> set:
    """
    Detects INSPIRE themes present in the core graph.
    
    Args:
        core_graph: rdflib Graph containing BIM-GIS core ontology
    
    Returns:
        set of theme codes (e.g., {"BU", "TN"})
    """
    detected_themes = set()
    
    # Query for all classes defined in the graph
    # Pattern: ?class rdf:type owl:Class
    # We look for app:IfcXXX classes
    
    for theme_code, ifc_classes in THEME_RULES.items():
        for ifc_class in ifc_classes:
            class_uri = APP[ifc_class]
            
            # Check if this class exists in the graph
            # Either as a class definition or as a type of an individual
            class_exists = (
                (class_uri, RDF.type, None) in core_graph or
                (None, RDF.type, class_uri) in core_graph
            )
            
            if class_exists:
                detected_themes.add(theme_code)
                print(f"[INSPIRE] Theme '{theme_code}' detected (found {ifc_class})")
                break  # One class is enough to detect the theme
    
    if not detected_themes:
        print("[INSPIRE] No INSPIRE themes detected in core graph")
    else:
        print(f"[INSPIRE] Detected themes: {detected_themes}")
    
    return detected_themes


def get_theme_classes(core_graph: Graph, theme_code: str) -> list:
    """
    Gets all IFC classes present in the graph for a specific theme.
    
    Args:
        core_graph: rdflib Graph
        theme_code: Theme code (e.g., "BU")
    
    Returns:
        List of IFC class names found
    """
    if theme_code not in THEME_RULES:
        return []
    
    found_classes = []
    for ifc_class in THEME_RULES[theme_code]:
        class_uri = APP[ifc_class]
        if (None, RDF.type, class_uri) in core_graph:
            found_classes.append(ifc_class)
    
    return found_classes
