# Copyright 2024 Akretion France
# Copyright 2024 Raphaël Reverdy <raphael.reverdy@akretion.com
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class OdooRepository(models.Model):
    _inherit = "odoo.repository"

    source_repository_id = fields.Many2one(
        comodel_name="odoo.repository",
        ondelete="cascade",
        string="Source Repository",
    )
    # is_fork = fields.Boolean(
    #     compute="_compute_is_fork",
    #     store=True,
    #     help="This repo is a forked of another repo",
    # )

    forked_branch_ids = fields.One2many(
        comodel_name="odoo.repository.anon.branch",
        inverse_name="source_repository_id",
        string="Anon Branches",
    )
