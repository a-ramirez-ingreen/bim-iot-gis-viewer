import json
import hashlib
from services import bim_gis

def verify_logs():
    print("--- START VERIFICATION ---")
    
    features = [{"type": "Feature", "properties": {"GlobalId": "GID-1", "IFC_Type": "IfcWall", "Sensor_ID": "SEN-001"}, "geometry": None}]
    all_props = [{"IFC_ID": "GID-1", "IFC_Type": "IfcWall", "Sensor_ID": "SEN-001"}]
    sensors = [{"sensor_id": "SEN-001", "value": 20.0}]
    config = {"sensors": [{"sensor_id": "SEN-001", "type": "Temp", "threshold": 25.0}]}
    
    config_str = json.dumps(config).encode("utf-8")
    config_hash = hashlib.sha256(config_str).hexdigest()
    
    # This should trigger all the print statements
    bim_gis.build_owl(features, all_props, sensors_list=sensors, config=config, config_hash=config_hash)

if __name__ == "__main__":
    verify_logs()
