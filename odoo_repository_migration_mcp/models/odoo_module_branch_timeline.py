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

from ..utils import (
    TimelineCreateFields,
    TimelineUpdateFields,
    check_confirmed_timeline_update,
    check_source_of_truth,
)


class Timeline(pydantic.BaseModel):
    """Timeline (rename/replacement proposal) of a module."""

    id: int
    module: str = pydantic.Field(description="Module technical name.")
    version: str = pydantic.Field(
        description="Odoo version of the source module branch."
    )
    timeline_type: Literal["renamed", "replaced"] = pydantic.Field(
        description="'renamed' or 'replaced'."
    )
    state: Literal["draft", "confirmed"] = pydantic.Field(
        description="Review state: 'draft' or 'confirmed'."
    )
    new_module: str = pydantic.Field(description="New module technical name.")
    starting_version: NullableStr = None
    note: NullableStr = pydantic.Field(
        default=None,
        description=(
            "HTML note explaining the module move/replacement; technical "
            "terms are wrapped in '<code>'."
        ),
    )


class ModuleTimelineInput(pydantic.BaseModel):
    """Module, version and repository identifying a module timeline."""

    module: str = pydantic.Field(description="Module technical name.")
    version: str = pydantic.Field(
        description="Odoo version of the source module branch."
    )
    repository: str | None = pydantic.Field(
        default=None, description=REPOSITORY_DESCRIPTION
    )


class ModuleTimelineFilter(pydantic.BaseModel):
    """Optional filters on module timelines."""

    module: str | None = pydantic.Field(
        default=None, description="Module technical name."
    )
    version: str | None = pydantic.Field(
        default=None, description="Filter by the source module Odoo version."
    )
    repository: str | None = pydantic.Field(
        default=None, description="Filter by repository ('name' or 'org/name')."
    )


class TimelineListInput(ModuleTimelineFilter):
    """Inputs of the `migration_list_timelines` tool."""

    state: Literal["draft", "confirmed"] | None = pydantic.Field(
        default=None, description="Filter by review state."
    )
    limit: int | None = pydantic.Field(
        default=None,
        ge=1,
        le=500,
        description=(
            "Number of timelines to return. All matching timelines when omitted."
        ),
    )
    offset: int = pydantic.Field(
        default=0, ge=0, description="Index of the first timeline to return."
    )


class TimelineListOutput(pydantic.BaseModel):
    """Output of the `migration_list_timelines` tool."""

    error: str | None = None
    total: int
    timelines: list[Timeline]


class TimelineCreateInput(ModuleTimelineInput, TimelineCreateFields):
    """Inputs of the `migration_create_timeline` tool."""

    new_module: str = pydantic.Field(description="Technical name of the new module.")
    timeline_type: Literal["renamed", "replaced"] | None = pydantic.Field(
        default=None, description="'renamed' (default) or 'replaced'."
    )


class TimelineOutput(pydantic.BaseModel):
    """Output of the timeline write tools."""

    error: str | None = None
    timeline: Timeline


class TimelineUpdateInput(ModuleTimelineInput, TimelineUpdateFields):
    """Inputs of the `migration_update_timeline` tool."""

    new_module: str | None = pydantic.Field(
        default=None, description="New technical name of the module."
    )
    timeline_type: Literal["renamed", "replaced"] | None = pydantic.Field(
        default=None, description="New type of the timeline."
    )


class TimelineDeleteInput(ModuleTimelineInput):
    """Inputs of the `migration_delete_timeline` tool."""


class TimelineDeletedOutput(pydantic.BaseModel):
    """Output of the `migration_delete_timeline` tool."""

    error: str | None = None
    deleted: bool


class OdooModuleBranchTimeline(models.Model):
    _inherit = "odoo.module.branch.timeline"

    # ------------------------------------------------------------------
    # Shared glue for the MCP tools
    # ------------------------------------------------------------------

    def _mcp_to_dict(self):
        """Convert timeline data to a dictionary."""
        self.ensure_one()
        return {
            "id": self.id,
            "module": self.module_branch_id.module_id.name,
            "version": self.module_branch_id.branch_id.name,
            "timeline_type": self.timeline_type,
            "state": self.state,
            "new_module": self.next_module_id.name,
            "starting_version": self.odoo_version_id.name,
            # The note is stored as HTML: keep the markup and links
            "note": str(self.note) if self.note else None,
        }

    def _mcp_get_module_branch(self, module, version, repository=None):
        """Return the single `odoo.module.branch` of a module on a version.

        Raise an error when the module is not found on this version, or
        when it is hosted by several repositories and no `repository`
        disambiguates.
        """
        module_branch_model = self.env["odoo.module.branch"]
        module_ = module_branch_model._mcp_get_module(module)
        branch = module_branch_model._mcp_get_branch(version)
        module_branches = module_branch_model._mcp_get_module_branches(
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
        return module_branches

    def _mcp_get_timeline(self, module, version, repository=None):
        """Return the timeline of a module on a version."""
        module_branch = self._mcp_get_module_branch(module, version, repository)
        timeline = self.search([("module_branch_id", "=", module_branch.id)])
        if not timeline:
            raise ValueError(
                f"No timeline for module '{module}' on version '{version}'."
            )
        return timeline

    # ------------------------------------------------------------------
    # MCP tools
    # ------------------------------------------------------------------

    @mcp_tool(TimelineListInput, TimelineListOutput)
    def _ai_migration_list_timelines(
        self,
        module=None,
        version=None,
        state=None,
        repository=None,
        limit=None,
        offset=None,
    ):
        """List the module renames/replacements declared in the database."""
        module_branch_model = self.env["odoo.module.branch"]
        domain = []
        if module:
            domain.append(
                (
                    "module_branch_id.module_id",
                    "=",
                    module_branch_model._mcp_get_module(module).id,
                )
            )
        if version:
            domain.append(
                (
                    "module_branch_id.branch_id",
                    "=",
                    module_branch_model._mcp_get_branch(version).id,
                )
            )
        if state:
            domain.append(("state", "=", state))
        if repository:
            domain.append(
                (
                    "repository_id",
                    "=",
                    module_branch_model._mcp_get_repository(repository).id,
                )
            )
        total = self.search_count(domain)
        timelines = self.search(domain, limit=limit, offset=offset)
        return {
            "total": total,
            "timelines": [timeline._mcp_to_dict() for timeline in timelines],
        }

    @mcp_tool(TimelineCreateInput, TimelineOutput)
    def _ai_migration_create_timeline(
        self,
        module=None,
        version=None,
        new_module=None,
        timeline_type=None,
        note=None,
        confirm=None,
        repository=None,
    ):
        """Declare a module rename/replacement, as a draft or confirmed timeline.

        Set 'confirm' to true for a high-confidence rename/replacement with a
        source-of-truth URL in 'note': a confirmed module timeline immediately
        activates the module lineage used by the code absent-elements workflow.
        """
        module_branch_model = self.env["odoo.module.branch"]
        module_branch = self._mcp_get_module_branch(
            module, version, repository=repository
        )
        existing = self.search([("module_branch_id", "=", module_branch.id)])
        if existing:
            raise ValueError(
                f"A timeline already exists for module '{module}' on "
                f"version '{version}'."
            )
        if confirm:
            check_source_of_truth(note)
        timeline = self.create(
            {
                "module_branch_id": module_branch.id,
                "next_module_id": module_branch_model._mcp_get_module(new_module).id,
                "timeline_type": timeline_type or "renamed",
                "note": note or False,
                # Proposal only by default: applied to the analysis once
                # confirmed (by a human, or directly for a high-confidence
                # proposal through the 'confirm' input)
                "state": "draft",
            }
        )
        if confirm:
            timeline.action_confirm()
        return {"timeline": timeline._mcp_to_dict()}

    def _mcp_update_confirmed_timeline_note(
        self, timeline, new_module, timeline_type, note, confirm
    ):
        """Annotate a confirmed module timeline (note only)."""
        check_confirmed_timeline_update(confirm, (new_module, timeline_type), note)
        timeline.write({"note": note})
        return {"timeline": timeline._mcp_to_dict()}

    @mcp_tool(TimelineUpdateInput, TimelineOutput)
    def _ai_migration_update_timeline(
        self,
        module=None,
        version=None,
        new_module=None,
        timeline_type=None,
        note=None,
        confirm=None,
        repository=None,
    ):
        """Update or confirm a draft module timeline proposal.

        The note is HTML; on a confirmed timeline only the note can be
        updated, and it must carry a source URL.
        """
        timeline = self._mcp_get_timeline(module, version, repository)
        if timeline.state != "draft":
            return self._mcp_update_confirmed_timeline_note(
                timeline, new_module, timeline_type, note, confirm
            )
        values = {}
        if new_module is not None:
            if new_module == module:
                raise ValueError("The new module must be different from the module.")
            values["next_module_id"] = (
                self.env["odoo.module.branch"]._mcp_get_module(new_module).id
            )
        if timeline_type is not None:
            values["timeline_type"] = timeline_type
        if note is not None:
            values["note"] = note
        if not values and not confirm:
            raise ValueError(
                "No field to update: provide 'new_module', 'timeline_type' or 'note'."
            )
        if confirm:
            check_source_of_truth(note if note is not None else timeline.note)
        if values:
            timeline.write(values)
        if confirm:
            timeline.action_confirm()
        return {"timeline": timeline._mcp_to_dict()}

    @mcp_tool(TimelineDeleteInput, TimelineDeletedOutput)
    def _ai_migration_delete_timeline(self, module=None, version=None, repository=None):
        """Delete a draft timeline proposal."""
        timeline = self._mcp_get_timeline(module, version, repository)
        if timeline.state != "draft":
            raise ValueError(
                f"The timeline of module '{module}' on version '{version}' "
                "is confirmed: only draft timelines can be deleted "
                "(managed by humans in the UI)."
            )
        timeline.unlink()
        return {"deleted": True}
