from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged


@tagged("-at_install", "post_install")
class TestStrictBaseAgentGuard(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({
            "name": "External Contact",
            "email": "external@example.com",
        })
        self.agent_user = self.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Agent User",
            "login": "agent-user@example.com",
            "email": "agent-user@example.com",
            "group_ids": [Command.set([self.env.ref("base.group_user").id])],
        })
        self.env.user.group_ids += self.env.ref("strictbase_agent_guard.group_agent_confirmation_approver")

    def test_message_post_allows_internal_note(self):
        record = self.partner.with_context(agent_mode=True)
        message = record.message_post(
            body="Internal note",
            subtype_xmlid="mail.mt_note",
            message_type="comment",
        )
        self.assertTrue(message)

    def test_message_post_blocks_external_partner_notification(self):
        record = self.partner.with_context(agent_mode=True)
        with self.assertRaisesRegex(UserError, "AGENT_CONFIRMATION_REQUIRED"):
            record.message_post(
                body="Client-facing update",
                subtype_xmlid="mail.mt_comment",
                message_type="comment",
                partner_ids=[self.partner.id],
            )

    def test_message_post_allows_with_confirmation_context(self):
        token = self.env["strictbase.agent.confirmation"].issue_token(
            "res.partner",
            "message_post",
            record_ids=[self.partner.id],
        )
        record = self.partner.with_context(agent_mode=True, agent_confirmation_token=token)
        message = record.message_post(
            body="Approved client-facing update",
            subtype_xmlid="mail.mt_comment",
            message_type="comment",
            partner_ids=[self.partner.id],
        )
        self.assertTrue(message)

    def test_message_post_rejects_reused_confirmation_token(self):
        token = self.env["strictbase.agent.confirmation"].issue_token(
            "res.partner",
            "message_post",
            record_ids=[self.partner.id],
        )
        record = self.partner.with_context(agent_mode=True, agent_confirmation_token=token)
        message = record.message_post(
            body="Approved client-facing update",
            subtype_xmlid="mail.mt_comment",
            message_type="comment",
            partner_ids=[self.partner.id],
        )
        self.assertTrue(message)

        with self.assertRaisesRegex(UserError, "AGENT_CONFIRMATION_REQUIRED"):
            record.message_post(
                body="Second client-facing update",
                subtype_xmlid="mail.mt_comment",
                message_type="comment",
                partner_ids=[self.partner.id],
            )

    def test_non_approver_cannot_issue_confirmation_token(self):
        with self.assertRaises(AccessError):
            self.env["strictbase.agent.confirmation"].with_user(self.agent_user).issue_token(
                "res.partner",
                "message_post",
                record_ids=[self.partner.id],
            )

    def test_mail_compose_log_note_is_allowed(self):
        wizard = self.env["mail.compose.message"].with_context(
            agent_mode=True,
            default_model="res.partner",
            default_res_ids=str([self.partner.id]),
        ).create({
            "composition_mode": "comment",
            "model": "res.partner",
            "res_ids": str([self.partner.id]),
            "body": "Internal log note",
            "message_type": "comment",
            "subtype_id": self.env.ref("mail.mt_note").id,
        })
        result = wizard.action_send_mail()
        self.assertEqual(result["type"], "ir.actions.act_window_close")

    def test_mail_compose_send_requires_confirmation(self):
        wizard = self.env["mail.compose.message"].with_context(
            agent_mode=True,
            default_model="res.partner",
            default_res_ids=str([self.partner.id]),
        ).create({
            "composition_mode": "comment",
            "model": "res.partner",
            "res_ids": str([self.partner.id]),
            "body": "Outbound send",
            "message_type": "comment",
            "partner_ids": [(6, 0, [self.partner.id])],
            "subtype_id": self.env.ref("mail.mt_comment").id,
        })
        with self.assertRaisesRegex(UserError, "AGENT_CONFIRMATION_REQUIRED"):
            wizard.action_send_mail()
