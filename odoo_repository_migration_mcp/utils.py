# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import re

import pydantic

SOURCE_OF_TRUTH_PATTERN = re.compile(r"https?://\S+")


def check_source_of_truth(note):
    """Ensure a note carries at least one source of truth URL.

    High-confidence timelines (created or confirmed through the MCP tools)
    must document the upstream change they rely on: a GitHub commit URL,
    an OpenUpgrade migration script URL, ...
    """
    if not note or not SOURCE_OF_TRUTH_PATTERN.search(note):
        raise ValueError(
            "A source of truth URL is required in 'note' to confirm a "
            "timeline (e.g. the GitHub commit or the OpenUpgrade "
            "migration script URL)."
        )


NOTE_DESCRIPTION = (
    "HTML note. Start the visible text with '[HIGHLY-CONFIDENT]' "
    "or '[LESS-CONFIDENT]', explain the change, then end with a "
    "bulleted Source section: "
    "'<p>Source:</p><ul><li><a href=\"URL\">URL</a></li></ul>' "
    "(one '<li>' per link). Put the full URL as link text, commit "
    "first. Wrap every technical term in '<code>...</code>': module, "
    "model, field, method and XML ID names, file paths, apriori.py "
    "and upgrade_analysis.txt entries. Keep version numbers, dates "
    "and prose plain: '<code>' is the only highlighting the "
    "sanitizer keeps ('<span>', 'class' and 'style' are dropped). "
    "Do not use Markdown."
)
NOTE_EXAMPLE = (
    "<p>[HIGHLY-CONFIDENT] <code>mail_preview_base</code> was merged "
    "into <code>mail</code> in 16.0; <code>mail.preview.mixin</code> "
    "became <code>mail.composer.mixin</code>.</p><p>Source:</p>"
    "<ul>"
    '<li><a href="https://github.com/odoo/odoo/commit/abc123">'
    "https://github.com/odoo/odoo/commit/abc123</a></li>"
    '<li><a href="https://github.com/OCA/OpenUpgrade">'
    "https://github.com/OCA/OpenUpgrade</a></li>"
    "</ul>"
)


class TimelineCreateFields(pydantic.BaseModel):
    """Common inputs of the timeline creation tools."""

    note: str | None = pydantic.Field(
        default=None,
        description=NOTE_DESCRIPTION,
        examples=[NOTE_EXAMPLE],
    )
    confirm: bool = pydantic.Field(
        default=False,
        description=(
            "Create the timeline as confirmed instead of draft. Only for "
            "high-confidence proposals: a confirmed timeline immediately "
            "impacts the migration analysis, and a source of truth URL is "
            "required in 'note'."
        ),
    )


class TimelineUpdateFields(pydantic.BaseModel):
    """Common inputs of the timeline update tools."""

    note: str | None = pydantic.Field(
        default=None,
        description=(
            f"{NOTE_DESCRIPTION} On a confirmed timeline, only the note can be updated."
        ),
        examples=[NOTE_EXAMPLE],
    )
    confirm: bool = pydantic.Field(
        default=False,
        description=(
            "Confirm the timeline instead of keeping it as a draft. Only "
            "for high-confidence proposals: a confirmed timeline "
            "immediately impacts the migration analysis, and a source of "
            "truth URL is required in 'note'."
        ),
    )


def check_confirmed_timeline_update(confirm, semantic_values, note):
    """Validate the update of an already confirmed timeline."""
    if confirm:
        raise ValueError(
            "The timeline is already confirmed: 'confirm' is not expected."
        )
    if any(value is not None for value in semantic_values):
        raise ValueError(
            "The timeline is confirmed: only its note can be updated "
            "(semantic fields are managed by humans in the UI)."
        )
    if note is None:
        raise ValueError(
            "The timeline is confirmed: provide 'note' to annotate it; "
            "semantic fields cannot be updated."
        )
    check_source_of_truth(note)
