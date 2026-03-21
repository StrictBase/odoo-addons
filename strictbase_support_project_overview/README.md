# strictbase_support_project_overview

Project-level support wallet overview for StrictBase's support-voucher workflow.

## Purpose

Support balances already exist in Odoo on the active support sales order line.
This module exposes those values directly on `project.project` so StrictBase can see
one current balance per real support project, without task clutter and without
historical reload lines polluting the overview.

## What it adds

- `project.project.support_hours_ordered`
- `project.project.support_hours_delivered`
- `project.project.support_remaining_hours`
- `project.project.is_support_ticket_project`

The balance fields are stored related fields based on the project's active
`sale_line_id`.

`is_support_ticket_project` is true only when:

- the project has the `Support Tickets` project tag
- the project is not a template

## User-facing result

This module adds:

- project search filters:
  - `Support Ticket Projects`
  - `Low Support Balance`
  - `Needs Reload`
- a dedicated menu:
  - `Project > Reporting > Support Reload Overview`

The overview is sorted by remaining hours ascending so the projects closest to
reload appear first.

## Why this exists

Task views are too noisy because every issue repeats the same support wallet.
Sales order line views are useful for audit, but they include historical reload
lines and therefore do not represent the current operational state.

In StrictBase's SOP, the project's `sale_line_id` is the active wallet pointer. This
module follows that rule directly.

## Dependencies

- `project`
- `sale_timesheet`

## Notes

- Historical reload lines remain in Sales for audit continuity.
- This module does not change the reload workflow itself.
- This module assumes real support projects are tagged with `Support Tickets`.
