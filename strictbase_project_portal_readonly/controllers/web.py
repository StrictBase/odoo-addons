from odoo import http
from odoo.http import request

from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.portal.controllers.web import Home as PortalHome


class StrictBaseReadonlyPortalHome(PortalHome):
    def _has_readonly_support_access(self, partner):
        return bool(request.env["project.project"].sudo().search_count([
            ("is_template", "=", False),
            ("collaborator_ids", "any", [
                ("partner_id", "=", partner.id),
                ("readonly_full_access", "=", True),
            ]),
        ]))

    def _login_redirect(self, uid, redirect=None):
        if not redirect:
            user = request.env["res.users"].sudo().browse(uid)
            if self._has_readonly_support_access(user.partner_id):
                redirect = "/my"
        return super()._login_redirect(uid, redirect=redirect)


class StrictBaseReadonlyAuthSignupHome(AuthSignupHome):
    def get_auth_signup_qcontext(self):
        qcontext = super().get_auth_signup_qcontext()
        qcontext["strictbase_hide_name_on_signup"] = False
        token = qcontext.get("token")
        if not token or qcontext.get("invalid_token"):
            return qcontext

        partner = request.env["res.partner"].sudo()._get_partner_from_token(token)
        if not partner:
            return qcontext

        if self._has_readonly_support_access(partner) and partner.user_ids.filtered(lambda user: user.share):
            qcontext["strictbase_hide_name_on_signup"] = True
            qcontext["name"] = partner.name
        return qcontext
