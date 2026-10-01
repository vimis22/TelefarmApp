"""Konfiguration: hvor R og regelmotoren findes."""

from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_WINDOWS_R_ROOTS = (Path(r"C:\Program Files\R"), Path.home() / "AppData" / "Local" / "Programs" / "R")


@dataclass(frozen=True)
class Settings:
    rscript_path: Path | None
    engine_script: Path
    engine_timeout_seconds: float = 30

    @classmethod
    def from_environment(cls) -> Settings:
        return cls(
            rscript_path=find_rscript(),
            engine_script=PROJECT_ROOT / "r" / "engine.R",
            engine_timeout_seconds=float(os.environ.get("TELEFARM_ENGINE_TIMEOUT", 30)),
        )


def find_rscript() -> Path | None:
    """Søger i rækkefølgen: TELEFARM_RSCRIPT → PATH → nyeste R under Program Files."""
    configured = os.environ.get("TELEFARM_RSCRIPT")
    if configured:
        return Path(configured)
    on_path = shutil.which("Rscript")
    if on_path:
        return Path(on_path)
    installations = [
        candidate
        for root in _WINDOWS_R_ROOTS if root.is_dir()
        for candidate in root.glob("R-*/bin/Rscript.exe")
    ]
    return max(installations, key=_r_version, default=None)


def _r_version(rscript: Path) -> tuple[int, ...]:
    match = re.search(r"R-(\d+)\.(\d+)\.(\d+)", str(rscript))
    return tuple(int(part) for part in match.groups()) if match else (0,)
