# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.exceptions import AccessError

from .common import McpCodeMigrationCommon


class TestCodeTimelineSecurity(McpCodeMigrationCommon):
    def test_write_requires_editor_group(self):
        timeline_model = self.env["odoo.code.timeline"]
        values = {
            "element_type": "field",
            "field_id": self.field_name_17.id,
            "next_field_id": self.field_name_18.id,
        }
        with self.assertRaises(AccessError):
            timeline_model.with_user(self.reader_user).create(dict(values))
        with self.assertRaises(AccessError):
            self.timeline_draft.with_user(self.reader_user).write({"note": "hack"})
        with self.assertRaises(AccessError):
            self.timeline_draft.with_user(self.reader_user).unlink()
        # A member of the editor group can create
        record = timeline_model.with_user(self.editor_user).create(
            dict(values, state="draft")
        )
        self.assertTrue(record.exists())

    def test_write_tool_returns_structured_error(self):
        timeline_model = self.env["odoo.code.timeline"]
        result = timeline_model.with_user(self.reader_user)._ai_code_create_timeline(
            element_type="field",
            version="17.0",
            module="test_module_a",
            model="res.partner",
            name="gone_field",
            timeline_type="removed",
        )
        self.assertIsNotNone(result["error"])
        self.assertNotIn("timeline", result)
