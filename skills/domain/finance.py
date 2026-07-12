"""Finance, CFO office, FP&A, and consolidation domain knowledge."""


def get_knowledge() -> dict:
    """Return structured knowledge for the finance and CFO-office functional domain."""
    return {
        "summary": (
            "The finance domain covers financial reporting, financial planning & analysis (FP&A), "
            "group consolidation, and statutory reporting. Key personas include the CFO, FP&A team, "
            "Group Controller, and Treasury. SAP solutions in this domain include S/4HANA Finance, "
            "SAP Group Reporting, SAC Planning (sFIN), and SAP BPC."
        ),
        "key_concepts": [
            "P&L (Profit & Loss Statement): Revenue → Gross Profit → EBITDA → EBIT → Net Income",
            "Balance Sheet: Assets (Current/Non-Current) vs Liabilities + Equity at a point in time",
            "Cash Flow Statement: Operating, Investing, Financing activities — direct and indirect method",
            "EBITDA: Earnings Before Interest, Tax, Depreciation, and Amortisation — primary operational profitability metric",
            "Working Capital: Current Assets minus Current Liabilities; measures short-term liquidity",
            "DSO (Days Sales Outstanding): Accounts Receivable ÷ (Revenue / Days) — debtor collection efficiency",
            "DPO (Days Payable Outstanding): Accounts Payable ÷ (COGS / Days) — creditor payment management",
            "Inventory Turns: COGS ÷ Average Inventory — stock efficiency",
            "Annual Operating Plan (AOP): formal budget approved before fiscal year start",
            "Rolling Forecast: continuously updated forward-looking plan (e.g. R12 — 12 months rolling)",
            "Zero-Based Budgeting (ZBB): every line item justified from zero rather than prior year baseline",
            "Driver-Based Planning: plan built from operational drivers (headcount, volume, rate) rather than line-item tweaks",
            "Scenario Planning: Base / Upside / Downside versions reflecting different macro assumptions",
            "Variance Analysis: Budget vs Actual, Prior Year vs Current Year, with volume/price/mix decomposition",
            "IFRS 16: lease accounting standard requiring operating leases on Balance Sheet as right-of-use assets",
            "Group Consolidation: combining subsidiary financial statements with IC eliminations into group accounts",
            "Intercompany (IC) Elimination: removing intragroup transactions (revenue/cost, payables/receivables, loans)",
            "Currency Translation: translating local entity financials to group reporting currency (closing rate, average rate, historical rate)",
            "Minority Interest (Non-Controlling Interest): share of subsidiary equity not owned by the parent",
            "Transfer Pricing: arm's-length pricing of intragroup transactions for tax compliance",
        ],
        "kpis": [
            "EBITDA margin (%)",
            "Net Income margin (%)",
            "Return on Equity (ROE)",
            "Return on Assets (ROA)",
            "Return on Invested Capital (ROIC)",
            "DSO (Days Sales Outstanding)",
            "DPO (Days Payable Outstanding)",
            "DIO (Days Inventory Outstanding)",
            "Cash Conversion Cycle (DIO + DSO - DPO)",
            "Debt-to-Equity ratio",
            "Interest Coverage ratio (EBIT / Interest Expense)",
            "Free Cash Flow (FCF)",
            "Budget vs Actual variance (absolute and %)",
            "Forecast accuracy (MAPE %)",
            "Cost of Goods Sold (COGS) as % of Revenue",
            "SG&A as % of Revenue",
            "Effective Tax Rate",
        ],
        "sap_objects": [
            "General Ledger Account (S/4HANA Chart of Accounts)",
            "Profit Centre / Cost Centre",
            "Controlling Area",
            "Company Code",
            "Financial Statement Version (FSV)",
            "Universal Journal (ACDOCA table in S/4HANA)",
            "SAP Group Reporting Consolidation Unit",
            "SAP Group Reporting Financial Statement Items (FS Items)",
            "SAC Planning Model (Account-based, sFIN content)",
            "BPC Model (Legal Consolidation or Planning type)",
            "BPC Application Set",
        ],
        "common_patterns": [
            "Actual vs Budget vs Forecast three-way comparison reports with variance drill-down",
            "Rolling 12-month P&L with month-by-month actuals and remaining months forecast",
            "Legal entity consolidation: local GAAP → group GAAP adjustments → IC eliminations → group P&L",
            "FX sensitivity analysis: re-stating prior year results at current year exchange rates (constant currency)",
            "Cost centre hierarchy reporting: company → business unit → cost centre → line item",
            "Cash flow bridge: EBITDA → working capital movement → capex → financing → net cash position",
            "Balance sheet walk: opening balance → movements by transaction type → closing balance",
            "Headcount-driven staff cost planning: FTEs × average salary × on-cost factor by department",
        ],
    }
