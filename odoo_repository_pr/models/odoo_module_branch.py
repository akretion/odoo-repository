# Copyright 2024 Akretion France
# Copyright 2024 Raphaël Reverdy <raphael.reverdy@akretion.com
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class OdooModuleBranch(models.Model):
    _inherit = "odoo.module.branch"

    repository_forked_branch_ids = fields.Many2many(
        comodel_name="odoo.repository.forked.branch",
    )
