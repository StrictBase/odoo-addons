# strictbase_worked_not_invoiced_report

Operational list view for sales order lines where service work was delivered but
the line still needs invoicing.

## Purpose

The standard Sales order list is too high-level for this question because it
works on `sale.order` headers, not on delivered service lines.

The standard Sales Analysis action is closer, but it opens in graphs and mixes
in more options than needed for day-to-day follow-up.

This module adds a dedicated list-first action on `sale.report`.

## What it adds

- `sale.report.product_type` so the report can be scoped to service lines
- a dedicated list view:
  - `Sales > Reporting > Worked Not Invoiced`
- production action:
  - `[your ERP URL]/odoo/action-545`
- default filters for:
  - confirmed sales orders
  - service lines only
  - delivered quantity greater than zero
  - line invoice status `To Invoice`
- quick filters for:
  - `Billable Only`
  - `Zero-Priced`

## Effective operational default

The live production action is intended to be used with a saved default favorite
that surfaces likely invoice misses only.

Effective criteria:

- `Qty Delivered > 0`
- `Qty Invoiced = 0`
- `Unit Price > 0`

This keeps zero-priced migration and support carry-over lines available in the
report, while excluding them from the default PM/admin follow-up view.

## Why the zero-priced filter matters

StrictBase's migrated support-wallet lines are intentionally confirmed at `0.00` and
not invoiced. They should remain visible for audit and triage, but they should
also be easy to separate from true invoice misses.

## Code layout

- `__manifest__.py` declares the addon and dependencies
- `report/sale_report.py` extends `sale.report` with `product_type`
- `report/sale_report_views.xml` defines the list view, search view, action, and menu
- `tests/test_worked_not_invoiced_report.py` covers the added field and action defaults

## Deployment

Example install:

```bash
python3 odoo-bin \
  -c <odoo.conf> \
  -d <db> \
  -i strictbase_worked_not_invoiced_report \
  --stop-after-init \
  --no-http
```

Example update:

```bash
python3 odoo-bin \
  -c <odoo.conf> \
  -d <db> \
  -u strictbase_worked_not_invoiced_report \
  --stop-after-init \
  --no-http
```

## Notes

- The report is backed by `sale.report`, not a custom reporting table.
- Rows open the underlying sales order on click.
- This module does not change invoicing logic.
