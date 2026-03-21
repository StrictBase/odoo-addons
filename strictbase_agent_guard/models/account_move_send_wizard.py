from odoo import models


class AccountMoveSendWizard(models.TransientModel):
    _name = "account.move.send.wizard"
    _inherit = ["account.move.send.wizard", "strictbase.agent.guard.mixin"]

    def action_send_and_print(self, allow_fallback_pdf=False):
        for wizard in self:
            if (
                wizard._agent_guard_is_enabled()
                and not wizard._agent_guard_is_confirmed_for("action_send_and_print")
                and wizard.sending_methods
                and "email" in wizard.sending_methods
            ):
                wizard._agent_guard_raise(
                    "outbound_client_communication",
                    f"{wizard._name}.action_send_and_print would email an invoice.",
                )
        return super().action_send_and_print(allow_fallback_pdf=allow_fallback_pdf)
