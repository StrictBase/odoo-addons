from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _strictbase_fixed_price_project_lines(self):
        self.ensure_one()
        return self.order_id.order_line.filtered(
            lambda line: line.is_service
            and line.product_id.service_tracking in ["project_only", "task_in_project"]
            and line.product_id.project_template_id == self.product_id.project_template_id
        )

    def _strictbase_should_clear_project_allocated_hours(self):
        self.ensure_one()
        if self.product_id.project_template_id.allocated_hours:
            return False

        uom_unit = self.env.ref("uom.product_uom_unit")
        project_lines = self._strictbase_fixed_price_project_lines()
        return bool(project_lines) and all(
            line.product_id.service_policy == "ordered_prepaid"
            and line.product_uom_id == uom_unit
            for line in project_lines
        )

    def _timesheet_create_project(self):
        project = super()._timesheet_create_project()
        if self._strictbase_should_clear_project_allocated_hours():
            project.allocated_hours = 0.0
        return project

