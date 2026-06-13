"""Guards for the ``stash_graphql_client.types`` flat export surface.

``stash_graphql_client.types`` is the canonical, complete, flat import surface:
every public class/function defined in a submodule must be re-exported and
listed in ``__all__`` so it round-trips under mypy's ``no-implicit-reexport``.
These tests fail if a new public symbol is added to a submodule without being
surfaced, preventing the gap from silently reopening.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil

import pytest

import stash_graphql_client.types as types_pkg


# Symbols that were reachable only via deep submodule paths before being
# surfaced; kept as an explicit regression set.
PREVIOUSLY_UNSURFACED = [
    "FileFilterType",
    "VideoFileFilterInput",
    "ImageFileFilterInput",
    "FingerprintFilterInput",
    "VideoCaption",
    "JobStatusUpdateType",
    "belongs_to",
    "habtm",
    "has_many",
    "has_many_through",
    "fingerprint_resolver",
]


def _public_submodule_symbols() -> list[tuple[str, str]]:
    """Return (module_name, symbol_name) for every public class/function
    *defined* in a ``types`` submodule (not merely re-imported)."""
    found: list[tuple[str, str]] = []
    for mod_info in pkgutil.iter_modules(types_pkg.__path__):
        module = importlib.import_module(f"{types_pkg.__name__}.{mod_info.name}")
        for name, obj in vars(module).items():
            if name.startswith("_"):
                continue
            if not (inspect.isclass(obj) or inspect.isfunction(obj)):
                continue
            if getattr(obj, "__module__", None) != module.__name__:
                continue
            found.append((mod_info.name, name))
    return found


def test_every_public_submodule_symbol_is_in_all() -> None:
    """Every public class/function defined in a submodule is in types.__all__."""
    exported = set(types_pkg.__all__)
    missing = sorted(
        f"{mod}.{name}"
        for mod, name in _public_submodule_symbols()
        if name not in exported
    )
    assert not missing, f"public symbols not surfaced in types.__all__: {missing}"


def test_all_entries_are_importable() -> None:
    """Every name in types.__all__ resolves on the package (no dangling entries)."""
    dangling = sorted(n for n in types_pkg.__all__ if not hasattr(types_pkg, n))
    assert not dangling, f"__all__ entries not importable from types: {dangling}"


def test_all_has_no_duplicates() -> None:
    """types.__all__ contains no duplicate entries."""
    names = types_pkg.__all__
    assert len(names) == len(set(names)), "duplicate entries in types.__all__"


@pytest.mark.parametrize("name", PREVIOUSLY_UNSURFACED)
def test_previously_unsurfaced_symbols_remain_exported(name: str) -> None:
    """Regression: symbols surfaced in the export-consistency pass stay exported."""
    assert name in types_pkg.__all__
    assert hasattr(types_pkg, name)
