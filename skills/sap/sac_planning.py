"""SAP Analytics Cloud (SAC) — Planning / FP&A knowledge."""


def get_knowledge() -> dict:
    """Return structured knowledge for SAP Analytics Cloud Planning."""
    return {
        "summary": (
            "SAP Analytics Cloud (SAC) Planning is SAP's cloud-native planning platform, "
            "supporting driver-based budgeting, rolling forecasts, and scenario planning with "
            "integrated analytics. Its Integrated Financial Planning (sFIN) content provides "
            "best-practice account-based planning for S/4HANA Finance."
        ),
        "key_concepts": [
            "Planning models: public/private versions, date range, audit trail, data locking",
            "Data Actions: value driver tree logic, predictive planning, distribution, breakback, currency conversion",
            "Multi-Actions: orchestrated sequences of data actions with conditional branching",
            "Allocation Processes: driver-based cost allocation with sender/receiver rules",
            "Integrated Financial Planning (sFIN): standard best-practice planning content for SAP S/4HANA Finance",
            "Value Driver Trees: visual, formula-linked planning logic connecting operational drivers to financial outcomes",
            "Data Locking: version/time-slice locking to freeze submitted plan data from further edits",
            "Version Management: public actual/budget/forecast versions vs private simulation/sandbox versions",
            "Planning Calendar / process workflow: task-based submission and approval workflow across planning cycles",
            "Currency conversion applied at data-action or model level using configurable rate types",
            "Integrated planning write-back to S/4HANA via APIs for operational execution",
            "Planning table (grid): dimension-based input template for manual plan entry",
        ],
        "kpis": [
            "Planning cycle time (days from kickoff to approved plan)",
            "Forecast accuracy (MAPE — Mean Absolute Percentage Error)",
            "% of plan submitted on time by cost centre/entity",
            "Number of data action executions per cycle",
            "Driver coverage ratio (% of costs allocated via drivers vs manual entry)",
        ],
        "sap_objects": [
            "SAC Planning Model (Account-based or Generic)",
            "SAC Data Action",
            "SAC Multi-Action",
            "SAC Allocation Process",
            "SAC Version (public / private)",
            "Value Driver Tree",
            "Planning Table / Input Template",
            "Data Lock (version / time slice)",
        ],
        "common_patterns": [
            "Top-down budget distribution using data actions with breakback logic",
            "Rolling forecast: 12-month forward view updated monthly with auto-copy from actuals",
            "Driver-based planning: headcount → salary cost, volume → revenue, via value driver trees",
            "Scenario planning: Base/Upside/Downside private versions compared against the public budget version",
            "Integrated planning write-back to S/4HANA operational systems via APIs",
            "Allocation process distributing shared service costs to receiving cost centres using driver quantities",
        ],
    }
