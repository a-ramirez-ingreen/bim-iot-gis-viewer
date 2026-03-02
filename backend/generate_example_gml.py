"""
Generate example GML output for documentation
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from services.ontology_service import OntologyBuilder
from services.inspire.inspire_mapper import INSPIREMapper
from services.inspire.gml.export_bu import export_bu_gml


# Create core graph with Buildings
builder = OntologyBuilder()
builder.add_bim_element("2O2Fr$t4X7Zf8NOew3FLNR", "IfcBuilding", "example.ifc")
builder.add_bim_element("3P3Gs$u5Y8Ag9OPfx4GMOT", "IfcBuildingStorey", "example.ifc")
owl_core = builder.export(format="xml")

# Generate alignment
mapper = INSPIREMapper(owl_core, ifc_hash="abc123def456")
mapper.generate_alignment()

# Create mock GeoJSON features
geojson_features = [
    {
        "type": "Feature",
        "properties": {"GlobalId": "2O2Fr$t4X7Zf8NOew3FLNR", "IfcType": "IfcBuilding"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-3.7038, 40.4168],
                [-3.7038, 40.4178],
                [-3.7028, 40.4178],
                [-3.7028, 40.4168],
                [-3.7038, 40.4168]
            ]]
        }
    },
    {
        "type": "Feature",
        "properties": {"GlobalId": "3P3Gs$u5Y8Ag9OPfx4GMOT", "IfcType": "IfcBuildingStorey"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-3.7035, 40.4170],
                [-3.7035, 40.4176],
                [-3.7030, 40.4176],
                [-3.7030, 40.4170],
                [-3.7035, 40.4170]
            ]]
        }
    }
]

# Generate GML
gml_metadata = {"dataset_id": "abc123def456", "crs": "EPSG:4326"}
gml_string = export_bu_gml(geojson_features, mapper.alignment_dataset, gml_metadata)

# Save to file
output_path = os.path.join(os.path.dirname(__file__), "example_bu.gml")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(gml_string)

print(f"Example GML saved to: {output_path}")
print("\n" + "=" * 60)
print("GML CONTENT:")
print("=" * 60)
print(gml_string)
