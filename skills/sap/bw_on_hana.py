"""SAP BW on HANA (7.5) — legacy data warehouse knowledge."""


def get_knowledge() -> dict:
    """Return structured knowledge for SAP BW 7.5 running on the HANA database."""
    return {
        "summary": (
            "SAP BW on HANA (7.5) is the legacy SAP BW platform running on the HANA in-memory "
            "database. It retains classic modelling objects — InfoCubes, DSOs, MultiProviders — "
            "accelerated by HANA, with LO Cockpit and generic extraction feeding BEx queries and "
            "Analysis for Office (AFO) reporting."
        ),
        "key_concepts": [
            "InfoCubes: star-schema fact/dimension storage — the BW 7.x modelling standard",
            "DSO types: Standard DSO (delta queue), Write-Optimised DSO (staging), Direct Update DSO (real-time)",
            "InfoObjects: characteristics and key figures, with navigation attributes and hierarchies",
            "MultiProvider: union-based virtual provider joining InfoCubes/DSOs for cross-domain reporting",
            "LO Cockpit extraction: V3 update, direct delta, LBWE customising for SD/MM logistics extraction",
            "Generic extraction via DB view, function module, or InfoSet for custom source tables",
            "BEx Query Designer: restricted/calculated key figures, variables, conditions, exceptions",
            "Analysis for Office (AFO): Excel add-in for BW queries, with write-back support via BW-IP",
            "BEx Web Application Designer: legacy web-based reporting templates",
            "Process chains: scheduling and monitoring of InfoPackages and DTPs",
            "Aggregates and HANA-optimised InfoCubes for query performance acceleration",
            "Transformations and routines: start/end/expert routine ABAP logic in field mapping",
        ],
        "kpis": [
            "Data load performance (records/hour, load duration vs SLA)",
            "Query response time (< 3 seconds for standard operational reports)",
            "Delta queue backlog (unprocessed delta records)",
            "InfoCube compression ratio",
            "Failed DTP/InfoPackage runs",
            "Aggregate hit ratio (query acceleration effectiveness)",
        ],
        "sap_objects": [
            "InfoCube",
            "Standard / Write-Optimised / Direct-Update DSO",
            "MultiProvider",
            "InfoObject (characteristic / key figure)",
            "DataSource (LO Cockpit / generic extraction)",
            "Transformation / InfoSource",
            "DTP (Data Transfer Process)",
            "InfoPackage",
            "Process Chain",
            "BEx Query (with RKF, CKF, variables, conditions, exceptions)",
            "Analysis for Office workbook",
            "Aggregate",
        ],
        "common_patterns": [
            "LO Cockpit extraction with V3 update queue for SD billing/delivery data",
            "Staging pattern: PSA → Write-Optimised DSO → Standard DSO → InfoCube reporting layer",
            "Analysis authorisation variables mapped to BEx queries for row-level security",
            "Currency translation in BEx queries using translation types and target currencies",
            "Aggregate-based query acceleration for high-volume operational reports",
            "AFO planning write-back via BW-IP for budget input templates",
            "Time-dependent hierarchy reporting using BW hierarchy InfoObjects (time- and version-dependent)",
        ],
    }
