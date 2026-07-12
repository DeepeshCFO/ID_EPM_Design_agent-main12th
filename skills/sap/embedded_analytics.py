"""SAP Embedded Analytics — CDS views, Virtual Data Model, and Fiori analytical apps knowledge."""


def get_knowledge() -> dict:
    """Return structured knowledge for SAP Embedded Analytics (CDS / Fiori)."""
    return {
        "summary": (
            "SAP Embedded Analytics delivers real-time operational reporting directly on "
            "S/4HANA using ABAP CDS views, the Virtual Data Model (VDM), and Fiori analytical "
            "apps — without extracting data to a separate data warehouse."
        ),
        "key_concepts": [
            "CDS view types: basic (DDIC-based), composite (joins/unions), consumption (Fiori/analytics-ready), analytical",
            "Virtual Data Model (VDM) layering: Private (P_), Basic (I_), Composite (C_), Consumption (Z_/Y_) naming convention",
            "CDS analytical annotations: @Analytics.query, @Cube, @Dimension, @Consumption.valueHelpDefinition",
            "Fiori Analytical List Page (ALP): filter bar plus analytical table/chart combination",
            "Fiori Overview Page (OVP): KPI card-based landing page tailored to a business role",
            "KPI tiles and cards backed directly by CDS analytical queries",
            "SAP Fiori Launchpad: role-based tile catalogue for analytical app access",
            "Smart Filter Bar / Smart Table: metadata-driven Fiori Elements UI controls",
            "OData services auto-exposed from consumption CDS views for Fiori and analytics consumption",
            "Embedded Analytics vs BW: real-time operational reporting directly on S/4HANA vs historised/harmonised BW reporting",
            "Multidimensional reporting on CDS cubes consumed directly in Analysis for Office or SAC without a BW layer",
        ],
        "kpis": [
            "Query response time on live CDS views",
            "KPI tile refresh latency",
            "Number of custom CDS extensions vs standard VDM reuse (customisation ratio)",
            "OData service call volume",
            "Fiori analytical app adoption rate",
        ],
        "sap_objects": [
            "CDS View (basic / composite / consumption / analytical)",
            "CDS View Extension (EXTEND VIEW)",
            "OData Service",
            "Fiori Analytical List Page",
            "Fiori Overview Page",
            "KPI Tile",
            "Smart Filter Bar / Smart Table",
        ],
        "common_patterns": [
            "Consumption CDS view with @Analytics.query:true replacing a BEx query for real-time embedded reporting",
            "Fiori Overview Page assembling KPI tiles from multiple CDS-based OData services",
            "CDS extension (EXTEND VIEW) adding custom fields to standard VDM views without modifying SAP standard",
            "SAC live connection directly to S/4HANA CDS views, bypassing BW for real-time reporting",
            "Analytical List Page combining a filter bar with a chart/table pair for operational drill-down",
        ],
    }
