# StrictBase Invoice Template

This module adds a branded StrictBase invoice / credit note PDF report for Odoo 19 CE and a shared `YYYYMM-XXX` yearly-reset sequence for customer invoices and credit notes.

## What it does

- Adds a custom invoice PDF report: `strictbase_invoice_template.action_report_strictbase_invoice`
- Uses an uploaded StrictBase invoice background asset stored in Odoo
- Supports invoices and credit notes on the same template
- Renders Dutch invoice wording for partners with `lang` starting with `nl`
- Uses a shared posted sequence format: `YYYYMM-XXX`
- Resets numbering to `001` at the start of each new year
- Supports a per-journal configurable starting number
- Allows the configured journal start number to move the next Odoo-issued invoice number forward within a year
- Never allows the configured start number to move numbering backward below the last already-posted StrictBase number
- Allows manual name override when needed in standard Odoo ways
- Adds a tax-note preview on sales orders and invoices so reverse-charge wording is visible before printing
- Hides internal sales-order references on the PDF while still showing an external customer reference when present
- Uses `VAT reverse-charged to <VAT>` / `BTW verlegd naar <VAT>` for intra-EU B2B reverse-charge VAT rows
- Uses `No VAT for delivery outside EU` for outside-EU export VAT rows
- Suppresses a redundant second-line English product-name fallback on translated invoice lines

## Payment terms

Odoo's standard model is:

- the customer holds the default payment term
- the sales order inherits it
- the invoice inherits it

This module adds two small safeguards on top of that standard flow:

- draft invoice forms recompute the due date immediately from the selected payment term, so a new invoice can show `invoice date + 14 days` before any line is added
- invoice creation from a sales order falls back to the customer payment term if the sales order itself has no payment term yet

In local `strictbase` testing, the default `14 Days` term was also backfilled onto the existing sales orders that were still empty.

## Journal configuration

On the sales journal you want to use for customer invoices:

- Set `Invoice Template PDF Report` to `StrictBase Invoice PDF`
- Enable `Use StrictBase Invoice Sequence`
- Set `StrictBase Sequence Start` as needed, usually `1`

The setup was validated on a sales journal such as `INV`.

## Runtime requirements

The PDF output depends on a patched Qt `wkhtmltopdf`. A working setup needs:

- `wkhtmltopdf 0.12.6.1 (with patched qt)`
- Odoo `bin_path` pointing to a directory where that binary is available as `wkhtmltopdf`

The module prefers the configured `bin_path` binary during report rendering.

## Local testing notes

Automated tests:

- `strictbase_invoice_template/tests/test_invoice_sequence.py`

Focused module test command:

    python3 odoo-bin \
      -c <odoo.conf> \
      -d <db> \
      -u strictbase_invoice_template \
      --test-tags /strictbase_invoice_template \
      --stop-after-init

What the tests cover:

- sequence progression across months
- yearly reset
- shared invoice / credit note sequence
- configured starting number
- skip-forward behavior after already-posted invoices exist in the same year
- protection against moving backward below the last already-used posted number
- resilience against many non-StrictBase manual names in the same journal/year
- empty draft invoices computing due date from the selected payment term
- invoice-form onchange computing due date from the partner payment term
- sales-order invoice generation falling back to the partner payment term
- HTML report output including A4 styling and optional uploaded background
- invoice note rendering preferring tax legal notes over fiscal-position legal notes when both are present
- hiding internal sales-order references while keeping external customer references
- suppressing a redundant English fallback line when the first line already contains the translated product name

## EU reverse charge setup

There are two separate Odoo mechanisms involved:

- Quotations / sales orders print the fiscal position `Legal Notes`
- Invoices can print either the fiscal position `Legal Notes` or the final sale tax `Legal Notes`

For StrictBase's intra-EU B2B service invoices:

- service products must use the Dutch service sale tax family, typically `21% ST S`
- the `EU intra B2B` fiscal position should have a legal note such as `Reverse charge - Article 196 of Council Directive 2006/112/EC`
- the final mapped tax should be `0% EX EU S`, which already carries the invoice legal note in `l10n_nl`

The custom invoice template suppresses the fiscal-position note when tax legal notes are already present, so invoices do not show duplicate reverse-charge wording while sales orders still can.

## Report behavior

The report background is embedded as a data URI from the company setting:

- `Invoicing > Settings > StrictBase Invoice Background`

The QWeb template is:

- `report/strictbase_invoice_templates.xml`

The custom sequence logic is:

- `models/account_move.py`

Sales-order fallback logic and tax-note preview support are in:

- `models/sale_order.py`

The custom PDF runner integration is:

- `models/ir_actions_report.py`

## Known operational detail

When rendering reports outside a normal web request context, Odoo asset bundle URLs may need a valid database-backed HTTP session to resolve correctly. Normal UI-based printing and sending is the intended path for this module.

## Pre-live checklist

- Verify invoice print/send from the UI in the target environment
- Verify the sales journal uses the StrictBase report and sequence settings
- Confirm the live server has patched Qt `wkhtmltopdf` configured via `bin_path`
- Confirm live `web.base.url` / `report.url` are correct for server-side report rendering
- Print one invoice and one credit note on live before broader use
