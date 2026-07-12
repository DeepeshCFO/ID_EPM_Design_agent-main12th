"""SAP ABAP, enhancements, BAdI, CDS annotations, and AMDP knowledge."""


def get_knowledge() -> dict:
    """Return structured knowledge for SAP ABAP custom development."""
    return {
        "summary": (
            "SAP ABAP is the primary programming language for SAP system customisation. "
            "ABAP OO (Object-Oriented ABAP) is the modern standard. Enhancement framework "
            "mechanisms (BAdI, user exits, enhancement spots) allow modifications without "
            "changing SAP standard objects. ABAP CDS views provide semantic data models "
            "consumed by analytics and Fiori apps. AMDP pushes ABAP logic into the HANA "
            "database engine for performance."
        ),
        "key_concepts": [
            "ABAP OO: classes, interfaces, inheritance, polymorphism — mandatory for modern ABAP development",
            "BAdI (Business Add-In): SAP's primary enhancement mechanism — definition in SE18, implementation in SE19",
            "Classic user exits: SMOD/CMOD framework (legacy — prefer BAdI for new development)",
            "Enhancement spots and explicit enhancement points: source code hooks without modifying standard",
            "ABAP CDS (Core Data Services): data definition language for semantic views, used in S/4HANA VDM",
            "CDS view types: basic (DDIC-based), composite (joins/unions), consumption (Fiori/analytics-ready)",
            "CDS analytical annotations: @Analytics.query, @Cube, @Dimension, @Consumption.valueHelpDefinition",
            "Virtual Data Model (VDM) layers: Private (P_), Basic (I_), Composite (C_), Consumption (Z_/Y_) naming convention",
            "AMDP (ABAP Managed Database Procedures): ABAP class methods implemented as HANA SQLScript procedures",
            "BW custom infosources: RSAP0001 (flexible update) and start/end/expert routines in transformations",
            "Start routine: row-level filtering of source package before transformation",
            "End routine: result set manipulation after all field routines execute",
            "Expert routine: complete replacement of field routines — full control of source-to-target mapping",
            "ABAP Unit testing: test classes (FOR TESTING), test methods, test doubles, mock injection via constructor injection",
            "Clean ABAP: official SAP style guide for readable, testable, maintainable ABAP code",
        ],
        "kpis": [
            "Custom code coverage by ABAP Unit tests (%)",
            "Number of user exits / BAdIs implemented (complexity indicator)",
            "Custom code modification index (standard vs custom ratio)",
            "ABAP runtime performance (response time in SM50/SM66)",
            "Transport success rate (% of transports reaching production without error)",
        ],
        "sap_objects": [
            "ABAP Class (SE24 / ABAP in Eclipse)",
            "ABAP Interface",
            "BAdI Definition (SE18)",
            "BAdI Implementation (SE19 / ABAP in Eclipse)",
            "Enhancement Spot (SE80)",
            "Function Module (SE37) — legacy; use classes for new development",
            "ABAP CDS View (DDL source in ABAP in Eclipse)",
            "CDS View Extension (EXTEND VIEW)",
            "ABAP Managed Database Procedure (AMDP method)",
            "BW Transformation with custom routine (ABAP editor in transformation)",
            "Start Routine (ABAP code in BW transformation)",
            "End Routine (ABAP code in BW transformation)",
            "Expert Routine (ABAP code replacing all field routines)",
            "Custom InfoSource (RSAR transaction)",
            "ABAP Report / Program (SE38)",
            "Transport Request (SE09/SE10)",
        ],
        "common_patterns": [
            "BAdI implementation for custom validation in S/4HANA standard processes (e.g. FI posting exit)",
            "AMDP-based complex allocation logic: push set-based HANA SQLScript into database layer for sub-second performance",
            "CDS consumption view with @Analytics.query:true as virtual BEx query replacement in S/4HANA Embedded Analytics",
            "Expert routine in BW transformation for complex master data derivation or currency conversion override",
            "Constructor injection pattern for unit-testable BAdI implementations (dependency injected via constructor)",
            "CDS extension (EXTEND VIEW) to add custom fields to standard VDM views without modifying SAP standard",
            "ABAP CDS with association-based navigation for Fiori element-driven analytical list pages",
            "Enhancement spot with pre/post implementation for standard ABAP method augmentation",
            "Start routine as data quality gate: reject source records failing business validation before transformation",
        ],
    }
