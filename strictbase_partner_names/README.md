# README – strictbase_partner_names

## Module: StrictBase Partner Names

**Technical name:** `strictbase_partner_names`

### Overview

`strictbase_partner_names` introduces **split firstname / lastname support** for partners and integrates this model change into **CRM lead creation workflows**, including the CRM Kanban “Quick Create” card.

The module ensures that contacts created via CRM are created consistently with split name fields, while preserving Odoo’s default behavior where appropriate.

### Functional behavior

This module provides:

* `firstname` and `lastname` fields on `res.partner`
* Computed display name logic for contacts based on first/last name
* CRM lead support for:

  * entering first and last name separately
  * creating contact persons from the CRM quick-create card
* A custom **Create Contact** action in the CRM quick-create flow that:

  * creates a `res.partner` record immediately (matching Odoo’s many2one behavior)
  * assigns the new contact to the unsaved lead
  * avoids premature lead creation

### Installation

1. Ensure all dependencies are available on the addons path.
2. Install via Apps, or from the command line:

```bash
./odoo-bin -d <database> -i strictbase_partner_names
```

### Dependencies

Declared in `__manifest__.py`:

* `base`
* `contacts`
* `crm`
* `strictbase_contact`

Because this module extends CRM views and models, **CRM must be installed**.

### Main technical changes to core Odoo

#### Model changes

* Extends `res.partner`

  * Adds `firstname` and `lastname`
  * Adjusts name computation logic for non-company partners
* Extends `crm.lead`

  * Adds helper fields for CRM lead creation
  * Adds computed fields used for UI logic (e.g. detecting existing contacts)

#### View changes

* Extends CRM form and quick-create views
* Modifies the CRM Kanban “New Lead” card to:

  * show separate firstname/lastname inputs when appropriate
  * hide or show the contact selector dynamically

All view changes are done via standard XML inheritance.

#### Frontend / Web client changes

This module introduces **OWL + QWeb frontend components**, specifically:

* A custom field widget used in the CRM quick-create form
* A QWeb template for a Create Contact button
* JavaScript logic that:

  * creates `res.partner` records via the web client ORM
  * updates unsaved form state (`record.update`)
  * handles keyboard events (Enter/Tab) correctly inside the quick-create dialog

These changes are scoped to CRM and do not affect other apps.

### Architectural notes

* This module intentionally builds on Odoo’s default many2one “create on the fly” behavior
* Contact records created via CRM quick-create are immediately persisted, matching standard Odoo semantics
* Lead records are only created when the user confirms the quick-create dialog

### Recommended usage

* Install together with `strictbase_contact`
* Intended for environments where CRM is in active use
* Not suitable for databases without CRM

---

## Suggested module relationship

Suggested order:

* `strictbase_contact`
* `strictbase_partner_names` (depends on `contacts` and `crm`)

This structure allows:

* reuse of contact logic outside CRM
* clean separation between base model changes and CRM-specific UI behavior
