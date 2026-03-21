from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    support_hours_ordered = fields.Float(
        string="Support Hours Ordered",
        related="sale_line_id.product_uom_qty",
        store=True,
        readonly=True,
    )
    support_hours_delivered = fields.Float(
        string="Support Hours Delivered",
        related="sale_line_id.qty_delivered",
        store=True,
        readonly=True,
    )
    support_remaining_hours = fields.Float(
        string="Support Hours Remaining",
        related="sale_line_id.remaining_hours",
        store=True,
        readonly=True,
    )
    is_support_ticket_project = fields.Boolean(
        string="Support Ticket Project",
        compute="_compute_is_support_ticket_project",
        store=True,
        readonly=True,
    )

    @api.depends("tag_ids", "tag_ids.name", "is_template")
    def _compute_is_support_ticket_project(self):
        for project in self:
            project.is_support_ticket_project = (
                not project.is_template
                and "Support Tickets" in project.tag_ids.mapped("name")
            )
