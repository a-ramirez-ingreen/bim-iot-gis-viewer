"""
Utility and Government Services Theme Mapper (US)

Maps BIM elements to INSPIRE Utility Services theme.
Sprint 2B: Updated to use skos:exactMatch instead of owl:sameAs.
"""

from rdflib import Graph, URIRef, RDF
from ..namespaces import APP, INSPIRE_US, DCT, OWL, SKOS, INSPIRE_TG


# Mapping rules: IFC class -> INSPIRE class (placeholder)
IFC_TO_INSPIRE_US = {
    "IfcPipeSegment": INSPIRE_US.Pipe,  # Placeholder
    "IfcValve": INSPIRE_US.Appurtenance,  # Placeholder
    "IfcFlowSegment": INSPIRE_US.UtilityLink,  # Generic
    "IfcCableSegment": INSPIRE_US.Cable,  # Placeholder
    "IfcPipeFitting": INSPIRE_US.Appurtenance,
    "IfcFlowController": INSPIRE_US.Appurtenance,
    "IfcDistributionElement": INSPIRE_US.UtilityLink
}


def map_utility(core_graph: Graph, alignment_graph: Graph, graph_uri: URIRef, use_sameas: bool = False) -> int:
    """
    Maps BIM elements to INSPIRE Utility Services theme.
    
    Args:
        core_graph: Core BIM-GIS ontology graph
        alignment_graph: Named graph for US alignment
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
        
        # Check if this IFC class maps to Utility Services theme
        if ifc_class_name in IFC_TO_INSPIRE_US:
            inspire_class = IFC_TO_INSPIRE_US[ifc_class_name]
            
            # Create deterministic INSPIRE URI
            inspire_uri = URIRef(f"urn:inspire:US:{global_id}")
            
            # Add triples to alignment graph
            alignment_graph.add((inspire_uri, RDF.type, inspire_class))
            alignment_graph.add((bim_uri, alignment_predicate, inspire_uri))
            
            # Conformance
            tg_uri = URIRef(INSPIRE_TG["US"])
            alignment_graph.add((inspire_uri, DCT.conformsTo, tg_uri))
            
            count += 1
    
    print(f"[INSPIRE-US] Mapped {count} elements to Utility Services theme (using {'owl:sameAs' if use_sameas else 'skos:exactMatch'})")
    return count
