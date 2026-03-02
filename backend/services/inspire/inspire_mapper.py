"""
INSPIRE Mapper Orchestrator

Coordinates theme detection and multi-theme alignment graph generation.
Sprint 2B: Added PROV-O and DCAT metadata.
"""

from rdflib import Graph, Dataset, URIRef, Literal, RDF, Namespace
from datetime import datetime
import hashlib
from . import theme_detector
from .mappers import buildings_mapper, transport_mapper, utility_mapper
from .namespaces import PROV, DCT, INSPIRE_TG


class INSPIREMapper:
    """
    Orchestrates INSPIRE alignment graph generation from BIM-GIS core ontology.
    """
    
    def __init__(self, core_owl_string: str, ifc_hash: str = None, config_hash: str = None):
        """
        Initialize mapper with core OWL content.
        
        Args:
            core_owl_string: Serialized OWL/RDF content (XML format)
            ifc_hash: Hash of IFC file (for provenance)
            config_hash: Hash of config file (optional, for provenance)
        """
        # Parse core graph
        self.core_graph = Graph()
        self.core_graph.parse(data=core_owl_string, format="xml")
        
        # Create dataset for named graphs
        self.alignment_dataset = Dataset()
        
        # Mapping results
        self.detected_themes = set()
        self.mapping_summary = {}
        
        # Provenance data
        self.ifc_hash = ifc_hash or hashlib.sha256(core_owl_string.encode()).hexdigest()[:16]
        self.config_hash = config_hash
        self.creation_time = datetime.now()
    
    def generate_alignment(self, use_sameas: bool = False) -> dict:
        """
        Generates INSPIRE alignment graphs for all detected themes.
        
        Args:
            use_sameas: If True, use owl:sameAs; if False (default), use skos:exactMatch
        
        Returns:
            dict with keys:
                - themes: list of detected theme codes
                - mapping_summary: dict of theme -> count
        """
        # 1. Detect themes
        self.detected_themes = theme_detector.detect(self.core_graph)
        
        if not self.detected_themes:
            print("[INSPIRE] No themes detected, skipping alignment generation")
            return {
                "themes": [],
                "mapping_summary": {}
            }
        
        # 2. For each theme, invoke appropriate mapper
        for theme in self.detected_themes:
            # Create named graph for this theme
            graph_uri = URIRef(f"urn:inspire:alignment:{theme}")
            alignment_graph = self.alignment_dataset.graph(graph_uri)
            
            # Invoke theme-specific mapper
            count = 0
            if theme == "BU":
                count = buildings_mapper.map_buildings(
                    self.core_graph, alignment_graph, graph_uri, use_sameas
                )
            elif theme == "TN":
                count = transport_mapper.map_transport(
                    self.core_graph, alignment_graph, graph_uri, use_sameas
                )
            elif theme == "US":
                count = utility_mapper.map_utility(
                    self.core_graph, alignment_graph, graph_uri, use_sameas
                )
            # EMF mapper not implemented yet
            
            self.mapping_summary[theme] = count
        
        # 3. Add dataset-level metadata
        self.add_dataset_metadata()
        
        return {
            "themes": list(self.detected_themes),
            "mapping_summary": self.mapping_summary
        }
    
    def add_dataset_metadata(self):
        """
        Adds PROV-O and DCAT metadata to a separate metadata graph.
        
        Creates:
        - Dataset-level metadata (dcat:Dataset)
        - Provenance (prov:wasDerivedFrom)
        - Creation timestamp
        - Creator information
        - Conformance declarations
        """
        DCAT = Namespace("http://www.w3.org/ns/dcat#")
        XSD = Namespace("http://www.w3.org/2001/XMLSchema#")
        
        # Create metadata graph
        metadata_graph_uri = URIRef("urn:inspire:alignment:metadata")
        metadata_graph = self.alignment_dataset.graph(metadata_graph_uri)
        
        # Dataset URI (deterministic based on IFC hash)
        dataset_id = f"{self.ifc_hash}_{self.config_hash}" if self.config_hash else self.ifc_hash
        dataset_uri = URIRef(f"urn:inspire:dataset:{dataset_id}")
        
        # 1. Dataset type
        metadata_graph.add((dataset_uri, RDF.type, DCAT.Dataset))
        
        # 2. Creation timestamp
        timestamp = self.creation_time.strftime("%Y-%m-%dT%H:%M:%S")
        metadata_graph.add((dataset_uri, DCT.created, Literal(timestamp, datatype=XSD.dateTime)))
        
        # 3. Creator
        metadata_graph.add((dataset_uri, DCT.creator, Literal("BIM-GIS Viewer v2.2")))
        
        # 4. Identifier (deterministic)
        metadata_graph.add((dataset_uri, DCT.identifier, Literal(dataset_id)))
        
        # 5. Provenance - derived from core dataset
        core_dataset_uri = URIRef(f"urn:bim-gis:core:{self.ifc_hash}")
        metadata_graph.add((dataset_uri, PROV.wasDerivedFrom, core_dataset_uri))
        
        # 6. Conformance - list all TG URIs for detected themes
        for theme in self.detected_themes:
            if theme in INSPIRE_TG:
                tg_uri = URIRef(INSPIRE_TG[theme])
                metadata_graph.add((dataset_uri, DCT.conformsTo, tg_uri))
        
        print(f"[INSPIRE] Added dataset metadata: {dataset_uri}")
    
    def export_alignment_trig(self) -> str:
        """
        Exports alignment dataset as TriG format (named graphs).
        
        Returns:
            TriG serialized string
        """
        return self.alignment_dataset.serialize(format="trig")
    
    def export_alignment_nquads(self) -> str:
        """
        Exports alignment dataset as N-Quads format.
        
        Returns:
            N-Quads serialized string
        """
        return self.alignment_dataset.serialize(format="nquads")
    
    def get_theme_graph(self, theme_code: str) -> Graph:
        """
        Gets the alignment graph for a specific theme.
        
        Args:
            theme_code: Theme code (e.g., "BU")
        
        Returns:
            rdflib Graph or None if theme not found
        """
        graph_uri = URIRef(f"urn:inspire:alignment:{theme_code}")
        return self.alignment_dataset.graph(graph_uri)
    
    def get_metadata_graph(self) -> Graph:
        """
        Gets the metadata graph.
        
        Returns:
            rdflib Graph containing PROV-O and DCAT metadata
        """
        metadata_graph_uri = URIRef("urn:inspire:alignment:metadata")
        return self.alignment_dataset.graph(metadata_graph_uri)
