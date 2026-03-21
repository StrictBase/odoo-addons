from odoo import fields, models


class ProjectCollaborator(models.Model):
    _inherit = "project.collaborator"

    readonly_full_access = fields.Boolean(
        string="Read-Only Full Access",
        default=False,
        help="Allow this portal collaborator to read all project tasks without enabling any task edits.",
        export_string_translation=False,
    )
