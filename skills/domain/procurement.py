"""Procurement, spend analytics, and supply chain domain knowledge."""


def get_knowledge() -> dict:
    """Return structured knowledge for the procurement and supply chain functional domain."""
    return {
        "summary": (
            "The procurement domain covers spend analytics, supplier performance, purchase price "
            "variance (PPV), inventory management, and demand planning. Key personas include the "
            "Chief Procurement Officer (CPO), Category Managers, Supply Chain Analysts, and "
            "Finance. SAP solutions include SAP MM/Ariba reporting, BW spend analytics, and "
            "SAC for supply chain."
        ),
        "key_concepts": [
            "Spend Analytics: categorised analysis of purchase spend by supplier, category, cost centre, and period",
            "Spend cube: multi-dimensional spend data with category hierarchy, supplier hierarchy, org unit hierarchy",
            "Purchase Price Variance (PPV): actual purchase price minus standard price × quantity — budget impact metric",
            "Price variance: difference between actual invoice price and purchase order price (invoice verification)",
            "Supplier Scorecard: structured performance evaluation across quality, delivery, price, and service dimensions",
            "OTIF (On-Time In-Full): % of deliveries received on the agreed date and in full quantity",
            "Maverick spend: purchase spend outside contracted suppliers or approved channels",
            "Contract compliance rate: % of spend against negotiated contracts vs off-contract",
            "Demand Planning: forecasting future material requirements based on historical consumption and demand signals",
            "MRP (Material Requirements Planning): S/4HANA process converting demand into planned orders",
            "Inventory turns: COGS ÷ Average Inventory — stock efficiency metric",
            "Weeks of Supply (WoS): Inventory ÷ (Annual COGS ÷ 52) — forward-looking inventory sufficiency",
            "Safety stock: minimum inventory buffer to absorb demand and supply variability",
            "Slow-moving and obsolete inventory (SLOB): items not consumed within a defined threshold period",
            "Three-way match: PO → Goods Receipt → Invoice matching for automated payment approval",
            "Goods Receipt / Invoice Receipt (GR/IR) clearing: reconciliation of received goods vs received invoices",
            "Total Cost of Ownership (TCO): price plus quality, logistics, risk, and relationship costs",
        ],
        "kpis": [
            "Total Spend (by category, supplier, cost centre, period)",
            "Spend under Management (% of total spend through procurement)",
            "Contract Compliance Rate (%)",
            "Maverick Spend Rate (%)",
            "Purchase Price Variance (PPV) — absolute and %",
            "Supplier OTIF (%)",
            "Supplier Quality Rate (% defect-free deliveries)",
            "Inventory Turns",
            "Weeks of Supply (WoS)",
            "Days Inventory Outstanding (DIO)",
            "Slow-Moving & Obsolete Inventory (SLOB) value",
            "GR/IR Clearing Balance (open items value)",
            "Cost Savings achieved vs target",
            "Number of Active Suppliers (rationalisation metric)",
            "PO Cycle Time (requisition to order days)",
        ],
        "sap_objects": [
            "SAP MM Purchase Order (ME21N)",
            "SAP MM Goods Receipt (MIGO)",
            "SAP MM Invoice (MIRO)",
            "Material Master (MM views: MRP, Purchasing, Accounting)",
            "Vendor Master (BP — Business Partner in S/4HANA)",
            "Purchasing Info Record (ME11)",
            "Source List (ME01)",
            "Contract / Scheduling Agreement (ME31K/ME31L)",
            "BW DataSource 2LIS_02_ITM (Purchase Order Items)",
            "BW DataSource 2LIS_02_HDR (Purchase Order Headers)",
            "BW DataSource 2LIS_02_SCL (Scheduling Agreement Schedules)",
            "SAC Procurement story / spend analytic model",
        ],
        "common_patterns": [
            "Spend cube report: spend by L1/L2/L3 category × supplier × cost centre × month with drill-through to PO line",
            "Supplier performance dashboard: OTIF, quality, price compliance, and savings by supplier with trend sparklines",
            "PPV root cause analysis: drill from total PPV to material group → material → supplier → PO line",
            "Inventory aging analysis: stock value buckets by days since last movement (0–30, 31–90, 91–180, 180+)",
            "Demand vs Supply reconciliation: MRP planned demand vs confirmed supply with exception highlighting",
            "Contract utilisation: contracted value vs spend by supplier agreement with expiry date monitoring",
            "GR/IR reconciliation report: open GR/IR items by age, amount, and responsible buyer for clearance",
            "Savings tracking: negotiated savings vs actual realised savings with delivery confirmation workflow",
        ],
    }
