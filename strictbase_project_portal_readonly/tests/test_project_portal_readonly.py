from types import SimpleNamespace
from unittest.mock import patch

from odoo.exceptions import AccessError
from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.strictbase_project_portal_readonly.controllers.portal import StrictBaseReadonlyPortalMixin
from odoo.addons.project.tests.test_project_sharing import TestProjectSharingCommon


@tagged("-at_install", "post_install")
class TestProjectPortalReadonly(TestProjectSharingCommon):
    def test_support_overview_brand_uses_website_company(self):
        class DummyPortal(StrictBaseReadonlyPortalMixin):
            def __init__(self, env):
                self.env = env

            def _prepare_portal_layout_values(self):
                return {}

            def _get_readonly_projects(self):
                return self.env["project.project"]

        brand_company = self.env["res.company"].create({"name": "Portal Brand Co"})
        fake_request = SimpleNamespace(
            website=SimpleNamespace(company_id=brand_company),
            env=self.env,
        )

        with patch("odoo.addons.strictbase_project_portal_readonly.controllers.portal.request", fake_request):
            values = DummyPortal(self.env)._prepare_support_overview_values()

        self.assertEqual(values["support_overview_brand_name"], "Portal Brand Co")
        self.assertEqual(values["page_title"], "Portal Brand Co Support Overview")

    def test_readonly_all_tasks_grants_full_project_read_without_write(self):
        wizard = self.env["project.share.wizard"].create({
            "res_model": "project.project",
            "res_id": self.project_portal.id,
            "collaborator_ids": [
                Command.create({
                    "partner_id": self.user_portal.partner_id.id,
                    "access_mode": "read_all",
                }),
            ],
        })
        wizard.action_send_mail()

        collaborator = self.project_portal.collaborator_ids.filtered(
            lambda record: record.partner_id == self.user_portal.partner_id
        )
        self.assertTrue(collaborator)
        self.assertTrue(collaborator.limited_access)
        self.assertTrue(collaborator.readonly_full_access)

        closed_task = self.env["project.task"].create({
            "name": "Closed Portal Task",
            "project_id": self.project_portal.id,
            "stage_id": self.project_portal.type_ids.filtered("fold")[:1].id,
        })
        closed_task.state = "1_done"
        closed_task.message_unsubscribe(partner_ids=self.user_portal.partner_id.ids)

        portal_tasks = self.env["project.task"].with_user(self.user_portal).search([
            ("project_id", "=", self.project_portal.id),
        ])

        self.assertIn(self.task_portal, portal_tasks)
        self.assertIn(closed_task, portal_tasks)

        self.task_portal.with_user(self.user_portal).check_access("read")
        closed_task.with_user(self.user_portal).check_access("read")

        with self.assertRaises(AccessError):
            self.task_portal.with_user(self.user_portal).check_access("write")
        with self.assertRaises(AccessError):
            self.env["project.task"].with_user(self.user_portal).create({
                "name": "Portal Write Attempt",
                "project_id": self.project_portal.id,
            })

    def test_default_get_maps_readonly_all_tasks_mode(self):
        self.project_portal.write({
            "collaborator_ids": [
                Command.create({
                    "partner_id": self.user_portal.partner_id.id,
                    "limited_access": True,
                    "readonly_full_access": True,
                }),
            ],
        })

        wizard = self.env["project.share.wizard"].with_context(
            active_model="project.project",
            active_id=self.project_portal.id,
        ).new({})
        collaborator_modes = {
            collaborator.partner_id.id: collaborator.access_mode
            for collaborator in wizard.collaborator_ids
        }

        self.assertEqual(
            collaborator_modes[self.user_portal.partner_id.id],
            "read_all",
        )
