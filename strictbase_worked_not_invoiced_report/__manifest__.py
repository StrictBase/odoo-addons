{
    "name": "StrictBase: Worked Not Invoiced Report",
    "version": "19.0.1.0.0",
    "category": "Sales/Sales",
    "summary": "Operational sales report for worked service lines that still need invoicing",
    "description": """
Worked Not Invoiced
===================

Adds a dedicated list-first sales report for service lines where work was
delivered and invoicing follow-up is still needed.

The report is based on sale.report and adds:
- a product type field for service scoping
- a dedicated list view and search view
- a Reporting menu entry under Sales
""",
    "author": "StrictBase",
    "depends": ["sale", "sale_timesheet"],
    "data": [
        "report/sale_report_views.xml",
    ],
    "installable": True,
    "license": "LGPL-3",
}
