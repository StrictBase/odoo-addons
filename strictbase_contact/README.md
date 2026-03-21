# README – strictbase_contact

## Module: StrictBase Contact Extensions

**Technical name:** `strictbase_contact`

### Overview

`strictbase_contact` provides foundational extensions to Odoo’s Contacts (`res.partner`) model.
It is designed as a **base module** that can be reused independently of CRM or other business apps.

The module introduces structural changes to how contact data is represented and displayed, without altering CRM workflows or frontend behavior.

### Functional behavior

This module:

* Extends `res.partner` with additional contact-related fields
* Provides a stable base for downstream modules that need enhanced contact semantics
* Does **not** alter CRM, Sales, or other app-specific workflows
* Does **not** introduce frontend widgets or JavaScript behavior

Typical use cases:

* Contacts-only databases
* Accounting-only or ERP-light setups
* As a dependency for CRM or Sales extensions that rely on richer contact data

### Installation

1. Ensure the module is available on the Odoo addons path.
2. Install via Apps, or from the command line:

```bash
./odoo-bin -d <database> -i strictbase_contact
```

### Dependencies

Declared in `__manifest__.py`:

* `base`
* `contacts`

This module **does not depend on CRM**.

### Main technical changes to core Odoo

#### Model changes

* Extends `res.partner`
* Adds new contact-related fields (exact fields depend on implementation)
* Does not remove or override core fields

#### Views

* May extend standard Contacts views to expose new fields
* Uses standard `<odoo>` XML view inheritance
* No JavaScript or OWL components are introduced

#### Architecture notes

* Designed as a **base layer**
* Safe to install without CRM
* Intended to be depended on by other StrictBase modules