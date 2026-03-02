import unittest
import hashlib
import json
from services.ontology_service import OntologyBuilder
from rdflib import Graph, URIRef, Literal, RDF, RDFS, OWL
from rdflib.namespace import XSD

class TestConfigTraceability(unittest.TestCase):
    def setUp(self):
        self.builder = OntologyBuilder()
        self.guid = "0123456789ABCDEF"
        self.sensor_id = "SEN-001"
        self.config_filename = "test_config.json"
        
        # Mock Config Data
        self.config_content = json.dumps({
            "sensors": [
                {
                    "sensor_id": "SEN-001",
                    "type": "Temperature",
                    "threshold": 25.5,
                    "unit": "C",
                    "rule_operator": ">"
                }
            ]
        }).encode('utf-8')
        
        self.config_hash = hashlib.sha256(self.config_content).hexdigest()
        self.config_data = json.loads(self.config_content)
        
        # 1. Create ConfigRun
        self.run_uri = self.builder.add_config_run(self.config_filename, self.config_hash)
        
        # 2. Add elements
        self.builder.add_bim_element(self.guid, "IfcWall", "demo.ifc")
        self.builder.add_feature(self.guid, "POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))")
        
        # 3. Create SensorConfig and Link Sensor
        rule = self.config_data["sensors"][0]
        self.sensor_config_uri = self.builder.add_sensor_config(self.sensor_id, rule, self.run_uri)
        
        sensor_data = {
            "sensor_id": self.sensor_id,
            "value": 26.0,
            "status": "Warning"
        }
        self.builder.add_sensor(self.guid, sensor_data, self.sensor_config_uri)
        
        # Parse output
        xml_content = self.builder.export(format="xml")
        self.g = Graph()
        self.g.parse(data=xml_content, format="xml")
        self.APP = ("http://bim-gis-viewer.local/ontology#")

    def test_config_run_exists(self):
        """Verify ConfigRun instance and properties"""
        self.assertIn((self.run_uri, RDF.type, URIRef(self.APP + "ConfigRun")), self.g)
        self.assertIn((self.run_uri, URIRef(self.APP + "configHash"), Literal(self.config_hash, datatype=XSD.string)), self.g)
        self.assertIn((self.run_uri, URIRef(self.APP + "configSourceFile"), Literal(self.config_filename, datatype=XSD.string)), self.g)
        
    def test_sensor_config_linking(self):
        """Verify SensorConfig linking to Run and Sensor"""
        # Sensor -> Config
        sensor_uri = URIRef(self.APP + f"sensor_{self.sensor_id}_{self.guid}")
        self.assertIn((sensor_uri, URIRef(self.APP + "hasConfiguration"), self.sensor_config_uri), self.g)
        
        # Config -> Run
        self.assertIn((self.sensor_config_uri, URIRef(self.APP + "fromConfigRun"), self.run_uri), self.g)
        
        # Config -> Sensor
        self.assertIn((self.sensor_config_uri, URIRef(self.APP + "configuresSensor"), sensor_uri), self.g)

    def test_sensor_config_props(self):
        """Verify Config properties (threshold decimal)"""
        self.assertIn((self.sensor_config_uri, URIRef(self.APP + "sensorThreshold"), Literal("25.5", datatype=XSD.decimal)), self.g)
        self.assertIn((self.sensor_config_uri, URIRef(self.APP + "sensorUnit"), Literal("C", datatype=XSD.string)), self.g)

if __name__ == '__main__':
    unittest.main()
