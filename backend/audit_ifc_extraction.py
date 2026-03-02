import ifcopenshell
import ifcopenshell.geom
from services import bim_gis

def create_mock_ifc():
    """Creates a basic IFC file with a wall and a Pset_Monitoring."""
    f = ifcopenshell.file()
    
    # 1. Organization & Context (Minimal)
    org = f.createIfcOrganization()
    app = f.createIfcApplication(org, "1.0", "TestApp", "TestApp")
    owner_hist = f.createIfcOwnerHistory(f.createIfcPersonAndOrganization(f.createIfcPerson(), org), app, None, "ADDED")
    
    project = f.createIfcProject(ifcopenshell.guid.new(), owner_hist, "Project", None, None)
    
    # 2. Geometric Context
    # Simplified (omitting full setup for properties audit)
    
    # 3. Create Element (IfcWall)
    wall = f.createIfcWall(ifcopenshell.guid.new(), owner_hist, "Wall_01", "Description", None, None, None, None)
    
    # 4. Create Pset_Monitoring
    # In IFC2x3, Psets are standard IfcPropertySet
    
    # Property: Sensor_ID
    prop_val = f.createIfcPropertySingleValue("Sensor_ID", "Description", f.createIfcText("SEN-001"), None)
    
    pset = f.createIfcPropertySet(ifcopenshell.guid.new(), owner_hist, "Pset_Monitoring", None, [prop_val])
    
    # Relate Pset to Wall
    f.createIfcRelDefinesByProperties(ifcopenshell.guid.new(), owner_hist, None, None, [wall], pset)
    
    # Add to file
    # (Entities are added by reference)
    
    file_path = "mock_test.ifc"
    f.write(file_path)
    return file_path, wall.GlobalId

def audit_extraction():
    print("--- START AUDIT IFC EXTRACTION ---")
    
    # 1. Create Data
    path, guid = create_mock_ifc()
    print(f"[SETUP] Created mock IFC at {path} with Wall GUID: {guid}")
    
    # 2. Load Model
    model = ifcopenshell.open(path)
    
    # 3. Extract Properties using current logic
    print("[TEST] Running extract_ifc_properties...")
    props_list = bim_gis.extract_ifc_properties(model, "IfcWall")
    
    # 4. Inspect Result
    target_props = next((p for p in props_list if p["IFC_ID"] == guid), None)
    
    if target_props:
        print(f"\n[RESULT] Properties for {guid}:")
        for k, v in target_props.items():
            print(f"  - {k}: {v}")
            
        if "Sensor_ID" in target_props:
             print("\n[SUCCESS] 'Sensor_ID' was extracted!")
             if target_props["Sensor_ID"] == "SEN-001":
                 print("   [PASS] Value matches 'SEN-001'")
             else:
                 print(f"   [FAIL] Value mismatch: {target_props['Sensor_ID']}")
        else:
             print("\n[FAIL] 'Sensor_ID' missing from extraction!")
    else:
        print("[FAIL] Target element not found in extraction results.")

if __name__ == "__main__":
    audit_extraction()
