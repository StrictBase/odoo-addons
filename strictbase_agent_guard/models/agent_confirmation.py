import hashlib
import json
import secrets

from odoo import _, api, fields, models
from odoo.exceptions import AccessError


class StrictBaseAgentConfirmation(models.Model):
    _name = "strictbase.agent.confirmation"
    _description = "Scoped outbound confirmation tokens for agent actions"
    _order = "id desc"

    user_id = fields.Many2one("res.users", required=True, index=True, readonly=True)
    token_digest = fields.Char(required=True, index=True, readonly=True)
    requested_model = fields.Char(required=True, readonly=True)
    requested_method = fields.Char(required=True, readonly=True)
    requested_ids_json = fields.Text(required=True, readonly=True)
    reason = fields.Char(readonly=True)
    expires_at = fields.Datetime(required=True, readonly=True)
    used = fields.Boolean(default=False, readonly=True)
    used_at = fields.Datetime(readonly=True)

    @api.model
    def issue_token(self, model_name, method_name, record_ids=(), reason="outbound_client_communication", ttl_seconds=600):
        self._require_confirmation_approver()
        token = secrets.token_urlsafe(24)
        self.sudo().create({
            "user_id": self.env.user.id,
            "token_digest": self._digest(token),
            "requested_model": model_name,
            "requested_method": method_name,
            "requested_ids_json": self._normalize_ids_json(record_ids),
            "reason": reason,
            "expires_at": fields.Datetime.add(fields.Datetime.now(), seconds=ttl_seconds),
        })
        return token

    @api.model
    def _require_confirmation_approver(self):
        if not self.env.user.has_group("strictbase_agent_guard.group_agent_confirmation_approver"):
            raise AccessError(
                _(
                    "Only users in the Agent Confirmation Approver group may issue outbound confirmation tokens."
                )
            )

    @api.model
    def validate_and_consume(self, token, model_name, method_name, ids=()):
        if not token:
            return False
        confirmation = self.sudo().search([
            ("user_id", "=", self.env.user.id),
            ("token_digest", "=", self._digest(token)),
            ("requested_model", "=", model_name),
            ("requested_method", "=", method_name),
            ("requested_ids_json", "=", self._normalize_ids_json(ids)),
            ("used", "=", False),
            ("expires_at", ">=", fields.Datetime.now()),
        ], limit=1)
        if not confirmation:
            return False
        confirmation.write({
            "used": True,
            "used_at": fields.Datetime.now(),
        })
        return True

    @api.model
    def _digest(self, token):
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @api.model
    def _normalize_ids_json(self, ids):
        normalized = [int(record_id) for record_id in (ids or ())]
        return json.dumps(normalized, separators=(",", ":"))

    @api.autovacuum
    def _gc_consumed_or_expired_confirmations(self):
        self.sudo().search([
            "|",
            ("expires_at", "<", fields.Datetime.now()),
            ("used", "=", True),
        ]).unlink()
