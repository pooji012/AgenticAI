from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "outputs"
STORAGE_DIR = ROOT_DIR / "storage"


@dataclass(frozen=True)
class PipelineConfig:
    bug_threshold: float = 0.55
    feature_threshold: float = 0.50
    spam_threshold: float = 0.45
    critical_keywords: tuple[str, ...] = ("data loss", "disappear", "crash", "cannot login", "can't login")
    high_keywords: tuple[str, ...] = ("login", "sync", "crashes", "invalid token")


DEFAULT_CONFIG = PipelineConfig()
