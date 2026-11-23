# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import McpCodeMigrationCommon


class TestToolSchemas(McpCodeMigrationCommon):
    def _tool(self, model_name, method_name):
        return getattr(self.env[model_name], method_name)._ai_tool

    def test_tool_inputs(self):
        identity = {"element_type", "version", "module", "name"}
        expected = {
            ("odoo.module.branch", "_ai_code_get_next_version_element"): identity,
            ("odoo.module.branch", "_ai_code_get_element_history"): identity,
            ("odoo.module.branch", "_ai_code_get_element_lineage"): identity,
            ("odoo.module.branch", "_ai_code_get_elements_lineage"): {"elements"},
            ("odoo.module.branch", "_ai_code_list_absent_elements"): {
                "module",
                "version",
            },
            ("odoo.code.timeline", "_ai_code_list_timelines"): set(),
            ("odoo.code.timeline", "_ai_code_create_timeline"): identity,
            ("odoo.code.timeline", "_ai_code_update_timeline"): identity,
            ("odoo.code.timeline", "_ai_code_delete_timeline"): identity,
        }
        for (model_name, method_name), required in expected.items():
            schema = self._tool(model_name, method_name)["input_schema"]
            self.assertEqual(set(schema["required"]), required, method_name)

        for model_name, method_name in (
            ("odoo.code.timeline", "_ai_code_list_timelines"),
            ("odoo.module.branch", "_ai_code_list_absent_elements"),
        ):
            limit_schema = self._tool(model_name, method_name)["input_schema"][
                "properties"
            ]["limit"]
            self.assertEqual(limit_schema["maximum"], 500, method_name)

    def test_tool_outputs(self):
        tool = self._tool("odoo.module.branch", "_ai_code_get_next_version_element")
        output_props = tool["output_schema"]["properties"]
        for field in ("state", "next", "timeline"):
            self.assertIn(field, output_props)
        self.assertEqual(
            set(output_props["state"]["enum"]),
            {"unknown", "available", "absent"},
        )

        tool = self._tool("odoo.module.branch", "_ai_code_get_element_history")
        self.assertIn("history", tool["output_schema"]["properties"])

        tool = self._tool("odoo.module.branch", "_ai_code_get_element_lineage")
        lineage_props = tool["output_schema"]["properties"]
        for field in ("start", "target_version", "steps"):
            self.assertIn(field, lineage_props)

        tool = self._tool("odoo.module.branch", "_ai_code_get_elements_lineage")
        self.assertIn("results", tool["output_schema"]["properties"])

        tool = self._tool("odoo.module.branch", "_ai_code_list_absent_elements")
        absent_props = tool["output_schema"]["properties"]
        for field in ("total", "next_version", "counts", "elements"):
            self.assertIn(field, absent_props)
        for field in ("uncovered", "draft", "removed", "moved"):
            self.assertIn(field, absent_props["counts"]["properties"])
        element_props = absent_props["elements"]["items"]["properties"]
        for field in (
            "timeline",
            "data_type",
            "noupdate",
            "is_override",
            "next_defined_in",
        ):
            self.assertIn(field, element_props)

        tool = self._tool("odoo.code.timeline", "_ai_code_list_timelines")
        list_props = tool["output_schema"]["properties"]
        for field in ("total", "timelines"):
            self.assertIn(field, list_props)

        for method_name in (
            "_ai_code_create_timeline",
            "_ai_code_update_timeline",
        ):
            tool = self._tool("odoo.code.timeline", method_name)
            self.assertIn("timeline", tool["output_schema"]["properties"])

        tool = self._tool("odoo.code.timeline", "_ai_code_delete_timeline")
        self.assertIn("deleted", tool["output_schema"]["properties"])

    def test_timeline_write_note_examples(self):
        for method_name in (
            "_ai_code_create_timeline",
            "_ai_code_update_timeline",
        ):
            note_schema = self._tool("odoo.code.timeline", method_name)["input_schema"][
                "properties"
            ]["note"]
            example = note_schema["examples"][0]
            self.assertIn("<p>Source:</p>", example)
            self.assertIn("<ul>", example)
            self.assertIn("<li>", example)
