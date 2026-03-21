# StrictBase Project Portal Read-Only

This addon extends Odoo 19 Project/Portal behavior for StrictBase's support workflow.

It adds a strict project-sharing mode for portal users:

- `Read-only (all tasks)`

That mode is intended for support clients who need visibility into:

- current tickets
- closed tickets
- time spent per ticket
- remaining support hours

without being able to edit tasks or create new ones.

## What It Does

### 1. Adds a full-project read-only sharing mode

The standard Odoo project sharing modes did not provide the exact combination StrictBase needed:

- access to all tasks in a shared project
- including historical/closed tickets
- with no task editing

This addon adds a collaborator flag and wizard option to support that mode.

### 2. Restricts access at the security-rule level

Portal users only get task read access when:

- they are explicit collaborators on the project
- and that collaborator row has `readonly_full_access=True`

This is enforced by record rules, not only by frontend hiding.

### 3. Replaces the generic portal flow for these users

For users in this readonly support-sharing mode, login redirects to a simplified support portal:

- `StrictBase Support Overview`

That page shows:

- current tickets
- past tickets
- time spent
- remaining support hours

Project/task portal routes for these users are redirected or replaced with simpler read-only pages.

### 4. Adds Excel export

The support overview includes an Excel-compatible export of the support data shown in the portal.

### 5. Cleans up the auth/signup UX for this use case

For readonly support invitees:

- the signup `Name` field is hidden because it is irrelevant and confusing in this flow

For public auth pages:

- the `Sign in with Odoo.com` option is hidden
- `Use a Passkey` remains available
- the password visibility button is patched so the icon/label reflect the current visibility state more clearly

## Main Files

- `wizard/project_share_wizard.py`
- `wizard/project_share_collaborator_wizard.py`
- `models/project_collaborator.py`
- `security/project_security.xml`
- `controllers/portal.py`
- `controllers/web.py`
- `views/project_share_wizard_views.xml`
- `views/support_portal_templates.xml`
- `views/auth_signup_templates.xml`
- `views/web_login_templates.xml`
- `static/src/public/auth_password_toggle_patch.js`

## Intended Usage

Typical flow for a support client contact:

1. Create the contact under the client company.
2. Grant portal access using Odoo's standard portal invite.
3. Open the client's support project.
4. Use `Share Project`.
5. Add the contact with access mode `Read-only (all tasks)`.

After login, that user lands on the simplified support overview.

## Notes

- Multiple readonly collaborators on the same support project are supported.
- Access remains project-scoped; users only see projects explicitly shared with them.
- This addon is intentionally narrow and support-portal specific. It does not try to redesign the generic Odoo portal for all users.
