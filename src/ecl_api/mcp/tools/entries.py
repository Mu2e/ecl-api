"""Search and retrieve ECL logbook entries."""

from __future__ import annotations

from typing import Any

from ..ecl_client import get_ecl
from ._common import wrap


@wrap
def search_entries(
    category: str = "",
    after: str = "",
    before: str = "",
    form_name: str = "",
    tag: str = "",
    username: str = "",
    substring: str = "",
    words: str = "",
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Search recent ECL entries with optional filters.

    Args:
        category: restrict to this category (use ``list_categories`` for valid values)
        after: lower time bound. ``"<n>days"``, ``"<n>hours"``, ``"<n>minutes"``,
               or ``"yyyy-mm-dd+hh:mm:ss"``.
        before: upper time bound, same formats as ``after``.
        form_name: restrict to this form
        tag: restrict to entries with this tag
        username: restrict to this author
        substring: free-text substring search (slow — no index)
        words: indexed full-text search
        limit: max number of entries to return (default 50)

    Returns a list of entry dicts. Each dict has at least: id (int), author,
    subject, category, timestamp, form, tags (list[str]), text, and may have
    ``fields`` (dict) when the entry's form has extra fields.
    """
    return get_ecl().search(
        category=category,
        after=after,
        before=before,
        form_name=form_name,
        tag=tag,
        username=username,
        substring=substring,
        words=words,
        limit=limit,
    )


@wrap
def search_entry_ids(
    category: str = "",
    after: str = "",
    before: str = "",
    form_name: str = "",
    tag: str = "",
    username: str = "",
    substring: str = "",
    words: str = "",
    limit: int = 200,
) -> list[int]:
    """Same filters as ``search_entries`` but returns only entry IDs.

    Cheaper than ``search_entries`` when you only need IDs (e.g. to count
    matches or to follow up with ``get_entry`` for specific ones).
    """
    return get_ecl().search(
        category=category,
        after=after,
        before=before,
        form_name=form_name,
        tag=tag,
        username=username,
        substring=substring,
        words=words,
        limit=limit,
        ids_only=True,
    )


@wrap
def get_entry(entry_id: int) -> dict[str, Any]:
    """Fetch a single ECL entry by its numeric ID."""
    return get_ecl().get_entry(entry_id=entry_id)


def register(mcp) -> None:
    mcp.tool()(search_entries)
    mcp.tool()(search_entry_ids)
    mcp.tool()(get_entry)
