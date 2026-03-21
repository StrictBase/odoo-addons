{
    "name": "StrictBase: Invoice Template",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "summary": "Branded StrictBase invoice PDF and yearly YYYYMM-XXX numbering for customer invoices",
    "author": "StrictBase",
    "depends": ["account", "sale"],
    "data": [
        "data/report_paperformat.xml",
        "data/report_action.xml",
        "report/strictbase_invoice_templates.xml",
        "views/account_journal_views.xml",
        "views/account_move_views.xml",
        "views/res_config_settings_views.xml",
        "views/sale_order_views.xml",
    ],
    "installable": True,
    "license": "LGPL-3",
}
