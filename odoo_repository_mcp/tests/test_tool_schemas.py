# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import McpCommon


class TestToolSchemas(McpCommon):
    def _tool(self, model_name, method_name):
        return getattr(self.env[model_name], method_name)._ai_tool

    def test_module_tool_inputs(self):
        expected = {
            "_ai_module_search": set(),
            "_ai_module_get_details": {"module", "version"},
            "_ai_module_get_dependencies": {"module", "version"},
            "_ai_module_list_versions": {"module"},
        }
        for method_name, required in expected.items():
            schema = self._tool("odoo.module.branch", method_name)["input_schema"]
            self.assertEqual(set(schema["required"]), required, method_name)
            limit_schema = schema["properties"].get("limit")
            if limit_schema:
                self.assertEqual(limit_schema["maximum"], 500, method_name)

    def test_module_tool_outputs(self):
        tool = self._tool("odoo.module.branch", "_ai_module_search")
        module_props = tool["output_schema"]["properties"]["modules"]["items"][
            "properties"
        ]
        for field in (
            "module",
            "version",
            "org",
            "repository",
            "global_dependency_level",
            "non_std_dependency_level",
        ):
            self.assertIn(field, module_props)

        tool = self._tool("odoo.module.branch", "_ai_module_get_details")
        details_props = tool["output_schema"]["properties"]["modules"]["items"][
            "properties"
        ]
        for field in (
            "module",
            "version",
            "repository",
            "manifest_version",
            "global_dependency_level",
            "non_std_dependency_level",
        ):
            self.assertIn(field, details_props)
        self.assertNotIn("branch", details_props)
        self.assertNotIn("org", details_props)
        repository_props = details_props["repository"]["properties"]
        for field in (
            "org",
            "name",
            "repo_url",
            "repo_type",
            "active",
            "last_scanned_commit",
        ):
            self.assertIn(field, repository_props)
        self.assertNotIn("branch", repository_props)
        version_props = details_props["versions"]["items"]["properties"]
        self.assertIn("manifest_version", version_props)
        self.assertNotIn("manifest_value", version_props)

        tool = self._tool("odoo.module.branch", "_ai_module_get_dependencies")
        dependency_props = tool["output_schema"]["properties"]["dependencies"]["items"][
            "properties"
        ]
        for field in (
            "module",
            "version",
            "org",
            "repository",
            "global_dependency_level",
            "non_std_dependency_level",
        ):
            self.assertIn(field, dependency_props)

        tool = self._tool("odoo.module.branch", "_ai_module_list_versions")
        version_props = tool["output_schema"]["properties"]["versions"]["items"][
            "properties"
        ]
        for field in (
            "version",
            "org",
            "repository",
            "manifest_version",
            "has_migration_script",
        ):
            self.assertIn(field, version_props)

    def test_repository_tool_outputs(self):
        tool = self._tool("odoo.branch", "_ai_repo_list_versions")
        version_props = tool["output_schema"]["properties"]["versions"]["items"][
            "properties"
        ]
        for field in ("name", "next", "previous"):
            self.assertIn(field, version_props)

        tool = self._tool("odoo.repository", "_ai_repo_list_repositories")
        repository_props = tool["output_schema"]["properties"]["repositories"]["items"][
            "properties"
        ]
        for field in ("org", "name", "branches", "specific"):
            self.assertIn(field, repository_props)
