import json
import hashlib
from services import bim_gis
from rdflib import Graph, Namespace, RDF, Literal, XSD, URIRef
from services.ontology_service import APP

def verify_changes():
    print("--- START VERIFICATION DATE & PROPS ---")
    
    # Mock Data with extra properties
    features = [{"type": "Feature", "properties": {"GlobalId": "GID-1", "IFC_Type": "IfcWall", "Sensor_ID": "SEN-001"}, "geometry": None}]
    
    all_props = [
        {
            "IFC_ID": "GID-1", 
            "IFC_Type": "IfcWall", 
            "Sensor_ID": "SEN-001",
            "FireRating": "EI60",        # String property
            "Height": 3.5,               # Decimal property
            "IsLoadBearing": True        # Boolean (should act as string/boolean? Logic attempts float then string)
        }
    ]
    
    sensors = [{"sensor_id": "SEN-001", "value": 20.0}]
    config = {"SEN-001": { "threshold": 25.0, "unit": "C" }}
    
    config_str = json.dumps(config).encode("utf-8")
    config_hash = hashlib.sha256(config_str).hexdigest()
    
    # Run Build
    import traceback
    try:
        owl_xml = bim_gis.build_owl(features, all_props, sensors_list=sensors, config=config, config_hash=config_hash)
    except Exception:
        traceback.print_exc()
        return
    
    # Analyze
    g = Graph()
    g.parse(data=owl_xml, format="xml")
    
    APP = Namespace("http://bim-gis-viewer.local/ontology#")
    
    # 1. Check Date Format
    print("\n[CHECK 1] Date Format:")
    runs = list(g.subjects(RDF.type, APP.ConfigRun))
    if runs:
        # Get generatedAt
        gen_at = list(g.objects(runs[0], APP.generatedAt))
        if gen_at:
            val = str(gen_at[0])
            print(f"   ConfigRun generatedAt: {val}")
            if "." in val and len(val.split(".")[-1]) > 3: # Microseconds check (roughly)
                 print("   [FAIL] Microseconds detected!")
            else:
                 print("   [PASS] Format looks correct (no microseconds).")
    
    # 2. Check BIM Properties
    print("\n[CHECK 2] BIM Properties:")
    bim_uri = URIRef("http://bim-gis-viewer.local/ontology#bim_GID-1")
    
    # Check FireRating
    fr = list(g.objects(bim_uri, APP.FireRating))
    print(f"   FireRating: {fr[0] if fr else 'None'} (Expected 'EI60')")
    
    # Check Height
    ht = list(g.objects(bim_uri, APP.Height))
    print(f"   Height: {ht[0] if ht else 'None'} (Expected '3.5'^^xsd:decimal)")
    
    if fr and str(fr[0]) == "EI60" and ht and str(ht[0]) == "3.5":
        print("   [PASS] Properties added correctly.")
    else:
        print("   [FAIL] Missing or incorrect properties.")

if __name__ == "__main__":
    verify_changes()
