{
    "name": "StrictBase: Strict Currency Formatting",
    "version": "19.0.1.0.0",
    "author": "StrictBase",
    "depends": ["base", "web"],
    "assets": {
        "web.assets_backend": [
            "strictbase_currency_fix/static/src/js/monetary_override.js",
        ],
    },
    "installable": True,
    "license": "LGPL-3",
    "application": False,
    "post_load": "post_load",
    "category": "Technical",
    "summary": "Locale-correct currency formatting without forced spaces",
}
