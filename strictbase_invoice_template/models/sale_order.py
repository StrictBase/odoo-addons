from odoo import api, fields, models
from odoo.tools import OrderedSet, is_html_empty


class SaleOrder(models.Model):
    _inherit = "sale.order"

    strictbase_tax_note_preview = fields.Html(
        string="Tax Note Preview",
        compute="_compute_strictbase_tax_note_preview",
    )

    @api.depends("order_line.tax_ids.invoice_legal_notes", "fiscal_position_id.note")
    def _compute_strictbase_tax_note_preview(self):
        for order in self:
            tax_notes = "".join(
                tax.invoice_legal_notes
                for tax in OrderedSet(order.order_line.tax_ids)
                if not is_html_empty(tax.invoice_legal_notes)
            )
            if not is_html_empty(tax_notes):
                order.strictbase_tax_note_preview = tax_notes
            elif not is_html_empty(order.fiscal_position_id.note):
                order.strictbase_tax_note_preview = order.fiscal_position_id.note
            else:
                order.strictbase_tax_note_preview = False

    def _prepare_invoice(self):
        values = super()._prepare_invoice()
        payment_term = self.payment_term_id or self.partner_id.with_company(self.company_id).property_payment_term_id
        if payment_term:
            values["invoice_payment_term_id"] = payment_term.id
        return values
