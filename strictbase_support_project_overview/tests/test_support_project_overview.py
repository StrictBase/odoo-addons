from odoo import Command
from odoo.tests import tagged

from odoo.addons.sale_timesheet.tests.common import TestCommonSaleTimesheet


@tagged("-at_install", "post_install")
class TestSupportProjectOverview(TestCommonSaleTimesheet):
    def setUp(self):
        super().setUp()
        self.support_tag = self.env["project.tags"].create({"name": "Support Tickets"})

    def test_support_balance_fields_follow_active_sale_line(self):
        project = self.project_task_rate
        old_sol = project.sale_line_id
        new_sol = self.so.order_line.filtered(lambda line: line != old_sol)[:1]
        project.tag_ids = [Command.link(self.support_tag.id)]

        self.assertTrue(project.is_support_ticket_project)
        self.assertEqual(project.support_hours_ordered, old_sol.product_uom_qty)
        self.assertEqual(project.support_hours_delivered, old_sol.qty_delivered)
        self.assertEqual(project.support_remaining_hours, old_sol.remaining_hours)

        project.write({"sale_line_id": new_sol.id})

        self.assertEqual(project.support_hours_ordered, new_sol.product_uom_qty)
        self.assertEqual(project.support_hours_delivered, new_sol.qty_delivered)
        self.assertEqual(project.support_remaining_hours, new_sol.remaining_hours)

    def test_support_project_domain_excludes_templates_and_unrelated_projects(self):
        support_project = self.project_task_rate
        support_project.tag_ids = [Command.link(self.support_tag.id)]

        unrelated_project = self.env["project.project"].create({
            "name": "Support with migrating Totara",
            "partner_id": self.partner_a.id,
        })

        template_project = self.env["project.project"].create({
            "name": "_Template_Client_Support",
            "is_template": True,
            "tag_ids": [Command.link(self.support_tag.id)],
        })

        matching_projects = self.env["project.project"].search([
            ("is_support_ticket_project", "=", True),
        ])

        self.assertIn(support_project, matching_projects)
        self.assertNotIn(unrelated_project, matching_projects)
        self.assertNotIn(template_project, matching_projects)
