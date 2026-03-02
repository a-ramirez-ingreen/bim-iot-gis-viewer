import json
import hashlib
from services import bim_gis
from rdflib import Graph, Namespace, RDF, Literal, XSD, URIRef
from services.ontology_service import APP

def verify_sensor_type():
    print("--- START VERIFICATION SENSOR TYPE ---")
    
    # Mock Data
    features = [{"type": "Feature", "properties": {"GlobalId": "GID-1", "IFC_Type": "IfcWall", "Sensor_ID": "SEN-001"}, "geometry": None}]
    
    all_props = [{"IFC_ID": "GID-1", "IFC_Type": "IfcWall", "Sensor_ID": "SEN-001"}]
    
    # Sensor data with TYPE
    sensors = [
        {"sensor_id": "SEN-001", "value": 20.0, "type": "temperature", "status": "OK"}
    ]
    
    config = {"SEN-001": { "threshold": 25.0, "unit": "C" }}
    config_str = json.dumps(config).encode("utf-8")
    config_hash = hashlib.sha256(config_str).hexdigest()
    
    # Run Build
    try:
        owl_xml = bim_gis.build_owl(features, all_props, sensors_list=sensors, config=config, config_hash=config_hash)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return

    # Analyze
    g = Graph()
    g.parse(data=owl_xml, format="xml")
    
    # Check Sensor Individual
    print("\n[CHECK] Sensor Properties:")
    # We don't know the exact URI due to randomness/logic, search by type
    sensors_found = list(g.subjects(RDF.type, APP.Sensor))
    
    if not sensors_found:
        print("[FAIL] No Sensor individual found!")
        return

    target_sensor = sensors_found[0]
    print(f"   Sensor URI: {target_sensor}")
    
    # Check sensorType
    s_types = list(g.objects(target_sensor, APP.sensorType))
    if s_types:
        val = str(s_types[0])
        print(f"   sensorType: {val}")
        if val == "temperature":
            print("   [PASS] sensorType value matches 'temperature'.")
        else:
            print(f"   [FAIL] Value mismatch: Expected 'temperature', got '{val}'")
    else:
        print("   [FAIL] sensorType property NOT found on Sensor!")

    # Check Domain (T-Box) implicitly by existence? 
    # Or check if property definition exists.
    print("\n[CHECK] T-Box Definition:")
    domains = list(g.objects(APP.sensorType, Namespace("http://www.w3.org/2000/01/rdf-schema#").domain))
    # Note: RDFLib might not return all if not explicitly reasoned, but we added them.
    
    domain_names = [str(d).split("#")[-1] for d in domains]
    print(f"   Domains for sensorType: {domain_names}")
    
    if "Sensor" in domain_names:
        print("   [PASS] Domain 'Sensor' is defined.")
    else:
        print("   [FAIL] Domain 'Sensor' missing from T-Box.")

if __name__ == "__main__":
    verify_sensor_type()
