"""Default TSD section structure — used when no template .docx is uploaded."""

TSD_DEFAULT_SECTIONS: list = [
    {
        "number": "1",
        "title": "Document Control",
        "description": "Version, author, approvers, and change history table",
        "format": "table",
    },
    {
        "number": "2",
        "title": "Technical Architecture Overview",
        "description": (
            "Component diagram, deployment model, technology stack, and system landscape"
        ),
        "format": "diagram+table",
    },
    {
        "number": "3",
        "title": "Data Modelling",
        "description": (
            "Entity-relationship concepts, InfoObject/dimension design, "
            "fact and dimension table specifications"
        ),
        "format": "table",
    },
    {
        "number": "4",
        "title": "ETL / Data Flow Design",
        "description": (
            "Source-to-target field mapping, transformation logic, "
            "delta/full load strategy, and error handling"
        ),
        "format": "table",
    },
    {
        "number": "5",
        "title": "Reporting / Query Objects",
        "description": (
            "Query/story design specs: key figures, characteristics, "
            "calculated measures, variables, and filters"
        ),
        "format": "table",
    },
    {
        "number": "6",
        "title": "Planning Model Design",
        "description": (
            "Aggregation levels, planning functions, sequences, data slices, "
            "and version management (omit if not in scope)"
        ),
        "format": "prose+table",
    },
    {
        "number": "7",
        "title": "SAP Object Inventory",
        "description": (
            "Complete list of all objects to be created or modified: InfoObjects, "
            "Transformations, DTPs, Queries, Models, CDS views, etc."
        ),
        "format": "table",
    },
    {
        "number": "8",
        "title": "ABAP / Custom Development Requirements",
        "description": (
            "ABAP enhancements, function modules, BAdI implementations, "
            "or custom data exits required"
        ),
        "format": "table+code",
    },
    {
        "number": "9",
        "title": "Performance Considerations",
        "description": (
            "Partitioning, aggregates, indexing, caching strategy, "
            "and expected data volumes"
        ),
        "format": "table",
    },
    {
        "number": "10",
        "title": "Security and Authorisation – Technical",
        "description": (
            "Analysis authorisations, role objects, BW authorisation variables, "
            "and team-based access controls"
        ),
        "format": "table",
    },
    {
        "number": "11",
        "title": "Interface and Integration – Technical",
        "description": (
            "API endpoints, RFC/BAPI calls, flat-file specs, and ODP/CDS extraction details"
        ),
        "format": "table",
    },
    {
        "number": "12",
        "title": "Technical Acceptance Criteria",
        "description": (
            "Technical test scenarios per object, covering unit and integration test cases"
        ),
        "format": "table",
    },
    {
        "number": "13",
        "title": "Naming Conventions",
        "description": "Object naming standards for all SAP artefacts in scope",
        "format": "table",
    },
    {
        "number": "14",
        "title": "Technical Assumptions and Constraints",
        "description": (
            "Environment assumptions, version assumptions, and performance constraints"
        ),
        "format": "table",
    },
]
