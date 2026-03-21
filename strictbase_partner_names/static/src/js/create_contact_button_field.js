/** @odoo-module **/

import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class CreateContactButtonField extends Component {
    static template = "strictbase_partner_names.CreateContactButton";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
    }

    _getM2OId(value) {
        // Many2one values can be:
        // - false
        // - [id, display_name]
        // - number (id)
        // - object (various shapes depending on the record layer)
        if (!value) {
            return false;
        }
        if (Array.isArray(value)) {
            return value[0];
        }
        if (typeof value === "number") {
            return value;
        }
        if (typeof value === "object") {
            // Common shapes across Odoo versions / layers
            return value.id || value.resId || value.res_id || false;
        }
        return false;
    }

    onKeydown(ev) {
        // Prevent Enter/Space from submitting the quick-create dialog ("Add")
        if (ev.key === "Enter" || ev.key === " ") {
            ev.preventDefault();
            ev.stopPropagation();
            // Trigger the same behavior as clicking the button
            this.onClick(ev);
        }
    }

    async onClick(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        const record = this.props.record;

        // IMPORTANT: In quick create, company is commercial_partner_id
        const companyId = this._getM2OId(record.data.commercial_partner_id);

        if (!companyId) {
            this.notification.add("Select a company first.", { type: "warning" });
            return;
        }

        const firstname = (record.data.contact_firstname || "").trim();
        const lastname = (record.data.contact_lastname || "").trim();

        if (!firstname && !lastname) {
            this.notification.add("Enter a first name or last name.", { type: "warning" });
            return;
        }

        // Create the res.partner contact immediately (like Odoo does for M2O “Create”)
        const displayName = [firstname, lastname].filter((p) => p).join(" ").trim();

        const partnerIds = await this.orm.create("res.partner", [{
            parent_id: companyId,
            is_company: false,
            type: "contact",
            name: displayName,              // IMPORTANT: satisfy base Odoo requirement
            firstname: firstname || false,
            lastname: lastname || false,
        }]);
        const partnerId = Array.isArray(partnerIds) ? partnerIds[0] : partnerIds;

        await record.update({
            // Set M2O in the shape the OWL record expects
            partner_id: { id: partnerId, display_name: displayName },

            // Clear the input fields
            contact_firstname: false,
            contact_lastname: false,

            // Helps your invisibility rule flip immediately
            company_has_contacts: true,
        });

        this.notification.add("Contact created.", { type: "success" });
    }
}

registry.category("fields").add("create_contact_button", {
    component: CreateContactButtonField,
    supportedTypes: ["char"],
});