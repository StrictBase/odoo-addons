from odoo import Command, api, fields, models


class ProjectShareWizard(models.TransientModel):
    _inherit = "project.share.wizard"

    collaborator_ids = fields.One2many(
        "project.share.collaborator.wizard",
        "parent_wizard_id",
        string="Collaborators",
    )

    def _readonly_collaborator_commands(self, project):
        collaborator_vals_list = []
        collaborator_partner_ids = set()

        for collaborator in project.collaborator_ids:
            collaborator_partner_ids.add(collaborator.partner_id.id)
            if collaborator.readonly_full_access:
                access_mode = "read_all"
            else:
                access_mode = "edit_limited" if collaborator.limited_access else "edit"
            collaborator_vals_list.append({
                "partner_id": collaborator.partner_id.id,
                "partner_name": collaborator.partner_id.display_name,
                "access_mode": access_mode,
            })

        for follower in project.message_partner_ids:
            if follower.partner_share and follower.id not in collaborator_partner_ids:
                collaborator_vals_list.append({
                    "partner_id": follower.id,
                    "partner_name": follower.display_name,
                    "access_mode": "read",
                })

        collaborator_vals_list.sort(key=lambda collaborator: collaborator["partner_name"])
        return [
            Command.create({
                "partner_id": collaborator["partner_id"],
                "access_mode": collaborator["access_mode"],
                "send_invitation": False,
            })
            for collaborator in collaborator_vals_list
        ]

    @api.model
    def default_get(self, field_names):
        result = super().default_get(field_names)
        if not result.get("res_model") or result.get("res_model") != "project.project" or not result.get("res_id"):
            return result

        project = self.env[result["res_model"]].browse(result["res_id"])
        commands = self._readonly_collaborator_commands(project)
        if commands:
            result["collaborator_ids"] = commands
        return result

    @api.model_create_multi
    def create(self, vals_list):
        prepared_vals_list = []
        for vals in vals_list:
            vals = dict(vals)
            if (
                vals.get("res_model") == "project.project"
                and vals.get("res_id")
                and "collaborator_ids" not in vals
            ):
                project = self.env[vals["res_model"]].browse(vals["res_id"])
                commands = self._readonly_collaborator_commands(project)
                if commands:
                    vals["collaborator_ids"] = commands
            prepared_vals_list.append(vals)

        wizards = super().create(prepared_vals_list)
        for wizard in wizards:
            if wizard.res_model != "project.project" or not wizard.res_id:
                continue

            project = wizard.resource_ref
            readonly_partners = wizard.collaborator_ids.filtered(
                lambda collaborator: collaborator.access_mode == "read_all"
            ).partner_id
            if not readonly_partners:
                continue

            existing_by_partner = {
                collaborator.partner_id.id: collaborator
                for collaborator in project.collaborator_ids.filtered(
                    lambda collaborator: collaborator.partner_id in readonly_partners
                )
            }
            commands = []
            for partner in readonly_partners:
                collaborator = existing_by_partner.get(partner.id)
                values = {
                    "limited_access": True,
                    "readonly_full_access": True,
                }
                if collaborator:
                    if (
                        collaborator.limited_access != values["limited_access"]
                        or collaborator.readonly_full_access != values["readonly_full_access"]
                    ):
                        commands.append(Command.update(collaborator.id, values))
                else:
                    commands.append(Command.create({
                        "partner_id": partner.id,
                        **values,
                    }))
            if commands:
                project.write({"collaborator_ids": commands})
            project.tasks.message_unsubscribe(partner_ids=readonly_partners.ids)
        return wizards
