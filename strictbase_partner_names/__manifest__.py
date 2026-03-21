{
    "name": "StrictBase: Split Partner Names",
    "version": "19.0.1.0.0",
    "category": "Tools",
    "summary": "Split partner names into first name and last name fields",
    "author": "StrictBase",
    "depends": ["contacts", "crm"],
    "data": [
        "views/res_partner_views.xml",
        "views/crm_lead_views.xml",
    ],
    "installable": True,
    "license": "LGPL-3",
    "assets": {
        "web.assets_backend": [
            "strictbase_partner_names/static/src/js/create_contact_button_field.js",
            "strictbase_partner_names/static/src/xml/create_contact_button.xml",
        ],
    },
}
