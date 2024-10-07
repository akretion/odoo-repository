# Copyright 2024 Akretion France
# Copyright 2024 Raphaël Reverdy <raphael.reverdy@akretion.com
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class OdooBranch(models.Model):
    _inherit = "odoo.branch"

    forked_branch_ids = fields.One2many(
        comodel_name="odoo.repository.forked.branch",
        inverse_name="branch_id",
        string="Forked branches",
        readonly=True,
    )
