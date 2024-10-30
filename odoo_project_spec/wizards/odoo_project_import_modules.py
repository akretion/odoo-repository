# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import yaml

from odoo import fields, models


class OdooProjectImportModules(models.TransientModel):
    _inherit = "odoo.project.import.modules"

    spec_yaml = fields.Text(
        help="Copy/paste your spec.yaml here.",
    )

    def action_import(self):
        if self.spec_yaml:
            project_module_ids = self._action_import_spec_yaml()
            project_module_ids.extend(self._action_import_additional_modules())
            if self.import_missing_dependencies:
                self._action_import_missing_dependencies(project_module_ids)
            return
        return super().action_import()

    def _action_import_spec_yaml(self):
        """Import a fresh list of installed modules into the project."""
        self.odoo_project_id.sudo().project_module_ids = False
        spec = yaml.safe_load(self.spec_yaml)

        project_module_ids = []
        for _key, repo in spec.items():
            project_module_ids.extend(self._import_spec_yaml_repo(repo))

        self.odoo_project_id.sudo().project_module_ids = project_module_ids
        return project_module_ids

    def _import_spec_yaml_repo(self, repo, **kwargs):
        project_module_ids = []
        modules = repo.get("modules", [])
        for module in modules:
            project_module = self._import_spec_yaml_module(module, repo, **kwargs)
            project_module_ids.append(project_module.id)
        return project_module_ids

    def _import_spec_yaml_module(self, module, repo, **kwargs):
        module = self._get_module(module)
        module_branch = self._get_module_branch(module)
        return self._get_project_module(module_branch, False)
