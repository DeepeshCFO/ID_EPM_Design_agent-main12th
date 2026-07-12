"""SAP BW/4HANA — modern cloud-ready data warehouse knowledge."""


def get_knowledge() -> dict:
    """Return structured knowledge for SAP BW/4HANA."""
    return {
        "summary": (
            "SAP BW/4HANA is SAP's modern, cloud-ready enterprise data warehouse built natively "
            "on HANA. It replaces InfoCubes and classic DSOs with a simplified layer of Advanced "
            "DSOs and HANA Calculation Views, extracts via ODP and CDS-based extraction, and "
            "exposes data to SAC and Analysis for Office for reporting."
        ),
        "key_concepts": [
            "Advanced DSO (aDSO): BW/4HANA's unified persistent layer replacing InfoCubes and classic DSOs",
            "CompositeProvider: virtual join layer over multiple InfoProviders",
            "Open ODS View / HANA Analysis Process: BW/4HANA lightweight virtual providers for pass-through access",
            "ODP (Operational Data Provisioning): standard extraction from S/4HANA / ECC using delta queues",
            "CDS-based extraction: ODP source using ABAP CDS views with the @Analytics.dataExtraction annotation",
            "HANA Calculation Views: columnar engine views for complex aggregations, consumed as InfoProviders",
            "BW/4HANA migration patterns: Shell Conversion, In-Place Migration, Remote Conversion, Mixed approach",
            "BW Modeling Tools in Eclipse: BW/4HANA's dedicated development environment",
            "DTP (Data Transfer Process): Full / Delta / Repair load strategies, real-time DTPs for HANA-optimised flows",
            "Transformations with AMDP-based expert routines for HANA-pushdown transformation logic",
            "Process chains for orchestration and monitoring of BW/4HANA data loads",
            "SAC Live Connection to BW/4HANA: zero-latency reporting on HANA Calculation Views and aDSOs",
        ],
        "kpis": [
            "Data load performance (records/hour, load duration vs SLA)",
            "Query response time (< 3 seconds for standard operational reports)",
            "Data freshness (latency from source transaction to BW/4HANA availability)",
            "Delta queue backlog (unprocessed delta records)",
            "aDSO compression ratio",
            "Failed DTP / process chain runs",
        ],
        "sap_objects": [
            "Advanced DSO (aDSO)",
            "CompositeProvider",
            "Open ODS View",
            "HANA Calculation View",
            "DataSource (ODP source)",
            "Transformation (AMDP / expert routine)",
            "DTP (Full / Delta / Repair)",
            "Process Chain",
            "BW Query (Query Designer / BEx on BW/4HANA)",
            "InfoObject (characteristic / key figure)",
            "InfoArea / InfoObject Catalog",
        ],
        "common_patterns": [
            "Delta extraction from S/4HANA via ODP using CDS views with change-document-based delta",
            "Simplified staging: PSA → Write-Optimised aDSO → aDSO reporting layer (single-layer model vs legacy multi-DSO layering)",
            "Universal Journal (ACDOCA) extraction for Finance reporting using standard ODP DataSources",
            "SAC Live Connection: HANA Calculation Views exposed as analytic models for zero-latency stories",
            "Shell Conversion migration: rebuild BW/4HANA objects from scratch, reusing transformation logic without migrating data history",
            "In-Place migration: upgrade the existing BW system while converting InfoCubes/DSOs to aDSO",
            "Exception aggregation for non-additive key figures (inventory balances, headcount)",
            "Open ODS View used for real-time pass-through queries directly against HANA tables",
        ],
    }
