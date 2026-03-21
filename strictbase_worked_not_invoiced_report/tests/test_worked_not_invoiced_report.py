from odoo.tests import tagged

from odoo.addons.sale_timesheet.tests.common import TestCommonSaleTimesheet


@tagged("-at_install", "post_install")
class TestWorkedNotInvoicedReport(TestCommonSaleTimesheet):
    def test_product_type_field_is_added_to_sale_report(self):
        product_type_field = self.env["sale.report"]._fields["product_type"]

        self.assertEqual(product_type_field.type, "selection")
        self.assertEqual(product_type_field.string, "Product Type")
        self.assertIn(("service", "Service"), product_type_field.selection)

    def test_action_defaults_target_worked_not_invoiced_service_lines(self):
        action = self.env.ref(
            "strictbase_worked_not_invoiced_report.action_sale_worked_not_invoiced"
        )

        self.assertEqual(action.res_model, "sale.report")
        self.assertEqual(action.domain, "[('state', '=', 'sale')]")
        self.assertIn("'search_default_filter_worked': 1", action.context)
        self.assertIn("'search_default_filter_to_invoice_lines': 1", action.context)
        self.assertIn("'search_default_filter_service_lines': 1", action.context)
