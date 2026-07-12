"""SAP Business Data Cloud (BDC), Datasphere, and HANA Cloud knowledge."""


def get_knowledge() -> dict:
    """Return structured knowledge for SAP Business Data Cloud (BDC) / Datasphere."""
    return {
        "summary": (
            "SAP Business Data Cloud (BDC) is SAP's converged analytics and data management "
            "platform combining SAP Datasphere and SAP Analytics Cloud. Datasphere provides a "
            "business data fabric with governed data integration, semantic modelling, and data "
            "warehousing. SAP HANA Cloud is the cloud-native in-memory database underpinning "
            "both Datasphere and BDC."
        ),
        "key_concepts": [
            "SAP Datasphere: cloud-native data warehouse and integration platform — successor to SAP Data Warehouse Cloud",
            "Spaces: isolated tenant-level workspaces in Datasphere with own connections, objects, and access controls",
            "Data Flows: ETL/ELT pipeline objects in Datasphere for batch data movement and transformation",
            "Replication Flows: near-real-time replication from SAP and non-SAP sources into Datasphere using change data capture",
            "Analytic Models: semantic layer objects in Datasphere analogous to BW queries — define measures, dimensions, hierarchies",
            "Business Layer: Datasphere's governed catalogue of business entities (Entities, Relationships, Perspectives) for self-service",
            "Data Builder: technical layer for tables, views, flows, and entity-relationship models",
            "Business Builder: semantic layer for business entities, KPIs, and consumption-ready objects",
            "SAP HANA Cloud: fully managed cloud HANA database with multi-model capabilities (columnar, graph, spatial, document)",
            "HANA Cloud Data Lake: cost-optimised cold storage for large volumes integrated with HANA Cloud via virtual access",
            "Federation: Datasphere's ability to query remote data sources in-place without physical replication (virtual tables)",
            "Open Connectors: pre-built connectors to 170+ non-SAP data sources (Salesforce, Snowflake, Azure, AWS, etc.)",
            "BDC Business Content: pre-built end-to-end analytic scenarios for Finance, Supply Chain, and HR from SAP",
            "SAC Live Connection to Datasphere: zero-copy analytics on Datasphere analytic models from SAC stories",
        ],
        "kpis": [
            "Data replication latency (seconds from source change to Datasphere availability)",
            "Data pipeline run duration and SLA adherence",
            "Space storage utilisation (GB used vs allocated)",
            "Number of federated vs replicated sources (architecture balance)",
            "Query performance on analytic models (response time SLA)",
            "Data quality rule pass rate (% of records passing validation)",
        ],
        "sap_objects": [
            "Datasphere Space",
            "Remote Table (federated virtual table from source system)",
            "Local Table (physically replicated table in Datasphere)",
            "Graphical View / SQL View",
            "Data Flow (batch ETL pipeline)",
            "Replication Flow (CDC-based near-real-time replication)",
            "Analytic Model (semantic consumption layer)",
            "Business Entity (Business Builder governed object)",
            "Relationship (Business Builder join definition)",
            "Perspective (Business Builder curated KPI view)",
            "Data Access Control (row-level security object)",
            "HANA Cloud Instance",
            "HANA Cloud Data Lake Files / Relational Engine",
            "Open Connector (third-party integration)",
        ],
        "common_patterns": [
            "BDC reference architecture: S/4HANA → Replication Flow → Datasphere local tables → Analytic Model → SAC story",
            "Medallion architecture in Datasphere: Bronze (raw replication) → Silver (cleansed local tables) → Gold (analytic models)",
            "Federated query pattern: large historical data in HANA Cloud Data Lake, recent data in HANA Cloud, unified via virtual access",
            "Hybrid cloud-on-premise: Datasphere space connected to on-premise BW/4HANA via HANA Cloud connector",
            "Business Content activation: standard SAP BDC content packages for Finance (Universal Journal, Profitability) as starting point",
            "Data marketplace: subscribing to Datasphere data products from partner or internal providers for cross-domain analytics",
            "Self-service analytics: Business Builder perspectives published to business users in SAC via governed semantic layer",
            "Delta replication: incremental change capture from S/4HANA ACDOCA using Replication Flow with delta run strategy",
        ],
    }
