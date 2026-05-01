"""Catalog tools: categories, tags, forms.

The ECL XML API does not expose these catalogs directly.  These helpers
sample recent entries and return the unique values seen.  Results are
cached on the shared ECL instance after the first call.
"""

from __future__ import annotations

from ..ecl_client import get_ecl
from ._common import wrap


@wrap
def list_categories(sample_size: int = 500, force_refresh: bool = False) -> list[str]:
    """Return sorted list of categories seen in recent entries.

    Sampled from the most recent ``sample_size`` entries (default 500).
    Cached after the first call; pass ``force_refresh=True`` to re-sample.
    """
    return get_ecl().list_categories(sample_size=sample_size, force_refresh=force_refresh)


@wrap
def list_tags(sample_size: int = 500, force_refresh: bool = False) -> list[str]:
    """Return sorted list of tags seen in recent entries."""
    return get_ecl().list_tags(sample_size=sample_size, force_refresh=force_refresh)


@wrap
def list_forms(sample_size: int = 500, force_refresh: bool = False) -> list[str]:
    """Return sorted list of forms seen in recent entries."""
    return get_ecl().list_forms(sample_size=sample_size, force_refresh=force_refresh)


def register(mcp) -> None:
    mcp.tool(name="ecl_list_categories")(list_categories)
    mcp.tool(name="ecl_list_tags")(list_tags)
    mcp.tool(name="ecl_list_forms")(list_forms)
