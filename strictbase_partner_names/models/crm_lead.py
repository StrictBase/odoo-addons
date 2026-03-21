from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CrmLead(models.Model):
    _inherit = "crm.lead"

    contact_firstname = fields.Char("Contact First Name", index=True)
    contact_lastname = fields.Char("Contact Last Name", index=True)
    is_company = fields.Boolean("Is Company", default=False)

    create_contact_button = fields.Char(store=False)

    contact_id = fields.Many2one("res.partner", string="Contact Person")

    def _prepare_customer_values(self, partner_name, is_company=False, parent_id=False):
        res = super()._prepare_customer_values(partner_name, is_company, parent_id)
        if not is_company:
            res.update(
                {
                    "firstname": self.contact_firstname,
                    "lastname": self.contact_lastname,
                }
            )
        return res

    @api.onchange("contact_firstname", "contact_lastname", "is_company")
    def _onchange_contact_names(self):
        for lead in self:
            if lead.is_company:
                continue
            if lead.contact_firstname or lead.contact_lastname:
                parts = [lead.contact_firstname, lead.contact_lastname]
                lead.contact_name = " ".join(filter(None, parts))

    @api.onchange("partner_id")
    def _onchange_partner_id_contact_names(self):
        for lead in self:
            partner = lead.partner_id
            if not partner:
                lead.contact_id = False
                continue
            if partner.is_company:
                if lead.contact_id.parent_id != partner:
                    lead.contact_id = False
                lead.contact_firstname = False
                lead.contact_lastname = False
                continue
            lead.contact_id = partner
            firstname = (partner.firstname or "").strip()
            lastname = (partner.lastname or "").strip()
            if not firstname and not lastname:
                firstname, lastname = lead._split_contact_name_fallback(partner.name)
            lead.contact_firstname = firstname or False
            lead.contact_lastname = lastname or False

    @api.onchange("contact_id")
    def _onchange_contact_id_partner(self):
        for lead in self:
            if not lead.contact_id:
                continue
            lead.partner_id = lead.contact_id
            firstname = (lead.contact_id.firstname or "").strip()
            lastname = (lead.contact_id.lastname or "").strip()
            if not firstname and not lastname:
                firstname, lastname = lead._split_contact_name_fallback(lead.contact_id.name)
            lead.contact_firstname = firstname or False
            lead.contact_lastname = lastname or False

    @api.model
    def _split_contact_name_fallback(self, name):
        parts = (name or "").split()
        if not parts:
            return False, False
        if len(parts) == 1:
            return parts[0], False
        return " ".join(parts[:-1]), parts[-1]

    company_has_contacts = fields.Boolean(
        compute="_compute_company_has_contacts",
        readonly=True,
    )

    @api.depends("commercial_partner_id")
    def _compute_company_has_contacts(self):
        Partner = self.env["res.partner"]
        for lead in self:
            company = lead.commercial_partner_id
            if not company:
                lead.company_has_contacts = False
                continue

            lead.company_has_contacts = bool(
                Partner.search_count(
                    [
                        ("parent_id", "=", company.id),
                        ("is_company", "=", False),
                        ("active", "=", True),
                    ],
                    limit=1,
                )
            )

    def action_create_contact_person(self):
        self.ensure_one()

        company = self.commercial_partner_id or self.partner_id.commercial_partner_id
        if not company:
            raise UserError(_("Select a company first."))

        firstname = (self.contact_firstname or "").strip()
        lastname = (self.contact_lastname or "").strip()
        if not firstname and not lastname:
            raise UserError(_("Enter a first name or last name."))

        partner = self.env["res.partner"].create(
            {
                "parent_id": company.id,
                "is_company": False,
                "type": "contact",
                "firstname": firstname or False,
                "lastname": lastname or False,
            }
        )

        self.partner_id = partner.id
        self.contact_id = partner.id
        self.contact_firstname = False
        self.contact_lastname = False

        self.company_has_contacts = True

        return True
