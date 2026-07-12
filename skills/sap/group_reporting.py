"""SAP Group Reporting — legal and management consolidation knowledge."""


def get_knowledge() -> dict:
    """Return structured knowledge for SAP Group Reporting."""
    return {
        "summary": (
            "SAP Group Reporting is SAP's legal and management consolidation solution on "
            "S/4HANA. It uses the Universal Journal (ACDOCA) as its single source of truth and "
            "runs consolidation through a task-based Consolidation Monitor covering data "
            "collection, validation, intercompany elimination, and currency translation."
        ),
        "key_concepts": [
            "Universal Journal (ACDOCA): single source of truth feeding Group Reporting without a separate reconciliation ledger",
            "Consolidation Monitor: task-based workflow orchestrating data collection, validation, and consolidation steps",
            "Data Collection Tasks: local entity submission of trial balance / reported financial data",
            "Validation Rules: automated checks on submitted data before it enters the consolidation run",
            "Matrix Consolidation: consolidation across multiple views (e.g. legal vs management) from one data set",
            "Currency Translation: spot rate, average rate, and historical rate types applied by account type",
            "Intercompany (IC) Elimination: automated IC matching and elimination by account and trading partner",
            "Consolidation of Investments: equity pickup, goodwill calculation, and minority interest determination",
            "Reclassification Rules: automated reclassification of reported items to the group chart of accounts",
            "Flexible Upload: structured template for non-SAP subsidiaries to submit data into Group Reporting",
        ],
        "kpis": [
            "Consolidation close time (days to complete statutory close)",
            "Number of manual consolidation adjustment journal entries",
            "Intercompany difference amount (IC matching quality)",
            "Validation rule pass rate (%)",
            "Data collection completeness (% of entities submitted on time)",
        ],
        "sap_objects": [
            "Consolidation Unit",
            "Consolidation Group / Hierarchy",
            "Financial Statement (FS) Item",
            "Data Collection Task",
            "Validation Rule",
            "Elimination Rule / Reclassification Rule",
            "Currency Translation Method",
        ],
        "common_patterns": [
            "Monthly/quarterly consolidation cycle: local data collection → validation → IC elimination → currency translation → consolidated group P&L/Balance Sheet",
            "Matrix consolidation producing both legal and management consolidation views from a single data collection",
            "Flexible upload template feeding Group Reporting from non-SAP subsidiary ERPs",
            "Automated IC matching by account, trading partner, and transaction currency ahead of the consolidation run",
            "Equity pickup and goodwill calculation on acquisition, reviewed each period for impairment triggers",
        ],
    }
