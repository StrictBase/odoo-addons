from odoo import models


class MailThread(models.AbstractModel):
    _name = "mail.thread"
    _inherit = ["mail.thread", "strictbase.agent.guard.mixin"]

    def _agent_guard_has_external_partners(self, partner_ids):
        if not partner_ids:
            return False
        partners = self.env["res.partner"].browse(partner_ids)
        return any(not partner.user_ids.filtered(lambda user: not user.share) for partner in partners)

    def message_post(self, **kwargs):
        if self._agent_guard_is_enabled() and not self._agent_guard_is_confirmed_for("message_post"):
            partner_ids = kwargs.get("partner_ids") or []
            outgoing_email_to = kwargs.get("outgoing_email_to")
            subtype_xmlid = kwargs.get("subtype_xmlid")
            subtype_id = kwargs.get("subtype_id")
            is_internal_note = subtype_xmlid == "mail.mt_note"
            if not is_internal_note and subtype_id:
                note_id = self.env["ir.model.data"]._xmlid_to_res_id("mail.mt_note")
                is_internal_note = subtype_id == note_id

            if outgoing_email_to:
                self._agent_guard_raise(
                    "outbound_client_communication",
                    f"{self._name}.message_post includes outgoing email recipients.",
                )
            if self._agent_guard_has_external_partners(partner_ids):
                self._agent_guard_raise(
                    "outbound_client_communication",
                    f"{self._name}.message_post targets external partner recipients.",
                )
            if not is_internal_note and kwargs.get("message_type") == "comment":
                self._agent_guard_raise(
                    "outbound_client_communication",
                    f"{self._name}.message_post would post a non-note comment.",
                )
        return super().message_post(**kwargs)
