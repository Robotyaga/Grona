"""Module registry for Grona."""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from .module import ExpertModule


class ModuleRegistry:
    """A simple in-memory catalog of available expert modules."""

    def __init__(self, modules: Iterable[ExpertModule] = ()) -> None:
        self._modules: dict[str, ExpertModule] = {}
        for module in modules:
            self.register(module)

    def register(self, module: ExpertModule) -> None:
        """Add or replace a module by name."""
        self._modules[module.name] = module

    def remove(self, name: str) -> None:
        """Remove a module from the registry."""
        del self._modules[name]

    def get(self, name: str) -> ExpertModule:
        """Return one module by name."""
        return self._modules[name]

    def all(self) -> tuple[ExpertModule, ...]:
        """Return all registered modules in insertion order."""
        return tuple(self._modules.values())

    def names(self) -> tuple[str, ...]:
        """Return registered module names in insertion order."""
        return tuple(self._modules.keys())

    def __iter__(self) -> Iterator[ExpertModule]:
        """Iterate over registered modules in insertion order."""
        return iter(self._modules.values())

    def __len__(self) -> int:
        """Return the number of registered modules."""
        return len(self._modules)
