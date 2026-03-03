import ifcopenshell
import ifcopenshell.geom
import json
import os
from shapely.geometry import Polygon, MultiPolygon, shape
from shapely.ops import unary_union
import numpy as np
from pyproj import Transformer

from dotenv import load_dotenv
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

# Cargar variables de entorno
load_dotenv()

import math

def evaluate_sensor(sensor, config):
    """
    Evalúa el estado del sensor basándose en la configuración.
    Enriquece el diccionario del sensor con 'threshold' y 'status'.
    config: Dict { "SENSOR_ID": { "threshold": X, ... } }
    """
    sid = str(sensor.get("sensor_id"))
    
    # Buscar configuración por ID
    rule = config.get(sid)
    
    if not rule:
        print(f"[LOG] Warning: No config found for sensor '{sid}'. Skipping evaluation.")
        return None
        
    threshold = rule.get("threshold")
    if threshold is None:
        print(f"[LOG] Warning: No threshold defined for sensor '{sid}'.")
        return None
        
    value = sensor.get("value")
    # Asegurar tipos numéricos
    try:
        val_num = float(value)
        thr_num = float(threshold)
    except:
        print(f"[LOG] Error: Non-numeric value/threshold for sensor {sid}")
        return None
        
    # Operator logic (Default >)
    operator = rule.get("operator", ">")
    status = "OK"
    
    if operator == ">":
        if val_num > thr_num: status = "ALERT"
    elif operator == "<":
        if val_num < thr_num: status = "ALERT"
    elif operator == ">=":
        if val_num >= thr_num: status = "ALERT"
    elif operator == "<=":
        if val_num <= thr_num: status = "ALERT"
        
    # Enriquecer datos
    sensor["threshold"] = thr_num
    sensor["status"] = status
    
    return sensor



def get_georeferencing_data(ifc_model):
    """
    Detects native IFC georeferencing (IfcMapConversion, IfcProjectedCRS).
    Returns a dictionary with georef data or None.
    """
    georef = {
        "is_georeferenced": False,
        "crs": None,
        "map_conversion": None
    }

    try:
        # 1. Look for IfcProjectedCRS
        projected_crs = ifc_model.by_type("IfcProjectedCRS")
        if projected_crs:
            crs_entity = projected_crs[0]
            # Try to construct an EPSG code or name
            if crs_entity.Name:
                georef["crs"] = crs_entity.Name 
            # Potentially map 'EPSG:XXXX' from Name or Description if available
            georef["is_georeferenced"] = True

        # 2. Look for IfcMapConversion (The most critical part for affine transform)
        map_conversions = ifc_model.by_type("IfcMapConversion")
        if map_conversions:
            mc = map_conversions[0]
            georef["map_conversion"] = {
                "Eastings": mc.Eastings if mc.Eastings else 0.0,
                "Northings": mc.Northings if mc.Northings else 0.0,
                "OrthogonalHeight": mc.OrthogonalHeight if mc.OrthogonalHeight else 0.0,
                "XAxisAbscissa": mc.XAxisAbscissa if mc.XAxisAbscissa else 1.0,
                "XAxisOrdinate": mc.XAxisOrdinate if mc.XAxisOrdinate else 0.0,
                "Scale": mc.Scale if mc.Scale else 1.0
            }
            georef["is_georeferenced"] = True
            
    except Exception as e:
        print(f"Error detecting georeferencing: {e}")

    return georef

def process_geometry_chunk_native(file_path, guids, georef_data=None):
    """
    Worker function that extracts geometry in NATIVE coordinates.
    Applies IfcMapConversion if present, but NO CRS transformation.
    
    Returns: List of GeoJSON-like features with native coordinates.
    """
    import ifcopenshell
    import ifcopenshell.geom
    from shapely.geometry import Polygon, MultiPolygon
    from shapely.ops import unary_union
    import math
    
    try:
        model = ifcopenshell.open(file_path)
        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS, True)
            
        # Prepare Map Conversion Constants
        mc = None
        if georef_data and georef_data.get("map_conversion"):
            mc = georef_data["map_conversion"]
            # Calculate rotation angle from XAxis
            mc["theta"] = math.atan2(mc["XAxisOrdinate"], mc["XAxisAbscissa"])
            mc["cos_theta"] = math.cos(mc["theta"])
            mc["sin_theta"] = math.sin(mc["theta"])
        
        chunk_results = []
        for guid in guids:
            try:
                entity = model.by_guid(guid)
                if not entity: continue
                
                shape = ifcopenshell.geom.create_shape(settings, entity)
                faces = shape.geometry.faces
                verts = shape.geometry.verts

                polygons = []
                unique_triangles = set()

                for i in range(0, len(faces), 3):
                    coords = []
                    for j in range(3):
                        idx = faces[i + j] * 3
                        x, y, _ = verts[idx : idx + 3]
                        
                        # Apply ONLY IfcMapConversion (if present)
                        # This transforms from IFC local coords to projected CRS coords
                        if mc:
                            # Apply Scale
                            sx = x * mc["Scale"]
                            sy = y * mc["Scale"]
                            
                            # Apply Rotation and Translation
                            px = (sx * mc["cos_theta"] - sy * mc["sin_theta"]) + mc["Eastings"]
                            py = (sx * mc["sin_theta"] + sy * mc["cos_theta"]) + mc["Northings"]
                            
                            x, y = px, py

                        # NO CRS transformation here - coordinates remain in native/projected CRS
                        coords.append([x, y])

                    if coords[0] != coords[-1]:
                        coords.append(coords[0])

                    key = tuple(map(tuple, sorted(coords)))
                    if key not in unique_triangles:
                        unique_triangles.add(key)
                        polygons.append(Polygon(coords))

                full_shape = unary_union(polygons) if len(polygons) > 1 else (polygons[0] if polygons else None)
                
                if full_shape and full_shape.is_valid:
                    if isinstance(full_shape, MultiPolygon):
                        coordinates = [[list(p.exterior.coords) for p in full_shape.geoms]]
                        geo_type = "MultiPolygon"
                    else:
                        coordinates = [list(full_shape.exterior.coords)]
                        geo_type = "Polygon"

                    chunk_results.append({
                        "type": "Feature",
                        "geometry": {"type": geo_type, "coordinates": coordinates},
                        "properties": {"GlobalId": guid}
                    })
            except:
                continue
        return chunk_results
    except Exception as e:
        print(f"Worker Error: {e}")
        return []

def extract_geometry_native_2d_parallel(file_path, entities, georef_data=None):
    """
    Orchestrates parallel extraction of geometry in NATIVE coordinates.
    
    Returns:
        tuple: (native_features, crs_info_dict)
        - native_features: List of GeoJSON-like features in native/projected CRS
        - crs_info_dict: {"from_crs": "EPSG:XXX", "has_mapconversion": bool}
    """
    guids = [e.GlobalId for e in entities]
    if not guids: 
        return [], {"from_crs": None, "has_mapconversion": False}
    
    # Debug log
    print(f"[DEBUG] Extracting native geometry with georef_data: {georef_data is not None}")
    if georef_data:
        print(f"[DEBUG] Map Conversion: {georef_data.get('map_conversion')}")
    
    # Sequential extraction to save memory on limited environments (Render Free Tier)
    print(f"[DEBUG] Extracting geometry sequentially for {len(guids)} entities...")
    native_features = process_geometry_chunk_native(file_path, guids, georef_data)
    
    # Build CRS info
    crs_info = {
        "from_crs": georef_data.get("crs") if georef_data else None,
        "has_mapconversion": bool(georef_data and georef_data.get("map_conversion"))
    }
            
    return native_features, crs_info


def transform_features_crs(features, from_crs, to_crs):
    """
    Transforms feature coordinates from one CRS to another.
    
    Args:
        features: List of GeoJSON-like features
        from_crs: Source CRS (e.g., "EPSG:25830")
        to_crs: Target CRS (e.g., "EPSG:4326")
    
    Returns:
        List of features with transformed coordinates
    """
    if not features or not from_crs or not to_crs:
        return features
    
    # Create transformer (NOT global)
    transformer = Transformer.from_crs(from_crs, to_crs, always_xy=True)
    
    transformed_features = []
    for feat in features:
        try:
            geom = feat.get("geometry")
            if not geom:
                transformed_features.append(feat)
                continue
            
            coords = geom.get("coordinates", [])
            geo_type = geom.get("type")
            
            # Transform coordinates based on geometry type
            if geo_type == "Polygon":
                new_coords = []
                for ring in coords:
                    new_ring = [list(transformer.transform(x, y)) for x, y in ring]
                    new_coords.append(new_ring)
                transformed_coords = new_coords
                
            elif geo_type == "MultiPolygon":
                new_coords = []
                for polygon in coords:
                    new_polygon = []
                    for ring in polygon:
                        new_ring = [list(transformer.transform(x, y)) for x, y in ring]
                        new_polygon.append(new_ring)
                    new_coords.append(new_polygon)
                transformed_coords = new_coords
            else:
                # Unsupported type, keep original
                transformed_coords = coords
            
            # Create transformed feature
            transformed_feat = {
                "type": feat.get("type"),
                "geometry": {
                    "type": geo_type,
                    "coordinates": transformed_coords
                },
                "properties": feat.get("properties", {})
            }
            transformed_features.append(transformed_feat)
            
        except Exception as e:
            print(f"[WARN] Failed to transform feature: {e}")
            transformed_features.append(feat)  # Keep original on error
    
    return transformed_features

# Global transformer variables REMOVED - now passed as parameters to avoid state issues

def load_ifc(file_path):
    return ifcopenshell.open(file_path)

def get_entity_types(ifc_model):
    try:
        types = {entity.is_a() for entity in ifc_model.by_type("IfcProduct")}
        types = sorted(types)
        if "IfcProduct" not in types:
             types.insert(0, "IfcProduct")
        return list(types)
    except Exception as e:
        print(f"Error getting entity types: {e}")
        return []

def get_entities_with_geometry(ifc_model, entity_type):
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    entities = []

    target_type = "IfcProduct" if entity_type == "IfcProduct" else entity_type
    try:
        target = ifc_model.by_type(target_type)
        for entity in target:
            try:
                # Basic check if it has geometry representation
                if hasattr(entity, "Representation") and entity.Representation:
                     entities.append(entity)
            except:
                continue
    except Exception as e:
        print(f"Error getting entities with geometry: {e}")
    
    return entities

def calculate_centroids(features):
    centroids = []
    for feature in features:
        try:
            coords = feature["geometry"].get("coordinates", [])
            # Normalizar estructura de coordenadas para encontrar el polígono exterior
            while isinstance(coords, list) and len(coords) > 0 and isinstance(coords[0], list) and isinstance(coords[0][0], list):
                 coords = coords[0]
            
            if not coords or len(coords) < 3:
                continue
                
            # Asegurar cierre del anillo
            if coords[0] != coords[-1]:
                coords.append(coords[0])

            polygon = Polygon(coords)
            if polygon.is_valid:
                centroid = polygon.centroid
                centroids.append({
                    "GlobalId": feature["properties"]["GlobalId"],
                    "centroid": (centroid.x, centroid.y)
                })
        except:
            continue
    return centroids

def extract_ifc_properties(ifc_model, entity_type):
    """
    Robust property extraction using ifcopenshell.util.element.
    Extracts all Psets and Qsets flattening structure: Pset_Name.Prop_Name -> key.
    """
    import ifcopenshell.util.element
    
    target_type = "IfcProduct" if entity_type == "IfcProduct" else entity_type
    target_entities = ifc_model.by_type(target_type)
    
    extracted_data = []

    for entity in target_entities:
        # Base Metadata
        props = {
            "IFC_ID": entity.GlobalId,
            "IFC_Type": entity.is_a()
        }
        
        try:
            # Automatic extraction of all Psets and Qsets
            psets = ifcopenshell.util.element.get_psets(entity)
            
            prop_count = 0
            for pset_name, pset_props in psets.items():
                for prop_name, value in pset_props.items():
                    # Skip internal/id keys often added by util
                    if prop_name == "id": continue 
                    
                    # Flatten Key: Pset_Name_Prop_Name
                    # We ensure safe keys for RDF
                    flat_key = f"{pset_name}_{prop_name}"
                    
                    # Store flattened key
                    props[flat_key] = value
                    
                    # PROMOTION: If property is 'Sensor_ID', promote to root for logic compatibility
                    if prop_name == "Sensor_ID":
                        props["Sensor_ID"] = value
                        
                    prop_count += 1
            
            # [DEBUG] Log extraction count for verification
            # (Start debug log with [DEBUG] as requested)
            if prop_count > 0:
                 print(f"[DEBUG] Extracted IFC properties for {entity.GlobalId}: {prop_count}")

            extracted_data.append(props)

        except Exception as e:
            print(f"[WARN] Failed to extract psets for {entity.GlobalId}: {e}")
            extracted_data.append(props) # Return at least base info

    return extracted_data

def build_geojson(features, centroids, all_props, selected_props):
    enriched = []
    
    # Crear índices para búsqueda rápida
    props_map = {p["IFC_ID"]: p for p in all_props}
    centroids_map = {c["GlobalId"]: c["centroid"] for c in centroids}

    for feat in features:
        gid = feat["properties"]["GlobalId"]
        
        prop = props_map.get(gid, {})
        centroid = centroids_map.get(gid)
        
        filtered = {}
        for k in selected_props:
            if k in prop:
                filtered[k] = prop[k]
                
        if centroid:
            filtered["centroid"] = centroid
            
        feat["properties"].update(filtered)
        enriched.append(feat)
        
    return {
        "type": "FeatureCollection",
        "features": enriched
    }



def build_owl_core(features, all_props, crs_uri=None):
    """
    Generates CORE OWL/RDF content (BIM + Feature + Geometry only).
    NO sensors, NO evaluation logic.
    
    Args:
        features: List of GeoJSON-like features
        all_props: List of IFC property dicts
        crs_uri: URI of the CRS (e.g., URIRef("http://www.opengis.net/def/crs/EPSG/0/4326"))
    
    Returns:
        OntologyBuilder instance (can be enriched further)
    """
    from services.ontology_service import OntologyBuilder
    from shapely.geometry import shape
    
    builder = OntologyBuilder()
    
    # Property Index
    props_map = {p["IFC_ID"]: p for p in all_props}
    
    # Iterate Features and Build Core Ontology
    for feat in features:
        props = feat["properties"]
        gid = props.get("GlobalId")
        if not gid: continue
        
        # Metadata
        source_file = props.get("Source_File", "Unknown")
        
        # Retrieve strict IFC Type from props
        full_props = props_map.get(gid, {})
        ifc_type = full_props.get("IFC_Type", "IfcElement")
        
        # A. Add BIM Element (Semantics)
        bim_uri = builder.add_bim_element(gid, ifc_type, source_file)
        
        # B. BIM Properties Enrichment
        if full_props:
            builder.add_bim_properties(bim_uri, full_props)
        
        # C. Add Feature (Geometry)
        wkt = None
        if "geometry" in feat and feat["geometry"]:
            try:
                geom_shape = shape(feat["geometry"])
                wkt = geom_shape.wkt
            except Exception as e:
                print(f"[WARN] Failed to convert geometry to WKT for {gid}: {e}")
        
        # Pass CRS URI to add_feature
        builder.add_feature(gid, wkt, crs_uri=crs_uri)
    
    return builder


def enrich_owl_sensors(builder, features, all_props, sensors_list, config, config_hash=None, config_filename="config.json"):
    """
    Enriches an existing OWL graph with Sensor data, evaluation, and config traceability.
    
    Args:
        builder: OntologyBuilder instance (from build_owl_core)
        features: List of GeoJSON-like features
        all_props: List of IFC property dicts
        sensors_list: List of sensor dicts
        config: Config dict (sensor_id -> rules)
        config_hash: SHA-256 hash of config file
        config_filename: Name of config file
    
    Returns:
        OntologyBuilder instance (enriched)
    """
    if not sensors_list or not config:
        print("[LOG] No sensors or config provided, skipping sensor enrichment")
        return builder
    
    # Property Index
    props_map = {p["IFC_ID"]: p for p in all_props}
    
    # 1. Build Sensor Index (Sensor_ID -> List of GUIDs)
    sensor_id_to_guids = {}
    
    for feat in features:
        props = feat["properties"]
        gid = props.get("GlobalId")
        if not gid: continue
        
        full_props = props_map.get(gid, {})
        
        # Index for Sensors
        if "Sensor_ID" in full_props:
            sid = str(full_props["Sensor_ID"])
            if sid not in sensor_id_to_guids:
                sensor_id_to_guids[sid] = []
            sensor_id_to_guids[sid].append(gid)
    
    # 2. Process Sensors & Config Traceability
    print(f"[LOG] Processing {len(sensors_list)} sensors for Ontology...")
    
    # Create ConfigRun instance
    run_uri = builder.add_config_run(config_filename, config_hash or "UNKNOWN_HASH")
    
    # Cache config URIs
    sensor_to_config_uri = {}
    
    for sensor in sensors_list:
        sid = sensor.get("sensor_id")
        if not sid: continue
        
        # Find linked GUIDs
        matches = sensor_id_to_guids.get(str(sid), [])
        
        if len(matches) == 0:
            continue  # Unlinked sensor
        
        # --- CONFIG TRACEABILITY ---
        rule = config.get(sid)
        
        print(f"[DEBUG] Rule Found for Sensor {sid}: {rule}")
        
        if not rule:
            print(f"[WARN] No rule found in config for sensor {sid}")
        
        # Create SensorConfig instance if rule exists
        s_config_uri = sensor_to_config_uri.get(sid)
        if not s_config_uri and rule:
            s_config_uri = builder.add_sensor_config(sid, rule, run_uri)
            sensor_to_config_uri[sid] = s_config_uri
        
        # --- EVALUATION ---
        enriched_sensor = evaluate_sensor(sensor, config)
        
        if enriched_sensor:
            for target_guid in matches:
                # Pass config URI to link it
                builder.add_sensor(target_guid, enriched_sensor, s_config_uri)
    
    return builder


# LEGACY WRAPPER (for backward compatibility during transition)
def build_owl(features, all_props, sensors_list=None, config=None, config_hash=None, config_filename="config.json", crs_uri=None):
    """
    LEGACY: Generates complete OWL/RDF content.
    Wrapper around build_owl_core + enrich_owl_sensors.
    
    Use build_owl_core + enrich_owl_sensors directly for more control.
    """
    # Build core
    builder = build_owl_core(features, all_props, crs_uri=crs_uri)
    
    # Enrich with sensors if provided
    if sensors_list and config:
        builder = enrich_owl_sensors(builder, features, all_props, sensors_list, config, config_hash, config_filename)
    
    return builder.export(format="xml")

