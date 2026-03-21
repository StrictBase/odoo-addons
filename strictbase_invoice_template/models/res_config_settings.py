from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    strictbase_invoice_background_image = fields.Binary(
        related="company_id.strictbase_invoice_background_image",
        readonly=False,
    )
    strictbase_invoice_background_filename = fields.Char(
        related="company_id.strictbase_invoice_background_filename",
        readonly=False,
    )
