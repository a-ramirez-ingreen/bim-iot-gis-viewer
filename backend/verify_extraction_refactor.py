import ifcopenshell
import ifcopenshell.util.element
from services import bim_gis
from rdflib import Graph, Namespace, Literal, XSD, URIRef

APP = Namespace("http://bim-gis-viewer.local/ontology#")

def create_mock_ifc():
    """Creates a basic IFC file with a wall and a Pset_Monitoring."""
    f = ifcopenshell.file()
    
    org = f.createIfcOrganization()
    app = f.createIfcApplication(org, "1.0", "TestApp", "TestApp")
    owner_hist = f.createIfcOwnerHistory(f.createIfcPersonAndOrganization(f.createIfcPerson(), org), app, None, "ADDED")
    
    project = f.createIfcProject(ifcopenshell.guid.new(), owner_hist, "Project", None, None)
    
    # Create Element (IfcWall)
    wall = f.createIfcWall(ifcopenshell.guid.new(), owner_hist, "Wall_01", "Description", None, None, None, None)
    
    # Create Pset_Monitoring
    # Using IfcPropertySet and IfcPropertySingleValue
    prop_val = f.createIfcPropertySingleValue("Sensor_ID", "Description", f.createIfcText("SEN-001"), None)
    pset = f.createIfcPropertySet(ifcopenshell.guid.new(), owner_hist, "Pset_Monitoring", None, [prop_val])
    
    # Relate Pset to Wall
    f.createIfcRelDefinesByProperties(ifcopenshell.guid.new(), owner_hist, None, None, [wall], pset)
    
    file_path = "mock_refactor_test.ifc"
    f.write(file_path)
    return file_path, wall.GlobalId

def verify_refactor():
    print("--- START VERIFICATION REFACTOR ---")
    
    # 1. Create Data
    path, guid = create_mock_ifc()
    print(f"[SETUP] Created mock IFC at {path} with Wall GUID: {guid}")
    
    # 2. Load Model
    model = ifcopenshell.open(path)
    
    # 3. Extract Properties using NEW logic
    print("[TEST] Running extract_ifc_properties (New Logic)...")
    try:
        props_list = bim_gis.extract_ifc_properties(model, "IfcWall")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return

    # 4. Inspect Result (Flattening)
    target_props = next((p for p in props_list if p["IFC_ID"] == guid), None)
    
    if target_props:
        print(f"\n[RESULT] Properties for {guid}:")
        found_flattened = False
        found_promoted = False
        
        for k, v in target_props.items():
            print(f"  - {k}: {v}")
            if k == "Pset_Monitoring_Sensor_ID" and v == "SEN-001":
                found_flattened = True
            if k == "Sensor_ID" and v == "SEN-001":
                found_promoted = True
                
        if found_flattened:
             print("\n[PASS] Flattened key 'Pset_Monitoring_Sensor_ID' found!")
        else:
             print("\n[FAIL] Flattened key missing!")
             
        if found_promoted:
             print("[PASS] Promoted 'Sensor_ID' found (Backward Compat)!")
        else:
             print("[FAIL] Promoted 'Sensor_ID' missing!")
             
        if found_flattened and found_promoted:
             print("[SUCCESS] Extraction logic verified.")
    else:
        print("[FAIL] Target element not found.")
        return

    # 5. Verify Ontology Generation (Underscore support)
    print("\n[TEST] Verifying Ontology Property Creation...")
    from services.ontology_service import OntologyBuilder
    builder = OntologyBuilder()
    bim_uri = URIRef(APP[f"bim_{guid}"])
    
    builder.add_bim_properties(bim_uri, target_props)
    
    # Check graph for app:Pset_Monitoring_Sensor_ID
    prop_uri = APP.Pset_Monitoring_Sensor_ID
    
    if (bim_uri, prop_uri, None) in builder.g:
        print(f"[PASS] Property {prop_uri} exists in RDF graph!")
        val = list(builder.g.objects(bim_uri, prop_uri))[0]
        print(f"   Value: {val}")
    else:
        print(f"[FAIL] Property {prop_uri} NOT found in RDF graph!")
        # Debug: check what exists
        print("   Existing properties:")
        for p, o in builder.g.predicate_objects(bim_uri):
            print(f"   - {p}: {o}")

if __name__ == "__main__":
    import sys
    original_stdout = sys.stdout
    with open("verify_refactor_output.txt", "w") as f:
        sys.stdout = f
        try:
            verify_refactor()
        finally:
            sys.stdout = original_stdout
            
    # Print summary
    print("Verification complete. Check verify_refactor_output.txt.")
