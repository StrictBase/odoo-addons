from odoo import Command
from odoo.addons.sale_project.tests.common import TestSaleProjectCommon
from odoo.tests import tagged


@tagged("-at_install", "post_install")
class TestFixedPriceProject(TestSaleProjectCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")

    def test_fixed_price_units_project_has_no_allocated_hours(self):
        product = self.env["product.product"].create({
            "name": "Fixed Price Project",
            "standard_price": 10,
            "list_price": 100,
            "type": "service",
            "invoice_policy": "order",
            "uom_id": self.uom_unit.id,
            "service_tracking": "project_only",
            "property_account_income_id": self.account_sale.id,
            "taxes_id": False,
        })
        sale_order = self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "order_line": [
                Command.create({
                    "product_id": product.id,
                    "product_uom_qty": 1,
                }),
            ],
        })

        sale_order.action_confirm()

        self.assertEqual(len(sale_order.project_ids), 1)
        self.assertEqual(sale_order.project_ids.allocated_hours, 0.0)

    def test_fixed_price_units_project_template_keeps_explicit_hours(self):
        template = self.env["project.project"].create({
            "name": "Fixed Price Template",
            "is_template": True,
            "allocated_hours": 6.0,
        })
        product = self.env["product.product"].create({
            "name": "Fixed Price Project With Template",
            "standard_price": 10,
            "list_price": 100,
            "type": "service",
            "invoice_policy": "order",
            "uom_id": self.uom_unit.id,
            "service_tracking": "project_only",
            "project_template_id": template.id,
            "property_account_income_id": self.account_sale.id,
            "taxes_id": False,
        })
        sale_order = self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "order_line": [
                Command.create({
                    "product_id": product.id,
                    "product_uom_qty": 1,
                }),
            ],
        })

        sale_order.action_confirm()

        self.assertEqual(len(sale_order.project_ids), 1)
        self.assertEqual(sale_order.project_ids.allocated_hours, 6.0)

