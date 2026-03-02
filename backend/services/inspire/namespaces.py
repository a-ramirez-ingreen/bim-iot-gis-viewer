"""
INSPIRE and related namespaces for alignment graph generation.
Sprint 2B: Updated with official TG URIs and PROV/SKOS namespaces.
"""

from rdflib import Namespace

# Core BIM-GIS Viewer
APP = Namespace("http://bim-gis-viewer.local/ontology#")
GEO = Namespace("http://www.opengis.net/ont/geosparql#")

# INSPIRE (placeholder URIs - will be replaced with official ones)
INSPIRE = Namespace("http://inspire.ec.europa.eu/schemas/")
INSPIRE_BU = Namespace("http://inspire.ec.europa.eu/schemas/bu-core3d/4.0#")
INSPIRE_TN = Namespace("http://inspire.ec.europa.eu/schemas/tn/4.0#")
INSPIRE_US = Namespace("http://inspire.ec.europa.eu/schemas/us-net-common/4.0#")
INSPIRE_EMF = Namespace("http://inspire.ec.europa.eu/schemas/ef/4.0#")

# Dublin Core
DCT = Namespace("http://purl.org/dc/terms/")

# OWL
OWL = Namespace("http://www.w3.org/2002/07/owl#")

# SKOS (for alignment - Sprint 2B)
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")

# PROV-O (for provenance - Sprint 2B)
PROV = Namespace("http://www.w3.org/ns/prov#")

# INSPIRE Technical Guidelines URIs (Official Knowledge Base - Sprint 2B)
INSPIRE_TG = {
    "BU": "https://knowledge-base.inspire.ec.europa.eu/publications/inspire-data-specification-buildings-technical-guidelines_en",
    "TN": "https://knowledge-base.inspire.ec.europa.eu/publications/inspire-data-specification-transport-networks-technical-guidelines_en",
    "US": "https://knowledge-base.inspire.ec.europa.eu/publications/inspire-data-specification-utility-and-government-services-technical-guidelines_en",
    "EMF": "https://knowledge-base.inspire.ec.europa.eu/publications/inspire-data-specification-environmental-monitoring-facilities-technical-guidelines_en"
}

# Theme codes
THEME_CODES = {
    "BU": "Buildings",
    "TN": "Transport Networks",
    "US": "Utility and Government Services",
    "EMF": "Environmental Monitoring Facilities"
}
