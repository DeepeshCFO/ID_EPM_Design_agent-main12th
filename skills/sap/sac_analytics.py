"""SAP Analytics Cloud (SAC) — Analytics knowledge."""


def get_knowledge() -> dict:
    """Return structured knowledge for SAP Analytics Cloud Analytics."""
    return {
        "summary": (
            "SAP Analytics Cloud (SAC) Analytics is SAP's cloud-native BI platform for stories, "
            "dashboards, and augmented analytics. It connects live to BW/4HANA, S/4HANA, and "
            "HANA Cloud/Datasphere, or imports a snapshot into its own in-memory model, and "
            "layers AI-driven Smart Insights and natural-language search on top."
        ),
        "key_concepts": [
            "Live Connection vs Import Model: live queries the source system directly; import loads a snapshot into SAC's in-memory model",
            "Stories: SAC's primary reporting artefact — canvas or responsive grid-based pages with charts, tables, and widgets",
            "Pages and Page Books: multi-page story structures for report packs and management reporting decks",
            "Smart Insights: AI-generated natural-language explanation of a data point's key drivers",
            "Search to Insight: natural-language query interface that generates charts automatically",
            "Geo Maps: location-based visualisation layers (choropleth, bubble) for regional analysis",
            "Digital Boardroom: presentation-optimised, interactive executive dashboard mode",
            "Calculated / Restricted Measures: story-level or model-level derived measures without source-system changes",
            "Analytic Model: read-optimised SAC data model defining measures, dimensions, and hierarchies",
            "Predictive Forecasting: built-in time-series forecasting applied directly on story charts",
            "Responsive design: story layouts that adapt across desktop, tablet, and mobile form factors",
            "SAC Mobile: native mobile app consumption of stories and Digital Boardroom",
        ],
        "kpis": [
            "Story load/render time",
            "Live connection query response time",
            "Number of active story consumers (adoption KPI)",
            "Data refresh latency for imported models",
            "Smart Insights usage rate",
            "Story/widget error rate (broken connections)",
        ],
        "sap_objects": [
            "SAC Story",
            "SAC Analytic Model",
            "Live Data Connection (to BW/4HANA, HANA Cloud, Datasphere)",
            "Import Data Connection",
            "Calculated Measure / Restricted Measure",
            "Widget (chart, table, geo map, filter)",
            "Digital Boardroom Agenda",
            "Page Book",
        ],
        "common_patterns": [
            "Live connection to BW/4HANA HANA Calculation Views for zero-latency executive dashboards",
            "Import model blended from multiple source systems for cross-functional reporting not natively joinable live",
            "Digital Boardroom monthly management reporting pack replacing static presentation decks",
            "Smart Insights embedded in variance charts to auto-explain KPI movements to business users",
            "Responsive story design reused across desktop review meetings and mobile field consumption",
        ],
    }
