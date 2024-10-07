# Copyright 2024 Akretion France
# Copyright 2024 Raphaël Reverdy <raphael.reverdy@akretion.com
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class OdooRepositoryForkedBranch(models.Model):
    _name = "odoo.repository.forked.branch"
    _description = "Forked branch and/or Pull Request"

    name = fields.Char(compute="_compute_name", store=True, index=True)

    # Git related stuff

    branch_name = fields.Char(help="Name of the git branch")

    source_repository_id = fields.Many2one(
        # we may have or not this repo
        comodel_name="odoo.repository",
        ondelete="cascade",
        string="Repository",
        index=True,
    )
    source_repository_url = fields.Char(help="git url")

    # main odoo branch (v16, v18...)
    branch_id = fields.Many2one(
        # do we need this ?
        comodel_name="odoo.branch",
        ondelete="cascade",
        string="Branch",
        required=False,
        index=True,
        readonly=False,
    )

    # modules in the branch / pr
    module_branch_ids = fields.Many2many(
        comodel_name="odoo.module.branch",
        ondelete="cascade",
    )
    description = fields.Text(help="Why theses modules are in this branch")
    # todo: mettre ici le change log ~ les commits messages
    # jusqu'a la branche principale ?
    # add pr

    # Github PR related fields
    pr_name = fields.Char(help="Name on gh")

    target_branch_id = fields.Many2one(
        comodel_name="odoo.repository.branch",
        ondelete="set null",
        string="Repository Branch",
        index=True,
    )

    target_repository_id = fields.Many2one(
        related="target_branch_id.repository_id",
        string="Target Repository",
    )

    pr_url = fields.Char(string="PR URL")

    date_open = fields.Datetime(string="Opening Date", readonly=True)
    date_updated = fields.Datetime(string="Date of Last Update", readonly=True)
    date_closed = fields.Datetime(string="Date of close", readonly=True)
    # reviewer_ids = fields.Many2many("res.users")
    # reviewer_count = fields.Integer(compute="_compute_reviewer_count", readonly=True)
    pr_state = fields.Selection(
        selection=[
            ("open_draft", "Draft"),
            ("open", "Open"),
            ("closed_closed", "Closed"),
            ("closed_merged", "Merged"),
            ("other", "N/A"),
        ],
        help="PR status",
    )
    external_id = fields.Char(index=True, string="Github number", readonly=True)
    author = fields.Char(index=True, readonly=True)
    orga = fields.Char(index=True, readonly=True)
    # need_review = fields.Boolean(string="Review requested")
    # reviewer_ids_nbr = fields.Integer(
    #    compute="_compute_reviewer_ids_nbr", readonly=True, store=True
    # )
    # author_user_id = fields.Many2one(
    #    "res.users", compute="_compute_author_user_id", store=True
    # )

    # _sql_constraints = [
    #     (
    #         "repository_id_branch_anon_id_uniq",
    #         "UNIQUE (source_repository_id, branch_name)",
    #         "This branch already exists for this repository.",
    #     ),
    # ]

    @api.depends("source_repository_id.display_name", "branch_id.name")
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.source_repository_id.display_name}#{rec.branch_name}"
