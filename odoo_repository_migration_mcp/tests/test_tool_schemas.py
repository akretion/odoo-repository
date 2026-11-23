# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import McpMigrationCommon


class TestToolSchemas(McpMigrationCommon):
    def _tool(self, model_name, method_name):
        return getattr(self.env[model_name], method_name)._ai_tool

    def test_tool_inputs(self):
        expected = {
            ("odoo.module.branch", "_ai_migration_get_module_status"): {"module"},
            ("odoo.module.branch", "_ai_migration_get_data"): {
                "module",
                "source_version",
                "target_version",
            },
            ("odoo.module.branch.timeline", "_ai_migration_list_timelines"): set(),
            ("odoo.module.branch.timeline", "_ai_migration_create_timeline"): {
                "module",
                "version",
                "new_module",
            },
            ("odoo.module.branch.timeline", "_ai_migration_update_timeline"): {
                "module",
                "version",
            },
            ("odoo.module.branch.timeline", "_ai_migration_delete_timeline"): {
                "module",
                "version",
            },
        }
        for (model_name, method_name), required in expected.items():
            schema = self._tool(model_name, method_name)["input_schema"]
            self.assertEqual(set(schema["required"]), required, method_name)

        list_schema = self._tool(
            "odoo.module.branch.timeline", "_ai_migration_list_timelines"
        )["input_schema"]
        limit_schema = list_schema["properties"]["limit"]
        if "anyOf" in limit_schema:
            limit_schema = next(
                option
                for option in limit_schema["anyOf"]
                if option.get("type") == "integer"
            )
        self.assertEqual(limit_schema["maximum"], 500)

    def test_timeline_tool_outputs(self):
        tool = self._tool("odoo.module.branch", "_ai_migration_get_module_status")
        migration_props = tool["output_schema"]["properties"]["migrations"]["items"][
            "properties"
        ]
        for field in (
            "source_version",
            "target_version",
            "status",
            "renamed_to",
            "replaced_by",
            "pr_url",
        ):
            self.assertIn(field, migration_props)
        self.assertNotIn("source", migration_props)
        self.assertNotIn("target", migration_props)
        self.assertIn("migrate", migration_props["status"]["enum"])

        tool = self._tool("odoo.module.branch", "_ai_migration_get_data")
        data_props = tool["output_schema"]["properties"]["migration"]["properties"]
        for field in (
            "source_version",
            "target_version",
            "process",
            "results",
            "state",
            "pr_url",
        ):
            self.assertIn(field, data_props)
        self.assertNotIn("source_branch", data_props)
        self.assertNotIn("target_branch", data_props)

        tool = self._tool("odoo.module.branch.timeline", "_ai_migration_list_timelines")
        output_props = tool["output_schema"]["properties"]
        self.assertIn("total", output_props)
        self.assertIn("timelines", output_props)
        timeline_props = output_props["timelines"]["items"]["properties"]
        for field in (
            "module",
            "version",
            "timeline_type",
            "state",
            "new_module",
            "note",
        ):
            self.assertIn(field, timeline_props)

    def test_timeline_write_note_examples(self):
        for method_name in (
            "_ai_migration_create_timeline",
            "_ai_migration_update_timeline",
        ):
            note_schema = self._tool("odoo.module.branch.timeline", method_name)[
                "input_schema"
            ]["properties"]["note"]
            example = note_schema["examples"][0]
            self.assertIn("<p>Source:</p>", example)
            self.assertIn("<ul>", example)
            self.assertIn("<li>", example)
