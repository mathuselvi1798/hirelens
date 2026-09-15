"""The module registry - the spine of the product.

Modules register themselves at import time with `@register`. The API exposes
whatever is registered, so shipping a new analysis type means adding a package
under `app/analysis/modules/` and nothing else.
"""
import importlib
import pkgutil

from app.analysis.base import AnalysisModule
from app.core.exceptions import ModuleNotFoundError_
from app.core.logging import get_logger

logger = get_logger(__name__)

_REGISTRY: dict[str, AnalysisModule] = {}
_discovered = False


def register(module_cls: type[AnalysisModule]) -> type[AnalysisModule]:
    instance = module_cls()
    if not getattr(instance, "id", None):
        raise ValueError(f"{module_cls.__name__} must define an 'id'.")
    if instance.id in _REGISTRY:
        raise ValueError(f"Duplicate analysis module id: '{instance.id}'.")
    _REGISTRY[instance.id] = instance
    return module_cls


def discover() -> None:
    """Import every package under `app.analysis.modules` exactly once."""
    global _discovered
    if _discovered:
        return

    import app.analysis.modules as modules_pkg

    for info in pkgutil.iter_modules(modules_pkg.__path__):
        importlib.import_module(f"{modules_pkg.__name__}.{info.name}")

    _discovered = True
    logger.info("modules_discovered", modules=sorted(_REGISTRY))


def all_modules() -> list[AnalysisModule]:
    discover()
    return sorted(_REGISTRY.values(), key=lambda m: (m.category, m.title))


def get_module(module_id: str) -> AnalysisModule:
    discover()
    module = _REGISTRY.get(module_id)
    if module is None:
        raise ModuleNotFoundError_(
            f"No analysis module named '{module_id}'.",
            details={"available": sorted(_REGISTRY)},
        )
    return module
