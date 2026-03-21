from odoo import _
from odoo.exceptions import UserError
from odoo.models import AbstractModel


class StrictBaseAgentGuardMixin(AbstractModel):
    _name = "strictbase.agent.guard.mixin"
    _description = "Shared helpers for StrictBase agent outbound guards"

    def _agent_guard_is_enabled(self):
        return bool(self.env.context.get("agent_mode"))

    def _agent_guard_is_confirmed_for(self, method_name, ids=None):
        token = self.env.context.get("agent_confirmation_token")
        return self.env["strictbase.agent.confirmation"].validate_and_consume(
            token=token,
            model_name=self._name,
            method_name=method_name,
            ids=ids if ids is not None else self.ids,
        )

    def _agent_guard_raise(self, reason, detail):
        raise UserError(
            _(
                "AGENT_CONFIRMATION_REQUIRED\n"
                "reason: %(reason)s\n"
                "detail: %(detail)s",
                reason=reason,
                detail=detail,
            )
        )
