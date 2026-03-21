from odoo import models


class ProjectTask(models.Model):
    _inherit = "project.task"

    def write(self, vals):
        """Lock historical timesheet SO lines before switching the task's sale_line_id.

        Standard Odoo behaviour: when task.sale_line_id changes, the ORM dependency
        system fires _compute_so_line() on every linked account.analytic.line that is
        not manually edited and not yet individually invoiced. This retroactively
        reassigns all historical timesheet entries to the new SO line - which is
        incorrect for prepaid wallet workflows where only future entries should count
        against the new batch.

        Fix: before calling super(), find all timesheet entries that the compute would
        touch and set is_so_line_edited = True on them. The compute then skips them.
        New entries (created after this write) start with is_so_line_edited = False and
        pick up the new SO line normally via the compute.

        Only triggered when a task already has a sale_line_id set (i.e. we are
        switching, not setting for the first time). Setting a SO line on a task that
        previously had none is intentional propagation and is left untouched.
        """
        if "sale_line_id" in vals:
            new_sale_line_id = vals.get("sale_line_id") or False
            tasks_switching = self.filtered(
                lambda task: task.sale_line_id and task.sale_line_id.id != new_sale_line_id
            )
            if tasks_switching:
                timesheets = self.env["account.analytic.line"].search(
                    [
                        ("task_id", "in", tasks_switching.ids),
                        ("is_so_line_edited", "=", False),
                    ]
                ).filtered(lambda t: t._is_not_billed())
                if timesheets:
                    timesheets.write({"is_so_line_edited": True})
        return super().write(vals)
