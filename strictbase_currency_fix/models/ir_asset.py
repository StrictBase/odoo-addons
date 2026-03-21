import os
import logging
from odoo import models, api
from odoo.modules.module import get_module_path

_logger = logging.getLogger(__name__)


class IrAsset(models.Model):
    _inherit = "ir.asset"

    @api.model
    def _get_asset_paths(self, bundle, assets_params=None):
        asset_paths = super()._get_asset_paths(bundle, assets_params=assets_params)

        target_suffix = "web/static/src/core/currency.js"
        my_module = "strictbase_currency_fix"
        my_relative_path = "static/src/core/currency.js"

        module_root_path = get_module_path(my_module)
        if not module_root_path:
            return asset_paths

        my_full_path = os.path.join(module_root_path, my_relative_path)
        if not os.path.exists(my_full_path):
            _logger.warning("STRICTBASE: Currency override file not found at %s", my_full_path)
            return asset_paths

        try:
            my_last_modified = os.path.getmtime(my_full_path)
        except OSError:
            my_last_modified = 0

        new_paths = []
        for asset in asset_paths:
            # Tuple: (path, full_path, bundle, last_modified)
            current_path = asset[0]
            if current_path and current_path.endswith(target_suffix):
                _logger.info("STRICTBASE: Replacing %s with content from %s", current_path, my_module)

                asset_list = list(asset)

                # Keep [0] as the ORIGINAL path ('web/...') so the module name stays '@web/core/currency'
                asset_list[0] = current_path
                # Read our file content instead of Odoo's
                asset_list[1] = my_full_path
                asset_list[3] = my_last_modified

                new_paths.append(tuple(asset_list))
            else:
                new_paths.append(asset)

        return new_paths
