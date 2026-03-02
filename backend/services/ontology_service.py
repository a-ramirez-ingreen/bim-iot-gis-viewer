import rdflib
from rdflib import Graph, URIRef, Literal, Namespace, RDF, RDFS, OWL, XSD
from datetime import datetime
import decimal

# --- NAMESPACES ---
APP = Namespace("http://bim-gis-viewer.local/ontology#")
GEO = Namespace("http://www.opengis.net/ont/geosparql#")

class OntologyBuilder:
    def __init__(self, base_uri="http://bim-gis-viewer.local/resource/"):
        self.g = Graph()
        self.base_uri = base_uri
        self.bind_namespaces()
        self.init_tbox()
        
        # Cache for created IfcType classes to avoid redundant declarations
        self.declared_ifc_types = set()

    def bind_namespaces(self):
        """Bind prefixes for readable XML/Turtle output."""
        self.g.bind("app", APP)
        self.g.bind("geo", GEO)
        self.g.bind("owl", OWL)
        self.g.bind("xsd", XSD)

    def init_tbox(self):
        """Initialize T-Box: Classes and Properties."""
        # 1. Base Classes
        self.g.add((APP.BIMElement, RDF.type, OWL.Class))
        self.g.add((APP.Feature, RDF.type, OWL.Class))
        self.g.add((APP.Sensor, RDF.type, OWL.Class))
        
        # 2. Object Properties
        # Feature -> represents -> BIMElement
        self.g.add((APP.represents, RDF.type, OWL.ObjectProperty))
        self.g.add((APP.represents, RDF.type, OWL.FunctionalProperty)) # 1 Feature represents 1 BIMElement
        self.g.add((APP.represents, RDFS.domain, APP.Feature))
        self.g.add((APP.represents, RDFS.range, APP.BIMElement))

        # BIMElement -> monitoredBy -> Sensor
        self.g.add((APP.monitoredBy, RDF.type, OWL.ObjectProperty))
        self.g.add((APP.monitoredBy, RDFS.domain, APP.BIMElement))
        self.g.add((APP.monitoredBy, RDFS.range, APP.Sensor))
        
        # GeoSPARQL Properties (External)
        self.g.add((GEO.hasGeometry, RDF.type, OWL.ObjectProperty))
        self.g.add((GEO.asWKT, RDF.type, OWL.DatatypeProperty))
        
        # CRS Property (for INSPIRE compliance)
        self.g.add((APP.crs, RDF.type, OWL.ObjectProperty))
        self.g.add((APP.crs, RDFS.domain, GEO.Geometry))
        self.g.add((APP.crs, RDFS.range, RDFS.Resource))  # URI to CRS definition

        # 3. Data Properties
        # GlobalId
        self.g.add((APP.hasGlobalId, RDF.type, OWL.DatatypeProperty))
        self.g.add((APP.hasGlobalId, RDFS.domain, APP.BIMElement))
        self.g.add((APP.hasGlobalId, RDFS.range, XSD.string))

        self.g.add((APP.sourceFile, RDF.type, OWL.DatatypeProperty))
        self.g.add((APP.processingTimestamp, RDF.type, OWL.DatatypeProperty))
        
        # Sensor Props
        self.g.add((APP.sensorId, RDF.type, OWL.DatatypeProperty))
        self.g.add((APP.sensorId, RDFS.domain, APP.Sensor))
        self.g.add((APP.sensorId, RDFS.range, XSD.string))

        # Sensor Value (Decimal)
        self.g.add((APP.sensorValue, RDF.type, OWL.DatatypeProperty))
        self.g.add((APP.sensorValue, RDFS.domain, APP.Sensor))
        self.g.add((APP.sensorValue, RDFS.range, XSD.decimal))

        # Sensor Status
        self.g.add((APP.sensorStatus, RDF.type, OWL.DatatypeProperty))
        self.g.add((APP.sensorStatus, RDFS.domain, APP.Sensor))
        self.g.add((APP.sensorStatus, RDFS.range, XSD.string))

        # 4. Config Traceability (T-Box)
        self.g.add((APP.ConfigRun, RDF.type, OWL.Class))
        self.g.add((APP.SensorConfig, RDF.type, OWL.Class))
        
        # Object Properties
        self.g.add((APP.hasConfiguration, RDF.type, OWL.ObjectProperty))
        self.g.add((APP.hasConfiguration, RDFS.domain, APP.Sensor))
        self.g.add((APP.hasConfiguration, RDFS.range, APP.SensorConfig))
        
        self.g.add((APP.fromConfigRun, RDF.type, OWL.ObjectProperty))
        self.g.add((APP.fromConfigRun, RDFS.domain, APP.SensorConfig))
        self.g.add((APP.fromConfigRun, RDFS.range, APP.ConfigRun))
        
        self.g.add((APP.configuresSensor, RDF.type, OWL.ObjectProperty))
        self.g.add((APP.configuresSensor, RDFS.domain, APP.SensorConfig))
        self.g.add((APP.configuresSensor, RDFS.range, APP.Sensor))

        # Data Properties (ConfigRun)
        self.g.add((APP.generatedAt, RDF.type, OWL.DatatypeProperty))
        self.g.add((APP.generatedAt, RDFS.domain, APP.ConfigRun)) # And Ontology
        self.g.add((APP.generatedAt, RDFS.range, XSD.dateTime))
        
        self.g.add((APP.configSourceFile, RDF.type, OWL.DatatypeProperty))
        self.g.add((APP.configSourceFile, RDFS.domain, APP.ConfigRun))
        self.g.add((APP.configSourceFile, RDFS.range, XSD.string))
        
        self.g.add((APP.configHash, RDF.type, OWL.DatatypeProperty))
        self.g.add((APP.configHash, RDFS.domain, APP.ConfigRun))
        self.g.add((APP.configHash, RDFS.range, XSD.string))

        # Data Properties (SensorConfig)
        self.g.add((APP.sensorThreshold, RDF.type, OWL.DatatypeProperty))
        self.g.add((APP.sensorThreshold, RDFS.domain, APP.SensorConfig))
        self.g.add((APP.sensorThreshold, RDFS.range, XSD.decimal))
        
        # SPLIT sensorType domain to avoid OWL intersection semantics
        # Sensor instances use app:sensorType
        self.g.add((APP.sensorType, RDF.type, OWL.DatatypeProperty))
        self.g.add((APP.sensorType, RDFS.domain, APP.Sensor))
        self.g.add((APP.sensorType, RDFS.range, XSD.string))
        
        # SensorConfig instances use app:configSensorType
        self.g.add((APP.configSensorType, RDF.type, OWL.DatatypeProperty))
        self.g.add((APP.configSensorType, RDFS.domain, APP.SensorConfig))
        self.g.add((APP.configSensorType, RDFS.range, XSD.string))
        
        self.g.add((APP.sensorUnit, RDF.type, OWL.DatatypeProperty))
        self.g.add((APP.sensorUnit, RDFS.domain, APP.SensorConfig))
        self.g.add((APP.sensorUnit, RDFS.range, XSD.string))

        self.g.add((APP.ruleOperator, RDF.type, OWL.DatatypeProperty))
        self.g.add((APP.ruleOperator, RDFS.domain, APP.SensorConfig))
        self.g.add((APP.ruleOperator, RDFS.range, XSD.string))

        # 5. Metadata
        ontology_uri = URIRef("http://bim-gis-viewer.local/ontology")
        self.g.add((ontology_uri, RDF.type, OWL.Ontology))
        self.g.add((ontology_uri, OWL.versionInfo, Literal("2.2 (INSPIRE Preparation - Phase 1)")))
        self.g.add((ontology_uri, APP.generatedAt, Literal(datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), datatype=XSD.dateTime)))

    def _ensure_ifc_class(self, ifc_type_name):
        """Dynamically declare app:<IfcType> subclass of app:BIMElement."""
        if ifc_type_name in self.declared_ifc_types:
            return
        
        ifc_class_uri = APP[ifc_type_name]
        self.g.add((ifc_class_uri, RDF.type, OWL.Class))
        self.g.add((ifc_class_uri, RDFS.subClassOf, APP.BIMElement))
        self.declared_ifc_types.add(ifc_type_name)

    def add_bim_element(self, global_id, ifc_type, source_file):
        """
        Creates a BIM instance: bim_<GlobalId>.
        Declares its type as app:<IfcType>.
        """
        self._ensure_ifc_class(ifc_type)
        
        bim_uri = URIRef(APP[f"bim_{global_id}"])
        type_uri = APP[ifc_type]
        
        self.g.add((bim_uri, RDF.type, type_uri))
        self.g.add((bim_uri, APP.hasGlobalId, Literal(global_id, datatype=XSD.string)))
        self.g.add((bim_uri, APP.sourceFile, Literal(source_file, datatype=XSD.string)))
        
        return bim_uri

    def add_bim_properties(self, bim_uri, properties_dict):
        """
        Dynamically adds semantic properties to a BIM Element.
        properties_dict: Key-Value pairs from IFC Psets.
        """
        for key, val in properties_dict.items():
            # Skip internal/metadata keys
            if key in ["GlobalId", "IFC_ID", "Source_File", "Sensor_ID", "centroid", "IFC_Type"]:
                continue
            
            # Skip complex types (dicts/lists) - only primitives
            if isinstance(val, (dict, list)):
                continue

            # Sanitize key for URI (alphanumeric + underscore)
            safe_key = "".join(c for c in key if c.isalnum() or c == "_")
            if not safe_key: continue
            
            prop_uri = APP[safe_key]
            
            # 1. Define Property if new (Auto-TBox)
            if (prop_uri, RDF.type, None) not in self.g:
                self.g.add((prop_uri, RDF.type, OWL.DatatypeProperty))
                self.g.add((prop_uri, RDFS.domain, APP.BIMElement))
                
            # 2. Add Value (Typed)
            try:
                # Check for strictly numeric string
                float(val)
                # Use Decimal for high precision/reasoner compatibility
                lit = Literal(str(val), datatype=XSD.decimal)
            except:
                lit = Literal(str(val), datatype=XSD.string)
                
            self.g.add((bim_uri, prop_uri, lit))

    def add_feature(self, global_id, wkt_string, crs_uri=None):
        """
        Creates a Feature instance: feature_<GlobalId>.
        Links to BIM element: feature_X app:represents bim_X.
        Adds Geometry: feature_X geo:hasGeometry geom_X.
        
        Args:
            global_id: GlobalId of the BIM element
            wkt_string: WKT representation of geometry
            crs_uri: Optional URIRef to CRS definition (e.g., URIRef("http://www.opengis.net/def/crs/EPSG/0/4326"))
        """
        feature_uri = URIRef(APP[f"feature_{global_id}"])
        bim_uri = URIRef(APP[f"bim_{global_id}"])
        geom_uri = URIRef(APP[f"geom_{global_id}"])
        
        # 1. Feature Instance
        self.g.add((feature_uri, RDF.type, APP.Feature))
        
        # 2. Link to BIM
        self.g.add((feature_uri, APP.represents, bim_uri))
        
        # 3. GeoSPARQL Geometry
        if wkt_string:
            self.g.add((feature_uri, GEO.hasGeometry, geom_uri))
            self.g.add((geom_uri, RDF.type, GEO.Geometry))
            
            # Safeguard: Check if WKT already exists to avoid SHACL violation (Functional Property)
            if (geom_uri, GEO.asWKT, None) not in self.g:
                self.g.add((geom_uri, GEO.asWKT, Literal(wkt_string, datatype=GEO.wktLiteral)))
            
            # Add CRS metadata if provided (INSPIRE requirement)
            if crs_uri:
                self.g.add((geom_uri, APP.crs, crs_uri))

    def add_config_run(self, config_source, config_hash):
        """
        Creates a ConfigRun instance for this execution.
        URI is deterministic based on config_hash for reproducibility.
        """
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        
        # Deterministic URI based on hash (not timestamp)
        run_uri = URIRef(APP[f"configRun_{config_hash}"])
        
        self.g.add((run_uri, RDF.type, APP.ConfigRun))
        self.g.add((run_uri, APP.generatedAt, Literal(timestamp, datatype=XSD.dateTime)))
        self.g.add((run_uri, APP.configSourceFile, Literal(config_source, datatype=XSD.string)))
        self.g.add((run_uri, APP.configHash, Literal(config_hash, datatype=XSD.string)))
        
        return run_uri

    def add_sensor_config(self, sensor_id, config_data, run_uri):
        """
        Creates a SensorConfig instance linked to the ConfigRun.
        """
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        ts_clean = timestamp.replace(":", "").replace("-", "").replace(".", "")
        config_uri = URIRef(APP[f"sensorConfig_{sensor_id}_{ts_clean}"])
        
        self.g.add((config_uri, RDF.type, APP.SensorConfig))
        self.g.add((config_uri, APP.fromConfigRun, run_uri))
        
        # Properties from config (use configSensorType for SensorConfig)
        if "type" in config_data:
            self.g.add((config_uri, APP.configSensorType, Literal(config_data["type"], datatype=XSD.string)))
            
        if "threshold" in config_data:
             print(f"[DEBUG] Creating SensorConfig: {config_uri}")
             print(f"[DEBUG]   Threshold: {config_data['threshold']}")
             self.g.add((config_uri, APP.sensorThreshold, Literal(str(config_data["threshold"]), datatype=XSD.decimal)))
             
        if "unit" in config_data:
            self.g.add((config_uri, APP.sensorUnit, Literal(config_data["unit"], datatype=XSD.string)))

        if "rule_operator" in config_data: # Assuming key is rule_operator or similar
            self.g.add((config_uri, APP.ruleOperator, Literal(config_data["rule_operator"], datatype=XSD.string)))
            
        return config_uri

    def add_sensor(self, global_id, sensor_data, sensor_config_uri=None):
        """
        Creates a Sensor instance: sensor_<SensorID> (STABLE URI).
        Links BIM element to Sensor: bim_X app:monitoredBy sensor_Y.
        Optionally links to SensorConfig.
        
        Note: Sensor URI is now stable (no global_id suffix) to avoid duplicates
        when same sensor monitors multiple elements.
        """
        sensor_id = sensor_data.get("sensor_id", "UNKNOWN")
        
        # STABLE URI (no global_id suffix)
        sensor_uri = URIRef(APP[f"sensor_{sensor_id}"])
        bim_uri = URIRef(APP[f"bim_{global_id}"])

        # 1. Sensor Instance (only add if not already exists)
        if (sensor_uri, RDF.type, APP.Sensor) not in self.g:
            self.g.add((sensor_uri, RDF.type, APP.Sensor))
            
            # 3. Link Config (if available)
            if sensor_config_uri:
                self.g.add((sensor_uri, APP.hasConfiguration, sensor_config_uri))
                self.g.add((sensor_config_uri, APP.configuresSensor, sensor_uri))
            
            # 4. Properties (Strict Decimal)
            self.g.add((sensor_uri, APP.sensorId, Literal(sensor_id, datatype=XSD.string)))
            
            val = sensor_data.get("value")
            if val is not None:
                 # Force Decimal
                 self.g.add((sensor_uri, APP.sensorValue, Literal(str(val), datatype=XSD.decimal)))
                 
            status = sensor_data.get("status")
            if status:
                self.g.add((sensor_uri, APP.sensorStatus, Literal(status, datatype=XSD.string)))

            # 5. Sensor Type (use sensorType for Sensor instances)
            s_type = sensor_data.get("type")
            if s_type:
                 self.g.add((sensor_uri, APP.sensorType, Literal(s_type, datatype=XSD.string)))
        
        # 2. Link BIM -> Sensor (always add, can have multiple BIM elements per sensor)
        self.g.add((bim_uri, APP.monitoredBy, sensor_uri))

    def export(self, format="xml"):
        """Serialize as RDF/XML (default) or other formats."""
        # [DEBUG] Graph Stats
        print(f"[DEBUG] Total Triples before export: {len(self.g)}")
        n_configs = len(list(self.g.subjects(RDF.type, APP.SensorConfig)))
        print(f"[DEBUG] Total SensorConfig instances: {n_configs}")
        
        return self.g.serialize(format=format)
