"""First-pass audit for sensitive data exposure in manuscript drafts.

Checks for:
- Exact coordinates (threatened species, archaeological sites, private land)
- Sensitive location names (patrol routes, ranger stations)
- Unpublished or confidential data markers
- Missing sensitive-data or data-sharing statements

Usage: python check_sensitive_data_security.py <manuscript.md>
"""

import sys
import re
from pathlib import Path

# Configurable sensitive data patterns
SENSITIVE_PATTERNS = {
    "exact_coordinates": {
        "pattern": re.compile(r"\b\d{2}\.\d{4,}"),  # Lat/lon with 4+ decimal places
        "message": "Exact coordinate detected — consider generalization to 0.01° or relative coordinates",
    },
    "threatened_species": {
        "pattern": re.compile(r"(?i)(endangered|threatened|CITES\s*Appendix\s*I|IUCN\s*Red\s*List.*(Critically|Endangered))"),
        "message": "Threatened species mentioned — verify coordinates are masked/generalized",
    },
    "patrol_locations": {
        "pattern": re.compile(r"(?i)(patrol\s*route|ranger\s*station|poaching\s*site|anti.poaching)"),
        "message": "Patrol-sensitive location mentioned — verify public disclosure is authorized",
    },
    "archaeological_sites": {
        "pattern": re.compile(r"(?i)(archaeological\s*site|burial\s*site|cultural\s*relic|heritage\s*site)"),
        "message": "Archaeological/cultural site mentioned — verify public disclosure is authorized",
    },
    "private_land": {
        "pattern": re.compile(r"(?i)(private\s*property|landowner|personal\s*address|GPS\s*coordinates.*private)"),
        "message": "Private land reference detected — verify permission for public disclosure",
    },
    "unpublished_data": {
        "pattern": re.compile(r"(?i)(unpublished\s*data|personal\s*communication|confidential|internal\s*report)"),
        "message": "Unpublished/confidential data reference — verify public disclosure is authorized",
    },
}

REQUIRED_STATEMENTS = [
    "data availability",
    "data sharing",
    "sensitive data",
    "data access",
]


def check_sensitive_data(filepath: str) -> dict:
    """Run sensitive data security audit on a manuscript file."""
    path = Path(filepath)
    if not path.exists():
        return {"error": f"File not found: {filepath}"}
    
    text = path.read_text(encoding="utf-8")
    findings = []
    
    for category, config in SENSITIVE_PATTERNS.items():
        matches = config["pattern"].findall(text)
        for match in matches:
            findings.append({
                "category": category,
                "match": str(match)[:80],
                "message": config["message"],
            })
    
    # Check for required statements
    missing_statements = []
    for stmt in REQUIRED_STATEMENTS:
        if stmt.lower() not in text.lower():
            missing_statements.append(stmt)
    
    return {
        "file": filepath,
        "findings": findings,
        "finding_count": len(findings),
        "missing_statements": missing_statements,
        "status": "pass" if len(findings) == 0 and len(missing_statements) == 0 else "review_needed",
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python check_sensitive_data_security.py <manuscript.md>")
        sys.exit(1)
    
    result = check_sensitive_data_security(sys.argv[1])
    
    print(f"# Sensitive Data Security Audit")
    print(f"\nFile: {result['file']}")
    print(f"Findings: {result['finding_count']}")
    print(f"Status: {result['status']}\n")
    
    if result["findings"]:
        print("## Findings")
        for f in result["findings"]:
            print(f"- [{f['category']}] {f['message']}")
            print(f"  Match: {f['match']}")
    
    if result["missing_statements"]:
        print("\n## Missing Statements")
        for s in result["missing_statements"]:
            print(f"- No '{s}' statement found")
    
    if result["status"] == "pass":
        print("\n✓ No sensitive data issues detected.")


if __name__ == "__main__":
    main()
