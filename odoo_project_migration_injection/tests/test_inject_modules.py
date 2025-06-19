# Copyright 2025 Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.odoo_project.tests import Common


class TestImportModules(Common):
    def test_match_project_repo_module(self):
        # Assign a repository to the project
        self.odoo_repository.odoo_version_id = self.branch1
        self.project.repository_id = self.odoo_repository
        mod0 = "purchase"  # b1, b2
        mod1 = "point_of_sale"  # b1, b2
        mod2 = "storage_backend"  # b1, b2
        mod3 = "fs_attachments"  # b1, b2
        mod4 = "storage_s3"  # b1
        mod5 = "fs_spec"  # b2

        mod1_in_repo = self.wiz_model._get_module(mod1)
        self.wiz_model._get_module(mod2)
        repo_branch1 = self._create_odoo_repository_branch(
            self.odoo_repository, self.branch1
        )
        repo_branch2 = self._create_odoo_repository_branch(
            self.odoo_repository, self.branch2
        )

        # exist in all branches
        for mod in (mod0, mod1, mod2, mod3):
            self._create_odoo_module_branch(
                mod1_in_repo,
                self.branch1,
                specific=True,
                repository_branch_id=repo_branch1.id,
            )
            self._create_odoo_module_branch(
                mod1_in_repo,
                self.branch2,
                specific=True,
                repository_branch_id=repo_branch2.id,
            )

        # exist only in one branch
        self._create_odoo_module_branch(
            mod4,
            self.branch1,
            specific=True,
            repository_branch_id=repo_branch1.id,
        )
        self._create_odoo_module_branch(
            mod5,
            self.branch2,
            specific=True,
            repository_branch_id=repo_branch2.id,
        )

        # expect 3 modules in b1
        # expect 3 modules in b2

        # project has mod0, mod1, mod2, mod4
        self.project.module_ids = (
            mod0,
            mod1,
            mod2,
            mod4,
        )

        # module inject
        # add mod3
        self.project.module_branch_id_to_inject_mig = mod3_b1, mod5_b2

        # remove mod1
        self.project.module_branch_id_to_reject_mig = mod1_b1
