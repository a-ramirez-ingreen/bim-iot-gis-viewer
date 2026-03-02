"""
INSPIRE SHACL Validator

Validates INSPIRE alignment graphs against minimum compliance shapes.
Sprint 2B: Structural validation only (no GML constraints yet).
"""

from pathlib import Path
from rdflib import Graph, URIRef, Dataset
from pyshacl import validate


class INSPIREValidator:
    """
    Validates INSPIRE alignment graphs using SHACL shapes.
    """
    
    def __init__(self):
        """Initialize validator and load SHACL shapes."""
        self.shapes = {}
        self._load_shapes()
    
    def _load_shapes(self):
        """Load SHACL shapes from files."""
        shapes_dir = Path(__file__).parent.parent.parent / "shapes" / "inspire"
        
        try:
            self.shapes["BU"] = Graph().parse(shapes_dir / "bu_min.ttl", format="turtle")
            print(f"[SHACL] Loaded BU shape: {len(self.shapes['BU'])} triples")
        except Exception as e:
            print(f"[SHACL] Warning: Could not load BU shape: {e}")
            self.shapes["BU"] = None
        
        try:
            self.shapes["TN"] = Graph().parse(shapes_dir / "tn_min.ttl", format="turtle")
            print(f"[SHACL] Loaded TN shape: {len(self.shapes['TN'])} triples")
        except Exception as e:
            print(f"[SHACL] Warning: Could not load TN shape: {e}")
            self.shapes["TN"] = None
        
        try:
            self.shapes["US"] = Graph().parse(shapes_dir / "us_min.ttl", format="turtle")
            print(f"[SHACL] Loaded US shape: {len(self.shapes['US'])} triples")
        except Exception as e:
            print(f"[SHACL] Warning: Could not load US shape: {e}")
            self.shapes["US"] = None
    
    def validate_theme(self, data_graph: Graph, theme_code: str) -> dict:
        """
        Validates a theme graph against its SHACL shape.
        
        Args:
            data_graph: Graph to validate
            theme_code: Theme code (e.g., "BU")
        
        Returns:
            {
                "theme": str,
                "conforms": bool,
                "violations": int,
                "violations_list": [{"message": str, "focusNode": str, ...}]
            }
        """
        if theme_code not in self.shapes or self.shapes[theme_code] is None:
            return {
                "theme": theme_code,
                "error": f"No shape loaded for theme {theme_code}",
                "conforms": None,
                "violations": 0
            }
        
        try:
            # Run SHACL validation
            conforms, results_graph, results_text = validate(
                data_graph,
                shacl_graph=self.shapes[theme_code],
                inference='rdfs',
                abort_on_first=False,
                allow_warnings=True
            )
            
            # Parse violations
            violations = self._parse_violations(results_graph)
            
            return {
                "theme": theme_code,
                "conforms": conforms,
                "violations": len(violations),
                "violations_list": violations
            }
            
        except Exception as e:
            print(f"[SHACL] Error validating {theme_code}: {e}")
            return {
                "theme": theme_code,
                "error": str(e),
                "conforms": False,
                "violations": 0
            }
    
    def _parse_violations(self, results_graph: Graph) -> list:
        """
        Parse SHACL validation results into violation list.
        Only includes sh:Violation severity (excludes sh:Warning).
        """
        from rdflib import Namespace
        
        SH = Namespace("http://www.w3.org/ns/shacl#")
        violations = []
        
        # Query for validation results
        query = """
        PREFIX sh: <http://www.w3.org/ns/shacl#>
        
        SELECT ?result ?focusNode ?message ?severity
        WHERE {
            ?result a sh:ValidationResult .
            ?result sh:focusNode ?focusNode .
            OPTIONAL { ?result sh:resultMessage ?message }
            OPTIONAL { ?result sh:resultSeverity ?severity }
        }
        """
        
        for row in results_graph.query(query):
            # Only include actual violations, not warnings
            severity_str = str(row.severity).split("#")[-1] if row.severity else "Violation"
            
            if severity_str == "Violation":
                violations.append({
                    "focusNode": str(row.focusNode),
                    "message": str(row.message) if row.message else "No message",
                    "severity": severity_str
                })
        
        return violations
    
    def validate_all(self, alignment_dataset: Dataset, detected_themes: list) -> dict:
        """
        Validates all detected themes in the alignment dataset.
        
        Args:
            alignment_dataset: Dataset containing named graphs
            detected_themes: List of theme codes to validate
        
        Returns:
            {
                "themes_validated": list,
                "overall_conforms": bool,
                "total_violations": int,
                "results": [...]
            }
        """
        results = []
        total_violations = 0
        
        for theme in detected_themes:
            # Skip EMF for now (no shape yet)
            if theme == "EMF":
                continue
            
            # Get theme graph
            graph_uri = URIRef(f"urn:inspire:alignment:{theme}")
            theme_graph = alignment_dataset.graph(graph_uri)
            
            # Validate
            result = self.validate_theme(theme_graph, theme)
            results.append(result)
            
            if "violations" in result:
                total_violations += result["violations"]
        
        return {
            "themes_validated": [r["theme"] for r in results],
            "overall_conforms": total_violations == 0,
            "total_violations": total_violations,
            "results": results
        }
