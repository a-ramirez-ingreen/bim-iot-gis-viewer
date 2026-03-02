"""
Buildings Theme Mapper (BU)

Maps BIM elements to INSPIRE Buildings theme.
Sprint 2B: Updated to use skos:exactMatch instead of owl:sameAs.
"""

from rdflib import Graph, URIRef, RDF, Literal
from ..namespaces import APP, INSPIRE_BU, DCT, OWL, SKOS, INSPIRE_TG


# Mapping rules: IFC class -> INSPIRE class
IFC_TO_INSPIRE_BU = {
    "IfcBuilding": INSPIRE_BU.Building,
    "IfcWall": INSPIRE_BU.BuildingPart,
    "IfcSlab": INSPIRE_BU.BuildingPart,
    "IfcRoof": INSPIRE_BU.BuildingPart,
    "IfcColumn": INSPIRE_BU.BuildingPart,
    "IfcBeam": INSPIRE_BU.BuildingPart,
    "IfcDoor": INSPIRE_BU.BuildingPart,
    "IfcWindow": INSPIRE_BU.BuildingPart,
    "IfcStair": INSPIRE_BU.BuildingPart,
    "IfcRailing": INSPIRE_BU.BuildingPart
}


def map_buildings(core_graph: Graph, alignment_graph: Graph, graph_uri: URIRef, use_sameas: bool = False) -> int:
    """
    Maps BIM elements to INSPIRE Buildings theme.
    
    Args:
        core_graph: Core BIM-GIS ontology graph
        alignment_graph: Named graph for BU alignment
        graph_uri: URI of the named graph
        use_sameas: If True, use owl:sameAs; if False (default), use skos:exactMatch
    
    Returns:
        Number of elements mapped
    """
    count = 0
    
    # Choose alignment predicate
    alignment_predicate = OWL.sameAs if use_sameas else SKOS.exactMatch
    
    # Query all BIM elements with their types
    query = """
    PREFIX app: <http://bim-gis-viewer.local/ontology#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    
    SELECT ?bim_element ?ifc_type ?global_id
    WHERE {
        ?bim_element rdf:type ?ifc_type .
        ?bim_element app:hasGlobalId ?global_id .
        
        FILTER(STRSTARTS(STR(?ifc_type), STR(app:Ifc)))
    }
    """
    
    results = core_graph.query(query)
    
    for row in results:
        bim_uri = row.bim_element
        ifc_type_uri = row.ifc_type
        global_id = str(row.global_id)
        
        # Extract IFC class name from URI
        ifc_class_name = str(ifc_type_uri).split("#")[-1]
        
        # Check if this IFC class maps to Buildings theme
        if ifc_class_name in IFC_TO_INSPIRE_BU:
            inspire_class = IFC_TO_INSPIRE_BU[ifc_class_name]
            
            # Create deterministic INSPIRE URI
            inspire_uri = URIRef(f"urn:inspire:BU:{global_id}")
            
            # Add triples to alignment graph
            # 1. Type
            alignment_graph.add((inspire_uri, RDF.type, inspire_class))
            
            # 2. Alignment relationship (skos:exactMatch or owl:sameAs)
            alignment_graph.add((bim_uri, alignment_predicate, inspire_uri))
            
            # 3. Conformance to INSPIRE Technical Guidelines
            tg_uri = URIRef(INSPIRE_TG["BU"])
            alignment_graph.add((inspire_uri, DCT.conformsTo, tg_uri))
            
            count += 1
    
    print(f"[INSPIRE-BU] Mapped {count} elements to Buildings theme (using {'owl:sameAs' if use_sameas else 'skos:exactMatch'})")
    return count
