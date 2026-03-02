"""
Debug script - Simplified to show only violations
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from services.ontology_service import OntologyBuilder
from services.inspire.inspire_mapper import INSPIREMapper
from services.inspire.validator import INSPIREValidator


# Create core graph
builder = OntologyBuilder()
builder.add_bim_element("GUID-001", "IfcBuilding", "test.ifc")
owl_core = builder.export(format="xml")

# Generate alignment
mapper = INSPIREMapper(owl_core, ifc_hash="test123")
alignment_result = mapper.generate_alignment()

# Validate
validator = INSPIREValidator()
validation_result = validator.validate_all(
    mapper.alignment_dataset,
    alignment_result["themes"]
)

print(f"Total violations: {validation_result['total_violations']}")

# Print violations
for result in validation_result["results"]:
    if result.get("violations", 0) > 0:
        print(f"\nTheme {result['theme']} has {result['violations']} violation(s):")
        for v in result.get("violations_list", []):
            print(f"  Focus: {v.get('focusNode')}")
            print(f"  Message: {v.get('message')}")
            print(f"  Severity: {v.get('severity')}")

# Show BU graph triples
print("\n--- BU Graph Triples ---")
bu_graph = mapper.get_theme_graph("BU")
for s, p, o in bu_graph:
    print(f"{s}")
    print(f"  {p}")
    print(f"    {o}")
    print()
