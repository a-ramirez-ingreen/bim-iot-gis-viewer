"""
INSPIRE Buildings GML Export

Generates minimal viable GML for INSPIRE Buildings theme.
Sprint 2C: Basic structure only, no full compliance yet.
"""

from shapely.geometry import shape
from rdflib import URIRef, Namespace  # Import here for type hints if needed, though used inside
try:
    from rdflib import Dataset
except ImportError:
    pass # Handle case where Dataset might not be directly importable or needed for type hint only

try:
    from lxml import etree
    msg_lib = "using lxml"
except ImportError:
    import xml.etree.ElementTree as etree
    msg_lib = "using xml.etree (lxml not found, restart backend recommended)"


def export_bu_gml(geojson_features: list, alignment_dataset, metadata: dict) -> str:
    """
    Export INSPIRE Buildings GML from GeoJSON features and alignment data.
    
    Args:
        geojson_features: List of GeoJSON features (from core processing)
        alignment_dataset: rdflib Dataset with alignment graphs
        metadata: Dict with CRS, hash, etc.
    
    Returns:
        GML XML string
    """
    print(f"[GML] Exporting BU GML {msg_lib}")
    
    # Namespaces
    GML = Namespace("http://www.opengis.net/gml/3.2")
    BU_CORE2D = Namespace("http://inspire.ec.europa.eu/schemas/bu-core2d/4.0")
    BU_BASE = Namespace("http://inspire.ec.europa.eu/schemas/bu-base/4.0")
    XSI = Namespace("http://www.w3.org/2001/XMLSchema-instance")
    XLINK = Namespace("http://www.w3.org/1999/xlink")
    
    # Schema locations (Sprint 2E: add bu-base)
    SCHEMA_LOCATIONS = [
        "http://www.opengis.net/gml/3.2 http://schemas.opengis.net/gml/3.2.1/gml.xsd",
        "http://inspire.ec.europa.eu/schemas/bu-core2d/4.0 http://inspire.ec.europa.eu/schemas/bu-core2d/4.0/BuildingsCore2D.xsd",
        "http://inspire.ec.europa.eu/schemas/bu-base/4.0 http://inspire.ec.europa.eu/schemas/bu-base/4.0/BuildingsBase.xsd"
    ]
    schema_loc_text = " ".join(SCHEMA_LOCATIONS)
    
    # Get BU alignment graph
    bu_graph_uri = URIRef("urn:inspire:alignment:BU")
    bu_graph = alignment_dataset.graph(bu_graph_uri)
    
    if len(bu_graph) == 0:
        print("[GML] No BU alignment found, returning empty GML")
        return _create_empty_gml(metadata)
    
    # Extract INSPIRE URI -> BIM GUID mapping
    inspire_to_guid = {}
    
    # Query: find all skos:exactMatch relationships
    SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
    for bim_uri, predicate, inspire_uri in bu_graph.triples((None, SKOS.exactMatch, None)):
        # Extract GUID from BIM URI (format: http://...#bim_GUID)
        bim_uri_str = str(bim_uri)
        if "#bim_" in bim_uri_str:
            guid = bim_uri_str.split("#bim_")[-1]
            inspire_to_guid[str(inspire_uri)] = guid
    
    print(f"[GML] Found {len(inspire_to_guid)} BU alignments")
    
    # Create GeoJSON GUID lookup
    guid_to_geojson = {}
    for feature in geojson_features:
        guid = feature["properties"].get("GlobalId")
        if guid:
            guid_to_geojson[guid] = feature
    
    # Build GML
    dataset_id = metadata.get("dataset_id", "unknown")
    crs = metadata.get("crs", "EPSG:4326")
    
    # Root element
    tag_root = f"{{{GML}}}FeatureCollection"
    
    # Define common nsmap (Sprint 2E: add bu-base)
    nsmap = {
        "gml": str(GML),
        "bu-core2d": str(BU_CORE2D),
        "bu-base": str(BU_BASE),
        "xsi": str(XSI),
        "xlink": str(XLINK)
    }
    
    # Define root attributes
    root_attribs = {
        f"{{{GML}}}id": f"BU_DATASET_{dataset_id}",
        f"{{{XSI}}}schemaLocation": schema_loc_text
    }
    
    # Check if we are using lxml (supports nsmap)
    if hasattr(etree, 'Element') and 'nsmap' in str(etree.Element.__doc__):
         root = etree.Element(
            tag_root,
            attrib=root_attribs,
            nsmap=nsmap
        )
    else:
        # ElementTree fallback
        try:
            for prefix, uri in nsmap.items():
                etree.register_namespace(prefix, uri)
        except:
            pass
            
        root = etree.Element(
            tag_root,
            attrib=root_attribs
        )
    
    # Add feature members
    feature_count = 0
    
    for inspire_uri, guid in inspire_to_guid.items():
        geojson_feature = guid_to_geojson.get(guid)
        
        if not geojson_feature:
            print(f"[GML] Warning: No GeoJSON for GUID {guid}")
            continue
        
        geometry = geojson_feature.get("geometry")
        if not geometry:
            print(f"[GML] Warning: No geometry for GUID {guid}")
            continue
        
        # Create feature member
        feature_member = etree.SubElement(root, f"{{{GML}}}featureMember")
        
        # Create Building element (bu-core2d:Building)
        building = etree.SubElement(
            feature_member,
            f"{{{BU_CORE2D}}}Building",
            attrib={f"{{{GML}}}id": f"BU_{guid}"}
        )
        
        # Sprint 2E: INSPIRE BU 2D geometry structure
        # bu-base:geometry2D > bu-base:BuildingGeometry2D > bu-base:geometry
        geometry2d_elem = etree.SubElement(building, f"{{{BU_BASE}}}geometry2D")
        building_geom_elem = etree.SubElement(geometry2d_elem, f"{{{BU_BASE}}}BuildingGeometry2D")
        geom_inner_elem = etree.SubElement(building_geom_elem, f"{{{BU_BASE}}}geometry")
        
        # Convert GeoJSON geometry to GML Polygon
        gml_geom = _geojson_to_gml_polygon(geometry, crs, GML)
        if gml_geom is not None:
            geom_inner_elem.append(gml_geom)
            feature_count += 1
        else:
            print(f"[GML] Warning: Could not convert geometry for GUID {guid}")
    
    print(f"[GML] Generated GML with {feature_count} buildings (bu-core2d)")
    
    # Serialize to string
    try:
        xml_string = etree.tostring(
            root,
            pretty_print=True,
            xml_declaration=True,
            encoding="UTF-8"
        ).decode("utf-8")
    except TypeError:
        # xml.etree fallback doesn't support pretty_print
        xml_string = etree.tostring(
            root,
            encoding="UTF-8"
        ).decode("utf-8")
    
    return xml_string


def _geojson_to_gml_polygon(geojson_geom: dict, crs: str, GML) -> etree.Element:
    """
    Convert GeoJSON geometry to GML Polygon.
    
    Args:
        geojson_geom: GeoJSON geometry dict
        crs: CRS string (e.g., "EPSG:4326")
        GML: GML namespace
    
    Returns:
        GML Polygon element or None
    """
    try:
        geom = shape(geojson_geom)
        
        # Handle Polygon
        if geom.geom_type == "Polygon":
            return _create_gml_polygon(geom, crs, GML)
        
        # Handle MultiPolygon (take first polygon)
        elif geom.geom_type == "MultiPolygon":
            if len(geom.geoms) > 0:
                return _create_gml_polygon(geom.geoms[0], crs, GML)
        
        else:
            print(f"[GML] Unsupported geometry type: {geom.geom_type}")
            return None
            
    except Exception as e:
        print(f"[GML] Error converting geometry: {e}")
        return None


def _create_gml_polygon(polygon, crs: str, GML) -> etree.Element:
    """
    Create GML Polygon element from shapely Polygon.
    
    Args:
        polygon: shapely Polygon
        crs: CRS string
        GML: GML namespace
    
    Returns:
        GML Polygon element
    """
    # CRS URI
    if crs.startswith("EPSG:"):
        epsg_code = crs.split(":")[1]
        srs_name = f"http://www.opengis.net/def/crs/EPSG/0/{epsg_code}"
    else:
        srs_name = crs
    
    # Create Polygon element
    polygon_elem = etree.Element(
        f"{{{GML}}}Polygon",
        attrib={"srsName": srs_name}
    )
    
    # Exterior ring
    exterior = etree.SubElement(polygon_elem, f"{{{GML}}}exterior")
    linear_ring = etree.SubElement(exterior, f"{{{GML}}}LinearRing")
    pos_list = etree.SubElement(linear_ring, f"{{{GML}}}posList")
    
    # Get coordinates (NO SWAP - keep lon lat order from GeoJSON)
    coords = list(polygon.exterior.coords)
    
    # Format as space-separated list: lon1 lat1 lon2 lat2 ...
    pos_list_text = " ".join(f"{lon} {lat}" for lon, lat in coords)
    pos_list.text = pos_list_text
    
    return polygon_elem


def _create_empty_gml(metadata: dict) -> str:
    """
    Create empty GML FeatureCollection.
    
    Args:
        metadata: Dict with dataset info
    
    Returns:
        Empty GML XML string
    """
    from rdflib import Namespace
    
    GML = Namespace("http://www.opengis.net/gml/3.2")
    BU_CORE2D = Namespace("http://inspire.ec.europa.eu/schemas/bu-core2d/4.0")
    XSI = Namespace("http://www.w3.org/2001/XMLSchema-instance")
    XLINK = Namespace("http://www.w3.org/1999/xlink")
    
    # Schema locations
    SCHEMA_LOCATIONS = [
        "http://www.opengis.net/gml/3.2 http://schemas.opengis.net/gml/3.2.1/gml.xsd",
        "http://inspire.ec.europa.eu/schemas/bu-core2d/4.0 http://inspire.ec.europa.eu/schemas/bu-core2d/4.0/BuildingsCore2D.xsd"
    ]
    schema_loc_text = " ".join(SCHEMA_LOCATIONS)
    
    nsmap = {
        "gml": str(GML),
        "bu-core2d": str(BU_CORE2D),
        "xsi": str(XSI),
        "xlink": str(XLINK)
    }
    
    root_attribs = {
        f"{{{GML}}}id": f"BU_DATASET_{metadata.get('dataset_id', 'unknown')}",
        f"{{{XSI}}}schemaLocation": schema_loc_text
    }
    
    if hasattr(etree, 'Element') and 'nsmap' in str(etree.Element.__doc__):
         root = etree.Element(
            f"{{{GML}}}FeatureCollection",
            attrib=root_attribs,
            nsmap=nsmap
        )
    else:
        try:
            for prefix, uri in nsmap.items():
                etree.register_namespace(prefix, uri)
        except:
            pass
            
        root = etree.Element(
            f"{{{GML}}}FeatureCollection",
            attrib=root_attribs
        )
    
    try:
        xml_string = etree.tostring(
            root,
            pretty_print=True,
            xml_declaration=True,
            encoding="UTF-8"
        ).decode("utf-8")
    except TypeError:
        xml_string = etree.tostring(
            root,
            encoding="UTF-8"
        ).decode("utf-8")
    
    return xml_string
