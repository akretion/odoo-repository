# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields
from odoo.tests.common import TransactionCase


class TestMcpServerLogAutovacuum(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.server = cls.env["mcp.server"].create({"name": "Test MCP Server"})
        cls.key = cls.env["mcp.server.key"].create(
            {
                "name": "Test MCP Key",
                "server_id": cls.server.id,
                "hashed_key": "test-autovacuum-key",
            }
        )

    def _create_log(self, date):
        return (
            self.env["mcp.server.log"]
            .sudo()
            .create(
                {
                    "server_id": self.server.id,
                    "server_key_id": self.key.id,
                    "date": date,
                }
            )
        )

    def test_gc_mcp_server_logs(self):
        now = fields.Datetime.now()
        old_log = self._create_log(fields.Datetime.subtract(now, months=2))
        recent_log = self._create_log(now)
        self.env["mcp.server.log"]._gc_mcp_server_logs()
        self.assertFalse(old_log.exists())
        self.assertTrue(recent_log.exists())

    def test_gc_mcp_server_logs_is_autovacuum(self):
        method = type(self.env["mcp.server.log"])._gc_mcp_server_logs
        self.assertTrue(getattr(method, "_autovacuum", False))
