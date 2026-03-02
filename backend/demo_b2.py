from services.ontology_service import OntologyBuilder
import sys

def demo():
    builder = OntologyBuilder()
    guid = "0123456789ABCDEF"
    sensor_id = "SEN-001"
    
    # Add B2 Elements
    builder.add_bim_element(guid, "IfcWall", "demo.ifc")
    builder.add_feature(guid, "POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))")
    
    sensor_data = {
        "sensor_id": sensor_id,
        "value": 12.5,
        "type": "Temperature",
        "status": "Normal"
    }
    builder.add_sensor(guid, sensor_data)
    
    # Print Turtle
    print(builder.export(format="turtle"))

if __name__ == "__main__":
    demo()
