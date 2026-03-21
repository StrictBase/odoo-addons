from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Keep a single source of truth: employee name fields are stored on the linked resource.
    firstname = fields.Char(related='resource_id.firstname', store=True, readonly=False)
    lastname = fields.Char(related='resource_id.lastname', store=True, readonly=False)

    # Ensure employee name stays in sync with the linked resource record.
    name = fields.Char(related='resource_id.name', store=True, readonly=False)
