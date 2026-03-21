import base64

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.sale.tests.common import SaleCommon
from odoo.fields import Command

@tagged("post_install", "-at_install")
class TestStrictBaseInvoiceSequence(AccountTestInvoicingCommon, SaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sale_journal = cls.company_data["default_journal_sale"]
        cls.sale_journal.strictbase_invoice_sequence_enabled = True
        cls.sale_journal.strictbase_invoice_sequence_start = 1

    @classmethod
    def _create_invoice(cls, invoice_date, move_type="out_invoice"):
        move = cls.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": cls.partner_a.id,
                "invoice_date": invoice_date,
                "date": invoice_date,
                "journal_id": cls.sale_journal.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Service",
                            "quantity": 1,
                            "price_unit": 100,
                        }
                    )
                ],
            }
        )
        move.action_post()
        return move

    def test_yearly_sequence_keeps_running_across_months(self):
        inv_1 = self._create_invoice("2026-03-13")
        inv_2 = self._create_invoice("2026-03-20")
        inv_3 = self._create_invoice("2026-04-01")

        self.assertEqual(inv_1.name, "202603-001")
        self.assertEqual(inv_2.name, "202603-002")
        self.assertEqual(inv_3.name, "202604-003")

    def test_sequence_resets_on_new_year(self):
        inv_1 = self._create_invoice("2026-12-31")
        inv_2 = self._create_invoice("2027-01-01")

        self.assertEqual(inv_1.name, "202612-001")
        self.assertEqual(inv_2.name, "202701-001")

    def test_credit_notes_share_sequence(self):
        inv = self._create_invoice("2026-06-10", move_type="out_invoice")
        credit = self._create_invoice("2026-06-11", move_type="out_refund")

        self.assertEqual(inv.name, "202606-001")
        self.assertEqual(credit.name, "202606-002")

    def test_sequence_respects_configured_start_number(self):
        self.sale_journal.strictbase_invoice_sequence_start = 17

        inv = self._create_invoice("2030-03-13")

        self.assertEqual(inv.name, "203003-017")

    def test_sequence_start_can_skip_forward_after_existing_invoice(self):
        first = self._create_invoice("2026-03-13")
        self.assertEqual(first.name, "202603-001")

        self.sale_journal.strictbase_invoice_sequence_start = 17

        second = self._create_invoice("2026-03-14")

        self.assertEqual(second.name, "202603-017")

    def test_sequence_start_cannot_move_backward_below_last_used_number(self):
        inv_1 = self._create_invoice("2026-03-13")
        inv_2 = self._create_invoice("2026-03-14")
        inv_3 = self._create_invoice("2026-03-15")

        self.assertEqual(inv_1.name, "202603-001")
        self.assertEqual(inv_2.name, "202603-002")
        self.assertEqual(inv_3.name, "202603-003")

        self.sale_journal.strictbase_invoice_sequence_start = 2

        inv_4 = self._create_invoice("2026-03-16")

        self.assertEqual(inv_4.name, "202603-004")

    def test_sequence_ignores_many_non_strictbase_names(self):
        first = self._create_invoice("2026-05-01")
        self.assertEqual(first.name, "202605-001")

        for index in range(60):
            manual_move = self._create_invoice("2026-05-02")
            manual_move.write({"name": f"MANUAL-{index + 1:03d}"})

        next_invoice = self._create_invoice("2026-05-03")

        self.assertEqual(next_invoice.name, "202605-002")

    def test_empty_draft_invoice_uses_payment_term_for_due_date(self):
        self.partner_a.property_payment_term_id = self.env.ref("account.account_payment_term_15days")
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "invoice_date": "2026-03-13",
                "date": "2026-03-13",
                "journal_id": self.sale_journal.id,
            }
        )

        self.assertEqual(invoice.invoice_payment_term_id, self.env.ref("account.account_payment_term_15days"))
        self.assertEqual(str(invoice.invoice_date_due), "2026-03-28")

    def test_onchange_sets_due_date_from_partner_payment_term(self):
        self.partner_a.property_payment_term_id = self.env.ref("account.account_payment_term_15days")
        invoice = self.env["account.move"].new(
            {
                "move_type": "out_invoice",
                "invoice_date": "2026-03-13",
                "date": "2026-03-13",
                "journal_id": self.sale_journal.id,
            }
        )

        invoice.partner_id = self.partner_a
        invoice._onchange_strictbase_partner_payment_term()

        self.assertEqual(invoice.invoice_payment_term_id, self.env.ref("account.account_payment_term_15days"))
        self.assertEqual(str(invoice.invoice_date_due), "2026-03-28")

    def test_report_html_contains_a4_background_template(self):
        invoice = self._create_invoice("2026-03-13")
        report = self.env.ref("strictbase_invoice_template.action_report_strictbase_invoice")
        self.env.company.strictbase_invoice_background_image = base64.b64encode(
            (
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
                b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
                b"\x00\x00\x0cIDAT\x08\x99c\xf8\xff\xff?\x00\x05\xfe"
                b"\x02\xfeA\xdd\x9d\xb3\x00\x00\x00\x00IEND\xaeB`\x82"
            )
        )

        html, report_type = report._render_qweb_html(report.report_name, invoice.ids)
        rendered = html.decode("utf-8") if isinstance(html, bytes) else html

        self.assertEqual(report_type, "html")
        self.assertIn("@page { size: A4; margin: 0; }", rendered)
        self.assertIn("data:image/png;base64,", rendered)
        self.assertIn("Invoice #", rendered)
        self.assertIn(invoice.name, rendered)

    def test_report_hides_internal_sales_order_reference(self):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "invoice_date": "2026-03-13",
                "date": "2026-03-13",
                "journal_id": self.sale_journal.id,
                "ref": "S00019",
                "invoice_origin": "S00019",
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Service",
                            "quantity": 1,
                            "price_unit": 100,
                        }
                    )
                ],
            }
        )
        report = self.env.ref("strictbase_invoice_template.action_report_strictbase_invoice")

        html, report_type = report._render_qweb_html(report.report_name, invoice.ids)
        rendered = html.decode("utf-8") if isinstance(html, bytes) else html

        self.assertEqual(report_type, "html")
        self.assertNotIn("S00019", rendered)

    def test_report_keeps_external_customer_reference(self):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "invoice_date": "2026-03-13",
                "date": "2026-03-13",
                "journal_id": self.sale_journal.id,
                "ref": "PO-7788",
                "invoice_origin": "S00019",
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Service",
                            "quantity": 1,
                            "price_unit": 100,
                        }
                    )
                ],
            }
        )
        report = self.env.ref("strictbase_invoice_template.action_report_strictbase_invoice")

        html, report_type = report._render_qweb_html(report.report_name, invoice.ids)
        rendered = html.decode("utf-8") if isinstance(html, bytes) else html

        self.assertEqual(report_type, "html")
        self.assertIn("PO-7788", rendered)

    def test_report_hides_redundant_english_product_fallback_line(self):
        partner = self.partner_a.copy({"lang": "nl_NL"})
        product = self.env["product.product"].create(
            {
                "name": "Support Hours",
            }
        )
        product.product_tmpl_id.with_context(lang="nl_NL").name = "Support-uren"
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner.id,
                "invoice_date": "2026-03-13",
                "date": "2026-03-13",
                "journal_id": self.sale_journal.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Support-uren\nSupport Hours",
                            "product_id": product.id,
                            "quantity": 1,
                            "price_unit": 100,
                        }
                    )
                ],
            }
        )
        report = self.env.ref("strictbase_invoice_template.action_report_strictbase_invoice")

        html, report_type = report._render_qweb_html(report.report_name, invoice.ids)
        rendered = html.decode("utf-8") if isinstance(html, bytes) else html

        self.assertEqual(report_type, "html")
        self.assertIn("Support-uren", rendered)
        self.assertEqual(rendered.count("Support Hours"), 0)

    def test_sales_order_invoice_falls_back_to_partner_payment_term(self):
        self.partner_a.property_payment_term_id = self.env.ref("account.account_payment_term_15days")
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_a.id,
                "payment_term_id": False,
                "order_line": [
                    Command.create(
                        {
                            "name": "Service",
                            "product_id": self.product_a.id,
                            "product_uom_qty": 1,
                            "price_unit": 100,
                        }
                    )
                ],
            }
        )

        invoice_vals = order._prepare_invoice()

        self.assertEqual(invoice_vals["invoice_payment_term_id"], self.env.ref("account.account_payment_term_15days").id)

    def test_report_prefers_tax_legal_notes_over_fiscal_position_note(self):
        sale_tax = self.env["account.tax"].search([("type_tax_use", "=", "sale")], limit=1)
        sale_tax.invoice_legal_notes = "<p>Reverse charge</p>"
        fiscal_position = self.env["account.fiscal.position"].create({
            "name": "Reverse Charge Test",
            "note": "<p>Reverse charge</p>",
        })
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "invoice_date": "2026-03-13",
                "date": "2026-03-13",
                "journal_id": self.sale_journal.id,
                "fiscal_position_id": fiscal_position.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Service",
                            "quantity": 1,
                            "price_unit": 100,
                            "tax_ids": [Command.set(sale_tax.ids)],
                        }
                    )
                ],
            }
        )
        report = self.env.ref("strictbase_invoice_template.action_report_strictbase_invoice")

        html, report_type = report._render_qweb_html(report.report_name, invoice.ids)
        rendered = html.decode("utf-8") if isinstance(html, bytes) else html

        self.assertEqual(report_type, "html")
        self.assertEqual(rendered.count("Reverse charge"), 1)

    def test_report_displays_tax_group_amount_from_tax_totals(self):
        sale_tax = self.env["account.tax"].search(
            [("type_tax_use", "=", "sale"), ("amount", ">", 0)],
            order="amount desc, id",
            limit=1,
        )
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "invoice_date": "2026-03-13",
                "date": "2026-03-13",
                "journal_id": self.sale_journal.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Taxed service",
                            "quantity": 1,
                            "price_unit": 100,
                            "tax_ids": [Command.set(sale_tax.ids)],
                        }
                    )
                ],
            }
        )
        report = self.env.ref("strictbase_invoice_template.action_report_strictbase_invoice")

        html, report_type = report._render_qweb_html(report.report_name, invoice.ids)
        rendered = html.decode("utf-8") if isinstance(html, bytes) else html
        tax_group_name = invoice.tax_totals["subtotals"][0]["tax_groups"][0]["group_name"]

        self.assertEqual(report_type, "html")
        self.assertIn(tax_group_name, rendered)
        self.assertIn(invoice._strictbase_format_amount_html(invoice.amount_tax, invoice.currency_id), rendered)

    def test_outside_eu_export_tax_uses_custom_label(self):
        sale_tax = self.env["account.tax"].create(
            {
                "name": "0% EX",
                "amount": 0.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
            }
        )
        invoice = self.env["account.move"].new({"move_type": "out_invoice"})
        label = invoice._strictbase_tax_group_label({"group_name": "VAT 0%", "involved_tax_ids": sale_tax.ids})

        self.assertEqual(label, "No VAT for delivery outside EU")

    def test_reverse_charge_tax_uses_partner_vat_in_label(self):
        sale_tax = self.env["account.tax"].create(
            {
                "name": "0% EX EU S",
                "amount": 0.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
            }
        )
        partner = self.partner_a.copy({"vat": "FR59383105137"})
        invoice = self.env["account.move"].new({"move_type": "out_invoice", "partner_id": partner.id})
        label = invoice._strictbase_tax_group_label({"group_name": "VAT 0%", "involved_tax_ids": sale_tax.ids})

        self.assertEqual(label, "VAT reverse-charged to FR59383105137")

    def test_reverse_charge_tax_uses_dutch_translation_when_language_is_dutch(self):
        sale_tax = self.env["account.tax"].create(
            {
                "name": "0% EX EU S",
                "amount": 0.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
            }
        )
        partner = self.partner_a.copy({"vat": "BE 0834.341.738", "lang": "nl_NL"})
        invoice = self.env["account.move"].with_context(lang="nl_NL").new({"move_type": "out_invoice", "partner_id": partner.id})
        label = invoice._strictbase_tax_group_label({"group_name": "VAT 0%", "involved_tax_ids": sale_tax.ids})

        self.assertEqual(label, "BTW verlegd naar BE 0834.341.738")

    def test_invoice_tax_note_preview_prefers_tax_legal_notes(self):
        sale_tax = self.env["account.tax"].create(
            {
                "name": "Reverse Charge Tax",
                "amount": 0.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
                "invoice_legal_notes": "<p>VAT Reverse charge</p>",
            }
        )
        fiscal_position = self.env["account.fiscal.position"].create({
            "name": "Preview Fiscal Position",
            "note": "<p>Fallback fiscal note</p>",
        })
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "invoice_date": "2026-03-13",
                "date": "2026-03-13",
                "journal_id": self.sale_journal.id,
                "fiscal_position_id": fiscal_position.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Service",
                            "quantity": 1,
                            "price_unit": 100,
                            "tax_ids": [Command.set(sale_tax.ids)],
                        }
                    )
                ],
            }
        )

        self.assertEqual(invoice.strictbase_tax_note_preview, sale_tax.invoice_legal_notes)

    def test_sale_order_tax_note_preview_uses_tax_legal_notes(self):
        sale_tax = self.env["account.tax"].create(
            {
                "name": "SO Reverse Charge Tax",
                "amount": 0.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
                "invoice_legal_notes": "<p>VAT Reverse charge</p>",
            }
        )
        fiscal_position = self.env["account.fiscal.position"].create({
            "name": "SO Preview Fiscal Position",
            "note": "<p>Fallback fiscal note</p>",
        })
        order = self.env["sale.order"].sudo().create(
            {
                "partner_id": self.partner_a.id,
                "fiscal_position_id": fiscal_position.id,
                "order_line": [
                    Command.create(
                        {
                            "name": "Support",
                            "product_uom_qty": 1,
                            "price_unit": 100,
                            "tax_ids": [Command.set(sale_tax.ids)],
                        }
                    )
                ],
            }
        )

        self.assertEqual(order.strictbase_tax_note_preview, sale_tax.invoice_legal_notes)
