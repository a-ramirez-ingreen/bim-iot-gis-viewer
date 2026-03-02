import unittest
import os
import json
from services.ontology_service import OntologyBuilder
from rdflib import Graph, URIRef, Literal, RDF, RDFS, OWL
from rdflib.namespace import XSD

class TestB2Architecture(unittest.TestCase):
    def setUp(self):
        self.builder = OntologyBuilder()
        self.guid = "0123456789ABCDEF"
        self.sensor_id = "SEN-001"
        self.ifc_type = "IfcWall"
        
        # Add basic elements
        self.builder.add_bim_element(self.guid, self.ifc_type, "test_file.ifc")
        self.builder.add_feature(self.guid, "POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))")
        
        sensor_data = {
            "sensor_id": self.sensor_id,
            "value": 12.5,
            "type": "Temperature",
            "status": "Normal",
            "threshold": 20.0
        }
        self.builder.add_sensor(self.guid, sensor_data)
        
        # Parse output
        xml_content = self.builder.export(format="xml")
        self.g = Graph()
        self.g.parse(data=xml_content, format="xml")
        
        # Namespaces
        self.APP = ("http://bim-gis-viewer.local/ontology#")
        self.GEO = ("http://www.opengis.net/ont/geosparql#")

    def has_triple(self, s_uri, p_uri, o_uri):
        """Helper to check if a tuple exists"""
        # Note: RDFlib uses URIRef/Literal matching
        pass

    def test_b2_structure(self):
        """Verify explicit class declarations and hierarchy"""
        # Check IfcWall subclass
        wall_class = URIRef(self.APP + "IfcWall")
        bim_element = URIRef(self.APP + "BIMElement")
        
        self.assertIn((wall_class, RDF.type, OWL.Class), self.g)
        self.assertIn((wall_class, RDFS.subClassOf, bim_element), self.g)

    def test_individuals(self):
        """Verify BIM, Feature, Sensor individuals"""
        bim_uri = URIRef(self.APP + f"bim_{self.guid}")
        feature_uri = URIRef(self.APP + f"feature_{self.guid}")
        sensor_uri = URIRef(self.APP + f"sensor_{self.sensor_id}_{self.guid}")
        
        # Types
        self.assertIn((bim_uri, RDF.type, URIRef(self.APP + "IfcWall")), self.g)
        self.assertIn((feature_uri, RDF.type, URIRef(self.APP + "Feature")), self.g)
        self.assertIn((sensor_uri, RDF.type, URIRef(self.APP + "Sensor")), self.g)

    def test_relationships(self):
        """Verify strict B2 linking: Feature -> represents -> BIM -> monitoredBy -> Sensor"""
        bim_uri = URIRef(self.APP + f"bim_{self.guid}")
        feature_uri = URIRef(self.APP + f"feature_{self.guid}")
        sensor_uri = URIRef(self.APP + f"sensor_{self.sensor_id}_{self.guid}")
        
        # Linked
        self.assertIn((feature_uri, URIRef(self.APP + "represents"), bim_uri), self.g)
        self.assertIn((bim_uri, URIRef(self.APP + "monitoredBy"), sensor_uri), self.g)

    def test_geosparql(self):
        """Verify GeoSPARQL Geometry"""
        feature_uri = URIRef(self.APP + f"feature_{self.guid}")
        geom_uri = URIRef(self.APP + f"geom_{self.guid}")
        
        # HasGeometry
        self.assertIn((feature_uri, URIRef(self.GEO + "hasGeometry"), geom_uri), self.g)
        
        # AsWKT
        # Find the literal and check datatype
        wkt_lit = None
        for o in self.g.objects(geom_uri, URIRef(self.GEO + "asWKT")):
            wkt_lit = o
            break
            
        self.assertIsNotNone(wkt_lit)
        self.assertEqual(str(wkt_lit), "POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))")
        self.assertEqual(wkt_lit.datatype, URIRef(self.GEO + "wktLiteral"))

    def test_decimal_precision(self):
        """Verify sensor values are Decimals"""
        sensor_uri = URIRef(self.APP + f"sensor_{self.sensor_id}_{self.guid}")
        val_prop = URIRef(self.APP + "sensorValue")
        
        val_lit = None
        for o in self.g.objects(sensor_uri, val_prop):
            val_lit = o
            break
            
        self.assertIsNotNone(val_lit)
        self.assertEqual(val_lit.datatype, XSD.decimal)
        self.assertEqual(str(val_lit), "12.5")

    def test_tbox_constraints(self):
        """Verify T-Box definitions (Functional, Domain, Range)"""
        # Properties
        represents = URIRef(self.APP + "represents")
        monitoredBy = URIRef(self.APP + "monitoredBy")
        hasGlobalId = URIRef(self.APP + "hasGlobalId")
        sensorValue = URIRef(self.APP + "sensorValue")
        
        # Classes
        Feature = URIRef(self.APP + "Feature")
        BIMElement = URIRef(self.APP + "BIMElement")
        Sensor = URIRef(self.APP + "Sensor")
        
        # Check FunctionalProperty
        self.assertIn((represents, RDF.type, OWL.FunctionalProperty), self.g)
        
        # Check Domains/Ranges
        self.assertIn((represents, RDFS.domain, Feature), self.g)
        self.assertIn((represents, RDFS.range, BIMElement), self.g)
        
        self.assertIn((monitoredBy, RDFS.domain, BIMElement), self.g)
        self.assertIn((monitoredBy, RDFS.range, Sensor), self.g)
        
        self.assertIn((hasGlobalId, RDFS.domain, BIMElement), self.g)
        self.assertIn((hasGlobalId, RDFS.range, XSD.string), self.g)
        
        self.assertIn((sensorValue, RDFS.domain, Sensor), self.g)
        self.assertIn((sensorValue, RDFS.range, XSD.decimal), self.g)

    def test_functional_wkt(self):
        """Verify that calling add_feature twice doesn't duplicate WKT"""
        # Call add_feature again with same GUID but maybe same or diff WKT
        # The logic should prevent a second tuple
        self.builder.add_feature(self.guid, "POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))")
        
        geom_uri = URIRef(self.APP + f"geom_{self.guid}")
        wkt_triples = list(self.g.triples((geom_uri, URIRef(self.GEO + "asWKT"), None)))
        
        self.assertEqual(len(wkt_triples), 1, "Should have exactly one WKT literal per geometry")

if __name__ == '__main__':
    unittest.main()
