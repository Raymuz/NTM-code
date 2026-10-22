# ORIGINAL NTM CONTENT HANDLERS; AST-extracted from verified 214-cell source, cell 174.
# Private prices, identity, service clients, credentials and customer data are not included.
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional

SCOPE_SECTIONS: Dict[str, List[Dict[str, Any]]] = {
    "construction": [
        {"name": "Site preparation and access", "items": [
            "Topographical survey of the construction site",
            "Clear and level approximately {area_plus_50} sqm including working space",
            "Remove vegetation, debris and any existing structures",
            "Establish site boundaries and construction access points",
            "Temporary site facilities: storage and worker welfare",
            "Access for construction vehicles and material delivery",
            "Temporary fencing and security per Cameroon safety regulations",
            "Soil bearing capacity tests to confirm foundation design",
            "Test for groundwater levels and drainage requirements",
            "Identify and mark existing utility lines",
            "Temporary power and water connections for construction",
        ]},
        {"name": "Foundation and substructure", "items": [
            "Excavate foundation trenches to a minimum 1.2 m below ground level",
            "Excavate for septic tank, soakaway and underground utilities",
            "Shoring and support to excavations as required",
            "{foundation_type} in reinforced concrete, Grade 25",
            "Foundation reinforcement to structural drawings",
            "Damp proof course at foundation level",
            "Curing of concrete for a minimum of 28 days",
            "Backfill in layers with approved material",
            "Underground plumbing rough-in, water supply and drainage",
            "Electrical conduits and grounding below ground",
            "Septic tank and soakaway per Cameroon health regulations",
            "Test all underground systems before backfilling",
        ]},
        {"name": "Superstructure", "items": [
            "Load-bearing walls in {wall_material}, 6 inch and 9 inch as specified",
            "Reinforced concrete columns and beams to structural design",
            "{floors} floor slab(s) in reinforced concrete",
            "Lintels over all door and window openings",
            "Wall ties and reinforcement at corners and junctions",
            "Roof structure in treated timber or steel trusses",
            "{roofing_material} with underlayment",
            "Gutters and downspouts for rainwater management",
            "Roof ventilation and insulation for tropical climate",
            "Minimum roof slope 1:40 for metal roofing",
        ]},
        {"name": "Mechanical, electrical and plumbing", "items": [
            "Main electrical panel and distribution boards",
            "Power points: minimum 4 per bedroom, 6 per living area",
            "Lighting fixtures suited to tropical climate",
            "Outdoor and security lighting",
            "Ceiling fans in all bedrooms and living areas",
            "Electrical testing and certification to Cameroon codes",
            "Water supply with overhead storage tank, minimum 2000 litres",
            "Hot water system, solar or electric as specified",
            "Plumbing fixtures to {bathrooms} bathroom(s)",
            "Pressure test all water supply and drainage systems",
            "Exhaust fans to bathrooms and kitchen",
            "Provisions for air conditioning: electrical and structural",
            "Security grilles to all windows and external doors",
        ]},
        {"name": "Finishes and interior", "items": [
            "Cement plaster to all internal and external walls",
            "Interior emulsion: 2 undercoats and 2 finish coats",
            "Weather-resistant external paint for tropical climate",
            "Wall tiling to bathrooms and kitchen",
            "{flooring_type} to all main areas with grouting",
            "Skirting boards and floor transitions",
            "Waterproofing to bathroom and kitchen floors",
            "Ceiling finishes with primer and finish coats",
            "Minimum ceiling height 3.0 m to ground floor",
            "Aluminium windows with security grilles and mosquito nets",
            "Solid core doors to bedrooms, hollow core internally",
            "Security door to main entrance with multiple locking",
            "Weather stripping and seals",
        ]},
        {"name": "External works", "items": [
            "External wall plastering and painting",
            "External lighting and security systems",
            "Walkways and access paths in concrete or paving",
            "Drainage around the building perimeter",
            "External water taps and utility connections",
            "Grade and level the surrounding site",
            "Basic landscaping including grass planting",
            "Boundary walls or fencing as specified",
            "Driveway and parking areas if required",
            "Connection to municipal water or borehole installation",
            "Electrical grid connection with metering",
        ]},
        {"name": "Quality control and standards", "items": [
            "Cement: Grade 42.5, Dangote or equivalent approved",
            "Reinforcement: high-yield deformed bars, Grade 460",
            "Blocks: well-cured sandcrete, 6 inch and 9 inch",
            "Roofing: corrosion-resistant aluminium sheets, 0.55 mm",
            "Plumbing: UPVC or approved tropical equivalent",
            "Work executed by qualified tradesmen under experienced foremen",
            "Compliance with the Cameroon National Building Code",
            "Concrete cube tests for all structural concrete",
            "Electrical installation testing and certification",
            "Final building inspection and occupancy certificate",
            "Handover documentation including warranties and manuals",
        ]},
        {"name": "Handover", "items": [
            "Snagging and making good",
            "Final clean of the property",
            "Handover of keys, warranties and maintenance manuals",
        ]},
    ],
    "cleaning": [
        {"name": "Preparation", "items": [
            "Site inspection and risk check",
            "Protection of fittings and finishes",
            "Set out equipment and consumables",
        ]},
        {"name": "Main clean", "items": [
            "Surfaces, floors and sanitary ware",
            "Windows and glazing where safely reachable",
            "Kitchen units, appliances and extract",
        ]},
        {"name": "Finishing", "items": [
            "Waste removal and disposal",
            "Supervisor inspection against checklist",
            "Free re-clean if the client is not satisfied",
        ]},
    ],
}

SCOPE_DEFAULTS = {
    # Descriptive material placeholders only. Numeric project facts such as
    # floors/bathrooms are intentionally NOT defaulted.
    "foundation_type": "the specified foundation system",
    "roofing_material": "the specified roofing material",
    "wall_material": "the specified wall material",
    "flooring_type": "the specified flooring material",
    "floors": "specified",
    "bathrooms": "specified",
}

def build_scope(specs: Optional[Dict] = None,
                service: str = "construction") -> List[Dict[str, Any]]:
    """Fill the scope sections from the project specs."""
    values = {**SCOPE_DEFAULTS, **(specs or {})}
    area = float(values.get("area_sqm") or 0)
    values["area_plus_50"] = f"{area + 50:g}" if area else "the required"
    out = []
    for section in SCOPE_SECTIONS.get(service, SCOPE_SECTIONS["construction"]):
        items = []
        for item in section["items"]:
            try:
                items.append(item.format(**values))
            except (KeyError, IndexError):
                items.append(re.sub(r"\\{[^}]*\\}", "the specified", item))
        out.append({"name": section["name"], "deliverables": items})
    return out

BASE_ASSUMPTIONS = [
    "Site is level and accessible for construction vehicles and material delivery",
    "No major soil remediation or excavation beyond standard foundation requirements",
    "Site has adequate drainage and is not in a flood-prone area",
    "No underground utilities or structures interfering with construction",
    "Water supply is available on site or nearby for construction use",
    "Electrical power is available for construction equipment",
    "Access roads can accommodate construction vehicles and deliveries",
    "Waste disposal facilities are available in the area",
    "All necessary building permits will be obtained before construction begins",
    "Construction will comply with the Cameroon National Building Code",
    "Local authority inspections will be scheduled as required",
    "No changes to local building regulations during the construction period",
    "Client approvals and decisions provided within agreed timeframes",
    "No major delays from material availability or labour shortages",
]

DOUALA_ASSUMPTIONS = [
    "Construction accounts for Douala's tropical climate and high humidity",
    "Materials sourced locally where possible to minimise transport costs",
    "Schedule allows for rainy season impacts between March and November",
]

CLASS_ASSUMPTIONS = {
    "standard": [
        "Standard quality materials to Cameroon building standards",
        "Cement: Dangote 42.5 or equivalent grade",
        "Roofing: standard aluminium roofing sheets",
        "Tiles: standard ceramic tiles to flooring",
        "Electrical: basic installation with standard fixtures",
    ],
    "premium": [
        "Premium materials exceeding standard Cameroon requirements",
        "High-grade cement and reinforcement",
        "Premium roofing with extended warranty",
        "Porcelain tiles and premium finishing materials",
        "Enhanced electrical systems with modern fixtures",
    ],
    "economy": [
        "Economy specification materials meeting Cameroon minimum standards",
        "Cement: Grade 42.5",
        "Basic fixtures and fittings throughout",
    ],
    "luxury": [
        "Luxury specification throughout, imported finishes where specified",
        "High-grade cement, reinforcement and waterproofing",
        "Premium roofing with extended warranty",
        "Imported sanitary ware and joinery",
    ],
}

STANDARD_EXCLUSIONS = [
    "Landscaping and garden development unless specifically included",
    "Furniture, fixtures and movable equipment",
    "Kitchen appliances and built-in equipment unless specified",
    "Air conditioning systems unless specifically included",
    "Security systems and CCTV installation unless specified",
    "Site survey and soil testing, client responsibility",
    "Demolition of existing structures unless specified",
    "Tree removal and clearing beyond basic preparation",
    "Retaining walls or major earthworks unless specified",
    "Connection to municipal water, sewer and electricity mains",
    "Owner-supplied materials and fixtures",
    "Imported materials requiring special permits or high customs duties",
    "Materials affected by price movement beyond 30 days",
    "Specialty items not readily available in the Cameroon market",
    "Architectural and engineering design fees unless specified",
    "Building permit fees and government charges",
    "Insurance cover during construction, client responsibility",
    "Temporary accommodation during construction",
    "Storage of client belongings during construction",
    "Currency movement beyond 5 percent against XAF",
    "Additional costs from changes in government taxes or duties",
    "Costs from project delays caused by the client",
    "Additional work requested beyond the original scope",
]

NO_FEATURE_EXCLUSIONS = [
    "Solar panel systems and renewable energy installations",
    "Smart home automation systems",
    "Swimming pool construction",
    "Generator installation and electrical backup systems",
]

def build_assumptions(specs: Optional[Dict] = None) -> Dict[str, List[str]]:
    """Assumptions and exclusions, varying by location, class and features."""
    specs = specs or {}
    location = str(specs.get("location") or specs.get("quarter") or "")
    finish = str(specs.get("finish_level") or "standard").lower()
    features = specs.get("special_features") or []
    assumptions = list(BASE_ASSUMPTIONS)
    if "douala" in location.lower():
        assumptions += DOUALA_ASSUMPTIONS
    assumptions += CLASS_ASSUMPTIONS.get(finish, CLASS_ASSUMPTIONS["standard"])
    if specs.get("timeline_months"):
        assumptions.append(f"Project duration estimated at "
                           f"{specs['timeline_months']} months on the current scope")
    exclusions = list(STANDARD_EXCLUSIONS)
    if not features:
        exclusions += NO_FEATURE_EXCLUSIONS
    return {"assumptions": assumptions, "exclusions": exclusions}

def scope_handler(state, service: str = "construction", **kw):
        pd = state.get("project_data") or {}
        specs = {**(pd.get("auto_filled_assumptions") or {}),
                 **(pd.get("extracted_specs") or {})}
        phases = build_scope(specs, service)
        return {"status": "ok", "service": service, "phases": phases,
                "source": "NTM scope of work, 8 sections"}

def assumptions_handler(state, **kw):
        pd = state.get("project_data") or {}
        specs = {**(pd.get("auto_filled_assumptions") or {}),
                 **(pd.get("extracted_specs") or {})}
        built = build_assumptions(specs)
        return {"status": "ok", "assumptions": built["assumptions"],
                "exclusions": built["exclusions"],
                "auto_filled": pd.get("auto_filled_assumptions") or {},
                "assumption_notes": pd.get("assumption_reasons") or {}}
