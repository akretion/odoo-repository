# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from typing import Literal

import pydantic

from odoo import models

from ..utils import NullableDict, NullableStr, mcp_tool

# ---------------------------------------------------------------------------
# Pydantic models of the MCP tools
# ---------------------------------------------------------------------------


class ModuleRef(pydantic.BaseModel):
    """Reference to a module on a given Odoo version."""

    module: str = pydantic.Field(description="Module technical name.")
    version: str = pydantic.Field(description="Odoo version.")
    title: NullableStr = pydantic.Field(default=None, description="Descriptive name.")


class ModuleSummary(ModuleRef):
    """Summary of a module on a given Odoo version."""

    org: str = pydantic.Field(description="Organization owning the repository.")
    repository: str = pydantic.Field(description="Repository name.")
    summary: NullableStr = pydantic.Field(default=None, description="Module summary.")
    category: NullableStr = pydantic.Field(default=None, description="Module category.")
    license: NullableStr = pydantic.Field(default=None, description="License.")
    authors: list[str] = pydantic.Field(default=[], description="Author names.")
    development_status: NullableStr = pydantic.Field(
        default=None, description="Development status."
    )
    application: bool = pydantic.Field(
        description="Whether the module is an application."
    )
    installable: bool = pydantic.Field(description="Whether the module is installable.")
    auto_install: bool = pydantic.Field(
        description="Whether the module is auto-installed."
    )
    removed: bool = pydantic.Field(
        description="Whether the module was removed from the repository."
    )
    specific: bool = pydantic.Field(
        description="Whether the module is specific to a project repository."
    )
    is_standard: bool = pydantic.Field(
        description="Whether the module is part of the Odoo standard."
    )
    is_enterprise: bool = pydantic.Field(
        description="Whether the module is an Odoo Enterprise module."
    )
    is_community: bool = pydantic.Field(
        description="Whether the module is a community contribution."
    )
    global_dependency_level: int = pydantic.Field(
        description="Dependency level including all standard Odoo modules."
    )
    non_std_dependency_level: int = pydantic.Field(
        description=(
            "Dependency level excluding standard Odoo modules "
            "(0 for standard Odoo modules)."
        )
    )


class ModuleSearchInput(pydantic.BaseModel):
    """Inputs of the `module_search` tool."""

    name: str | None = pydantic.Field(
        default=None, description="Module technical name (searched with 'ilike')."
    )
    version: str | None = pydantic.Field(
        default=None, description="Odoo version (e.g. '18.0')."
    )
    org: str | None = pydantic.Field(
        default=None, description="Organization owning the repository (e.g. 'OCA')."
    )
    repository: str | None = pydantic.Field(
        default=None, description="Repository name ('name' or 'org/name')."
    )
    category: str | None = pydantic.Field(
        default=None, description="Module category (e.g. 'Tools')."
    )
    author: str | None = pydantic.Field(default=None, description="Module author name.")
    limit: int = pydantic.Field(
        default=20, ge=1, description="Number of modules to return."
    )
    offset: int = pydantic.Field(
        default=0, ge=0, description="Index of the first module to return."
    )


class ModuleSearchOutput(pydantic.BaseModel):
    """Output of the `module_search` tool."""

    error: str | None = None
    total: int
    modules: list[ModuleSummary]


class RepositoryInfo(pydantic.BaseModel):
    """Repository hosting a module."""

    org: str = pydantic.Field(description="Organization owning the repository.")
    name: str = pydantic.Field(description="Repository name.")
    repo_url: str = pydantic.Field(description="Repository URL.")
    repo_type: NullableStr = pydantic.Field(
        default=None, description="Repository type."
    )
    active: bool = pydantic.Field(description="Whether the repository is active.")
    last_scanned_commit: NullableStr = pydantic.Field(
        default=None,
        description="Last commit scanned for the repository branch.",
    )


class ModuleVersionInfo(pydantic.BaseModel):
    """Version (manifest value) of a module, with its commit."""

    name: str
    manifest_value: str
    commit: NullableStr = None
    has_migration_script: bool
    sequence: int


class ModuleDetails(ModuleRef):
    """Full details of a module on a given Odoo version."""

    repository: RepositoryInfo = pydantic.Field(
        description="Repository hosting the module."
    )
    summary: NullableStr = None
    authors: list[str] = []
    maintainers: list[str] = []
    depends: list[str] = []
    global_dependency_level: int = pydantic.Field(
        description="Dependency level including all standard Odoo modules."
    )
    non_std_dependency_level: int = pydantic.Field(
        description=(
            "Dependency level excluding standard Odoo modules "
            "(0 for standard Odoo modules)."
        )
    )
    category: NullableStr = None
    license: NullableStr = None
    manifest_version: NullableStr = pydantic.Field(
        default=None, description="Last version declared in the manifest."
    )
    versions: list[ModuleVersionInfo] = []
    development_status: NullableStr = None
    application: bool
    installable: bool
    auto_install: bool
    external_dependencies: NullableDict = None
    is_standard: bool
    is_enterprise: bool
    is_community: bool
    sloc_python: int
    sloc_xml: int
    sloc_js: int
    sloc_css: int
    last_scanned_commit: NullableStr = None
    addons_path: NullableStr = None
    pr_url: NullableStr = None
    url: NullableStr = None


class ModuleDetailsInput(pydantic.BaseModel):
    """Inputs of the `module_get_details` tool."""

    module: str = pydantic.Field(description="Module technical name.")
    version: str = pydantic.Field(description="Odoo version (e.g. '18.0').")
    repository: str | None = pydantic.Field(
        default=None,
        description=(
            "Restrict to one repository ('name' or 'org/name'). "
            "All the repositories hosting the module otherwise."
        ),
    )


class ModuleDetailsOutput(pydantic.BaseModel):
    """Output of the `module_get_details` tool."""

    error: str | None = None
    modules: list[ModuleDetails]


class DependencySummary(ModuleRef):
    """Summary of a module related to the dependencies of another one.

    Orphaned modules (dependency stubs) have no organization nor repository.
    """

    org: NullableStr = pydantic.Field(
        default=None, description="Organization owning the repository."
    )
    repository: NullableStr = pydantic.Field(
        default=None, description="Repository name."
    )
    global_dependency_level: int = pydantic.Field(
        description="Dependency level including all standard Odoo modules."
    )
    non_std_dependency_level: int = pydantic.Field(
        description=(
            "Dependency level excluding standard Odoo modules "
            "(0 for standard Odoo modules)."
        )
    )


class ModuleDependenciesInput(pydantic.BaseModel):
    """Inputs of the `module_get_dependencies` tool."""

    module: str = pydantic.Field(description="Module technical name.")
    version: str = pydantic.Field(description="Odoo version (e.g. '18.0').")
    repository: str | None = pydantic.Field(
        default=None,
        description=(
            "Restrict to one repository ('name' or 'org/name'). "
            "Required when several repositories host the module."
        ),
    )
    direction: Literal["depends", "reverse"] | None = pydantic.Field(
        default=None,
        description=(
            "'depends' (default) for the dependencies of the module, "
            "'reverse' for the modules depending on it."
        ),
    )
    scope: Literal["direct", "recursive"] | None = pydantic.Field(
        default=None, description="'direct' (default) or 'recursive'."
    )
    org: str | None = pydantic.Field(
        default=None,
        description="Filter the modules by organization (e.g. 'OCA').",
    )
    limit: int = pydantic.Field(
        default=20, ge=1, description="Number of modules to return."
    )
    offset: int = pydantic.Field(
        default=0, ge=0, description="Index of the first module to return."
    )


class ModuleDependenciesOutput(pydantic.BaseModel):
    """Output of the `module_get_dependencies` tool."""

    error: str | None = None
    total: int
    dependencies: list[DependencySummary]


class ModuleVersionRef(pydantic.BaseModel):
    """Version and repository hosting a module."""

    version: str = pydantic.Field(description="Odoo version.")
    org: str = pydantic.Field(description="Organization owning the repository.")
    repository: str = pydantic.Field(description="Repository name.")


class ModuleVersionSummary(ModuleVersionRef):
    """Version of a module, across the Odoo versions and repositories."""

    manifest_version: str = pydantic.Field(
        description="Version declared in the manifest."
    )
    commit: NullableStr = None
    has_migration_script: bool


class ModuleVersionsInput(pydantic.BaseModel):
    """Inputs of the `module_list_versions` tool."""

    module: str = pydantic.Field(description="Module technical name.")


class ModuleVersionsOutput(pydantic.BaseModel):
    """Output of the `module_list_versions` tool."""

    error: str | None = None
    versions: list[ModuleVersionSummary]


class OdooModuleBranch(models.Model):
    _inherit = "odoo.module.branch"

    # ------------------------------------------------------------------
    # Shared glue for the MCP tools
    # ------------------------------------------------------------------

    def _mcp_get_branch(self, name):
        """Return the `odoo.branch` record matching a version name."""
        branch = self.env["odoo.branch"].search([("name", "=", name)], limit=1)
        if not branch:
            raise ValueError(f"Unknown Odoo version: '{name}'.")
        return branch

    def _mcp_get_module(self, name):
        """Return the `odoo.module` record matching a technical name."""
        module = self.env["odoo.module"].search([("name", "=", name)], limit=1)
        if not module:
            raise ValueError(f"Unknown module: '{name}'.")
        return module

    def _mcp_get_repository(self, name):
        """Return the `odoo.repository` record matching 'org/name' or 'name'."""
        repository = self.env["odoo.repository"]
        if "/" in name:
            org_name, _, repo_name = name.partition("/")
            repository = self.env["odoo.repository"]._find_from_org_and_name(
                org_name, repo_name
            )
        else:
            repositories = self.env["odoo.repository"].search([("name", "=", name)])
            if len(repositories) > 1:
                orgs = ", ".join(repositories.mapped("org_id.name"))
                raise ValueError(
                    f"Repository name '{name}' is ambiguous "
                    f"(used by organizations: {orgs}). "
                    "Use the 'org/name' format to disambiguate."
                )
            repository = repositories[:1]
        if not repository:
            raise ValueError(f"Unknown repository: '{name}'.")
        return repository

    def _mcp_get_category(self, name):
        """Return the `odoo.module.category` record matching a name."""
        category = self.env["odoo.module.category"].search(
            [("name", "=", name)], limit=1
        )
        if not category:
            raise ValueError(f"Unknown module category: '{name}'.")
        return category

    def _mcp_get_author(self, name):
        """Return the `odoo.author` record matching a name."""
        author = self.env["odoo.author"].search([("name", "=", name)], limit=1)
        if not author:
            raise ValueError(f"Unknown author: '{name}'.")
        return author

    def _mcp_get_module_branches(self, module, branch, repository=None):
        """Return the `odoo.module.branch` records of a module on a version.

        Orphaned modules (not bound to a repository yet) are excluded, as
        they carry no scanned data.
        """
        domain = [
            ("module_id", "=", module.id),
            ("branch_id", "=", branch.id),
        ]
        if repository:
            domain.append(
                ("repository_id", "=", self._mcp_get_repository(repository).id)
            )
        else:
            domain.append(("repository_id", "!=", False))
        return self.search(domain)

    def _mcp_to_dict(self):
        """Convert module data to a summary dictionary (for search results)."""
        self.ensure_one()
        return {
            "module": self.module_name,
            "version": self.branch_id.name,
            "org": self.org_id.name,
            "repository": self.repository_id.name,
            "title": self.title,
            "summary": self.summary,
            "category": self.category_id.name,
            "license": self.license_id.name,
            "authors": self.author_ids.mapped("name"),
            "development_status": self.development_status_id.name,
            "application": self.application,
            "installable": self.installable,
            "auto_install": self.auto_install,
            "removed": self.removed,
            "specific": self.specific,
            "is_standard": self.is_standard,
            "is_enterprise": self.is_enterprise,
            "is_community": self.is_community,
            "global_dependency_level": self.global_dependency_level,
            "non_std_dependency_level": self.non_std_dependency_level,
        }

    def _mcp_to_dict_short(self):
        """Convert module data to a minimal dictionary (for dependency lists)."""
        self.ensure_one()
        return {
            "module": self.module_name,
            "version": self.branch_id.name,
            "org": self.org_id.name,
            "repository": self.repository_id.name,
            "title": self.title,
            "global_dependency_level": self.global_dependency_level,
            "non_std_dependency_level": self.non_std_dependency_level,
        }

    def _mcp_get_recursive_reverse_dependencies(self, domain=None, _visited=None):
        """Return all the reverse dependencies recursively.

        A domain can be applied to restrict the modules to return, e.g:

        >>> mod._mcp_get_recursive_reverse_dependencies(
        ...     [("org_id.name", "=", "OCA")]
        ... )

        This is the mirror of `_get_recursive_dependencies` for reverse
        dependencies.
        """
        # NOTE: Circular dependencies are allowed
        if not domain:
            domain = []
        if _visited is None:
            _visited = set()
        current_ids = set(self.ids)
        if current_ids.issubset(_visited):
            return self.browse()
        _visited |= current_ids
        # Apply domain and exclude self
        dependencies = (self.reverse_dependency_ids - self).filtered_domain(domain)
        dependency_ids = set(dependencies.ids)
        for dependency in dependencies:
            dependency_ids |= set(
                dependency._mcp_get_recursive_reverse_dependencies(domain, _visited)
                .filtered_domain(domain)
                .ids
            )
        return self.browse(dependency_ids)

    # ------------------------------------------------------------------
    # MCP tools
    # ------------------------------------------------------------------

    @mcp_tool(ModuleSearchInput, ModuleSearchOutput)
    def _ai_module_search(
        self,
        name=None,
        version=None,
        org=None,
        repository=None,
        category=None,
        author=None,
        limit=None,
        offset=None,
    ):
        """Search the modules collected from the scanned repositories."""
        domain = [
            ("repository_id", "!=", False),
            ("branch_id", "!=", False),
        ]
        if name:
            domain.append(("module_name", "ilike", name))
        if version:
            domain.append(("branch_id", "=", self._mcp_get_branch(version).id))
        if org:
            domain.append(
                ("org_id", "=", self.env["odoo.repository"]._mcp_get_org(org).id)
            )
        if repository:
            domain.append(
                ("repository_id", "=", self._mcp_get_repository(repository).id)
            )
        if category:
            domain.append(("category_id", "=", self._mcp_get_category(category).id))
        if author:
            domain.append(("author_ids", "=", self._mcp_get_author(author).id))
        total = self.search_count(domain)
        module_branches = self.search(domain, limit=limit, offset=offset)
        return {
            "total": total,
            "modules": [mb._mcp_to_dict() for mb in module_branches],
        }

    @mcp_tool(ModuleDetailsInput, ModuleDetailsOutput)
    def _ai_module_get_details(self, module=None, version=None, repository=None):
        """Get the full details of a module for a given Odoo version.

        The same module can be hosted by several repositories: one entry
        is returned per hosting repository.
        """
        branch = self._mcp_get_branch(version)
        module_ = self._mcp_get_module(module)
        module_branches = self._mcp_get_module_branches(
            module_, branch, repository=repository
        )
        if not module_branches:
            raise ValueError(
                f"Module '{module}' not found for Odoo version '{version}'."
            )
        modules = []
        for module_branch in module_branches:
            data = module_branch._to_dict()
            repository = data.pop("repository")
            repository.pop("branch")
            manifest_version = data.pop("version")
            data["version"] = data.pop("branch")
            data["manifest_version"] = manifest_version
            data.update(
                {
                    "repository": repository,
                    "url": module_branch.url,
                    "global_dependency_level": (module_branch.global_dependency_level),
                    "non_std_dependency_level": (
                        module_branch.non_std_dependency_level
                    ),
                }
            )
            modules.append(data)
        return {"modules": modules}

    @mcp_tool(ModuleDependenciesInput, ModuleDependenciesOutput)
    def _ai_module_get_dependencies(
        self,
        module=None,
        version=None,
        repository=None,
        direction=None,
        scope=None,
        org=None,
        limit=None,
        offset=None,
    ):
        """Get the dependencies of a module for a given Odoo version."""
        direction = direction or "depends"
        scope = scope or "direct"
        branch = self._mcp_get_branch(version)
        module_ = self._mcp_get_module(module)
        module_branches = self._mcp_get_module_branches(
            module_, branch, repository=repository
        )
        if not module_branches:
            raise ValueError(
                f"Module '{module}' not found for Odoo version '{version}'."
            )
        if len(module_branches) > 1:
            repositories = ", ".join(
                module_branches.mapped("repository_id.display_name")
            )
            raise ValueError(
                f"Module '{module}' is hosted by several repositories "
                f"for Odoo version '{version}': {repositories}. "
                "Please specify the 'repository' input."
            )
        module_branch = module_branches
        if direction == "reverse":
            if scope == "recursive":
                dependencies = module_branch._mcp_get_recursive_reverse_dependencies()
            else:
                dependencies = module_branch.reverse_dependency_ids
        elif scope == "recursive":
            dependencies = module_branch._get_recursive_dependencies()
        else:
            dependencies = module_branch.dependency_ids
        if org:
            dependencies = dependencies.filtered_domain(
                [("org_id", "=", self.env["odoo.repository"]._mcp_get_org(org).id)]
            )
        dependencies = dependencies.sorted("module_name")
        return {
            "total": len(dependencies),
            "dependencies": [
                dependency._mcp_to_dict_short()
                for dependency in dependencies[offset : offset + limit]
            ],
        }

    @mcp_tool(ModuleVersionsInput, ModuleVersionsOutput)
    def _ai_module_list_versions(self, module=None):
        """List the versions of a module across the Odoo versions and
        repositories."""
        module_ = self._mcp_get_module(module)
        module_branches = self.search(
            [
                ("module_id", "=", module_.id),
                ("repository_id", "!=", False),
            ]
        )
        versions = []
        for module_branch in module_branches:
            for version in module_branch.version_ids:
                versions.append(
                    {
                        "version": module_branch.branch_id.name,
                        "org": module_branch.org_id.name,
                        "repository": module_branch.repository_id.name,
                        "manifest_version": version.manifest_value,
                        "commit": version.commit,
                        "has_migration_script": version.has_migration_script,
                    }
                )
        return {"versions": versions}
