"""SAP PaPM (Profitability and Performance Management) knowledge."""


def get_knowledge() -> dict:
    """Return structured knowledge for SAP PaPM."""
    return {
        "summary": (
            "SAP PaPM (Profitability and Performance Management) is SAP's driver-based "
            "allocation and profitability modelling platform on HANA. It models cost and "
            "revenue flows through configurable calculation flows, integrating with CO-PA and "
            "S/4HANA to produce granular, on-demand profitability views."
        ),
        "key_concepts": [
            "Calculation Flows: sender → allocation rule → receiver chains, driven by quantity or value drivers",
            "PaPM Environments: logical grouping of calculation flows for phased or modular execution",
            "Driver-Based Costing: costs allocated using operational drivers (headcount, machine hours, transaction volume) rather than flat ratios",
            "Activity-Based Costing (ABC): multi-step allocation from resource costs to activities to cost objects (products, customers, channels)",
            "Cost Component Splits: retaining the origin/type of cost through successive allocation steps for transparency",
            "Multi-Step Calculation Chains: sequential functions (mapping, allocation, pivot, aggregation) building a full profitability model",
            "What-If Simulation: re-running a calculation flow with adjusted driver rates without touching source data",
            "Model Versioning: maintaining parallel calculation flow versions for simulation vs published results",
            "Integration with CO-PA and S/4HANA: sourcing actuals directly from Controlling and the Universal Journal",
        ],
        "kpis": [
            "Allocation cycle runtime",
            "Driver coverage ratio (% of costs allocated via drivers vs manual)",
            "Model recalculation time (for what-if simulations)",
            "Number of calculation steps per model (complexity indicator)",
            "Profitability report accuracy / reconciliation to GL",
        ],
        "sap_objects": [
            "PaPM Environment",
            "Calculation Flow",
            "Allocation Rule",
            "Function (mapping, allocation, pivot, aggregation)",
            "Rate (driver-based unit rate)",
            "Field Mapping",
        ],
        "common_patterns": [
            "Activity-based costing chain from GL/CO-PA source data to product or customer profitability",
            "What-if simulation adjusting driver rates in a calculation flow before publishing results",
            "Multi-step allocation cascading indirect cost centres → production cost centres → products",
            "Parallel calculation flow versions maintained for legal vs management profitability views",
        ],
    }
