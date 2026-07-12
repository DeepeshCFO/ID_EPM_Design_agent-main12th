"""Default FSD section structure — used when no template .docx is uploaded."""

FSD_DEFAULT_SECTIONS: list = [
    {
        "number": "1",
        "title": "Document Control",
        "description": "Version, author, approvers, and change history table",
        "format": "table",
    },
    {
        "number": "2",
        "title": "Executive Summary",
        "description": "Business context, project goals, and scope in plain language",
        "format": "prose",
    },
    {
        "number": "3",
        "title": "Business Requirements Summary",
        "description": "Structured tabular summary of all requirements extracted from the BRD",
        "format": "table",
    },
    {
        "number": "4",
        "title": "Functional Domain Context",
        "description": "Domain-specific background, relevant KPIs, and business process context",
        "format": "prose",
    },
    {
        "number": "5",
        "title": "Solution Architecture",
        "description": "High-level architecture block diagram, data flow, and integration landscape",
        "format": "diagram+prose",
    },
    {
        "number": "6",
        "title": "Functional Design – Reporting / Analytics",
        "description": "Report catalogue: name, type, source, frequency, key fields, and filters",
        "format": "table",
    },
    {
        "number": "7",
        "title": "Functional Design – Planning",
        "description": (
            "Planning model design: version management, driver-based logic, allocation rules, "
            "and workflow (omit if planning is not in scope)"
        ),
        "format": "prose+table",
    },
    {
        "number": "8",
        "title": "Data Requirements",
        "description": (
            "Data entities, source mappings, master data objects, hierarchies, "
            "and data governance"
        ),
        "format": "table",
    },
    {
        "number": "9",
        "title": "User Roles and Authorisation Concept",
        "description": "Functional role matrix: role name, permissions, and data access scope",
        "format": "table",
    },
    {
        "number": "10",
        "title": "Integration Requirements",
        "description": (
            "Source-to-target integration touchpoints, transformation rules, and frequency"
        ),
        "format": "table",
    },
    {
        "number": "11",
        "title": "Assumptions Register",
        "description": (
            "All assumptions made by the agent where the BRD was silent or questions were skipped"
        ),
        "format": "table",
    },
    {
        "number": "12",
        "title": "Open Questions Register",
        "description": (
            "Unresolved items requiring client clarification, with priority and impact rating"
        ),
        "format": "table",
    },
    {
        "number": "13",
        "title": "Functional Acceptance Criteria",
        "description": (
            "Testable acceptance criteria per requirement, usable as input for test script creation"
        ),
        "format": "table",
    },
    {
        "number": "14",
        "title": "Glossary",
        "description": "Domain and SAP-specific terms used in the document",
        "format": "table",
    },
]
