# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import McpCodeCommon


class TestToolSchemas(McpCodeCommon):
    def _tool(self, method_name):
        return getattr(self.env["odoo.module.branch"], method_name)._ai_tool

    def test_tool_inputs(self):
        expected = {
            "_ai_code_search_elements": {"element_type"},
            "_ai_code_get_element_details": {
                "element_type",
                "version",
                "module",
                "name",
            },
        }
        for method_name, required in expected.items():
            schema = self._tool(method_name)["input_schema"]
            self.assertEqual(set(schema["required"]), required, method_name)
            limit_schema = schema["properties"].get("limit")
            if limit_schema:
                self.assertEqual(limit_schema["maximum"], 500, method_name)

        element_type_schema = self._tool("_ai_code_search_elements")["input_schema"][
            "properties"
        ]["element_type"]
        self.assertEqual(
            set(element_type_schema["enum"]),
            {"model", "field", "method", "data"},
        )

    def test_tool_outputs(self):
        tool = self._tool("_ai_code_search_elements")
        element_props = tool["output_schema"]["properties"]["elements"]["items"][
            "properties"
        ]
        for field in (
            "element_type",
            "module",
            "version",
            "model",
            "name",
            "org",
            "repository",
        ):
            self.assertIn(field, element_props)

        tool = self._tool("_ai_code_get_element_details")
        details_props = tool["output_schema"]["properties"]["element"]["properties"]
        for field in (
            "element_type",
            "module",
            "version",
            "model",
            "name",
            "org",
            "repository",
            "fields",
            "methods",
        ):
            self.assertIn(field, details_props)
