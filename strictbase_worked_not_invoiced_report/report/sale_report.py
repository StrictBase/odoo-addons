from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    product_type = fields.Selection(
        selection=[
            ("consu", "Goods"),
            ("service", "Service"),
            ("combo", "Combo"),
        ],
        string="Product Type",
        readonly=True,
    )

    def _select_additional_fields(self):
        fields_map = super()._select_additional_fields()
        fields_map["product_type"] = "t.type"
        return fields_map

    def _group_by_sale(self):
        return f"{super()._group_by_sale()}, t.type"
