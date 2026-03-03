from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import shutil
import os
import tempfile
import json
from services import bim_gis
from pydantic import BaseModel

app = FastAPI()

origins = [
    "https://bim-gis-frontend.onrender.com",
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FeatureRequest(BaseModel):
    selected_files: List[str] = []
    entity_types: List[str] = []
    selected_props: List[str] = []

class EntitySelection(BaseModel):
    entity_types: List[str]

# In-memory storage
MODELS_DB = {}

# Configurable Default CRS
DEFAULT_CRS = os.getenv("DEFAULT_CRS", "EPSG:25830")

@app.post("/api/process")
async def process_model(
    file_ifc: UploadFile = File(...),
    file_sensors: UploadFile = File(None),
    file_config: UploadFile = File(None)
):
    """
    Definitive Single-Step Flow (Phase 1 Refactored):
    1. Upload IFC (Mandatory) + Sensors/Config (Optional)
    2. Auto-detect CRS or use Default
    3. Extract ALL geometric entities in NATIVE coordinates
    4. Transform to target CRS (EPSG:4326)
    5. Generate GeoJSON + OWL (with CRS metadata)
    """
    # 1. Save IFC to Temp
    suffix = os.path.splitext(file_ifc.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file_ifc.file, tmp)
        tmp_path = tmp.name

    try:
        # 2. Load Model
        model = bim_gis.load_ifc(tmp_path)
        if not model:
            raise HTTPException(status_code=400, detail="Could not load IFC file")

        # 3. CRS Handling
        georef_data = bim_gis.get_georeferencing_data(model)
        
        # Determine Source CRS
        source_crs = DEFAULT_CRS
        if georef_data.get("crs"):
            source_crs = georef_data["crs"]
        else:
            print(f"[WARN] No specific CRS detected. Using Default: {DEFAULT_CRS}")
        
        target_crs = "EPSG:4326"  # Always transform to WGS84 for GeoJSON
        
        # 4. Extract ALL Geometric Entities (NATIVE coordinates)
        all_types = bim_gis.get_entity_types(model)
        all_native_features = []
        all_centroids = []
        all_models_props = []
        crs_info = None
        
        for etype in all_types:
            entities = bim_gis.get_entities_with_geometry(model, etype)
            if not entities: continue
            
            # Extract Props
            props = bim_gis.extract_ifc_properties(model, etype)
            for p in props: p["Source_File"] = file_ifc.filename
            all_models_props.extend(props)
            
            # Extract Geometry (NATIVE coordinates)
            native_features, crs_info = bim_gis.extract_geometry_native_2d_parallel(
                tmp_path,
                entities,
                georef_data
            )
            all_native_features.extend(native_features)
            
            # Centroids (from native features)
            for feat in native_features:
                gid = feat["properties"]["GlobalId"]
                geom = feat.get("geometry")
                if geom:
                    from shapely.geometry import shape
                    try:
                        centroid = shape(geom).centroid
                        all_centroids.append({
                            "GlobalId": gid,
                            "centroid": [centroid.x, centroid.y]
                        })
                    except:
                        pass
        
        # 5. Transform to Target CRS
        all_transformed_features = bim_gis.transform_features_crs(
            all_native_features,
            crs_info.get("from_crs") or source_crs,
            target_crs
        )
        
        # 6. Deduplicate by GUID
        seen_guids = set()
        unique_features = []
        unique_centroids = []
        
        for feat in all_transformed_features:
            gid = feat["properties"]["GlobalId"]
            if gid not in seen_guids:
                seen_guids.add(gid)
                unique_features.append(feat)
        
        for cent in all_centroids:
            gid = cent["GlobalId"]
            if gid in seen_guids:
                unique_centroids.append(cent)
        
        # 7. Build GeoJSON
        selected_props = ["IFC_Type", "GlobalId", "Source_File"]
        geojson_result = bim_gis.build_geojson(
            unique_features,
            unique_centroids,
            all_models_props,
            selected_props
        )
        
        # 8. Build OWL with CRS metadata
        from rdflib import URIRef
        
        # Create CRS URI for target CRS
        crs_uri = URIRef(f"http://www.opengis.net/def/crs/EPSG/0/{target_crs.split(':')[1]}")
        
        # Build core OWL
        builder = bim_gis.build_owl_core(
            unique_features,
            all_models_props,
            crs_uri=crs_uri
        )
        
        # 9. Enrich with Sensors (if provided)
        sensors_list = None
        config_data = None
        config_hash = None
        
        if file_sensors and file_config:
            # Read Sensors JSON
            sensors_content = await file_sensors.read()
            sensors_list = json.loads(sensors_content.decode("utf-8"))
            
            # Read Config JSON and compute hash
            import hashlib
            config_content = await file_config.read()
            config_data = json.loads(config_content.decode("utf-8"))
            config_hash = hashlib.sha256(config_content).hexdigest()
            
            # Enrich OWL with sensors
            builder = bim_gis.enrich_owl_sensors(
                builder,
                unique_features,
                all_models_props,
                sensors_list,
                config_data,
                config_hash=config_hash,
                config_filename=file_config.filename
            )
        
        # 10. Export OWL
        owl_content = builder.export(format="xml")
        
        # 11. Return Response with Metadata
        return {
            "status": "success",
            "geojson": geojson_result,
            "owl": owl_content,
            "metadata": {
                "crs_from": crs_info.get("from_crs") or source_crs,
                "crs_to": target_crs,
                "has_ifc_mapconversion": crs_info.get("has_mapconversion", False),
                "total_features": len(unique_features),
                "sensors_processed": len(sensors_list) if sensors_list else 0
            }
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup Temp
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/api/process/inspire-alignment")
async def process_inspire_alignment(
    file_ifc: UploadFile = File(...),
    file_sensors: UploadFile = File(None),
    file_config: UploadFile = File(None)
):
    """
    Sprint 2A: INSPIRE Alignment Multi-Tema
    
    Generates INSPIRE alignment graphs with automatic theme detection.
    Returns core OWL + alignment graphs (TriG format) without GML.
    """
    # 1. Execute core processing (reuse /api/process logic)
    # Save IFC to temp
    suffix = os.path.splitext(file_ifc.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file_ifc.file, tmp)
        tmp_path = tmp.name
    
    try:
        # 2. Load Model
        model = bim_gis.load_ifc(tmp_path)
        if not model:
            raise HTTPException(status_code=400, detail="Could not load IFC file")
        
        # 3. CRS Handling
        georef_data = bim_gis.get_georeferencing_data(model)
        source_crs = DEFAULT_CRS
        if georef_data.get("crs"):
            source_crs = georef_data["crs"]
        target_crs = "EPSG:4326"
        
        # 4. Extract geometry (native + transform)
        all_types = bim_gis.get_entity_types(model)
        all_native_features = []
        all_centroids = []
        all_models_props = []
        crs_info = None
        
        for etype in all_types:
            entities = bim_gis.get_entities_with_geometry(model, etype)
            if not entities: continue
            
            props = bim_gis.extract_ifc_properties(model, etype)
            for p in props: p["Source_File"] = file_ifc.filename
            all_models_props.extend(props)
            
            native_features, crs_info = bim_gis.extract_geometry_native_2d_parallel(
                tmp_path, entities, georef_data
            )
            all_native_features.extend(native_features)
            
            for feat in native_features:
                gid = feat["properties"]["GlobalId"]
                geom = feat.get("geometry")
                if geom:
                    from shapely.geometry import shape
                    try:
                        centroid = shape(geom).centroid
                        all_centroids.append({
                            "GlobalId": gid,
                            "centroid": [centroid.x, centroid.y]
                        })
                    except:
                        pass
        
        # 5. Transform to target CRS
        all_transformed_features = bim_gis.transform_features_crs(
            all_native_features,
            crs_info.get("from_crs") or source_crs,
            target_crs
        )
        
        # 6. Deduplicate
        seen_guids = set()
        unique_features = []
        unique_centroids = []
        
        for feat in all_transformed_features:
            gid = feat["properties"]["GlobalId"]
            if gid not in seen_guids:
                seen_guids.add(gid)
                unique_features.append(feat)
        
        for cent in all_centroids:
            gid = cent["GlobalId"]
            if gid in seen_guids:
                unique_centroids.append(cent)
        
        # 7. Build core OWL
        from rdflib import URIRef
        crs_uri = URIRef(f"http://www.opengis.net/def/crs/EPSG/0/{target_crs.split(':')[1]}")
        
        builder = bim_gis.build_owl_core(
            unique_features,
            all_models_props,
            crs_uri=crs_uri
        )
        
        # 8. Enrich with sensors (if provided)
        if file_sensors and file_config:
            sensors_content = await file_sensors.read()
            sensors_list = json.loads(sensors_content.decode("utf-8"))
            
            import hashlib
            config_content = await file_config.read()
            config_data = json.loads(config_content.decode("utf-8"))
            config_hash = hashlib.sha256(config_content).hexdigest()
            
            builder = bim_gis.enrich_owl_sensors(
                builder, unique_features, all_models_props,
                sensors_list, config_data, config_hash, file_config.filename
            )
        
        # 9. Export core OWL
        owl_core = builder.export(format="xml")
        
        # 10. Generate INSPIRE alignment
        
        mapper = INSPIREMapper(owl_core)
        alignment_result = mapper.generate_alignment()
        
        # 11. Export alignment as TriG
        alignment_trig = mapper.export_alignment_trig()
        
        # 12. Return combined result
        return {
            "status": "success",
            "owl_core": owl_core,
            "owl_alignment_trig": alignment_trig,
            "themes_detected": alignment_result["themes"],
            "mapping_summary": alignment_result["mapping_summary"],
            "metadata": {
                "crs_from": crs_info.get("from_crs") or source_crs,
                "crs_to": target_crs,
                "total_features": len(unique_features)
            }
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/api/validate/inspire")
async def validate_inspire(
    file_ifc: UploadFile = File(...),
    file_sensors: UploadFile = File(None),
    file_config: UploadFile = File(None)
):
    """
    Sprint 2B: INSPIRE SHACL Validation
    
    Generates alignment and validates against SHACL minimum compliance shapes.
    Returns validation report with conformance status per theme.
    """
    # Save IFC to temp
    suffix = os.path.splitext(file_ifc.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file_ifc.file, tmp)
        tmp_path = tmp.name
    
    try:
        # 1. Load Model
        model = bim_gis.load_ifc(tmp_path)
        if not model:
            raise HTTPException(status_code=400, detail="Could not load IFC file")
        
        # 2. CRS Handling
        georef_data = bim_gis.get_georeferencing_data(model)
        source_crs = DEFAULT_CRS
        if georef_data.get("crs"):
            source_crs = georef_data["crs"]
        target_crs = "EPSG:4326"
        
        # 3. Extract geometry (native + transform)
        all_types = bim_gis.get_entity_types(model)
        all_native_features = []
        all_models_props = []
        crs_info = None
        
        for etype in all_types:
            entities = bim_gis.get_entities_with_geometry(model, etype)
            if not entities: continue
            
            props = bim_gis.extract_ifc_properties(model, etype)
            for p in props: p["Source_File"] = file_ifc.filename
            all_models_props.extend(props)
            
            native_features, crs_info = bim_gis.extract_geometry_native_2d_parallel(
                tmp_path, entities, georef_data
            )
            all_native_features.extend(native_features)
        
        # 4. Transform to target CRS
        all_transformed_features = bim_gis.transform_features_crs(
            all_native_features,
            crs_info.get("from_crs") or source_crs,
            target_crs
        )
        
        # 5. Deduplicate
        seen_guids = set()
        unique_features = []
        
        for feat in all_transformed_features:
            gid = feat["properties"]["GlobalId"]
            if gid not in seen_guids:
                seen_guids.add(gid)
                unique_features.append(feat)
        
        # 6. Build core OWL
        from rdflib import URIRef
        crs_uri = URIRef(f"http://www.opengis.net/def/crs/EPSG/0/{target_crs.split(':')[1]}")
        
        builder = bim_gis.build_owl_core(
            unique_features,
            all_models_props,
            crs_uri=crs_uri
        )
        
        # 7. Enrich with sensors (if provided)
        config_hash = None
        if file_sensors and file_config:
            sensors_content = await file_sensors.read()
            sensors_list = json.loads(sensors_content.decode("utf-8"))
            
            import hashlib
            config_content = await file_config.read()
            config_data = json.loads(config_content.decode("utf-8"))
            config_hash = hashlib.sha256(config_content).hexdigest()[:16]
            
            builder = bim_gis.enrich_owl_sensors(
                builder, unique_features, all_models_props,
                sensors_list, config_data, config_hash, file_config.filename
            )
        
        # 8. Export core OWL
        owl_core = builder.export(format="xml")
        
        # 9. Generate INSPIRE alignment with provenance
        from services.inspire.inspire_mapper import INSPIREMapper
        import hashlib
        
        ifc_hash = hashlib.sha256(owl_core.encode()).hexdigest()[:16]
        mapper = INSPIREMapper(owl_core, ifc_hash=ifc_hash, config_hash=config_hash)
        alignment_result = mapper.generate_alignment()
        
        # 10. Validate alignment with SHACL
        from services.inspire.validator import INSPIREValidator
        
        validator = INSPIREValidator()
        validation_result = validator.validate_all(
            mapper.alignment_dataset,
            alignment_result["themes"]
        )
        
        # 11. Check metadata graph
        metadata_graph = mapper.get_metadata_graph()
        metadata_checked = len(metadata_graph) > 0
        
        # 12. Return validation report
        return {
            "status": "success",
            "themes": alignment_result["themes"],
            "overall_conforms": validation_result["overall_conforms"],
            "total_violations": validation_result["total_violations"],
            "results": validation_result["results"],
            "metadata_checked": metadata_checked,
            "metadata_triples": len(metadata_graph)
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/api/process/inspire-gml")
async def process_inspire_gml(
    file_ifc: UploadFile = File(...),
    file_sensors: UploadFile = File(None),
    file_config: UploadFile = File(None)
):
    """
    Sprint 2C: INSPIRE GML Export
    
    Generates INSPIRE Buildings GML from IFC.
    Returns minimal viable GML structure.
    """
    # Save IFC to temp
    suffix = os.path.splitext(file_ifc.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file_ifc.file, tmp)
        tmp_path = tmp.name
    
    try:
        # 1. Load Model
        model = bim_gis.load_ifc(tmp_path)
        if not model:
            raise HTTPException(status_code=400, detail="Could not load IFC file")
        
        # 2. CRS Handling
        georef_data = bim_gis.get_georeferencing_data(model)
        source_crs = DEFAULT_CRS
        if georef_data.get("crs"):
            source_crs = georef_data["crs"]
        target_crs = "EPSG:4326"
        
        # 3. Extract geometry (native + transform)
        all_types = bim_gis.get_entity_types(model)
        all_native_features = []
        all_models_props = []
        crs_info = None
        
        for etype in all_types:
            entities = bim_gis.get_entities_with_geometry(model, etype)
            if not entities: continue
            
            props = bim_gis.extract_ifc_properties(model, etype)
            for p in props: p["Source_File"] = file_ifc.filename
            all_models_props.extend(props)
            
            native_features, crs_info = bim_gis.extract_geometry_native_2d_parallel(
                tmp_path, entities, georef_data
            )
            all_native_features.extend(native_features)
        
        # 4. Transform to target CRS
        all_transformed_features = bim_gis.transform_features_crs(
            all_native_features,
            crs_info.get("from_crs") or source_crs,
            target_crs
        )
        
        # 5. Deduplicate
        seen_guids = set()
        unique_features = []
        
        for feat in all_transformed_features:
            gid = feat["properties"]["GlobalId"]
            if gid not in seen_guids:
                seen_guids.add(gid)
                unique_features.append(feat)
        
        # 6. Build core OWL
        from rdflib import URIRef
        crs_uri = URIRef(f"http://www.opengis.net/def/crs/EPSG/0/{target_crs.split(':')[1]}")
        
        builder = bim_gis.build_owl_core(
            unique_features,
            all_models_props,
            crs_uri=crs_uri
        )
        
        # 7. Enrich with sensors (if provided)
        config_hash = None
        if file_sensors and file_config:
            sensors_content = await file_sensors.read()
            sensors_list = json.loads(sensors_content.decode("utf-8"))
            
            import hashlib
            config_content = await file_config.read()
            config_data = json.loads(config_content.decode("utf-8"))
            config_hash = hashlib.sha256(config_content).hexdigest()[:16]
            
            builder = bim_gis.enrich_owl_sensors(
                builder, unique_features, all_models_props,
                sensors_list, config_data, config_hash, file_config.filename
            )
        
        # 8. Export core OWL
        owl_core = builder.export(format="xml")
        
        # 9. Generate INSPIRE alignment
        from services.inspire.inspire_mapper import INSPIREMapper
        import hashlib
        
        ifc_hash = hashlib.sha256(owl_core.encode()).hexdigest()[:16]
        mapper = INSPIREMapper(owl_core, ifc_hash=ifc_hash, config_hash=config_hash)
        alignment_result = mapper.generate_alignment()
        
        # 10. Generate GML
        from services.inspire.gml.export_bu import export_bu_gml
        
        gml_metadata = {
            "dataset_id": ifc_hash,
            "crs": target_crs
        }
        
        bu_gml = export_bu_gml(
            unique_features,
            mapper.alignment_dataset,
            gml_metadata
        )
        
        # 11. Return GML + metadata
        return {
            "status": "success",
            "themes": alignment_result["themes"],
            "bu_gml": bu_gml,
            "metadata": {
                "crs": target_crs,
                "feature_count": len(unique_features),
                "dataset_id": ifc_hash,
                "bu_features": alignment_result["mapping_summary"].get("BU", 0)
            }
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# --- Deprecated Endpoints (Kept for rollback safety) ---

@app.post("/api/reset_session")
async def reset_session():
    MODELS_DB.clear()
    return {"status": "ok"}

@app.post("/api/upload_ifc")
async def upload_ifc(files: List[UploadFile] = File(...)):
    return {"status": "deprecated"}

@app.post("/api/gis/sugerir_crs")
async def sugerir_crs(ubicacion: str = Form(...)):
    return {"status": "deprecated"}

@app.post("/api/gis/set_crs")
async def set_crs(from_crs: str = Form(...), to_crs: str = Form("EPSG:4326")):
    return {"status": "deprecated"}

@app.get("/api/gis/entities")
async def get_entity_types_endpoint():
    return {"status": "deprecated"}

@app.post("/api/gis/properties")
async def get_available_properties(req: EntitySelection):
    return {"status": "deprecated"}

@app.post("/api/gis/generate")
async def generate_gis_deprecated(
    data: str = Form(...),
    file_sensors: UploadFile = File(None),
    file_config: UploadFile = File(None)
):
    return {"status": "deprecated"}

@app.post("/api/pilot/process")
async def pilot_process(
    file_ifc: UploadFile = File(...),
    file_sensors: UploadFile = File(...),
    file_config: UploadFile = File(...)
):
    """
    Endpoint principal para el piloto. 
    Recibe IFC, Sensores y Configuración.
    Devuelve GeoJSON y OWL enriquecido.
    """
    # 1. Guardar archivos temporalmente
    files_map = {}
    for f, key in [(file_ifc, "ifc"), (file_sensors, "sensors"), (file_config, "config")]:
        suffix = os.path.splitext(f.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(f.file, tmp)
            files_map[key] = tmp.name

    try:
        # 2. Leer JSONs
        with open(files_map["sensors"], "r", encoding="utf-8") as f:
            sensors_data = json.load(f)
            
        with open(files_map["config"], "r", encoding="utf-8") as f:
            config_data = json.load(f)

        # 3. Cargar Modelo IFC
        model = bim_gis.load_ifc(files_map["ifc"])
        if not model:
            raise HTTPException(status_code=400, detail="Error loading IFC file")

        # 4. Procesar Geometría (Entidades básicas: productos)
        # Por simplicidad del piloto, asumimos que queremos procesar todo lo que tenga geometría
        # O definimos un set estándar (IfcWall, IfcWindow, etc).
        # Usaremos get_entity_types para obtener todo.
        entity_types = bim_gis.get_entity_types(model)
        
        georef_data = bim_gis.get_georeferencing_data(model)
        crs_info = bim_gis.get_transformer() # Default or existing global
        
        all_features = []
        all_centroids = []
        all_models_props = []
        
        for etype in entity_types:
            props = bim_gis.extract_ifc_properties(model, etype)
            for p in props: 
                p["Source_File"] = file_ifc.filename
            all_models_props.extend(props)
            
            entities = bim_gis.get_entities_with_geometry(model, etype)
            
            features = bim_gis.extract_clean_geometry_2D_parallel(
                files_map["ifc"],
                entities,
                crs_info.get("from"),
                crs_info.get("to"),
                georef_data=georef_data
            )
            centroids = bim_gis.calculate_centroids(features)
            
            for feat in features:
                feat["properties"]["Source_File"] = file_ifc.filename
                
            all_features.extend(features)
            all_centroids.extend(centroids)

        # 5. Generar Resultados
        # GeoJSON
        geojson = bim_gis.build_geojson(
            all_features,
            all_centroids,
            all_models_props,
            [] # No pre-filtering of props for GeoJSON in pilot
        )
        
        # OWL Enriquecido con Sensores
        owl_content = bim_gis.build_owl(
            all_features, 
            all_models_props, 
            sensors_list=sensors_data, 
            config=config_data
        )
        
        return {
            "status": "success",
            "geojson": geojson,
            "owl": owl_content
        }

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format in sensors or config file")
    except Exception as e:
        print(f"Pilot Error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        # Cleanup
        for path in files_map.values():
            if os.path.exists(path):
                try: os.remove(path)
                except: pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
