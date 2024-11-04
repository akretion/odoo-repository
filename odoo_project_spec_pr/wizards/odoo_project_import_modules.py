# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import _, models
from odoo.exceptions import UserError


class OdooProjectImportModules(models.TransientModel):
    _inherit = "odoo.project.import.modules"

    def _get_repository(self, repo_url):
        return self.env["odoo.repository"]._get_or_create_from_url(repo_url)

    def _get_repo_branches(self, repo):
        repo_branches = defaultdict(list)

        if "src" in repo:
            src_branch_commit = repo["src"].split(" ")
            if len(src_branch_commit) == 2:
                src_branch_commit.append(False)
            if len(src_branch_commit) != 3:
                raise UserError(
                    _(
                        "%(src)s: src should be a string with 2 or 3 parts: "
                        "repo branch commit.\n%(repo)r"
                    )
                    % {"src": repo["src"], "repo": repo}
                )
            # Ignoring commit for now
            repo_branches[src_branch_commit[0]].append(src_branch_commit[1])

        elif "remotes" not in repo or "merges" not in repo:
            raise UserError(
                _("You must provide either src or remotes and merges in the spec file")
            )
        else:
            for merge in repo["merges"]:
                remote, ref = (
                    (merge["remote"], str(merge["ref"]))
                    if isinstance(merge, dict)
                    else merge.split(" ")
                )
                if remote not in repo["remotes"]:
                    raise UserError(
                        _("Merge remote %(remote)s is not in remotes %(remotes)s")
                        % ({"remote": remote, "remotes": repo["remotes"]})
                    )
                src = repo["remotes"][remote]
                repo_branches[src].append(ref)

        return repo_branches

    def _import_spec_yaml_repo(self, repo):
        # Create missing branches/forks/repositories/orgs

        repo_branches = self._get_repo_branches(repo)
        # Create the missing repositories/orgs
        odoo_branches = {
            branch.name: branch
            for branch in self.env["odoo.branch"]
            .with_context(active_test=False)
            .search([])
        }
        main_branch = False
        for repo_url, refs in repo_branches.items():
            repository = self._get_repository(repo_url)

            for ref in refs[:]:
                if ref in odoo_branches:
                    branch = odoo_branches[ref]

                    main_branch = (
                        self.env["odoo.repository.branch"]
                        .with_context(active_test=False)
                        .search(
                            [
                                ("repository_id", "=", repository.id),
                                ("branch_id", "=", branch.id),
                            ]
                        )
                    )

                    if not main_branch:
                        main_branch = (
                            self.env["odoo.repository.branch"]
                            .sudo()
                            .create(
                                {"repository_id": repository.id, "branch_id": branch.id}
                            )
                        )
                    refs.remove(ref)
                    break
            if main_branch:
                break

        forked_branches = []
        if main_branch:
            # Remaining refs are forks
            for repo_url, refs in repo_branches.items():
                repository = self._get_repository(repo_url)
                for ref in refs:
                    forked_branch = self.env[
                        "odoo.repository.forked.branch"
                    ]._get_from_ref(repository, ref)

                    if not forked_branch:
                        vals = {
                            "source_repository_id": repository.id,
                        }
                        if ref.startswith("refs/pull/"):
                            ref = ref.split("/")[2]
                            vals["external_id"] = ref
                        else:
                            vals["branch_name"] = ref
                        forked_branch = (
                            self.env["odoo.repository.forked.branch"]
                            .sudo()
                            .create(vals)
                        )
                    forked_branch.sudo().target_branch_id = main_branch
                    forked_branches.append(forked_branch)

        return super()._import_spec_yaml_repo(
            repo, main_branch=main_branch, forked_branches=forked_branches
        )

    def _get_module_branch_from_spec_repo(self, module, main_branch, forked_branches):
        module_branch_model = self.env["odoo.module.branch"]
        args = [
            ("module_id", "=", module.id),
            ("branch_id", "=", self.odoo_project_id.odoo_version_id.id),
        ]
        module_branch = module_branch_model.search(args)
        if not module_branch:
            # Create the module
            branch = self.odoo_project_id.odoo_version_id
            values = {
                "module_id": module.id,
                "branch_id": branch.id,
            }
            module_branch = module_branch_model.sudo().create(values)
        module_branch.sudo().repository_branch_id = main_branch
        module_branch.sudo().repository_forked_branch_ids = [
            (6, 0, [x.id for x in forked_branches])
        ]
        return module_branch

    def _import_spec_yaml_module(self, module, repo, **kwargs):
        main_branch = kwargs.get("main_branch")
        if main_branch:
            forked_branches = kwargs.get("forked_branches")
            module = self._get_module(module)
            module_branch = self._get_module_branch_from_spec_repo(
                module, main_branch, forked_branches
            )
            return self._get_project_module(module_branch, False)

        return super()._import_spec_yaml_module(module, repo, **kwargs)
