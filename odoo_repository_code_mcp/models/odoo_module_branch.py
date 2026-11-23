# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from typing import Literal

import pydantic

from odoo import models

from odoo.addons.odoo_repository_mcp.utils import (
    REPOSITORY_DESCRIPTION,
    NullableStr,
    mcp_tool,
)

ELEMENT_MODELS = {
    "model": "odoo.module.branch.model",
    "field": "odoo.module.branch.model.field",
    "method": "odoo.module.branch.model.method",
    "data": "odoo.module.branch.data",
}


# ---------------------------------------------------------------------------
# Pydantic models of the MCP tools
# ---------------------------------------------------------------------------


class ElementRef(pydantic.BaseModel):
    """Reference to a code element."""

    element_type: Literal["model", "field", "method", "data"] = pydantic.Field(
        description="'model', 'field', 'method' or 'data'."
    )
    module: str = pydantic.Field(description="Technical module name.")
    version: str = pydantic.Field(description="Odoo version.")
    model: NullableStr = pydantic.Field(
        default=None,
        description="Model the element belongs to (None for model elements).",
    )
    name: str = pydantic.Field(
        description="Element name (the full XML ID for data elements)."
    )


class ElementInput(pydantic.BaseModel):
    """Inputs identifying a code element."""

    element_type: Literal["model", "field", "method", "data"] = pydantic.Field(
        description="Type of the element."
    )
    version: str = pydantic.Field(
        description="Odoo version of the element (e.g. '17.0')."
    )
    module: str = pydantic.Field(description="Technical module name.")
    model: str | None = pydantic.Field(
        default=None,
        description=(
            "Model name the element belongs to (required for fields and methods)."
        ),
    )
    name: str = pydantic.Field(
        description=(
            "Element name (the external ID for data elements, local or fully "
            "qualified)."
        )
    )
    repository: str | None = pydantic.Field(
        default=None, description=REPOSITORY_DESCRIPTION
    )


class ModelFieldSummary(pydantic.BaseModel):
    """Field of a model (summary)."""

    name: str
    field_type: str


class ModelMethodSummary(pydantic.BaseModel):
    """Method of a model (summary)."""

    name: str
    signature: NullableStr = None


class ElementSummary(ElementRef):
    """Summary of a code element."""

    org: NullableStr = pydantic.Field(
        default=None, description="Organization owning the repository."
    )
    repository: NullableStr = pydantic.Field(
        default=None, description="Repository name."
    )
    # Type-specific summary
    model_type: NullableStr = pydantic.Field(
        default=None, description="Model type (for model elements)."
    )
    field_type: NullableStr = pydantic.Field(
        default=None, description="Field type (for field elements)."
    )
    comodel_name: NullableStr = pydantic.Field(
        default=None, description="Comodel name (for relational fields)."
    )
    signature: NullableStr = pydantic.Field(
        default=None, description="Signature (for method elements)."
    )
    xml_id: NullableStr = pydantic.Field(
        default=None, description="External ID (for data elements)."
    )
    data_type: NullableStr = pydantic.Field(
        default=None, description="'data' or 'demo' (for data elements)."
    )


class ElementSearchInput(pydantic.BaseModel):
    """Inputs of the `code_search_elements` tool."""

    element_type: Literal["model", "field", "method", "data"] = pydantic.Field(
        description="Type of the elements to search."
    )
    version: str | None = pydantic.Field(
        default=None, description="Odoo version (e.g. '18.0')."
    )
    module: str | None = pydantic.Field(
        default=None, description="Technical module name."
    )
    model: str | None = pydantic.Field(
        default=None,
        description=(
            "Model name the elements belong to (for fields, methods and data)."
        ),
    )
    name: str | None = pydantic.Field(
        default=None,
        description=(
            "Element name (searched with 'ilike'). For data elements, the "
            "display name, the local XML ID and the full XML ID are searched."
        ),
    )
    repository: str | None = pydantic.Field(
        default=None, description="Filter by repository ('name' or 'org/name')."
    )
    limit: int = pydantic.Field(
        default=20, ge=1, le=500, description="Number of elements to return."
    )
    offset: int = pydantic.Field(
        default=0, ge=0, description="Index of the first element to return."
    )


class ElementSearchOutput(pydantic.BaseModel):
    """Output of the `code_search_elements` tool."""

    error: str | None = None
    total: int
    elements: list[ElementSummary]


class ElementDetails(ElementRef):
    """Full details of a code element."""

    org: NullableStr = None
    repository: NullableStr = None
    # Model elements
    model_type: NullableStr = pydantic.Field(
        default=None, description="Model type (for model elements)."
    )
    order: NullableStr = pydantic.Field(
        default=None, description="Model order (for model elements)."
    )
    inherit: list[str] = pydantic.Field(
        default=[], description="Inherited model names (for model elements)."
    )
    inherits: list[str] = pydantic.Field(
        default=[], description="Delegated model names (for model elements)."
    )
    fields: list[ModelFieldSummary] = pydantic.Field(
        default=[], description="Fields of the model (for model elements)."
    )
    methods: list[ModelMethodSummary] = pydantic.Field(
        default=[], description="Methods of the model (for model elements)."
    )
    # Field elements
    field_type: NullableStr = pydantic.Field(
        default=None, description="Field type (for field elements)."
    )
    comodel_name: NullableStr = pydantic.Field(
        default=None, description="Comodel name (for relational fields)."
    )
    is_relational: bool | None = pydantic.Field(
        default=None, description="Whether the field is relational."
    )
    inverse_method: NullableStr = pydantic.Field(
        default=None, description="Inverse method name (for relational fields)."
    )
    search_method: NullableStr = pydantic.Field(
        default=None, description="Search method name (for relational fields)."
    )
    # Field and method elements
    code: NullableStr = pydantic.Field(
        default=None, description="Source code (for field and method elements)."
    )
    # Method elements
    signature: NullableStr = pydantic.Field(
        default=None, description="Signature (for method elements)."
    )
    # Data elements
    xml_id: NullableStr = pydantic.Field(
        default=None, description="External ID (for data elements)."
    )
    data_type: NullableStr = pydantic.Field(
        default=None, description="'data' or 'demo' (for data elements)."
    )
    noupdate: bool | None = pydantic.Field(
        default=None, description="Whether the data is in noupdate mode."
    )
    loaded: bool | None = pydantic.Field(
        default=None, description="Whether the data is loaded by the module."
    )
    is_override: bool | None = pydantic.Field(
        default=None,
        description=(
            "Whether the data record overrides a record of another module "
            "(for data elements)."
        ),
    )
    overridden_xml_id: NullableStr = pydantic.Field(
        default=None,
        description=(
            "XML ID of the overridden record when 'is_override' is true "
            "(for data elements)."
        ),
    )
    data_json: NullableStr = pydantic.Field(
        default=None, description="JSON data of the record (for data elements)."
    )
    data_xml: NullableStr = pydantic.Field(
        default=None, description="XML source of the record (for data elements)."
    )


class ElementDetailsInput(ElementInput):
    """Inputs of the `code_get_element_details` tool."""


class ElementDetailsOutput(pydantic.BaseModel):
    """Output of the `code_get_element_details` tool."""

    error: str | None = None
    element: ElementDetails


class OdooModuleBranch(models.Model):
    _inherit = "odoo.module.branch"

    # ------------------------------------------------------------------
    # Shared glue for the MCP tools
    # ------------------------------------------------------------------

    def _mcp_get_element_domain(
        self,
        element_type,
        version=None,
        module=None,
        model=None,
        name=None,
        repository=None,
    ):
        """Return the domain to search code elements of a given type."""
        domain = []
        if module:
            domain.append(("module_name", "=", module))
        if version:
            domain.append(("odoo_version_id", "=", self._mcp_get_branch(version).id))
        if repository:
            domain.append(
                ("repository_id", "=", self._mcp_get_repository(repository).id)
            )
        if model:
            domain.append(("odoo_model_name", "=", model))
        if name:
            if element_type == "model":
                domain.append(("odoo_model_name", "ilike", name))
            elif element_type == "data":
                domain.extend(
                    [
                        "|",
                        "|",
                        ("name", "ilike", name),
                        ("xml_id", "ilike", name),
                        ("full_xml_id", "ilike", name),
                    ]
                )
            else:
                domain.append(("name", "ilike", name))
        return domain

    def _mcp_get_element(
        self,
        element_type,
        version,
        module,
        model=None,
        name=None,
        repository=None,
    ):
        """Return the single code element matching the inputs."""
        domain = self._mcp_get_element_domain(
            element_type,
            version=version,
            module=module,
            model=model,
            repository=repository,
        )
        if element_type == "model":
            domain.append(("odoo_model_name", "=", name))
        elif element_type == "data":
            domain.extend(["|", ("full_xml_id", "=", name), ("xml_id", "=", name)])
        else:
            domain.append(("name", "=", name))
        elements = self.env[ELEMENT_MODELS[element_type]].search(domain)
        if not elements:
            context = f" (model '{model}')" if model else ""
            raise ValueError(
                f"No {element_type} '{name}' found for module '{module}' "
                f"on Odoo version '{version}'{context}."
            )
        if len(elements) > 1:
            repositories = ", ".join(elements.mapped("repository_id.display_name"))
            raise ValueError(
                f"The {element_type} '{name}' is defined in several repositories "
                f"for module '{module}' on Odoo version '{version}': "
                f"{repositories}. Please specify the 'repository' input."
            )
        return elements

    # ------------------------------------------------------------------
    # MCP tools
    # ------------------------------------------------------------------

    @mcp_tool(ElementSearchInput, ElementSearchOutput)
    def _ai_code_search_elements(
        self,
        element_type=None,
        version=None,
        module=None,
        model=None,
        name=None,
        repository=None,
        limit=None,
        offset=None,
    ):
        """Search the code elements collected from the scanned repositories."""
        element_model = ELEMENT_MODELS[element_type]
        domain = self._mcp_get_element_domain(
            element_type,
            version=version,
            module=module,
            model=model,
            name=name,
            repository=repository,
        )
        elements = self.env[element_model]
        total = elements.search_count(domain)
        records = elements.search(domain, limit=limit, offset=offset)
        return {
            "total": total,
            "elements": [record._mcp_to_dict() for record in records],
        }

    @mcp_tool(ElementDetailsInput, ElementDetailsOutput)
    def _ai_code_get_element_details(
        self,
        element_type=None,
        version=None,
        module=None,
        name=None,
        model=None,
        repository=None,
    ):
        """Get the full details of a code element."""
        if element_type in ("field", "method") and not model:
            raise ValueError(
                f"The 'model' input is required for {element_type} elements."
            )
        element = self._mcp_get_element(
            element_type,
            version,
            module,
            model=model,
            name=name,
            repository=repository,
        )
        return {"element": element._mcp_get_details()}
