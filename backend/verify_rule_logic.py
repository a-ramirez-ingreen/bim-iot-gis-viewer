import json
import hashlib
from services import bim_gis

def verify_rule_logic():
    print("--- START VERIFICATION RULE LOGIC ---")
    
    features = [{"type": "Feature", "properties": {"GlobalId": "GID-1", "IFC_Type": "IfcWall", "Sensor_ID": "SEN-001"}, "geometry": None}]
    all_props = [{"IFC_ID": "GID-1", "IFC_Type": "IfcWall", "Sensor_ID": "SEN-001"}]
    sensors = [{"sensor_id": "SEN-001", "value": 80.0}]
    
    # NEW CONFIG STRUCTURE: Dictionary by ID
    config = {
        "SEN-001": { 
            "threshold": 70.0, 
            "unit": "C", 
            "operator": ">" 
        }
    }
    
    config_str = json.dumps(config).encode("utf-8")
    config_hash = hashlib.sha256(config_str).hexdigest()
    
    # Redirect stdout to capture logs
    import sys
    original_stdout = sys.stdout
    with open("verify_rule_logs.txt", "w") as f:
        sys.stdout = f
        try:
            print("--- START VERIFICATION RULE LOGIC ---")
            print(f"[TEST] Calling build_owl with config keys: {list(config.keys())}")
            bim_gis.build_owl(features, all_props, sensors_list=sensors, config=config, config_hash=config_hash)
        finally:
            sys.stdout = original_stdout
            
    # Print file content to console (short summary)
    print("Verification complete. Logs written to verify_rule_logs.txt.")

if __name__ == "__main__":
    verify_rule_logic()
