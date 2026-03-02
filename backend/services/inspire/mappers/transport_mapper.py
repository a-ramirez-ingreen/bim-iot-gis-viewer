"""
Transport Networks Theme Mapper (TN)

Maps BIM elements to INSPIRE Transport Networks theme.
Sprint 2B: Updated to use skos:exactMatch instead of owl:sameAs.
"""

from rdflib import Graph, URIRef, RDF
from ..namespaces import APP, INSPIRE_TN, DCT, OWL, SKOS, INSPIRE_TG


# Mapping rules: IFC class -> INSPIRE class (placeholder)
IFC_TO_INSPIRE_TN = {
    "IfcRoad": INSPIRE_TN.RoadLink,  # Placeholder
    "IfcRail": INSPIRE_TN.RailwayLink,  # Placeholder
    "IfcAlignment": INSPIRE_TN.TransportLink,  # Generic
    "IfcRailway": INSPIRE_TN.RailwayLink,
    "IfcBridge": INSPIRE_TN.TransportLink,
    "IfcTunnel": INSPIRE_TN.TransportLink
}


def map_transport(core_graph: Graph, alignment_graph: Graph, graph_uri: URIRef, use_sameas: bool = False) -> int:
    """
    Maps BIM elements to INSPIRE Transport Networks theme.
    
    Args:
        core_graph: Core BIM-GIS ontology graph
        alignment_graph: Named graph for TN alignment
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
        
        # Extract IFC class name
        ifc_class_name = str(ifc_type_uri).split("#")[-1]
        
        # Check if this IFC class maps to Transport Networks theme
        if ifc_class_name in IFC_TO_INSPIRE_TN:
            inspire_class = IFC_TO_INSPIRE_TN[ifc_class_name]
            
            # Create deterministic INSPIRE URI
            inspire_uri = URIRef(f"urn:inspire:TN:{global_id}")
            
            # Add triples to alignment graph
            alignment_graph.add((inspire_uri, RDF.type, inspire_class))
            alignment_graph.add((bim_uri, alignment_predicate, inspire_uri))
            
            # Conformance
            tg_uri = URIRef(INSPIRE_TG["TN"])
            alignment_graph.add((inspire_uri, DCT.conformsTo, tg_uri))
            
            count += 1
    
    print(f"[INSPIRE-TN] Mapped {count} elements to Transport Networks theme (using {'owl:sameAs' if use_sameas else 'skos:exactMatch'})")
    return count
