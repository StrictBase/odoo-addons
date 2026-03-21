from odoo import fields, models


class ProjectShareCollaboratorWizard(models.TransientModel):
    _inherit = "project.share.collaborator.wizard"

    access_mode = fields.Selection(
        selection_add=[("read_all", "Read-only (all tasks)")],
        ondelete={"read_all": "set default"},
    )
