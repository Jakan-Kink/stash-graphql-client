"""Stash client protocols and type definitions.

This module re-exports the main protocol definition for backward compatibility.
All mixins should import from the parent protocols module.
"""

from ..protocols import StashClientProtocol


__all__ = ["StashClientProtocol"]
