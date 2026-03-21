from odoo.tests.common import TransactionCase


class TestCrmLeadContactNames(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Contact = cls.env["res.partner"]
        cls.Lead = cls.env["crm.lead"]

    def _new_opportunity(self):
        return self.Lead.new(
            {
                "name": "Test Opportunity",
                "type": "opportunity",
                "is_company": False,
            }
        )

    def test_partner_id_onchange_populates_split_names(self):
        partner = self.Contact.create(
            {
                "is_company": False,
                "name": "Ada Lovelace",
                "firstname": "Ada",
                "lastname": "Lovelace",
            }
        )
        lead = self._new_opportunity()

        lead.partner_id = partner
        lead._onchange_partner_id_contact_names()

        self.assertEqual(lead.contact_firstname, "Ada")
        self.assertEqual(lead.contact_lastname, "Lovelace")

    def test_partner_id_onchange_falls_back_to_name_split(self):
        partner = self.Contact.create(
            {
                "is_company": False,
                "name": "Madonna",
                "firstname": False,
                "lastname": False,
            }
        )
        lead = self._new_opportunity()

        lead.partner_id = partner
        lead._onchange_partner_id_contact_names()

        self.assertEqual(lead.contact_firstname, "Madonna")
        self.assertFalse(lead.contact_lastname)

    def test_contact_id_onchange_syncs_partner_and_names(self):
        partner = self.Contact.create(
            {
                "is_company": False,
                "name": "Grace Hopper",
                "firstname": "Grace",
                "lastname": "Hopper",
            }
        )
        lead = self._new_opportunity()

        lead.contact_id = partner
        lead._onchange_contact_id_partner()

        self.assertEqual(lead.partner_id, partner)
        self.assertEqual(lead.contact_firstname, "Grace")
        self.assertEqual(lead.contact_lastname, "Hopper")

    def test_partner_id_onchange_company_clears_split_names(self):
        company = self.Contact.create(
            {
                "is_company": True,
                "name": "Acme BV",
            }
        )
        lead = self._new_opportunity()
        lead.contact_firstname = "Temp"
        lead.contact_lastname = "Value"

        lead.partner_id = company
        lead._onchange_partner_id_contact_names()

        self.assertFalse(lead.contact_firstname)
        self.assertFalse(lead.contact_lastname)

    def test_action_create_contact_person_creates_and_links_contact(self):
        company = self.Contact.create(
            {
                "is_company": True,
                "name": "Acme BV",
            }
        )
        lead = self.Lead.create(
            {
                "name": "Opportunity",
                "type": "opportunity",
                "partner_id": company.id,
                "contact_firstname": "Ada",
                "contact_lastname": "Lovelace",
            }
        )

        lead.action_create_contact_person()

        self.assertEqual(lead.partner_id.parent_id, company)
        self.assertEqual(lead.partner_id.firstname, "Ada")
        self.assertEqual(lead.partner_id.lastname, "Lovelace")
        self.assertEqual(lead.partner_id.name, "Ada Lovelace")
        self.assertEqual(lead.contact_id, lead.partner_id)
        self.assertFalse(lead.contact_firstname)
        self.assertFalse(lead.contact_lastname)

    def test_partner_name_sync_and_name_search(self):
        partner = self.Contact.create(
            {
                "is_company": False,
                "firstname": "Grace",
                "lastname": "Hopper",
            }
        )

        self.assertEqual(partner.name, "Grace Hopper")

        partner.write({"firstname": "Amazing"})

        self.assertEqual(partner.name, "Amazing Hopper")
        self.assertIn(partner.id, [partner_id for partner_id, _display_name in self.Contact.name_search("Amazing")])
