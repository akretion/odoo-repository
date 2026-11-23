# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class McpServerLog(models.Model):
    _inherit = "mcp.server.log"

    @api.autovacuum
    def _gc_mcp_server_logs(self):
        """Delete MCP server logs older than one month.

        TODO: move this retention policy to the OCA `ai_oca_mcp` module.
        MCP server logs are not MCA-specific; the upstream module does not
        provide any cleanup yet.
        """
        limit_date = fields.Datetime.subtract(fields.Datetime.now(), months=1)
        logs = self.sudo().search(
            [("date", "<", limit_date)], limit=models.GC_UNLINK_LIMIT
        )
        if len(logs) >= models.GC_UNLINK_LIMIT:
            self.env.ref("base.autovacuum_job")._trigger()
        return logs.unlink()
