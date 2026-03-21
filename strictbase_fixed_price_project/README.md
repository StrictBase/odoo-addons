# README - strictbase_fixed_price_project

**Technical name:** `strictbase_fixed_price_project`

## Purpose

This module removes the misleading `01:00` allocated/remaining time indicator from fixed-price projects created from sales orders.

In the StrictBase workflow, a fixed-price custom development project is sold as a single service line with:

- service policy: `Prepaid/Fixed Price` (`ordered_prepaid`)
- unit of measure: `Units`
- project creation enabled

When `sale_timesheet` is installed, standard Odoo treats that `1 Unit` as `1.0` allocated hour on the generated project. That produces the `01:00` "Time remaining" badge on the project card, even though the project is budgeted in money rather than hours.

This addon clears that bogus allocated time.

## How it works

The module overrides the project creation hook on `sale.order.line`.

After Odoo generates the project, the addon checks the sales order lines that feed that project. If all relevant lines are:

- service products
- project-generating products (`project_only` or `task_in_project`)
- fixed-price/prepaid (`service_policy == ordered_prepaid`)
- sold in `Units`

then the addon sets the generated project's `allocated_hours` to `0.0`.

## What it does not do

- It does **not** look at the project name.
- It does **not** look for words like `fixed` in any field.
- It does **not** disable timesheets.
- It does **not** change time-based services sold in hours or days.
- It does **not** overwrite explicit `allocated_hours` configured on a project template.

## Scope

This is intentionally narrow. The module only changes the case that produces the misleading placeholder hour for fixed-price projects created from sales.

## Dependencies

- `sale_project`
- `sale_timesheet`

## Tests

The module includes tests for:

- fixed-price project creation from a `Units`-based service line resulting in `0.0` allocated hours
- project template behavior where explicit template hours are preserved

