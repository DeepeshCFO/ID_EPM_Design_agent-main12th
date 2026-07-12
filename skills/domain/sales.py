"""Sales, revenue, and commercial performance domain knowledge."""


def get_knowledge() -> dict:
    """Return structured knowledge for the sales and revenue functional domain."""
    return {
        "summary": (
            "The sales domain covers revenue management, commercial performance, sales pipeline "
            "analytics, and customer profitability. Key personas include the Chief Revenue Officer (CRO), "
            "VP Sales, Sales Operations, and FP&A. SAP solutions include SAC Analytics, SAP SD "
            "reporting, and CRM analytics."
        ),
        "key_concepts": [
            "Revenue recognition: point-in-time vs over-time recognition (IFRS 15 / ASC 606)",
            "Gross Revenue vs Net Revenue: Net = Gross minus rebates, returns, allowances",
            "Gross Margin: Net Revenue minus Cost of Goods Sold — primary product profitability metric",
            "Contribution Margin: Revenue minus variable costs — measures product line profitability before fixed cost allocation",
            "Sales pipeline: opportunities by stage (Suspect → Prospect → Qualified → Proposal → Negotiation → Won/Lost)",
            "Pipeline coverage ratio: total pipeline value ÷ target — healthy pipeline = 3–4× quota",
            "Win Rate: won deals ÷ total qualified deals — sales effectiveness metric",
            "Average Deal Size / Average Selling Price (ASP)",
            "Sales cycle length: average days from opportunity creation to close",
            "Net Revenue Retention (NRR): measures revenue growth/churn within existing customer base",
            "Gross Revenue Retention (GRR): measures churn excluding upsell/cross-sell",
            "Customer Acquisition Cost (CAC): total sales & marketing spend ÷ new customers acquired",
            "Customer Lifetime Value (CLV/LTV): predicted total revenue from a customer relationship",
            "LTV:CAC ratio: benchmark for sales investment efficiency (healthy ≥ 3:1)",
            "Churn Rate: % of customers or ARR lost in a period",
            "Revenue by dimension: product line, geography, channel, customer segment, salesperson",
            "Rebate accruals: volume-based and performance-based rebates accrued monthly against sales",
        ],
        "kpis": [
            "Total Revenue (by product, region, channel, period)",
            "Revenue Growth rate (YoY, QoQ)",
            "Gross Margin % (by product, region, customer)",
            "Net Revenue Retention (NRR %)",
            "Gross Revenue Retention (GRR %)",
            "Win Rate (%)",
            "Pipeline Coverage Ratio",
            "Average Deal Size",
            "Sales Cycle Length (days)",
            "Customer Acquisition Cost (CAC)",
            "Customer Lifetime Value (CLV)",
            "LTV:CAC Ratio",
            "Churn Rate (%)",
            "Quota Attainment (% of reps at/above quota)",
            "Revenue per Sales Rep",
            "Order Intake vs Revenue (bookings-to-billings ratio)",
        ],
        "sap_objects": [
            "SD Sales Order",
            "SD Billing Document",
            "SD Condition Types (pricing, rebates, surcharges)",
            "Customer Master (BP — Business Partner in S/4HANA)",
            "Material Master (SD views)",
            "Revenue Account Determination (VKOA)",
            "SAP BW DataSource 2LIS_13_VDITM (SD billing items)",
            "SAP BW DataSource 2LIS_11_VAHDR / 2LIS_11_VAITM (sales orders)",
            "SAC Revenue story / planning model",
            "BEx Query for revenue analysis",
        ],
        "common_patterns": [
            "Revenue waterfall: Gross Revenue → Rebates → Net Revenue → COGS → Gross Margin → SG&A → EBIT",
            "Pipeline funnel report: opportunities by stage with conversion rates between stages",
            "Actuals vs forecast vs prior year revenue by month with variance commentary fields",
            "Customer profitability: net revenue minus directly attributable costs by customer / customer segment",
            "Geographic revenue heat map: revenue and growth by country/region for management review",
            "Rebate management: accrual tracking by customer agreement with actual vs accrued reconciliation",
            "Sales rep performance scorecard: quota, actuals, attainment %, pipeline, win rate by rep",
            "Product mix analysis: revenue and margin contribution by product family with trend",
        ],
    }
