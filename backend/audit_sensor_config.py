import json
import hashlib
from services import bim_gis
from rdflib import Graph, URIRef, RDF
from rdflib.namespace import Namespace

def audit_process():
    print("--- INICIO AUDITORÍA SENSOR CONFIG ---")

    # 1. Mock Data
    features = [
        {
            "type": "Feature",
            "properties": {
                "GlobalId": "GUID_WALL_01",
                "IFC_Type": "IfcWall",
                "Sensor_ID": "SEN-001" 
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0,0], [10,0], [10,10], [0,10], [0,0]]]
            }
        },
        {
             "type": "Feature",
            "properties": {
                "GlobalId": "GUID_WINDOW_02",
                "IFC_Type": "IfcWindow",
                "Sensor_ID": "SEN-002"
            },
            "geometry": None
        }
    ]
    
    all_props = [
        {"IFC_ID": "GUID_WALL_01", "IFC_Type": "IfcWall", "Sensor_ID": "SEN-001"},
        {"IFC_ID": "GUID_WINDOW_02", "IFC_Type": "IfcWindow", "Sensor_ID": "SEN-002"}
    ]
    
    sensors = [
        {"sensor_id": "SEN-001", "value": 22.5},
        {"sensor_id": "SEN-002", "value": 15.0} # This one has NO config in the mock below
    ]
    
    config_dict = {
        "sensors": [
            {
                "sensor_id": "SEN-001",
                "type": "Temperature",
                "threshold": 25.0,
                "unit": "C"
            }
            # SEN-002 missing intentionally to verify it DOES NOT create config
        ]
    }
    
    config_str = json.dumps(config_dict).encode('utf-8')
    config_hash = hashlib.sha256(config_str).hexdigest()

    # 2. Execute process
    print(f"[AUDIT] Ejecutando bim_gis.build_owl con {len(sensors)} sensores y configuración para 'SEN-001'...")
    owl_xml = bim_gis.build_owl(
        features, 
        all_props, 
        sensors_list=sensors, 
        config=config_dict, 
        config_hash=config_hash, 
        config_filename="audit_config.json"
    )

    # 3. Analyze Output
    g = Graph()
    g.parse(data=owl_xml, format="xml")
    
    APP = Namespace("http://bim-gis-viewer.local/ontology#")
    
    # Count SensorConfig
    configs = list(g.subjects(RDF.type, APP.SensorConfig))
    count = len(configs)
    
    with open("audit_output.txt", "w", encoding="utf-8") as f:
        f.write(f"--- INICIO AUDITORÍA SENSOR CONFIG ---\n")
        f.write(f"[AUDIT] RESULTADOS:\n")
        f.write(f"1. Instancias 'SensorConfig' encontradas en el OWL: {count}\n")
        
        for uri in configs:
            f.write(f"   -> URI Generada: {uri}\n")
            # Verify Links
            runs = list(g.objects(uri, APP.fromConfigRun))
            f.write(f"      Linked to ConfigRun: {len(runs) > 0} ({runs[0] if runs else 'None'})\n")
            
            sensors_linked = list(g.objects(uri, APP.configuresSensor))
            f.write(f"      Configures Sensors: {len(sensors_linked)} instance(s)\n")

        # Verify ConfigRun
        runs = list(g.subjects(RDF.type, APP.ConfigRun))
        f.write(f"\n2. Instancias 'ConfigRun' encontradas: {len(runs)}\n")
        if runs:
            f.write(f"   -> URI ConfigRun: {runs[0]}\n")

        # Conclusion
        if count == 1 and str(configs[0]).startswith("http://bim-gis-viewer.local/ontology#sensorConfig_SEN-001"):
            f.write("\n[ÉXITO] Auditoría correcta: Se creó 1 configuración solo para el sensor definido.\n")
        else:
            f.write(f"\n[FALLO] Auditoría inesperada. Se esperaban 1 config, obtenidos {count}.\n")

if __name__ == "__main__":
    audit_process()
