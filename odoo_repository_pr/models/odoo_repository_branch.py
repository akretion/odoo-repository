# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class OdooRepositoryBranch(models.Model):
    _inherit = "odoo.repository.branch"

    forked_branch_ids = fields.One2many(
        comodel_name="odoo.repository.forked.branch",
        inverse_name="target_branch_id",
        string="Forked branches",
        readonly=True,
    )
