{
    "name": "StrictBase: Project Portal Read-Only",
    "version": "19.0.1.1.0",
    "category": "Services/Project",
    "summary": "Full-project read-only portal access for shared projects",
    "author": "StrictBase",
    "depends": ["project", "hr_timesheet", "sale_timesheet", "auth_signup"],
    "data": [
        "views/project_share_wizard_views.xml",
        "views/support_portal_templates.xml",
        "views/auth_signup_templates.xml",
        "views/web_login_templates.xml",
        "security/project_security.xml",
    ],
    "installable": True,
    "license": "LGPL-3",
    "assets": {
        "web.assets_frontend_minimal": [
            "strictbase_project_portal_readonly/static/src/public/auth_password_toggle_patch.js",
        ],
    },
}
