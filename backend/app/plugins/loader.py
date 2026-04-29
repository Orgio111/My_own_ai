"""Auto-discover plugins under app/plugins/contrib/."""
from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from typing import List

from app.agents.executor import register_tool
from app.plugins.base import Plugin
from app.utils.logger import log

CONTRIB = Path(__file__).parent / "contrib"


def discover() -> List[Plugin]:
    plugins: List[Plugin] = []
    if not CONTRIB.exists():
        CONTRIB.mkdir(parents=True, exist_ok=True)
        (CONTRIB / "__init__.py").write_text("")
        return plugins
    pkg = importlib.import_module("app.plugins.contrib")
    for _, name, _ in pkgutil.iter_modules(pkg.__path__):
        mod = importlib.import_module(f"app.plugins.contrib.{name}")
        for attr in dir(mod):
            obj = getattr(mod, attr)
            if isinstance(obj, type) and issubclass(obj, Plugin) and obj is not Plugin:
                inst = obj()
                inst.on_load()
                for tname, fn in inst.tools().items():
                    register_tool(tname, fn)
                    log.info("plugin.tool.register", plugin=inst.name, tool=tname)
                plugins.append(inst)
    return plugins
