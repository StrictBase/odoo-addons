from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    strictbase_invoice_sequence_enabled = fields.Boolean(
        string="Use StrictBase Invoice Sequence",
        help="Use the StrictBase YYYYMM-XXX yearly-reset numbering for customer invoices and credit notes.",
    )
    strictbase_invoice_sequence_start = fields.Integer(
        string="StrictBase Sequence Start",
        default=1,
        help="Starting number to use for the first customer invoice or credit note of each year.",
    )
