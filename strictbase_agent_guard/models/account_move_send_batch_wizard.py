from odoo import models


class AccountMoveSendBatchWizard(models.TransientModel):
    _name = "account.move.send.batch.wizard"
    _inherit = ["account.move.send.batch.wizard", "strictbase.agent.guard.mixin"]

    def action_send_and_print(self, force_synchronous=False, allow_fallback_pdf=False):
        for wizard in self:
            if (
                wizard._agent_guard_is_enabled()
                and not wizard._agent_guard_is_confirmed_for("action_send_and_print")
                and wizard.summary_data
                and wizard.summary_data.get("email", {}).get("count")
            ):
                wizard._agent_guard_raise(
                    "outbound_client_communication",
                    f"{wizard._name}.action_send_and_print would send invoices in batch.",
                )
        return super().action_send_and_print(
            force_synchronous=force_synchronous,
            allow_fallback_pdf=allow_fallback_pdf,
        )
