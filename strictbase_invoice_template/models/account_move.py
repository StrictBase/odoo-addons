import base64
import re

from odoo import api, fields, models
from odoo.tools import OrderedSet, format_amount, is_html_empty
from markupsafe import Markup


class AccountMove(models.Model):
    _inherit = "account.move"

    _strictbase_invoice_sequence_regex = re.compile(r"^(?P<year>\d{4})(?P<month>\d{2})-(?P<seq>\d+)$")
    _strictbase_invoice_sequence_sql_regex = r"^[0-9]{6}-[0-9]+$"

    strictbase_tax_note_preview = fields.Html(
        string="Tax Note Preview",
        compute="_compute_strictbase_tax_note_preview",
    )

    def _use_strictbase_invoice_sequence(self):
        self.ensure_one()
        return (
            self.move_type in ("out_invoice", "out_refund")
            and self.journal_id.type == "sale"
            and self.journal_id.strictbase_invoice_sequence_enabled
        )

    @api.model
    def _parse_strictbase_invoice_sequence(self, name):
        if not name:
            return None
        match = self._strictbase_invoice_sequence_regex.match(name)
        if not match:
            return None
        values = match.groupdict()
        return {
            "year": int(values["year"]),
            "month": int(values["month"]),
            "seq": int(values["seq"]),
            "seq_length": len(values["seq"]),
            "year_length": 4,
            "year_end": 0,
            "year_end_length": 0,
            "prefix1": "",
            "prefix2": "",
            "prefix3": "-",
            "suffix": "",
        }

    @api.model
    def _strictbase_invoice_background_data_uri(self):
        encoded = self.env.company.strictbase_invoice_background_image
        if not encoded:
            return False
        if isinstance(encoded, bytes):
            encoded = encoded.decode("ascii")
        return f"data:image/png;base64,{encoded}"

    def _strictbase_format_amount_html(self, amount, currency=None):
        self.ensure_one()
        currency = currency or self.currency_id
        formatted = format_amount(self.env, amount, currency)
        formatted = formatted.replace("€", "&euro;").replace("\xa0", " ")
        return Markup(formatted)

    def _strictbase_tax_group_label(self, tax_group):
        self.ensure_one()
        involved_ids = tax_group.get("involved_tax_ids") or []
        taxes = self.env["account.tax"].browse(involved_ids)
        tax_names = set(taxes.mapped("name"))
        if tax_names == {"0% EX EU S"}:
            is_dutch = (self.env.context.get("lang") or self.partner_id.lang or "").startswith("nl")
            if self.partner_id.vat:
                if is_dutch:
                    return f"BTW verlegd naar {self.partner_id.vat}"
                return f"VAT reverse-charged to {self.partner_id.vat}"
            if is_dutch:
                return "BTW verlegd"
            return "VAT reverse-charged"
        if tax_names == {"0% EX"}:
            return "No VAT for delivery outside EU"
        if tax_names == {"0% EX I"}:
            return "No VAT for delivery outside EU"
        return tax_group.get("group_name")

    def _strictbase_invoice_line_parts(self, line):
        self.ensure_one()
        parts = (line.name or "").splitlines()
        main = parts[0] if parts else ""
        note = "\n".join(parts[1:]).strip()
        if note and line.product_id:
            tmpl = line.product_id.product_tmpl_id
            english_name = (tmpl.with_context(lang="en_US").name or "").strip()
            if note == english_name and main.strip() and main.strip() != english_name:
                note = ""
        return {
            "main": main,
            "note": note,
        }

    def _strictbase_due_date_from_payment_term(self):
        self.ensure_one()
        if not self.is_invoice(True) or not self.invoice_payment_term_id:
            return False
        date_ref = self.invoice_date or self.date or fields.Date.context_today(self)
        terms = self.invoice_payment_term_id._compute_terms(
            date_ref=date_ref,
            currency=self.currency_id or self.company_id.currency_id,
            tax_amount_currency=0.0,
            tax_amount=0.0,
            untaxed_amount_currency=0.0,
            untaxed_amount=0.0,
            company=self.company_id,
            cash_rounding=self.invoice_cash_rounding_id,
            sign=self.direction_sign,
        )
        due_dates = [line["date"] for line in terms.get("line_ids", []) if line.get("date")]
        return max(due_dates) if due_dates else False

    @api.depends("taxes_legal_notes", "fiscal_position_id.note", "line_ids.tax_ids.invoice_legal_notes")
    def _compute_strictbase_tax_note_preview(self):
        for move in self:
            tax_notes = "".join(
                tax.invoice_legal_notes
                for tax in OrderedSet(move.line_ids.tax_ids)
                if not is_html_empty(tax.invoice_legal_notes)
            )
            if not is_html_empty(tax_notes):
                move.strictbase_tax_note_preview = tax_notes
            elif not is_html_empty(move.fiscal_position_id.note):
                move.strictbase_tax_note_preview = move.fiscal_position_id.note
            else:
                move.strictbase_tax_note_preview = False

    @api.depends("needed_terms", "invoice_payment_term_id", "invoice_date", "currency_id", "company_id")
    def _compute_invoice_date_due(self):
        super()._compute_invoice_date_due()
        for move in self:
            if (
                not move.is_invoice(True)
                or not move.invoice_payment_term_id
                or move.needed_terms
            ):
                continue
            date_ref = move.invoice_date or move.date or fields.Date.context_today(move)
            terms = move.invoice_payment_term_id._compute_terms(
                date_ref=date_ref,
                currency=move.currency_id or move.company_id.currency_id,
                tax_amount_currency=0.0,
                tax_amount=0.0,
                untaxed_amount_currency=0.0,
                untaxed_amount=0.0,
                company=move.company_id,
                cash_rounding=move.invoice_cash_rounding_id,
                sign=move.direction_sign,
            )
            due_dates = [line["date"] for line in terms.get("line_ids", []) if line.get("date")]
            if due_dates:
                move.invoice_date_due = max(due_dates)

    @api.onchange("partner_id")
    def _onchange_strictbase_partner_payment_term(self):
        for move in self:
            if not move.is_sale_document(include_receipts=True):
                continue
            if move.partner_id and move.partner_id.property_payment_term_id:
                move.invoice_payment_term_id = move.partner_id.property_payment_term_id
            move.invoice_date_due = move._strictbase_due_date_from_payment_term() or move.invoice_date_due

    @api.onchange("invoice_payment_term_id", "invoice_date", "date", "currency_id")
    def _onchange_strictbase_invoice_payment_term_due_date(self):
        for move in self:
            due_date = move._strictbase_due_date_from_payment_term()
            if due_date:
                move.invoice_date_due = due_date

    def _deduce_sequence_number_reset(self, name):
        if self and self._use_strictbase_invoice_sequence() and self._parse_strictbase_invoice_sequence(name):
            return "year"
        return super()._deduce_sequence_number_reset(name)

    def _get_sequence_format_param(self, previous):
        if self._use_strictbase_invoice_sequence():
            values = self._parse_strictbase_invoice_sequence(previous)
            if values:
                return "{year:04d}{month:02d}-{seq:0{seq_length}d}", values
        return super()._get_sequence_format_param(previous)

    def _get_starting_sequence(self):
        if self._use_strictbase_invoice_sequence():
            self.ensure_one()
            move_date = self.date or self.invoice_date or fields.Date.context_today(self)
            start = max(self.journal_id.strictbase_invoice_sequence_start or 1, 1) - 1
            return f"{move_date.year:04d}{move_date.month:02d}-{start:03d}"
        return super()._get_starting_sequence()

    def _strictbase_sequence_floor(self):
        self.ensure_one()
        return max(self.journal_id.strictbase_invoice_sequence_start or 1, 1) - 1

    def _get_next_sequence_format(self):
        if not self._use_strictbase_invoice_sequence():
            return super()._get_next_sequence_format()

        self.ensure_one()
        move_date = self.date or self.invoice_date or fields.Date.context_today(self)
        last_sequence = self._get_last_sequence()
        if last_sequence:
            format_string, format_values = self._get_sequence_format_param(last_sequence)
            format_values["seq"] = max(format_values["seq"], self._strictbase_sequence_floor())
        else:
            last_sequence = self._get_last_sequence(relaxed=True) or self._get_starting_sequence()
            format_string, format_values = self._get_sequence_format_param(last_sequence)
            format_values["seq"] = self._strictbase_sequence_floor()
        format_values["year"] = move_date.year
        format_values["month"] = move_date.month
        return format_string, format_values

    def _locked_increment(self, format_string, format_values):
        if self._use_strictbase_invoice_sequence():
            cache = self._get_sequence_cache()
            cache_key = (
                format_string.format(**{**format_values, "seq": 0}),
                self._sequence_index and self[self._sequence_index],
            )
            if cache_key in cache:
                cache[cache_key] = max(cache[cache_key], format_values["seq"])
        return super()._locked_increment(format_string, format_values)

    def _get_last_sequence(self, relaxed=False, with_prefix=None):
        if not self._use_strictbase_invoice_sequence():
            return super()._get_last_sequence(relaxed=relaxed, with_prefix=with_prefix)

        self.ensure_one()
        self.flush_model([self._sequence_field, "sequence_number", "sequence_prefix", "date", "state", "move_type"])
        move_date = self.date or self.invoice_date or fields.Date.context_today(self)
        params = {
            "journal_id": self.journal_id.id,
            "excluded_id": self._origin.id or self.id or 0,
            "sequence_regex": self._strictbase_invoice_sequence_sql_regex,
        }
        where_clauses = [
            "journal_id = %(journal_id)s",
            "id != %(excluded_id)s",
            "state = 'posted'",
            "name NOT IN ('/', '')",
            "move_type IN ('out_invoice', 'out_refund')",
            "name ~ %(sequence_regex)s",
        ]
        order_by = "sequence_number DESC, id DESC"

        if with_prefix is not None:
            where_clauses.append("sequence_prefix = %(with_prefix)s")
            params["with_prefix"] = with_prefix
        elif not relaxed:
            params["date_start"] = fields.Date.to_string(move_date.replace(month=1, day=1))
            params["date_end"] = fields.Date.to_string(move_date.replace(month=12, day=31))
            where_clauses.append("date BETWEEN %(date_start)s AND %(date_end)s")
        else:
            order_by = "date DESC, sequence_number DESC, id DESC"

        query = f"""
            SELECT {self._sequence_field}
              FROM {self._table}
             WHERE {" AND ".join(where_clauses)}
             ORDER BY {order_by}
             LIMIT 1
        """
        self.env.cr.execute(query, params)
        return (self.env.cr.fetchone() or [None])[0]
