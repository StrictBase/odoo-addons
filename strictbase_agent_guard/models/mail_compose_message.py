from odoo import models


class MailComposeMessage(models.TransientModel):
    _name = "mail.compose.message"
    _inherit = ["mail.compose.message", "strictbase.agent.guard.mixin"]

    def action_send_mail(self):
        for wizard in self:
            if not wizard._agent_guard_is_enabled() or wizard._agent_guard_is_confirmed_for("action_send_mail"):
                continue
            if wizard.subtype_is_log:
                continue
            wizard._agent_guard_raise(
                "outbound_client_communication",
                f"{wizard._name}.action_send_mail requires confirmation for non-log sends.",
            )
        return super().action_send_mail()
