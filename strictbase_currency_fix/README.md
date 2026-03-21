# strictbase_currency_fix

## Purpose

`strictbase_currency_fix` enforces **correct, locale-aware currency formatting** in Odoo Community Edition.

The goal of this module is to ensure that monetary amounts:

* Follow **international localization standards** (CLDR/Babel-based formatting rules).
* Display the correct **currency symbol position** and spacing per locale.
* Use a **non-breaking space (NBSP)** where required.
* Remain consistent between:

  * Python backend formatting
  * JavaScript frontend formatting
  * List views (including x2many trees)
  * Form views
  * Totals widgets

This module exists because Odoo CE does not always strictly adhere to localized currency formatting standards in all UI contexts, especially when:

* Currency symbols are omitted in list views.
* Spacing around currency symbols is incorrect.
* Formatting differs between backend and frontend.
* Certain views fall back to float formatting instead of monetary formatting.

The objective is one unified, standards-compliant solution.

---

# What This Module Patches

This module modifies both **Python (backend)** and **JavaScript (frontend)** currency formatting behavior.

---

# Python (Backend) Patches

The following backend functions are patched via `post_load()` in `patch.py`:

## 1. `odoo.tools.format_amount`

This is Odoo’s primary backend monetary formatter.

### Original behavior:

* Uses Babel for formatting.
* May not enforce spacing behavior consistently across contexts.
* Can behave differently from frontend formatting.

### Our patch:

* Ensures Babel formatting is used consistently.
* Enforces correct symbol placement.
* Ensures spacing adheres to locale rules.
* Keeps backend formatting aligned with frontend formatting logic.

---

## 2. `odoo.tools.formatLang` (monetary usage)

Where monetary values pass through `formatLang`, we ensure:

* Decimal precision is preserved.
* Currency formatting rules are not bypassed.
* Output remains consistent with `format_amount`.

---

# JavaScript (Frontend) Patches

This module replaces and patches several frontend formatters.

---

## 1. Replacement of Core File:

### `@web/core/currency`

File replaced:

```
web/static/src/core/currency.js
```

We override this file using an `ir.asset` override so that:

* The module name remains `@web/core/currency`
* But the implementation is loaded from:

```
strictbase_currency_fix/static/src/core/currency.js
```

### Patched Function:

```
formatCurrency()
```

### Our modifications:

* Proper resolution of `currencyId` even when:

  * Passed as `[id, "EUR"]`
  * Missing but available in row data
  * Provided via currencyField
* Ensures correct symbol placement.
* Ensures correct spacing per locale.
* Uses NBSP when required.
* Aligns behavior with Babel backend formatting.

---

## ⚠️ IMPORTANT WARNING — Core File Replacement

We fully replace Odoo’s `currency.js`.

This means:

If Odoo is upgraded (e.g., 19.0 → 19.x or 20.0):

* Odoo’s original `currency.js` may change.
* New logic introduced by Odoo may not be present in our version.
* We must manually compare:

  ```
  addons/web/static/src/core/currency.js
  ```

  with our replacement version.

### Upgrade Procedure Recommendation

After every Odoo upgrade:

1. Diff upstream `currency.js` against ours.
2. Review any new logic introduced by Odoo.
3. Merge relevant upstream improvements.
4. Re-test all monetary formatting contexts.

Failure to do so may silently break formatting behavior.

---

## 2. Monetary Formatter Override

File:

```
static/src/js/monetary_override.js
```

We override the frontend monetary formatter registered in the field registry.

### Patched Behavior:

* Correctly resolves currency id when:

  * `options.currencyId` is undefined.
  * `currencyField` is empty.
  * Currency is available in row data (`currency_id`).
* Ensures list view monetary fields display currency symbols correctly.
* Prevents fallback to raw float formatting.

This fix specifically addresses missing currency symbols in:

* Sale Order line "Amount"
* x2many list/tree monetary fields

---

## 3. Float Formatter Override (Scoped)

Problem:
`price_unit` in list views is rendered as a float, not monetary.

Solution:
We override the float formatter **only when the field name is `price_unit`**.

We do NOT globally override float formatting.

### Why this matters:

Without scoping:

* Quantity
* Delivered
* Invoiced

would incorrectly receive currency formatting.

By scoping to `price_unit`, we:

* Add currency symbol where expected.
* Preserve correct float formatting everywhere else.

---

# Why This Module Exists

International standards (CLDR / Babel-based localization rules) define:

* Currency symbol position (before or after)
* Whether spacing is required
* Whether spacing must be non-breaking
* Decimal separator and grouping rules

Odoo CE does not always consistently apply these rules across:

* Form views
* List views
* Aggregated totals
* Embedded x2many trees

This module enforces:

* Strict adherence to localized monetary formatting standards.
* Consistency between backend and frontend.
* Elimination of missing currency symbols.
* Predictable behavior across all UI contexts.

---

# Design Philosophy

This module:

* Does NOT introduce consumer-specific logic.
* Does NOT modify sale/order-specific views.
* Does NOT hack templates.

Instead, it:

* Patches core formatting layers.
* Keeps behavior centralized.
* Ensures consistent formatting globally.

---

# Deployment Notes

After updating this module:

Always:

```
systemctl --user stop odoo.service
./odoo-bin -c <config> -d <db> -u strictbase_currency_fix --stop-after-init
systemctl --user start odoo.service
```
(Or the equivalent on your system.)

Then hard-refresh browser assets (especially if using `debug=assets`).

---

# Risks

Because we:

* Replace core JS
* Patch formatter registries

This module must be:

* Carefully reviewed after Odoo upgrades.
* Re-tested in:

  * Sale orders
  * Invoices
  * Reports
  * List views
  * Totals widgets

---

# Summary

`strictbase_currency_fix` provides:

✔ Unified backend + frontend currency formatting
✔ Locale-compliant monetary display
✔ Correct symbol positioning and spacing
✔ Consistency across all Odoo views
✔ Strict adherence to international formatting standards

And it does so by patching the correct abstraction layers — not by modifying business views.

