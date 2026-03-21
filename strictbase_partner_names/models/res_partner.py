from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    firstname = fields.Char("First Name", index=True)
    lastname = fields.Char("Last Name", index=True)

    @api.model
    def _build_person_name(self, firstname=False, lastname=False):
        firstname = (firstname or "").strip()
        lastname = (lastname or "").strip()
        return " ".join(part for part in (firstname, lastname) if part)

    @api.onchange("firstname", "lastname", "is_company")
    def _onchange_name_from_split_fields(self):
        for partner in self:
            if partner.is_company:
                continue
            derived_name = partner._build_person_name(partner.firstname, partner.lastname)
            if derived_name:
                partner.name = derived_name

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("is_company"):
                continue
            if vals.get("name"):
                continue
            derived_name = self._build_person_name(vals.get("firstname"), vals.get("lastname"))
            if derived_name:
                vals["name"] = derived_name
        return super().create(vals_list)

    def write(self, vals):
        if "name" in vals or not any(field in vals for field in ("firstname", "lastname", "is_company")):
            return super().write(vals)

        partners_with_synced_name = self.filtered(
            lambda partner: not vals.get("is_company", partner.is_company)
        )
        remaining_partners = self - partners_with_synced_name

        result = True
        for partner in partners_with_synced_name:
            partner_vals = dict(vals)
            derived_name = self._build_person_name(
                partner_vals.get("firstname", partner.firstname),
                partner_vals.get("lastname", partner.lastname),
            )
            if derived_name:
                partner_vals["name"] = derived_name
            result = super(ResPartner, partner).write(partner_vals) and result

        if remaining_partners:
            result = super(ResPartner, remaining_partners).write(vals) and result

        return result

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        args = args or []
        if name:
            domain = [
                "|",
                "|",
                ("name", operator, name),
                ("firstname", operator, name),
                ("lastname", operator, name),
            ]
            return [(partner.id, partner.display_name) for partner in self.search(domain + args, limit=limit)]
        return super().name_search(name=name, args=args, operator=operator, limit=limit)
