"""Posting tool — only registered when ``ECL_MCP_READ_ONLY=false``.

Destructive: every successful call appends a new entry to the live ECL.
"""

from __future__ import annotations

from typing import Any

from ecl_api import ECLEntry

from ..ecl_client import get_ecl
from ._common import wrap


@wrap
def post_entry(
    category: str,
    text: str,
    formname: str = "default",
    subject: str = "",
    tags: list[str] | None = None,
    fields: dict[str, str] | None = None,
    preformatted: bool = False,
    private: bool = False,
    related_entry_id: int | None = None,
    do_post: bool = False,
) -> dict[str, Any]:
    """Post a new entry to the ECL logbook.

    DESTRUCTIVE: when ``do_post=True`` (the default is False — dry run),
    a real entry is written to the live logbook.  There is no undo.

    Args:
        category: target category (must exist — see ``list_categories``)
        text: free-form body of the entry
        formname: form to use (default ``"default"`` — see ``list_forms``)
        subject: short subject line
        tags: list of tag names to attach (see ``list_tags``)
        fields: extra form fields as ``{"field_name": "value"}``
        preformatted: if True, body is treated as preformatted text
        private: if True, entry is visible only to authenticated users
        related_entry_id: optional ID of an existing entry to link to
        do_post: must be set to True to actually submit. False (the default)
                 returns the prepared XML for inspection.

    Returns ``{"posted": bool, "xml": str, "response": ...}``.  When
    ``do_post=False``, ``response`` is None and ``xml`` is the prepared body.
    """
    entry = ECLEntry(
        category=category,
        tags=tuple(tags or ()),
        formname=formname,
        text=text,
        preformatted=preformatted,
        private=private,
        related_entry=related_entry_id,
    )
    if subject:
        entry._entry.attrib["subject"] = subject  # noqa: SLF001 — no public setter
    if fields:
        entry.set_form_elements(fields)

    xml = entry.show()
    response = get_ecl().post(entry, do_post=do_post)

    return {
        "posted": bool(do_post),
        "xml": xml,
        "response": response,
    }


def register(mcp) -> None:
    mcp.tool(name="ecl_post_entry")(post_entry)
