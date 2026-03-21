from odoo import api, fields, models, _


class ResourceResource(models.Model):
    _inherit = "resource.resource"

    firstname = fields.Char("First Name", index=True)
    lastname = fields.Char("Last Name", index=True)

    @api.onchange("firstname", "lastname", "resource_type")
    def _onchange_first_last_name(self):
        # Helpful UX: update name live for human resources.
        for resource in self:
            if resource.resource_type != "user":
                continue
            parts = [resource.firstname, resource.lastname]
            derived = " ".join([p for p in parts if p]).strip()
            if derived:
                resource.name = derived

    @api.model_create_multi
    def create(self, vals_list):
        # resource.resource.name is mandatory (DB NOT NULL). Ensure it is always set.
        for vals in vals_list:
            name = (vals.get("name") or "").strip()
            firstname = (vals.get("firstname") or "").strip()
            lastname = (vals.get("lastname") or "").strip()
            resource_type = vals.get("resource_type") or "user"

            derived = " ".join([p for p in [firstname, lastname] if p]).strip()

            if not name:
                if resource_type == "user" and derived:
                    vals["name"] = derived
                else:
                    vals["name"] = _("New Resource")
            else:
                # If a name was provided explicitly but first/last is also given, keep them consistent.
                if resource_type == "user" and (firstname or lastname) and derived and name != derived:
                    vals["name"] = derived

        return super().create(vals_list)

    def write(self, vals):
        # Keep name in sync when first/last are changed for human resources,
        # but don't overwrite if user explicitly sets name in the same write().
        if "name" not in vals and ("firstname" in vals or "lastname" in vals or "resource_type" in vals):
            for resource in self:
                resource_type = vals.get("resource_type", resource.resource_type) or "user"
                if resource_type != "user":
                    continue

                firstname = (vals.get("firstname", resource.firstname) or "").strip()
                lastname = (vals.get("lastname", resource.lastname) or "").strip()
                derived = " ".join([p for p in [firstname, lastname] if p]).strip()
                if derived:
                    # Write via vals so it's a single write() call.
                    vals = dict(vals)
                    vals["name"] = derived
                    break

        return super().write(vals)

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        args = args or []
        if name:
            domain = [
                "|",
                "|",
                ("name", operator, name),
                ("firstname", operator, name),
                ("lastname", operator, name),
            ]
            return self.search(domain + args, limit=limit).name_get()

        return super().name_search(name=name, args=args, operator=operator, limit=limit)
