from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    strictbase_invoice_background_image = fields.Binary(
        string="StrictBase Invoice Background",
        attachment=True,
    )
    strictbase_invoice_background_filename = fields.Char(
        string="StrictBase Invoice Background Filename",
    )
