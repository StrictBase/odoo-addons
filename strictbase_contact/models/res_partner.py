from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    moodle_website = fields.Char(string="Moodle Website")
    moodle_version = fields.Char(string="Moodle Version")
    git_repo = fields.Char(string="Git Repository")
    hosted_here = fields.Boolean(string="Hosted by StrictBase", default=False)
    main_use_case = fields.Text(string="Main Use Case")
    improvement_suggestions = fields.Text(string="Improvement Suggestions")

    mailgun_implemented = fields.Boolean(string="Mailgun Implemented")
    mailgun_we_pay = fields.Boolean(string="StrictBase pays Mailgun")
    mailgun_access_notes = fields.Char(string="Mailgun Access/Notes")

    esp_implemented = fields.Boolean(string="ESP Implemented")
    esp_we_pay = fields.Boolean(string="StrictBase pays ESP")
    esp_account_access = fields.Boolean(string="StrictBase has ESP account")
