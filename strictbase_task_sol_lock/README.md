# strictbase_task_sol_lock

**Odoo 19.0 CE — StrictBase custom module**

Preserves historical timesheet SO lines when a task's Sales Order Item (`sale_line_id`) is switched to a new one.

## The problem this solves

In Odoo's support voucher ("wallet") workflow, prepaid hour batches are modelled as confirmed Sales Orders. When a client's batch runs out, a new SO is created and all open tasks are updated to point at the new SO line (batch reload, Phase 3 of the Support SOP).

The intent is clear: **only future timesheet entries should count against the new batch**. Historical entries (logged against the old SO) must stay put.

Odoo CE does not honour this intent out of the box.

### What Odoo actually does

`account.analytic.line.so_line` is a **stored computed field**::

    # sale_timesheet/models/hr_timesheet.py
    @api.depends('task_id.sale_line_id', 'project_id.sale_line_id', 'employee_id', 'project_id.allow_billable')
    def _compute_so_line(self):
        for timesheet in self.filtered(lambda t: not t.is_so_line_edited and t._is_not_billed()):
            timesheet.so_line = timesheet.project_id.allow_billable and timesheet._timesheet_determine_sale_line()

When `task.sale_line_id` changes, the ORM dependency system marks every linked timesheet as stale and fires `_compute_so_line()` on them. The compute skips only two categories:

- `is_so_line_edited`: User manually edited the SO line on this entry.
- `_is_not_billed()`: Entry has an active invoice (`timesheet_invoice_id`).

In a prepaid wallet model, the SO is invoiced **upfront** as a fixed-price lump sum. The individual timesheet entries are never individually invoiced — `timesheet_invoice_id` stays empty on all of them, permanently. The "not billed" guard never fires. **Every historical timesheet entry gets silently reassigned to the new SO** the moment you update the task.

The Support SOP (Phase 3, Step 5) contains a note saying this only affects future entries. That note reflects the intended behaviour; it does not reflect what Odoo does without this module.

## How this module fixes it

`project.task.write()` is overridden. When `sale_line_id` is present in the write values **and** the task already has an existing SO line (i.e. this is a switch, not an initial assignment), the module:

1. Finds all timesheet entries on the affected tasks where `is_so_line_edited = False` and `_is_not_billed()` is True — exactly the set the compute would have touched.
2. Sets `is_so_line_edited = True` on those entries **before** calling `super()`.
3. Calls `super().write(vals)` — the ORM fires the compute, which now skips all the locked entries.

New timesheet entries created after the switch start with `is_so_line_edited = False` and pick up the new SO line normally via the compute. No process change required.

## Consequences and trade-offs

### What changes

- Historical timesheet entries on a task get `is_so_line_edited = True` set at the moment the task's SO line is switched.
- Their `so_line` value is frozen at whatever it was before the switch.
- These entries will **never** be automatically updated by the compute again, even if the task's SO line is changed a second time.

### What does not change

- The `is_so_line_edited` flag already existed in Odoo for this exact purpose (manual overrides). This module uses it as designed.
- Entries can still be corrected manually: open the timesheet entry, change the SO line field directly. That field is `readonly=False`. The flag remains True, but the value is now whatever you set manually.
- The compute still runs normally for new entries.

### Initial assignment is not affected

If a task has no SO line set (`sale_line_id = False`) and you assign one for the first time, the module does nothing. Existing timesheets pick up the new SO line via the compute as normal. Only a **switch** (from a non-empty value to a different value) triggers the lock.

### Invoiced entries are not affected

Entries that already have `timesheet_invoice_id` set are skipped — both by the compute (standard Odoo) and by this module's search filter. They are already frozen by the invoicing state.

## Impact on other StrictBase workflows

### T&M Consultancy

The SO line is controlled at **project level** (`project.sale_line_id`), not at task level. Individual tasks do not carry a `sale_line_id` in this workflow. The override in this module only fires when `task.sale_line_id` is present in a write call — it is never triggered during normal T&M operation.

### Fixed-Price / Milestone Projects

Timesheets on fixed-price projects are internal cost tracking only; they do not drive invoicing. The SO line on timesheet entries has no billing consequence. The module is not triggered in this workflow for the same reason as T&M (no task-level SO switching).

### Custom Development (Lead-to-Project)

Same as Fixed-Price. Timesheets optional, no task-level SO switching, module not triggered.

---

## Correcting a mistake after the fact

If a timesheet entry was locked by this module but has the wrong SO line (e.g. it was already on the wrong SO before the switch), correct it directly on the timesheet entry:

1. Open the task → Timesheets tab.
2. Edit the SO line field on the specific entry.
3. Save.

The `is_so_line_edited` flag stays True, but the value is now corrected. This entry will not be touched by future automated compute runs.

---

## Installation

From the Odoo root, with your venv active::

    ./odoo-bin -c <your.conf> -i strictbase_task_sol_lock

No migration scripts, no new database columns, no new views.

---

## Technical reference

- Model patched: `project.task`
- Method overridden: `write()`
- Field set on timesheets: `account.analytic.line.is_so_line_edited` (Boolean)
- Compute avoided: `account.analytic.line._compute_so_line()`
- Native guard used: `account.analytic.line._is_not_billed()`
- Source studied: `sale_timesheet/models/hr_timesheet.py` lines 39-136
