# Copyright 2024 Akretion France
# Copyright 2024 Raphaël Reverdy <raphael.reverdy@akretion.com
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import os
import re
from datetime import datetime
from urllib.parse import urlparse

import requests

from odoo import api, fields, models

from odoo.addons.odoo_repository.utils import github
from odoo.addons.queue_job.exception import RetryableJobError


def format_date_from_gh(date):
    if not date:
        return False
    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")


class OdooRepository(models.Model):
    _inherit = "odoo.repository"

    source_repository_id = fields.Many2one(
        comodel_name="odoo.repository",
        string="Source Repository",
        compute="_compute_source_repository_id",
        store=True,
    )
    forked_repository_ids = fields.One2many(
        comodel_name="odoo.repository",
        inverse_name="source_repository_id",
        string="Forked Repositories",
    )
    is_fork = fields.Boolean(
        compute="_compute_source_repository_id",
        store=True,
        help="This repo is a forked of another repo",
    )
    forked_branch_ids = fields.One2many(
        comodel_name="odoo.repository.forked.branch",
        inverse_name="source_repository_id",
        string="Forked branches",
        readonly=True,
    )
    last_pr_fetched = fields.Datetime(
        string="Last PR fetched",
        help="Last PRs date fetched from the source repository",
    )

    @api.depends("forked_branch_ids.target_repository_id")
    def _compute_source_repository_id(self):
        for record in self:
            source = record.forked_branch_ids.target_repository_id
            record.source_repository_id = source if source != record else False
            record.is_fork = bool(record.source_repository_id)

    def action_fetch_prs(self):
        """Fetch PRs from the source repository."""
        for record in self:
            if record.repo_type == "github" or record.repo_url.startswith(
                github.GITHUB_URL
            ):
                if record.repo_type != "github":
                    record.repo_type = "github"
                record.with_delay()._action_fetch_prs()

    def _get_or_create_from_url(self, url):
        url = url.replace(".git", "").strip()
        repository = (
            self.env["odoo.repository"]
            .with_context(active_test=False)
            .search([("repo_url", "=", url)])
        )
        if repository:
            return repository

        path_parts = list(filter(None, urlparse(url).path.split("/")))
        org_name, name = path_parts[:2]
        orgs = {
            org.name.lower(): org
            for org in self.env["odoo.repository.org"]
            .with_context(active_test=False)
            .search([])
        }
        org = orgs.get(org_name.lower())
        if not org:
            org = self.env["odoo.repository.org"].sudo().create({"name": org_name})

        return (
            self.env["odoo.repository"]
            .sudo()
            .create({"name": name, "repo_url": url, "org_id": org.id})
        )

    def _action_fetch_prs(self):
        """Fetch PRs from the source repository."""
        self.ensure_one()
        prs = []
        page = 1
        while True:
            try:
                response = github.request(
                    self.env,
                    f"repos/{self.org_id.name}/{self.name}/pulls"
                    f"?state=all&per_page=100&page={page}"
                    "&sort=updated&direction=desc",
                )
            except RuntimeError as exc:
                raise RetryableJobError("Error while looking for PR URL") from exc
            except Exception:
                break

            if not response:
                break

            prs.extend(response)
            if (
                self.last_pr_fetched
                and datetime.strptime(response[-1]["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
                < self.last_pr_fetched
            ):
                break

            page += 1

        for repo_branch in self.branch_ids:
            # Keep only pr for this odoo branch
            branch_prs = [
                pr for pr in prs if pr["base"]["ref"][:4] == repo_branch.branch_id.name
            ]
            for pr in branch_prs:
                self._upsert_forked_branch(pr, repo_branch)

        if prs:
            self.last_pr_fetched = format_date_from_gh(prs[0]["updated_at"])

    def _upsert_forked_branch(self, pr, repo_branch):
        repo_url = (pr["head"]["repo"] or {}).get("html_url")
        if not repo_url:
            return
        repo = self._get_or_create_from_url(repo_url)
        if repo_branch.branch_id.name not in repo.branch_ids.mapped("branch_id.name"):
            self.env["odoo.repository.branch"].create(
                {"branch_id": repo_branch.branch_id.id, "repository_id": repo.id}
            )

        forked_branch = self.env["odoo.repository.forked.branch"]._get_from_ref(
            repo, pr["head"]["ref"]
        )
        if not forked_branch:
            forked_branch = self.env["odoo.repository.forked.branch"]._get_from_ref(
                repo, f"refs/pull/{pr['number']}/head"
            )

        state = pr["state"]
        if state == "open" and pr["draft"]:
            state = "open_draft"
        if state == "closed":
            if pr["merged_at"]:
                state = "closed_merged"
            else:
                state = "closed_closed"

        vals = {
            "branch_name": pr["head"]["ref"],
            "source_repository_id": repo.id,
            "module_branch_ids": [
                (6, 0, self._get_impacted_modules_in_pr(pr, repo_branch.module_ids).ids)
            ],
            "target_branch_id": repo_branch.id,
            "pr_name": pr["title"],
            "pr_url": pr["html_url"],
            "date_open": format_date_from_gh(pr["created_at"]),
            "date_updated": format_date_from_gh(pr["updated_at"]),
            "date_closed": format_date_from_gh(pr["closed_at"]),
            "pr_state": state,
            "external_id": pr["number"],
            "author": pr["user"]["login"],
        }

        if not forked_branch:
            forked_branch = (
                self.env["odoo.repository.forked.branch"].sudo().create(vals)
            )
        else:
            forked_branch.sudo().write(vals)

        return forked_branch

    def _get_impacted_modules_in_pr(self, pr, module_ids):
        # Inspired from https://github.com/akretion/partner-module-information
        # /blob/14.0/module_info_pull_request/models/pull_request.py#L70-L88
        url = pr["diff_url"]
        headers = {}
        key = "odoo_repository_github_token"
        token = self.env["ir.config_parameter"].get_param(key, "") or os.environ.get(
            "GITHUB_TOKEN"
        )
        if token:
            headers.update({"Authorization": f"token {token}"})
        response = requests.get(url, headers=headers, timeout=10)
        matchs = re.findall(r"\+{3,5} b.*", response.text)
        modules = {module.module_name: module for module in module_ids}
        impacted_modules = self.env["odoo.module.branch"]
        for line in matchs:
            # regex get first /module/
            module_name = re.search(r"(?<=/)(\w*)(?=/)", line)
            if not module_name:
                continue
            module_name = module_name.group(0)
            if module_name in modules:
                impacted_modules |= modules[module_name]
        return impacted_modules
