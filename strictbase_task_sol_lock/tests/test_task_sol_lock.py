from odoo.tests import tagged

from odoo.addons.sale_timesheet.tests.common import TestCommonSaleTimesheet


@tagged("-at_install", "post_install")
class TestTaskSolLock(TestCommonSaleTimesheet):
    """Verify that switching a task's sale_line_id preserves historical timesheet
    SO lines instead of retroactively reassigning them to the new batch."""

    def _make_timesheet(self, task, project, unit_amount=1.0):
        return self.env["account.analytic.line"].create({
            "name": "Test timesheet entry",
            "unit_amount": unit_amount,
            "employee_id": self.employee_manager.id,
            "project_id": project.id,
            "task_id": task.id,
        })

    def test_switching_sol_locks_historical_timesheets(self):
        """Core case: switching a task's SOL must freeze existing timesheet entries
        on the old SO line and prevent the ORM compute from reassigning them."""
        task = self.env["project.task"].create({
            "name": "Support Issue - Batch Switch",
            "project_id": self.project_task_rate.id,
        })
        old_sol = task.sale_line_id
        self.assertTrue(old_sol, "Task should have a SOL via project setup.")

        timesheet = self._make_timesheet(task, self.project_task_rate, unit_amount=0.5)
        self.assertEqual(timesheet.so_line, old_sol)
        self.assertFalse(timesheet.is_so_line_edited)

        # Pick a different SOL from the same SO to simulate a batch reload.
        new_sol = self.so.order_line.filtered(lambda l: l != old_sol)[:1]
        self.assertTrue(new_sol, "Need at least two SOLs on the SO for this test.")

        task.write({"sale_line_id": new_sol.id})

        self.assertEqual(
            timesheet.so_line,
            old_sol,
            "Historical timesheet SOL must not be updated after task SOL switch.",
        )
        self.assertTrue(
            timesheet.is_so_line_edited,
            "Historical timesheet must be flagged so the compute skips it in future.",
        )

    def test_new_timesheet_after_switch_picks_up_new_sol(self):
        """Timesheets logged after the batch switch must get the new SOL — the lock
        only applies to entries that existed at the moment of the switch."""
        task = self.env["project.task"].create({
            "name": "Support Issue - After Switch",
            "project_id": self.project_task_rate.id,
        })
        old_sol = task.sale_line_id
        new_sol = self.so.order_line.filtered(lambda l: l != old_sol)[:1]
        self.assertTrue(new_sol)

        task.write({"sale_line_id": new_sol.id})

        # New timesheet created after the switch.
        timesheet = self._make_timesheet(task, self.project_task_rate, unit_amount=0.5)

        self.assertEqual(
            timesheet.so_line,
            new_sol,
            "Timesheet created after the switch must be linked to the new SOL.",
        )
        self.assertFalse(
            timesheet.is_so_line_edited,
            "New timesheet must not be pre-locked.",
        )

    def test_first_sol_assignment_does_not_lock_timesheets(self):
        """Setting a SOL on a task that previously had none is an initial assignment,
        not a switch. Existing timesheets must not be locked."""
        # A billable project with no SO linked: tasks start with no SOL.
        project = self.env["project.project"].create({
            "name": "Billable Project (no SO)",
            "allow_billable": True,
            "partner_id": self.partner_a.id,
        })
        task = self.env["project.task"].create({
            "name": "Task Without SOL",
            "project_id": project.id,
        })
        self.assertFalse(task.sale_line_id, "Task must start with no SOL.")

        timesheet = self._make_timesheet(task, project, unit_amount=1.0)
        self.assertFalse(timesheet.is_so_line_edited)

        # Assign a SOL for the first time.
        task.write({"sale_line_id": self.so.order_line[0].id})

        self.assertFalse(
            timesheet.is_so_line_edited,
            "Timesheets must not be locked on first-time SOL assignment.",
        )

    def test_already_locked_timesheets_are_untouched(self):
        """Timesheets already flagged as is_so_line_edited must keep their manually
        set SOL regardless of subsequent task SOL switches."""
        task = self.env["project.task"].create({
            "name": "Support Issue - Pre-locked",
            "project_id": self.project_task_rate.id,
        })
        old_sol = task.sale_line_id

        timesheet = self._make_timesheet(task, self.project_task_rate, unit_amount=1.0)
        # Simulate a prior manual override on this timesheet.
        timesheet.write({"is_so_line_edited": True, "so_line": old_sol.id})

        new_sol = self.so.order_line.filtered(lambda l: l != old_sol)[:1]
        self.assertTrue(new_sol)
        task.write({"sale_line_id": new_sol.id})

        self.assertEqual(
            timesheet.so_line,
            old_sol,
            "Pre-locked timesheet SOL must not be changed by a task switch.",
        )
        self.assertTrue(timesheet.is_so_line_edited)

    def test_writing_same_sol_does_not_lock_timesheets(self):
        """A no-op write with the existing SOL must not lock historical entries."""
        task = self.env["project.task"].create(
            {
                "name": "Support Issue - Same SOL",
                "project_id": self.project_task_rate.id,
            }
        )
        current_sol = task.sale_line_id
        self.assertTrue(current_sol)

        timesheet = self._make_timesheet(task, self.project_task_rate, unit_amount=0.5)
        self.assertFalse(timesheet.is_so_line_edited)

        task.write({"sale_line_id": current_sol.id})

        self.assertEqual(timesheet.so_line, current_sol)
        self.assertFalse(
            timesheet.is_so_line_edited,
            "No-op SOL writes must not freeze historical entries.",
        )
