"""SAP BPC (Business Planning & Consolidation) — Standard and Embedded knowledge."""


def get_knowledge() -> dict:
    """Return structured knowledge for SAP BPC Standard and Embedded."""
    return {
        "summary": (
            "SAP BPC (Business Planning & Consolidation) covers budgeting, forecasting, and "
            "statutory consolidation. BPC Standard runs on its own OLAP engine; BPC Embedded "
            "runs directly on BW-IP (BW Integrated Planning), using aggregation levels and "
            "planning functions on top of the BW data model."
        ),
        "key_concepts": [
            "Application Set / Environment: BPC's top-level container for models, dimensions, and security",
            "Dimensions: Account, Entity, Category, Time, and custom dimensions defining the planning cube",
            "Models: Standard (planning) or Consolidation type, each mapped to a set of dimensions",
            "Input Schedules: EPM Add-in Excel templates for structured plan data entry",
            "BPC Standard vs Embedded: Standard has its own OLAP engine; Embedded runs on BW-IP directly on BW/4HANA",
            "Script Logic (.LGF): BPC's server-side calculation language, including DEFAULT.LGF and custom logic scripts",
            "FOX formulas: BW-IP's formula language for planning calculations on aggregation levels",
            "BW-IP Aggregation Levels: the planning-enabled subset of an InfoProvider's characteristics/key figures",
            "BW-IP Planning Functions and Sequences: copy, delete, repost, distribute, and custom FOX logic, chained in sequences",
            "Business Rules: currency translation, intercompany elimination, and carry-forward, executed as part of a consolidation run",
            "BPC-to-SAC migration: dimension mapping, model type selection, and data action replacement for Script Logic",
        ],
        "kpis": [
            "Planning cycle time (days from kickoff to approved plan)",
            "Consolidation close time (days to complete statutory close)",
            "Forecast accuracy (MAPE)",
            "Number of manual journal entries (consolidation adjustment quality KPI)",
            "Business rule / script logic execution time",
        ],
        "sap_objects": [
            "BPC Application Set / Environment",
            "BPC Dimension (Account, Entity, Category, Time, custom)",
            "BPC Model (Standard or Consolidation type)",
            "BPC Input Schedule (EPM Add-in template)",
            "BPC Business Rule (currency translation, intercompany elimination, carry-forward)",
            "BPC Script Logic file (.LGF)",
            "BW-IP Aggregation Level",
            "BW-IP Planning Function (formula, copy, delete, repost, FOX)",
            "BW-IP Planning Sequence",
        ],
        "common_patterns": [
            "BPC Embedded planning write-back to BW aDSO aggregation levels via BW-IP planning functions",
            "Consolidation business rules (IC elimination, currency translation, carry-forward) chained in a single run package",
            "EPM Add-in input schedule for decentralised cost centre budget entry",
            "Top-down/bottom-up planning cycle reconciled via Script Logic allocation rules",
            "BPC-to-SAC migration mapping: BPC dimensions translated to SAC model dimensions, Script Logic reworked as data actions",
        ],
    }
