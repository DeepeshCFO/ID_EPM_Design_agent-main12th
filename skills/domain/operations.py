"""Manufacturing, operations, and production performance domain knowledge."""


def get_knowledge() -> dict:
    """Return structured knowledge for the manufacturing and operations functional domain."""
    return {
        "summary": (
            "The operations domain covers manufacturing performance, production efficiency, "
            "quality management, and capacity planning. Key personas include the VP Operations, "
            "Plant Manager, Production Planner, and Quality Manager. SAP solutions include "
            "SAP PP/QM reporting on BW/4HANA and SAC operational dashboards."
        ),
        "key_concepts": [
            "OEE (Overall Equipment Effectiveness): Availability × Performance × Quality — master manufacturing KPI",
            "Availability: actual run time ÷ planned run time — measures unplanned downtime",
            "Performance: actual output rate ÷ ideal output rate — measures speed losses",
            "Quality Rate: good units ÷ total units produced — measures defect losses",
            "World-class OEE benchmark: ≥ 85% (Availability 90%, Performance 95%, Quality 99%)",
            "Yield: good output ÷ total input material — first-pass yield and final yield distinction",
            "Scrap Rate: defective/scrapped units ÷ total units — inverse of quality rate",
            "Rework Rate: units requiring rework ÷ total units — quality process efficiency",
            "Throughput: units produced per unit time (hour, shift, day)",
            "Cycle Time: time to complete one unit from start to finish",
            "Takt Time: available production time ÷ customer demand rate — target cycle time",
            "Capacity Utilisation: actual hours used ÷ available capacity hours × 100%",
            "Production Order Variance: actual cost of production order vs standard (planned) cost",
            "Material consumption variance: actual material usage vs standard BOM quantity",
            "Labour efficiency variance: actual hours vs standard hours at standard rate",
            "Work Centre: SAP PP object representing a production resource (machine, workcell, operator group)",
            "Routing: sequence of operations (work centres + standard times) for manufacturing a product",
            "Bill of Materials (BOM): hierarchical list of components required to produce a finished good",
        ],
        "kpis": [
            "OEE (%) — Overall Equipment Effectiveness",
            "Availability (%)",
            "Performance (%)",
            "Quality Rate (%)",
            "Yield / First Pass Yield (%)",
            "Scrap Rate (%)",
            "Rework Rate (%)",
            "Throughput (units/hour or units/shift)",
            "Capacity Utilisation (%)",
            "Production Order Variance (absolute and %)",
            "Material Consumption Variance",
            "Labour Efficiency Variance",
            "Mean Time Between Failures (MTBF) — hours",
            "Mean Time To Repair (MTTR) — hours",
            "Schedule Adherence (% of orders completed on-time)",
            "Defects Per Million Opportunities (DPMO)",
        ],
        "sap_objects": [
            "Production Order (PP)",
            "Process Order (PP-PI for process industries)",
            "Work Centre (CR01/CR02)",
            "Routing (CA01/CA02)",
            "Bill of Materials (CS01/CS02)",
            "Confirmation (CO11N — time and quantity confirmation)",
            "Goods Issue to Production Order (MIGO 261)",
            "Goods Receipt from Production Order (MIGO 101)",
            "Quality Inspection Lot (QM)",
            "Usage Decision (QA11)",
            "Plant Maintenance Order (PM)",
            "Functional Location / Equipment Master (PM)",
            "BW DataSource 2LIS_04_P_ARBPL (production — work centre)",
            "BW DataSource 2LIS_04_PBORD (production orders)",
            "SAC Operations story / OEE dashboard model",
        ],
        "common_patterns": [
            "OEE waterfall: planned time → availability losses → performance losses → quality losses → OEE %",
            "Shift-level production dashboard: target vs actual output, scrap, OEE by shift and work centre",
            "Production order variance analysis: drill from total variance to material/labour/overhead components",
            "Downtime Pareto chart: top causes of unplanned downtime by machine/line with cumulative % line",
            "Quality defect analysis: defect codes by product/line/shift with Pareto ranking and trend",
            "Capacity loading report: work centre capacity (hours) vs demand load by week/period with overload highlighting",
            "BOM actual vs standard consumption: component usage variance by production order for material efficiency analysis",
            "Plant benchmarking: OEE, yield, and scrap rate by plant with ranking and gap-to-best visibility",
        ],
    }
