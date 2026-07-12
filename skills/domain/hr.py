"""HR, workforce planning, and payroll domain knowledge."""


def get_knowledge() -> dict:
    """Return structured knowledge for the HR and workforce functional domain."""
    return {
        "summary": (
            "The HR domain covers workforce planning, headcount budgeting, and payroll "
            "reconciliation. Key personas include the CHRO, HR Business Partners, and "
            "Compensation & Benefits teams. SAP solutions in this domain include SuccessFactors "
            "Employee Central, S/4HANA HCM, and SAC Planning for workforce cost planning."
        ),
        "key_concepts": [
            "Headcount Planning: budgeted vs actual FTE by department, cost centre, and job family",
            "FTE (Full-Time Equivalent): normalises part-time and contract roles into full-time units",
            "Attrition: voluntary and involuntary turnover, typically measured as a rolling 12-month rate",
            "Cost per Hire: total recruiting cost divided by number of hires in a period",
            "Time to Fill: elapsed days between requisition opening and offer acceptance",
            "Payroll Reconciliation: matching payroll run output to GL postings and budgeted staff cost",
            "On-Cost Factor: employer costs beyond base salary (social security, benefits, pension) applied as a percentage uplift",
            "Position Management: budgeted positions vs filled/vacant positions by org unit",
            "Compensation Planning: merit increases, bonus pools, and pay equity analysis by band/grade",
            "Organisational Hierarchy: reporting lines used for headcount roll-up and authorisation scoping",
        ],
        "kpis": [
            "Headcount (budgeted vs actual)",
            "Attrition rate (voluntary / involuntary, %)",
            "Cost per Hire",
            "Time to Fill (days)",
            "FTE vs Budget variance",
            "Staff cost as % of Revenue",
            "Payroll variance (actual vs budgeted staff cost)",
        ],
        "sap_objects": [
            "Employee Central Position / Job Classification",
            "S/4HANA HCM Personnel Number / Org Unit",
            "Cost Centre (staff cost assignment)",
            "SAC Planning Model — Workforce/People Cost",
            "Position Budget Control object",
        ],
        "common_patterns": [
            "Headcount-driven staff cost planning: FTEs × average salary × on-cost factor by department",
            "Budgeted vs filled position reconciliation feeding recruitment prioritisation",
            "Payroll-to-GL reconciliation: payroll run totals matched to cost centre postings",
            "Attrition-adjusted headcount forecast: opening headcount + planned hires − expected attrition",
        ],
    }
